#!/usr/bin/env python

from __future__ import with_statement

import base64
import os
import sys
import errno
import json
import requests

from fuse import FUSE, FuseOSError, Operations

from matrix.common.endpoints import FuseEndpoints


class HttpFS(Operations):
    def __init__(self, url):
        self.url = url

    # Helpers
    # =======

    def _request(self, method, path, **kwargs):
        url = f"{self.url}{method.value}"
        payload = {'path': path, **kwargs}
        try:
            response = requests.post(url, json=payload)
            response.raise_for_status()  # This will raise an exception for HTTP error codes
            return response.json()
        except requests.exceptions.RequestException as e:
            raise FuseOSError(errno.ECOMM) from e

    # Filesystem methods
    # ==================

    def access(self, path, mode):
        result = self._request(FuseEndpoints.ACCESS, path, mode=mode)
        if not result['status']:
            raise FuseOSError(errno.EACCES)

    def chmod(self, path, mode):
        return self._request(FuseEndpoints.CHMOD, path, mode=mode)

    def chown(self, path, uid, gid):
        return self._request(FuseEndpoints.CHOWN, path, uid=uid, gid=gid)

    def getattr(self, path, fh=None):
        return self._request(FuseEndpoints.GETATTR, path, fh=fh)

    def readdir(self, path, fh):
        dirents = self._request(FuseEndpoints.READDIR, path, fh=fh)
        for r in dirents['content']:
            yield r

    def readlink(self, path):
        result = self._request(FuseEndpoints.READLINK, path)
        return result['path']

    def mknod(self, path, mode, dev):
        return self._request(FuseEndpoints.MKNOD, path, mode=mode, dev=dev)

    def rmdir(self, path):
        return self._request(FuseEndpoints.RMDIR, path)

    def mkdir(self, path, mode):
        return self._request(FuseEndpoints.MKDIR, path, mode=mode)

    def statfs(self, path):
        return self._request(FuseEndpoints.STATFS, path)

    def unlink(self, path):
        return self._request(FuseEndpoints.UNLINK, path)

    def symlink(self, name, target):
        return self._request(FuseEndpoints.SYMLINK, name, target=target)

    def rename(self, old, new):
        return self._request(FuseEndpoints.RENAME, old=old, new=new)

    def link(self, target, name):
        return self._request(FuseEndpoints.LINK, target=target, name=name)

    def utimens(self, path, times=None):
        return self._request(FuseEndpoints.UTIMENS, path, times=times)

    # File methods
    # ============

    def open(self, path, flags):
        res: dict = self._request(FuseEndpoints.OPEN, path, flags=flags)
        return int(res['handle'])

    def create(self, path, mode, fi=None):
        return self._request(FuseEndpoints.CREATE, path, mode=mode, fi=fi)

    def read(self, path, size, offset, fh):
        """Read file data from server."""
        url = f"{self.url}{FuseEndpoints.READ.value}"
        payload = {'path': path, 'length': size, 'offset': offset}
        response = requests.post(url, json=payload)
        if response.status_code == 200:
            base64_data = response.json()['data']
            file_data = base64.b64decode(base64_data)
            return file_data[offset:offset + size]
        else:
            raise FuseOSError(errno.EIO)  # Input/Output Error

    def write(self, path, buf, offset, fh):
        encoded_data = base64.b64encode(buf).decode('ascii')
        return self._request(FuseEndpoints.WRITE, path, buf=encoded_data, offset=offset, fh=fh)

    def truncate(self, path, length, fh=None):
        return self._request(FuseEndpoints.TRUNCATE, path, length=length, fh=fh)

    def flush(self, path, fh):
        return self._request(FuseEndpoints.FLUSH, path, fh=fh)

    def release(self, path, fh):
        return self._request(FuseEndpoints.RELEASE, path, fh=fh)

    def fsync(self, path, fdatasync, fh):
        return self._request(FuseEndpoints.FSYNC, path, fdatasync=fdatasync, fh=fh)


def main(mountpoint, url):
    FUSE(HttpFS(url), mountpoint, nothreads=True, foreground=True)


if __name__ == '__main__':
    # if len(sys.argv) != 3:
    #     print('usage: %s <mountpoint> <url>' % sys.argv[0])
    #     sys.exit(1)
    #
    # main(sys.argv[1], sys.argv[2])
    main("C:\\mnt", "http://localhost:5000")
