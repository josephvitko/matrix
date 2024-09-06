import errno
import os

from fuse import FuseOSError

from matrix.common.schema.output import GetattrOutput, ReaddirOutput, StatfsOutput, OpenOutput, CreateOutput, \
    ReadOutput, WriteOutput, ReadlinkOutput


def get_full_path(root: str, partial: str) -> str:
    if partial.startswith("/"):
        partial = partial[1:]
    path: str = os.path.join(root, partial)
    return path

# Filesystem methods
# ==================

def access(path: str, mode: int) -> None:
    if not os.access(path, mode):
        raise FuseOSError(errno.EACCES)

def chmod(path: str, mode: int) -> None:
    os.chmod(path, mode)

def chown(path: str, uid: int, gid: int) -> None:
    os.chown(path, uid, gid)

def fuse_getattr(path: str, fh: int=None) -> GetattrOutput:
    st = os.lstat(path)

    return GetattrOutput(
        st_atime=st.st_atime,
        st_ctime=st.st_ctime,
        st_gid=st.st_gid,
        st_mode=st.st_mode,
        st_mtime=st.st_mtime,
        st_nlink=st.st_nlink,
        st_size=st.st_size,
        st_uid=st.st_uid
    )

def readdir(path: str, fh: int) -> ReaddirOutput:
    dirents = ['.', '..']
    if os.path.isdir(path):
        dirents.extend(os.listdir(path))
    return ReaddirOutput(content=dirents)

def readlink(path: str) -> ReadlinkOutput:
    return ReadlinkOutput(destination_path=os.readlink(path))

def mknod(path: str, mode: int, dev: int) -> None:
    os.mknod(path, mode, dev)

def rmdir(path: str) -> None:
    os.rmdir(path)

def mkdir(path: str, mode: int) -> None:
    os.mkdir(path, mode)

def statfs(path: str) -> StatfsOutput:
    stv: os.statvfs_result = os.statvfs(path)
    return StatfsOutput(
        f_bavail=stv.f_bavail,
        f_bfree=stv.f_bfree,
        f_blocks=stv.f_blocks,
        f_bsize=stv.f_bsize,
        f_favail=stv.f_favail,
        f_ffree=stv.f_ffree,
        f_files=stv.f_files,
        f_flag=stv.f_flag,
        f_frsize=stv.f_frsize,
        f_namemax=stv.f_namemax
    )

def unlink(path: str) -> None:
    os.unlink(path)

def symlink(name: str, target: str) -> None:
    os.symlink(name, target)

def rename(old: str, new: str) -> None:
    os.rename(old, new)

def link(target: str, name: str) -> None:
    os.link(target, name)

def utimens(path: str, times: tuple=None) -> None:
    os.utime(path, times)

# File methods
# ============

def fuse_open(path: str, flags: int) -> OpenOutput:
    fh = os.open(path, flags)
    return OpenOutput(handle=fh)

def create(path: str, mode: int) -> CreateOutput:
    fd = os.open(path, os.O_WRONLY | os.O_CREAT, mode)
    return CreateOutput(handle=fd)


def read(path: str, size: int, offset: int, fh: int) -> ReadOutput:
    os.lseek(fh, offset, os.SEEK_SET)
    return ReadOutput(content=os.read(fh, size))

def write(path: str, data: bytes, offset: int, fh: int) -> WriteOutput:
    os.lseek(fh, offset, os.SEEK_SET)
    return WriteOutput(bytes_written=os.write(fh, data))

def truncate(path: str, length: int, fh: int=None) -> None:
    with open(path, 'r+') as f:
        f.truncate(length)

def flush(path: str, fh: int) -> None:
    return os.fsync(fh)

def release(path: str, fh: int) -> None:
    return os.close(fh)

def fsync(path: str, datasync: int, fh: int) -> None:
    return os.fsync(fh)
