import os
import errno
import logging
import traceback
from typing import Dict, List, Any, Optional, Union

import pywintypes
import win32api
import win32file
import win32security
import ntsecuritycon as con
from fuse import Operations, FuseOSError


class NtOpenFileManager:
    def __init__(self, logger: logging.Logger):
        self.open_files = {}  # Dictionary to store open file handles
        self.logger = logger

    def add(self, path: str, fh: int, flags: int):
        """Add a new open file handle."""
        if fh in self.open_files:
            self.logger.warning(f"File handle {fh} for {path} is already open.")
        self.open_files[fh] = {'path': path, 'flags': flags}
        self.logger.info(f"Added file handle: {fh} for file: {path}")

    def get(self, fh: int):
        """Retrieve file info by file handle."""
        if fh not in self.open_files:
            self.logger.warning(f"Tried to access non-existent file handle: {fh}")
            return None
        return self.open_files[fh]

    def remove(self, fh: int):
        """Remove an open file handle and close the file."""
        if fh in self.open_files:
            try:
                os.close(fh)
                self.logger.info(f"Closed and removed file handle: {fh} for file: {self.open_files[fh]['path']}")
                del self.open_files[fh]
            except OSError as e:
                self.logger.error(f"Error closing file handle {fh}: {str(e)}")
                raise FuseOSError(e.errno)
        else:
            self.logger.warning(f"Tried to remove non-existent file handle: {fh}")

    def is_open(self, fh: int) -> bool:
        """Check if a file handle is currently open."""
        return fh in self.open_files


