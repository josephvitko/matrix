import threading
from pathlib import Path, PureWindowsPath
from typing import Dict, List, Union, Optional

from winfspy import (
    BaseFileSystemOperations,
    FILE_ATTRIBUTE,
    CREATE_FILE_CREATE_OPTIONS,
    NTStatusObjectNameNotFound,
    NTStatusDirectoryNotEmpty,
    NTStatusNotADirectory,
    NTStatusObjectNameCollision,
    NTStatusAccessDenied,
    NTStatusMediaWriteProtected,
)
from winfspy.plumbing.security_descriptor import SecurityDescriptor
from winfspy.plumbing.win32_filetime import filetime_now

from src.win_tests.file_info import FileInfo
from src.win_tests.obj.file import FileObj
from src.win_tests.obj.folder import FolderObj
from src.win_tests.obj.opened import OpenedObj
from src.win_tests.operation import operation


class InMemoryFileSystemOperations(BaseFileSystemOperations):
    def __init__(self, volume_label: str, read_only: bool = False):
        super().__init__()
        if len(volume_label) > 31:
            raise ValueError("`volume_label` must be 31 characters long max")

        max_file_nodes: int = 1024
        max_file_size: int = 16 * 1024 * 1024
        file_nodes: int = 1

        self._volume_info: Dict[str, Union[int, str]] = {
            "total_size": max_file_nodes * max_file_size,
            "free_size": (max_file_nodes - file_nodes) * max_file_size,
            "volume_label": volume_label,
        }

        self.read_only: bool = read_only
        self._root_path: PureWindowsPath = PureWindowsPath("/")
        self._root_obj: FolderObj = FolderObj(
            self._root_path,
            FILE_ATTRIBUTE.FILE_ATTRIBUTE_DIRECTORY,
            SecurityDescriptor.from_string("O:BAG:BAD:P(A;;FA;;;SY)(A;;FA;;;BA)(A;;FA;;;WD)"),
        )
        self._entries: Dict[PureWindowsPath, Union[FileObj, FolderObj]] = {self._root_path: self._root_obj}
        self._thread_lock: threading.Lock = threading.Lock()

    # Debugging helpers

    def _create_directory(self, path: Union[str, PureWindowsPath]) -> None:
        path = self._root_path / path
        obj = FolderObj(
            path,
            FILE_ATTRIBUTE.FILE_ATTRIBUTE_DIRECTORY,
            self._root_obj.security_descriptor,
        )
        self._entries[path] = obj

    def _import_files(self, file_path: Union[str, Path]) -> None:
        file_path = Path(file_path)
        path = self._root_path / file_path.name
        obj = FileObj(
            path,
            FILE_ATTRIBUTE.FILE_ATTRIBUTE_ARCHIVE,
            self._root_obj.security_descriptor,
        )
        self._entries[path] = obj
        obj.write(file_path.read_bytes(), 0, False)

    # Winfsp operations

    @operation
    def get_volume_info(self) -> Dict[str, Union[int, str]]:
        return self._volume_info

    @operation
    def set_volume_label(self, volume_label: str) -> None:
        self._volume_info["volume_label"] = volume_label

    @operation
    def get_security_by_name(self, file_name: str) -> tuple[FILE_ATTRIBUTE, int, int]:
        file_name = PureWindowsPath(file_name)

        # Retrieve file
        try:
            file_obj = self._entries[file_name]
        except KeyError:
            raise NTStatusObjectNameNotFound()

        return (
            file_obj.attributes,
            file_obj.security_descriptor.handle,
            file_obj.security_descriptor.size,
        )

    @operation
    def create(
            self,
            file_name: str,
            create_options: int,
            granted_access: int,
            file_attributes: FILE_ATTRIBUTE,
            security_descriptor: SecurityDescriptor,
            allocation_size: int,
    ) -> OpenedObj:
        if self.read_only:
            raise NTStatusMediaWriteProtected()

        file_name = PureWindowsPath(file_name)

        # Retrieve file
        try:
            parent_file_obj = self._entries[file_name.parent]
            if isinstance(parent_file_obj, FileObj):
                raise NTStatusNotADirectory()
        except KeyError:
            raise NTStatusObjectNameNotFound()

        # File/Folder already exists
        if file_name in self._entries:
            raise NTStatusObjectNameCollision()

        if create_options & CREATE_FILE_CREATE_OPTIONS.FILE_DIRECTORY_FILE:
            file_obj = self._entries[file_name] = FolderObj(
                file_name, file_attributes, security_descriptor
            )
        else:
            file_obj = self._entries[file_name] = FileObj(
                file_name,
                file_attributes,
                security_descriptor,
                allocation_size,
            )

        return OpenedObj(file_obj)

    @operation
    def get_security(self, file_context: OpenedObj) -> SecurityDescriptor:
        return file_context.file_obj.security_descriptor

    @operation
    def set_security(self, file_context: OpenedObj, security_information: int,
                     modification_descriptor: SecurityDescriptor) -> None:
        if self.read_only:
            raise NTStatusMediaWriteProtected()

        new_descriptor = file_context.file_obj.security_descriptor.evolve(
            security_information, modification_descriptor
        )
        file_context.file_obj.security_descriptor = new_descriptor

    @operation
    def rename(self, file_context: OpenedObj, file_name: str, new_file_name: str, replace_if_exists: bool) -> None:
        if self.read_only:
            raise NTStatusMediaWriteProtected()

        file_name = PureWindowsPath(file_name)
        new_file_name = PureWindowsPath(new_file_name)

        # Retrieve file
        try:
            file_obj = self._entries[file_name]
        except KeyError:
            raise NTStatusObjectNameNotFound()

        if new_file_name in self._entries:
            # Case-sensitive comparison
            if new_file_name.name != self._entries[new_file_name].path.name:
                pass
            elif not replace_if_exists:
                raise NTStatusObjectNameCollision()
            elif not isinstance(file_obj, FileObj):
                raise NTStatusAccessDenied()

        for entry_path in list(self._entries):
            try:
                relative = entry_path.relative_to(file_name)
                new_entry_path = new_file_name / relative
                entry = self._entries.pop(entry_path)
                entry.path = new_entry_path
                self._entries[new_entry_path] = entry
            except ValueError:
                continue

    @operation
    def open(self, file_name: str, create_options: int, granted_access: int) -> OpenedObj:
        file_name = PureWindowsPath(file_name)

        # Retrieve file
        try:
            file_obj = self._entries[file_name]
        except KeyError:
            raise NTStatusObjectNameNotFound()

        return OpenedObj(file_obj)

    @operation
    def close(self, file_context: OpenedObj) -> None:
        pass

    @operation
    def get_file_info(self, file_context: OpenedObj) -> Dict[str, Union[int, FILE_ATTRIBUTE]]:
        return file_context.file_obj.get_file_info()

    @operation
    def set_basic_info(
            self,
            file_context: OpenedObj,
            file_attributes: FILE_ATTRIBUTE,
            creation_time: Optional[int],
            last_access_time: Optional[int],
            last_write_time: Optional[int],
            change_time: Optional[int],
            file_info: Dict[str, Union[int, FILE_ATTRIBUTE]],
    ) -> Dict[str, Union[int, FILE_ATTRIBUTE]]:
        if self.read_only:
            raise NTStatusMediaWriteProtected()

        file_obj = file_context.file_obj
        if file_attributes != FILE_ATTRIBUTE.INVALID_FILE_ATTRIBUTES:
            file_obj.attributes = file_attributes
        if creation_time:
            file_obj.creation_time = creation_time
        if last_access_time:
            file_obj.last_access_time = last_access_time
        if last_write_time:
            file_obj.last_write_time = last_write_time
        if change_time:
            file_obj.change_time = change_time

        return file_obj.get_file_info()

    @operation
    def set_file_size(self, file_context: OpenedObj, new_size: int, set_allocation_size: bool) -> None:
        if self.read_only:
            raise NTStatusMediaWriteProtected()

        if not isinstance(file_context.file_obj, FileObj):
            raise NTStatusNotADirectory()

        if set_allocation_size:
            file_context.file_obj.set_allocation_size(new_size)
        else:
            file_context.file_obj.set_file_size(new_size)

    @operation
    def can_delete(self, file_context: OpenedObj, file_name: str) -> None:
        file_name = PureWindowsPath(file_name)

        # Retrieve file
        try:
            file_obj = self._entries[file_name]
        except KeyError:
            raise NTStatusObjectNameNotFound

        if isinstance(file_obj, FolderObj):
            for entry in self._entries.keys():
                try:
                    if entry.relative_to(file_name).parts:
                        raise NTStatusDirectoryNotEmpty()
                except ValueError:
                    continue

    @operation
    def read_directory(self, file_context: OpenedObj, marker: Optional[str]) -> List[FileInfo]:
        entries: List[FileInfo] = []
        file_obj = file_context.file_obj

        # Not a directory
        if isinstance(file_obj, FileObj):
            raise NTStatusNotADirectory()

        # The "." and ".." should ONLY be included if the queried directory is not root
        if file_obj.path != self._root_path:
            parent_obj = self._entries[file_obj.path.parent]
            entries.append({"file_name": ".", **file_obj.get_file_info()})
            entries.append({"file_name": "..", **parent_obj.get_file_info()})

        # Loop over all entries
        for entry_path, entry_obj in self._entries.items():
            try:
                relative = entry_path.relative_to(file_obj.path)
            # Filter out unrelated entries
            except ValueError:
                continue
            # Filter out ourself or our grandchildren
            if len(relative.parts) != 1:
                continue
            # Add direct chidren to the entry list
            entries.append({"file_name": entry_path.name, **entry_obj.get_file_info()})

        # Sort the entries
        entries = sorted(entries, key=lambda x: x["file_name"])

        # No filtering to apply
        if marker is None:
            return entries

        # Filter out all results before the marker
        for i, entry in enumerate(entries):
            if entry["file_name"] == marker:
                return entries[i + 1:]

        return []

    @operation
    def get_dir_info_by_name(self, file_context: OpenedObj, file_name: str) -> FileInfo:
        path = file_context.file_obj.path / file_name
        try:
            entry_obj = self._entries[path]
        except KeyError:
            raise NTStatusObjectNameNotFound()

        return {"file_name": file_name, **entry_obj.get_file_info()}

    @operation
    def read(self, file_context: OpenedObj, offset: int, length: int) -> bytes:
        if not isinstance(file_context.file_obj, FileObj):
            raise NTStatusNotADirectory()
        return file_context.file_obj.read(offset, length)

    @operation
    def write(self, file_context: OpenedObj, buffer: bytes, offset: int, write_to_end_of_file: bool,
              constrained_io: bool) -> int:
        if self.read_only:
            raise NTStatusMediaWriteProtected()

        if not isinstance(file_context.file_obj, FileObj):
            raise NTStatusNotADirectory()

        if constrained_io:
            return file_context.file_obj.constrained_write(buffer, offset)
        else:
            return file_context.file_obj.write(buffer, offset, write_to_end_of_file)

    @operation
    def cleanup(self, file_context: OpenedObj, file_name: Optional[str], flags: int) -> None:
        if self.read_only:
            raise NTStatusMediaWriteProtected()

        # TODO: expose FspCleanupDelete & friends
        FspCleanupDelete = 0x01
        FspCleanupSetAllocationSize = 0x02
        FspCleanupSetArchiveBit = 0x10
        FspCleanupSetLastAccessTime = 0x20
        FspCleanupSetLastWriteTime = 0x40
        FspCleanupSetChangeTime = 0x80
        file_obj = file_context.file_obj

        # Delete
        if flags & FspCleanupDelete:
            # Check for non-empty directory
            if any(key.parent == file_obj.path for key in self._entries):
                return

            # Delete immediately
            try:
                del self._entries[file_obj.path]
            except KeyError:
                raise NTStatusObjectNameNotFound()

        # Resize
        if flags & FspCleanupSetAllocationSize and isinstance(file_obj, FileObj):
            file_obj.adapt_allocation_size(file_obj.file_size)

        # Set archive bit
        if flags & FspCleanupSetArchiveBit and isinstance(file_obj, FileObj):
            file_obj.attributes |= FILE_ATTRIBUTE.FILE_ATTRIBUTE_ARCHIVE

        # Set last access time
        if flags & FspCleanupSetLastAccessTime:
            file_obj.last_access_time = filetime_now()

        # Set last write time
        if flags & FspCleanupSetLastWriteTime:
            file_obj.last_write_time = filetime_now()

        # Set change time
        if flags & FspCleanupSetChangeTime:
            file_obj.change_time = filetime_now()

    @operation
    def overwrite(
            self, file_context: OpenedObj, file_attributes: FILE_ATTRIBUTE, replace_file_attributes: bool,
            allocation_size: int
    ) -> None:
        if self.read_only:
            raise NTStatusMediaWriteProtected()

        file_obj = file_context.file_obj

        if not isinstance(file_obj, FileObj):
            raise NTStatusNotADirectory()

        # File attributes
        file_attributes |= FILE_ATTRIBUTE.FILE_ATTRIBUTE_ARCHIVE
        if replace_file_attributes:
            file_obj.attributes = file_attributes
        else:
            file_obj.attributes |= file_attributes

        # Allocation size
        file_obj.set_allocation_size(allocation_size)

        # Set times
        now = filetime_now()
        file_obj.last_access_time = now
        file_obj.last_write_time = now
        file_obj.change_time = now

    @operation
    def flush(self, file_context: Optional[OpenedObj]) -> None:
        pass
