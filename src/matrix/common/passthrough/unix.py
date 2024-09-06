import errno
import os
from typing import Dict, List, Union, Optional, Iterator

from fuse import Operations, FuseOSError


class UnixPassthrough(Operations):
    """
    Class that defines FUSE operations for a Unix-like passthrough filesystem
    """

    def access(self, path: str, amode: int) -> None:
        if not os.access(path, amode):
            raise FuseOSError(errno.EACCES)

    def chmod(self, path: str, mode: int) -> None:
        return os.chmod(path, mode)

    def chown(self, path: str, uid: int, gid: int) -> None:
        return os.chown(path, uid, gid)

    def create(self, path: str, mode: int, fi: Optional[object] = None) -> int:
        """
        When raw_fi is False (default case), fi is None and create should
        return a numerical file handle.

        When raw_fi is True the file handle should be set directly by create
        and return 0.
        """
        return os.open(path, os.O_WRONLY | os.O_CREAT, mode)

    def destroy(self, path: str) -> None:
        """Called on filesystem destruction. Path is always /"""
        pass

    def flush(self, path: str, fh: int) -> None:
        return os.fsync(fh)

    def fsync(self, path: str, datasync: bool, fh: int) -> None:
        return self.flush(path, fh)

    def fsyncdir(self, path: str, datasync: bool, fh: int) -> None:
        pass

    def getattr(self, path: str, fh: Optional[int] = None) -> Dict[str, Union[int, float]]:
        """
        Returns a dictionary with keys identical to the stat C structure of
        stat(2).

        st_atime, st_mtime and st_ctime should be floats.

        NOTE: There is an incompatibility between Linux and Mac OS X
        concerning st_nlink of directories. Mac OS X counts all files inside
        the directory, while Linux counts only the subdirectories.
        """
        st: os.stat_result = os.lstat(path)
        return dict((key, getattr(st, key)) for key in ('st_atime', 'st_ctime',
                                                        'st_gid', 'st_mode', 'st_mtime', 'st_nlink', 'st_size',
                                                        'st_uid'))

    def getxattr(self, path: str, name: str, position: int = 0) -> bytes:
        try:
            return os.getxattr(path, name)
        except OSError as e:
            if e.errno == errno.ENOTSUP:
                return b''  # Not supported
            raise FuseOSError(e.errno)

    def init(self, path: str) -> None:
        """
        Called on filesystem initialization. (Path is always /)

        Use it instead of __init__ if you start threads on initialization.
        """
        pass

    def ioctl(self, path: str, cmd: int, arg: int, fip: object, flags: int, data: object) -> None:
        raise FuseOSError(errno.ENOTTY)  # Not implemented

    def link(self, target: str, source: str) -> None:
        """creates a hard link `target -> source` (e.g. ln source target)"""
        return os.link(target, source)

    def listxattr(self, path: str) -> List[str]:
        try:
            return os.listxattr(path)
        except OSError as e:
            if e.errno == errno.ENOTSUP:
                return []
            raise FuseOSError(e.errno)

    def mkdir(self, path: str, mode: int) -> None:
        return os.mkdir(path, mode)

    def mknod(self, path: str, mode: int, dev: int) -> None:
        return os.mknod(path, mode, dev)

    def open(self, path: str, flags: int) -> int:
        return os.open(path, flags)

    def opendir(self, path: str) -> int:
        return 0

    def read(self, path: str, size: int, offset: int, fh: int) -> bytes:
        os.lseek(fh, offset, os.SEEK_SET)
        return os.read(fh, size)

    def readdir(self, path: str, fh: int) -> Iterator[str]:
        dirents: List[str] = ['.', '..']
        if os.path.isdir(path):
            dirents.extend(os.listdir(path))
        for r in dirents:
            yield r

    def readlink(self, path: str) -> str:
        return os.readlink(path)

    def release(self, path: str, fh: int) -> None:
        return os.close(fh)

    def releasedir(self, path: str, fh: int) -> None:
        pass

    def removexattr(self, path: str, name: str) -> None:
        try:
            os.removexattr(path, name)
        except OSError as e:
            if e.errno == errno.ENOTSUP:
                pass  # Not supported
            else:
                raise FuseOSError(e.errno)

    def rename(self, old: str, new: str) -> None:
        return os.rename(old, new)

    def rmdir(self, path: str) -> None:
        return os.rmdir(path)

    def setxattr(self, path: str, name: str, value: bytes, options: int, position: int = 0) -> None:
        try:
            os.setxattr(path, name, value, options)
        except OSError as e:
            if e.errno == errno.ENOTSUP:
                pass  # Not supported
            else:
                raise FuseOSError(e.errno)

    def statfs(self, path: str) -> Dict[str, int]:
        """
        Returns a dictionary with keys identical to the statvfs C structure of
        statvfs(3).

        On Mac OS X f_bsize and f_frsize must be a power of 2
        (minimum 512).
        """
        stv: os.statvfs_result = os.statvfs(path)
        return dict((key, getattr(stv, key)) for key in ('f_bavail', 'f_bfree',
                                                         'f_blocks', 'f_bsize', 'f_favail', 'f_ffree', 'f_files',
                                                         'f_flag',
                                                         'f_frsize', 'f_namemax'))

    def symlink(self, target: str, source: str) -> None:
        """creates a symlink `target -> source` (e.g. ln -s source target)"""
        return os.symlink(source, target)

    def truncate(self, path: str, length: int, fh: Optional[int] = None) -> None:
        with open(path, 'r+') as f:
            f.truncate(length)

    def unlink(self, path: str) -> None:
        return os.unlink(path)

    def utimens(self, path: str, times: Optional[tuple] = None) -> None:
        """Times is a (atime, mtime) tuple. If None use current time."""
        return os.utime(path, times)

    def write(self, path: str, data: bytes, offset: int, fh: int) -> int:
        os.lseek(fh, offset, os.SEEK_SET)
        return os.write(fh, data)
