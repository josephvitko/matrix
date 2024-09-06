import os
import errno
from typing import Dict, List, Any, Optional, Union

import pywintypes
import win32file
import win32security
import ntsecuritycon as con
from fuse import Operations, FuseOSError
import stat
import datetime


class WindowsNTPassthrough(Operations):
    """
    Class that defines FUSE operations for a Windows NT-like passthrough filesystem
    """
    def __init__(self, root: str):
        self.root = root
        self.open_files = {}
        self.reserved_names = ['CON', 'PRN', 'AUX', 'NUL', 'COM1', 'COM2', 'COM3', 'COM4',
                               'COM5', 'COM6', 'COM7', 'COM8', 'COM9', 'LPT1', 'LPT2',
                               'LPT3', 'LPT4', 'LPT5', 'LPT6', 'LPT7', 'LPT8', 'LPT9']

    def _full_path(self, partial: str) -> str:
        if partial.startswith("/"):
            partial = partial[1:]
        path = os.path.join(self.root, partial)
        return path

    def _check_reserved_name(self, path: str) -> None:
        name = os.path.basename(path).upper()
        if name in self.reserved_names or any(name.startswith(f"{rn}.") for rn in self.reserved_names):
            raise FuseOSError(errno.EINVAL)

    def getattr(self, path: str, fh: Optional[int] = None) -> Dict[str, Any]:
        full_path = self._full_path(path)
        st = os.lstat(full_path)
        return {
            'st_mode': st.st_mode,
            'st_ino': st.st_ino,
            'st_dev': st.st_dev,
            'st_nlink': st.st_nlink,
            'st_uid': 0,  # Windows doesn't use uid/gid
            'st_gid': 0,
            'st_size': st.st_size,
            'st_atime': int(st.st_atime),
            'st_mtime': int(st.st_mtime),
            'st_ctime': int(st.st_ctime),
        }

    def readdir(self, path: str, fh: int) -> List[str]:
        full_path = self._full_path(path)
        dirents = ['.', '..']
        if os.path.isdir(full_path):
            dirents.extend(os.listdir(full_path))
        return dirents

    def mkdir(self, path: str, mode: int) -> None:
        full_path = self._full_path(path)
        self._check_reserved_name(full_path)
        try:
            os.mkdir(full_path)

            # Set appropriate Windows permissions
            security_descriptor = win32security.GetFileSecurity(full_path, win32security.DACL_SECURITY_INFORMATION)
            dacl = security_descriptor.GetSecurityDescriptorDacl()

            # Get the SID for the current user
            user_sid = win32security.GetFileSecurity(full_path,
                                                     win32security.OWNER_SECURITY_INFORMATION).GetSecurityDescriptorOwner()

            # Set full control for the owner
            dacl.AddAccessAllowedAce(win32security.ACL_REVISION, con.FILE_ALL_ACCESS, user_sid)

            security_descriptor.SetSecurityDescriptorDacl(1, dacl, 0)
            win32security.SetFileSecurity(full_path, win32security.DACL_SECURITY_INFORMATION, security_descriptor)
        except OSError as e:
            raise FuseOSError(e.errno)

    def rmdir(self, path: str) -> None:
        full_path = self._full_path(path)
        os.rmdir(full_path)

    def create(self, path: str, mode: int, fi: Any = None) -> int:
        full_path = self._full_path(path)
        self._check_reserved_name(full_path)
        try:
            fh = os.open(full_path, os.O_WRONLY | os.O_CREAT, mode)
            self.open_files[fh] = full_path
            return fh
        except OSError as e:
            raise FuseOSError(e.errno)

    def open(self, path: str, flags: int) -> int:
        full_path = self._full_path(path)
        fh = os.open(full_path, flags)
        self.open_files[fh] = full_path
        return fh

    def read(self, path: str, size: int, offset: int, fh: int) -> bytes:
        os.lseek(fh, offset, 0)
        return os.read(fh, size)

    def write(self, path: str, data: bytes, offset: int, fh: int) -> int:
        os.lseek(fh, offset, 0)
        return os.write(fh, data)

    def truncate(self, path: str, length: int, fh: Optional[int] = None) -> None:
        full_path = self._full_path(path)
        with open(full_path, 'r+') as f:
            f.truncate(length)

    def flush(self, path: str, fh: int) -> None:
        return os.fsync(fh)

    def release(self, path: str, fh: int) -> None:
        os.close(fh)
        self.open_files.pop(fh, None)

    def unlink(self, path: str) -> None:
        full_path = self._full_path(path)
        os.unlink(full_path)

    def rename(self, old: str, new: str) -> None:
        full_old = self._full_path(old)
        full_new = self._full_path(new)
        os.rename(full_old, full_new)

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
        stv = os.statvfs(full_path)
        return {
            'f_bsize': stv.f_bsize,
            'f_frsize': stv.f_frsize,
            'f_blocks': stv.f_blocks,
            'f_bfree': stv.f_bfree,
            'f_bavail': stv.f_bavail,
            'f_files': stv.f_files,
            'f_ffree': stv.f_ffree,
            'f_favail': stv.f_favail,
            'f_flag': stv.f_flag,
            'f_namemax': stv.f_namemax
        }

    def __del__(self):
        for fh in list(self.open_files.keys()):
            try:
                os.close(fh)
            except:
                pass
        self.open_files.clear()


def main(mountpoint: str, root: str):
    from fuse import FUSE
    FUSE(WindowsNTPassthrough(root), mountpoint, nothreads=True, foreground=True)


if __name__ == '__main__':
    import sys
    if len(sys.argv) != 3:
        print(f'usage: {sys.argv[0]} <mountpoint> <root>')
        sys.exit(1)
    main(sys.argv[1], sys.argv[2])
