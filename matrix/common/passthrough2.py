#!/usr/bin/env python

from __future__ import with_statement

import os
import errno

from fuse import FUSE, FuseOSError, Operations

import matrix.common.pt_func as pt_func


class Passthrough2(Operations):
    def __init__(self, root):
        self.root = root

    # Filesystem methods
    # ==================

    def access(self, path, mode):
        full_path: str = pt_func.full_path(path, self.root)
        pt_func.access(full_path, mode)

    def chmod(self, path, mode):
        full_path: str = pt_func.full_path(path, self.root)
        pt_func.chmod(full_path, mode)

    def chown(self, path, uid, gid):
        full_path: str = pt_func.full_path(path, self.root)
        pt_func.chown(full_path, uid, gid)

    def getattr(self, path, fh=None):
        full_path: str = pt_func.full_path(path, self.root)
        return pt_func.f_getattr(full_path, fh)

    def readdir(self, path, fh):
        full_path: str = pt_func.full_path(path, self.root)
        return pt_func.readdir(full_path, fh)

    def readlink(self, path):
        full_path: str = pt_func.full_path(path, self.root)
        return pt_func

    def mknod(self, path, mode, dev):
        full_path: str = pt_func.full_path(path, self.root)
        pt_func.mknod(full_path, mode, dev)

    def rmdir(self, path):
        full_path: str = pt_func.full_path(path, self.root)
        pt_func.rmdir(full_path)

    def mkdir(self, path, mode):
        full_path: str = pt_func.full_path(path, self.root)
        pt_func.mkdir(full_path, mode)

    def statfs(self, path):
        full_path: str = pt_func.full_path(path, self.root)
        return pt_func.statfs(full_path)

    def unlink(self, path):
        full_path: str = pt_func.full_path(path, self.root)
        return pt_func.unlink(full_path)

    def symlink(self, name, target):
        full_path: str = pt_func.full_path(name, self.root)
        pt_func.symlink(full_path, target)

    def rename(self, old, new):
        full_old: str = pt_func.full_path(old, self.root)
        full_new: str = pt_func.full_path(new, self.root)
        pt_func.rename(full_old, full_new)

    def link(self, target, name):
        full_target: str = pt_func.full_path(target, self.root)
        full_name: str = pt_func.full_path(name, self.root)
        pt_func.link(full_target, full_name)

    def utimens(self, path, times=None):
        full_path: str = pt_func.full_path(path, self.root)
        pt_func.utimens(full_path, times)

    # File methods
    # ============

    def open(self, path, flags):
        full_path: str = pt_func.full_path(path, self.root)
        return pt_func.f_open(full_path, flags)

    def create(self, path, mode, fi=None):
        full_path: str = pt_func.full_path(path, self.root)
        return pt_func.create(full_path, mode, fi)

    def read(self, path, length, offset, fh):
        full_path: str = pt_func.full_path(path, self.root)
        return pt_func.read(full_path, length, offset, fh)

    def write(self, path, buf, offset, fh):
        full_path: str = pt_func.full_path(path, self.root)
        return pt_func.write(full_path, buf, offset, fh)

    def truncate(self, path, length, fh=None):
        full_path: str = pt_func.full_path(path, self.root)
        return pt_func.truncate(full_path, length, fh)

    def flush(self, path, fh):
        full_path: str = pt_func.full_path(path, self.root)
        return pt_func.flush(full_path, fh)

    def release(self, path, fh):
        full_path: str = pt_func.full_path(path, self.root)
        return pt_func.release(full_path, fh)

    def fsync(self, path, fdatasync, fh):
        full_path: str = pt_func.full_path(path, self.root)
        return pt_func.fsync(full_path, fdatasync, fh)


def main(mountpoint, root):
    FUSE(Passthrough2(root), mountpoint, nothreads=True, foreground=True)

if __name__ == '__main__':
    main("/Users/josephvitko/PycharmProjects/matrix/test/mnt_main", "/Users/josephvitko/PycharmProjects/matrix/test/root")
    # main(sys.argv[2], sys.argv[1])
