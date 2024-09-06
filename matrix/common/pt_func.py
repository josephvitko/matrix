import errno
import os

from fuse import FuseOSError


def full_path(partial, root):
    if partial.startswith("/"):
        partial = partial[1:]
    path = os.path.join(root, partial)
    return path


def access(path, mode):
    if not os.access(path, mode):
        raise FuseOSError(errno.EACCES)


def chmod(path, mode):
    return os.chmod(path, mode)


def chown(path, uid, gid):
    return os.chown(path, uid, gid)


def f_getattr(path, fh=None):
    st = os.lstat(path)
    return dict((key, getattr(st, key)) for key in ('st_atime', 'st_ctime',
                                                    'st_gid', 'st_mode', 'st_mtime', 'st_nlink', 'st_size', 'st_uid'))


def readdir(path, fh):
    dirents = ['.', '..']
    if os.path.isdir(path):
        dirents.extend(os.listdir(path))
    for r in dirents:
        yield r


def readlink(path, root):
    pathname = os.readlink(path)
    if pathname.startswith("/"):
        # Path name is absolute, sanitize it.
        return os.path.relpath(pathname, root)
    else:
        return pathname


def mknod(path, mode, dev):
    return os.mknod(path, mode, dev)


def rmdir(path):
    return os.rmdir(path)


def mkdir(path, mode):
    return os.mkdir(path, mode)


def statfs(path):
    stv = os.statvfs(path)
    return dict((key, getattr(stv, key)) for key in ('f_bavail', 'f_bfree',
                                                     'f_blocks', 'f_bsize', 'f_favail', 'f_ffree', 'f_files', 'f_flag',
                                                     'f_frsize', 'f_namemax'))


def unlink(path):
    return os.unlink(path)


def symlink(name, target):
    return os.symlink(name, target)


def rename(old, new):
    return os.rename(old, new)


def link(target, name):
    return os.link(target, name)


def utimens(path, times=None):
    return os.utime(path, times)


# File methods
# ============

def f_open(path, flags):
    return os.open(path, flags)


def create(path, mode, fi=None):
    return os.open(path, os.O_WRONLY | os.O_CREAT, mode)


def read(path, length, offset, fh):
    os.lseek(fh, offset, os.SEEK_SET)
    return os.read(fh, length)


def write(path, buf, offset, fh):
    os.lseek(fh, offset, os.SEEK_SET)
    return os.write(fh, buf)


def truncate(path, length, fh=None):
    with open(path, 'r+') as f:
        f.truncate(length)


def flush(path, fh):
    return os.fsync(fh)


def release(path, fh):
    return os.close(fh)


def fsync(path, fdatasync, fh):
    return flush(path, fh)