class WindowsNTPassthrough(Operations):
    def __init__(self, root: str, logger: Optional[logging.Logger] = None):
        self.root = root
        self.file_manager = NtOpenFileManager(logger or self._setup_default_logger())
        self.reserved_names = ['CON', 'PRN', 'AUX', 'NUL', 'COM1', 'COM2', 'COM3', 'COM4',
                               'COM5', 'COM6', 'COM7', 'COM8', 'COM9', 'LPT1', 'LPT2',
                               'LPT3', 'LPT4', 'LPT5', 'LPT6', 'LPT7', 'LPT8', 'LPT9']

        # Set up logging
        self.logger = logger or self._setup_default_logger()
        self.logger.info(f"Initialized WindowsNTPassthrough with root: {root}")

    @staticmethod
    def _setup_default_logger():
        logger = logging.getLogger('WindowsNTPassthrough')
        logger.setLevel(logging.INFO)
        handler = logging.StreamHandler()
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        return logger

    def _full_path(self, partial: str) -> str:
        if partial.startswith("/"):
            partial = partial[1:]
        path = os.path.join(self.root, partial)
        self.logger.debug(f"Full path: {path}")
        return path

    def _check_reserved_name(self, path: str) -> None:
        name = os.path.basename(path).upper()
        if name in self.reserved_names or any(name.startswith(f"{rn}.") for rn in self.reserved_names):
            self.logger.warning(f"Attempted to use reserved name: {name}")
            raise FuseOSError(errno.EINVAL)

    def _set_file_permissions(self, path: str) -> None:
        try:
            self.logger.debug(f"Setting permissions for: {path}")
            security_descriptor = win32security.GetFileSecurity(path, win32security.DACL_SECURITY_INFORMATION)
            dacl = security_descriptor.GetSecurityDescriptorDacl()

            user_sid = win32security.GetFileSecurity(path,
                                                     win32security.OWNER_SECURITY_INFORMATION).GetSecurityDescriptorOwner()

            dacl.AddAccessAllowedAce(win32security.ACL_REVISION, con.FILE_ALL_ACCESS, user_sid)

            security_descriptor.SetSecurityDescriptorDacl(1, dacl, 0)
            win32security.SetFileSecurity(path, win32security.DACL_SECURITY_INFORMATION, security_descriptor)
            self.logger.info(f"Successfully set permissions for: {path}")
        except Exception as e:
            self.logger.error(f"Error setting permissions for {path}: {str(e)}")
            self.logger.error(traceback.format_exc())

    def getattr(self, path: str, fh: Optional[int] = None) -> Dict[str, Any]:
        full_path = self._full_path(path)
        try:
            st = os.lstat(full_path)
            permissions = oct(st.st_mode & 0o777)  # Get file permissions in octal format
            self.logger.info(
                f"File attributes for {path}: mode={permissions}, size={st.st_size}, owner_uid={st.st_uid}, owner_gid={st.st_gid}")
            return {
                'st_mode': st.st_mode,
                'st_ino': st.st_ino,
                'st_dev': st.st_dev,
                'st_nlink': st.st_nlink,
                'st_uid': 0,
                'st_gid': 0,
                'st_size': st.st_size,
                'st_atime': int(st.st_atime),
                'st_mtime': int(st.st_mtime),
                'st_ctime': int(st.st_ctime),
            }
        except FileNotFoundError:
            raise FuseOSError(errno.ENOENT)

    def readdir(self, path: str, fh: int) -> List[str]:
        full_path = self._full_path(path)
        dirents = ['.', '..']
        if os.path.isdir(full_path):
            dirents.extend(os.listdir(full_path))
        return dirents

    def mkdir(self, path: str, mode: int) -> None:
        full_path = self._full_path(path)
        self._check_reserved_name(full_path)
        os.mkdir(full_path)
        self._set_file_permissions(full_path)

    def rmdir(self, path: str) -> None:
        full_path = self._full_path(path)
        os.rmdir(full_path)

    def create(self, path: str, mode: int, fi: Any = None) -> int:
        full_path = self._full_path(path)
        self.logger.info(f"Creating file: {full_path} with mode: {mode}")
        try:
            self._check_reserved_name(full_path)
            fh = os.open(full_path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, mode)
            self._set_file_permissions(full_path)
            self.file_manager.add(full_path, fh, os.O_WRONLY | os.O_CREAT)
            return fh
        except OSError as e:
            if e.errno == errno.EEXIST:
                # If the file already exists, open it in write mode
                fh = os.open(full_path, os.O_WRONLY, mode)
                self.file_manager.add(full_path, fh, os.O_WRONLY)
                return fh
            self.logger.error(f"Error creating file {full_path}: {str(e)}")
            raise FuseOSError(e.errno)

    def open(self, path: str, flags: int) -> int:
        full_path = self._full_path(path)
        self.logger.info(f"Opening file: {full_path} with flags: {flags}")
        try:
            fh = os.open(full_path, flags)
            self.file_manager.add(full_path, fh, flags)
            self.logger.info(f"Successfully opened file: {full_path}, file handle: {fh}")
            self.logger.info(f"Open file handles: {self.file_manager.open_files.keys()}")
            return fh
        except OSError as e:
            self.logger.error(f"Error opening file {full_path}: {str(e)}")
            raise FuseOSError(e.errno)

    def read(self, path: str, size: int, offset: int, fh: int) -> bytes:
        if not self.file_manager.is_open(fh):
            raise FuseOSError(errno.EBADF)  # Bad file descriptor
        os.lseek(fh, offset, 0)
        data = os.read(fh, size)
        self.logger.info(f"Read {len(data)} bytes from file handle {fh}")
        return data

    def write(self, path: str, data: bytes, offset: int, fh: int) -> int:
        if not self.file_manager.is_open(fh):
            raise FuseOSError(errno.EBADF)  # Bad file descriptor
        os.lseek(fh, offset, 0)
        bytes_written = os.write(fh, data)
        self.logger.info(f"Successfully wrote {bytes_written} bytes to {path}")
        return bytes_written

    def truncate(self, path: str, length: int, fh: Optional[int] = None) -> None:
        if fh is not None:
            if not self.file_manager.is_open(fh):
                raise FuseOSError(errno.EBADF)  # Bad file descriptor
            os.ftruncate(fh, length)
        else:
            full_path = self._full_path(path)
            with open(full_path, 'r+') as f:
                f.truncate(length)
        self.logger.info(f"Truncated file: {path} to {length} bytes")

    def flush(self, path: str, fh: int) -> None:
        # Retrieve file information
        file_info = self.file_manager.get(fh)

        if not file_info:
            self.logger.error(f"Tried to flush a non-existent or closed file handle: {fh}")
            raise FuseOSError(errno.EBADF)

        # Only flush if the file was opened with write permissions
        if file_info['flags'] & (os.O_WRONLY | os.O_RDWR):
            try:
                os.fsync(fh)
                self.logger.info(f"Successfully flushed file handle: {fh}")
            except OSError as e:
                self.logger.error(f"Error flushing file handle {fh}: {str(e)}")
                raise FuseOSError(e.errno)
        else:
            self.logger.info(f"Skipping flush for read-only file handle: {fh}")

    def release(self, path: str, fh: int) -> None:
        self.file_manager.remove(fh)

    def fsync(self, path: str, fdatasync: bool, fh: int) -> None:
        if not self.file_manager.is_open(fh):
            raise FuseOSError(errno.EBADF)  # Bad file descriptor
        try:
            if fdatasync:
                os.fdatasync(fh)
            else:
                os.fsync(fh)
            self.logger.info(f"Successfully synced file: {path}, handle: {fh}")
        except OSError as e:
            self.logger.error(f"Error syncing file {path}, handle {fh}: {str(e)}")
            raise FuseOSError(e.errno)

    def unlink(self, path: str) -> None:
        full_path = self._full_path(path)
        self.logger.info(f"Unlinking file: {full_path}")
        try:
            # Close any open handles to the file
            for fh, info in list(self.file_manager.open_files.items()):
                if info['path'] == full_path:
                    self.file_manager.remove(fh)

            os.unlink(full_path)
            self.logger.info(f"Successfully unlinked file: {full_path}")
        except OSError as e:
            self.logger.error(f"Error unlinking file {full_path}: {str(e)}")
            raise FuseOSError(e.errno)

    def rename(self, old: str, new: str) -> None:
        full_old = self._full_path(old)
        full_new = self._full_path(new)
        self.logger.info(f"Renaming file from {full_old} to {full_new}")
        try:
            # Close any open handles to the old file
            for fh, info in list(self.file_manager.open_files.items()):
                if info['path'] == full_old:
                    self.file_manager.remove(fh)

            os.rename(full_old, full_new)
            self._set_file_permissions(full_new)
            self.logger.info(f"Successfully renamed file from {full_old} to {full_new}")
        except OSError as e:
            self.logger.error(f"Error renaming file from {full_old} to {full_new}: {str(e)}")
            raise FuseOSError(e.errno)

    def utimens(self, path: str, times: Optional[Union[tuple[float, float], None]] = None) -> None:
        full_path = self._full_path(path)
        if times:
            atime, mtime = times
            win_time = pywintypes.Time(int(mtime))
            handle = win32file.CreateFile(
                full_path, win32file.GENERIC_WRITE,
                win32file.FILE_SHARE_READ | win32file.FILE_SHARE_WRITE | win32file.FILE_SHARE_DELETE,
                None, win32file.OPEN_EXISTING, 0, None
            )
            try:
                win32file.SetFileTime(handle, None, pywintypes.Time(int(atime)), win_time)
            finally:
                win32file.CloseHandle(handle)
        else:
            os.utime(full_path, None)

    def chmod(self, path: str, mode: int) -> None:
        full_path = self._full_path(path)
        os.chmod(full_path, mode)

    def statfs(self, path: str) -> Dict[str, int]:
        full_path = self._full_path(path)
        root_path = os.path.splitdrive(full_path)[0] + '\\'

        sectors_per_cluster, bytes_per_sector, free_clusters, total_clusters = win32file.GetDiskFreeSpace(root_path)

        block_size = sectors_per_cluster * bytes_per_sector
        total_blocks = total_clusters
        free_blocks = free_clusters

        volume_name, volume_serial_number, max_component_length, sys_flags, fs_name = win32api.GetVolumeInformation(
            root_path)

        return {
            'f_bsize': block_size,
            'f_frsize': block_size,
            'f_blocks': total_blocks,
            'f_bfree': free_blocks,
            'f_bavail': free_blocks,
            'f_files': 0,
            'f_ffree': 0,
            'f_favail': 0,
            'f_flag': sys_flags,
            'f_namemax': max_component_length
        }

    def getxattr(self, path, name, position=0):
        return b''

    def listxattr(self, path):
        return []

    def __del__(self):
        self.logger.info("Destroying WindowsNTPassthrough instance, closing all open files.")
        for fh in list(self.file_manager.open_files.keys()):
            self.file_manager.remove(fh)
        self.logger.info("All file handles successfully closed.")


def main(mountpoint: str, root: str, log_level: str = 'INFO'):
    from fuse import FUSE

    # Set up logging for the main function
    logger = logging.getLogger('WindowsNTPassthrough')
    logger.setLevel(getattr(logging, log_level.upper()))
    handler = logging.StreamHandler()
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    logger.info(f"Initializing FUSE filesystem: mountpoint={mountpoint}, root={root}")
    try:
        FUSE(WindowsNTPassthrough(root, logger), mountpoint, nothreads=False, foreground=True, allow_other=True,
             debug=log_level.upper() == 'DEBUG')
    except Exception as e:
        logger.error(f"Error in main FUSE loop: {str(e)}")
        logger.error(traceback.format_exc())


if __name__ == '__main__':
    import sys
    import argparse

    parser = argparse.ArgumentParser(description='FUSE filesystem for Windows NT Passthrough')
    parser.add_argument('mountpoint', help='Mountpoint for the FUSE filesystem')
    parser.add_argument('root', help='Root directory to be mounted')
    parser.add_argument('--log-level', choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
                        default='INFO', help='Set the logging level')

    args = parser.parse_args()

    main(args.mountpoint, args.root, args.log_level)
