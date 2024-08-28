#!/usr/bin/env python

from __future__ import with_statement

import errno
import requests

import matrix.common.schema.input as fuse_input

from fuse import FUSE, FuseOSError, Operations

from matrix.common.endpoints import FuseEndpoints
from matrix.common.schema import output
from matrix.common.schema.input import FuseInput
from matrix.common.schema.output import FuseResponse, FuseOutput, OpenOutput, StatfsOutput, ReadlinkOutput, \
    ReaddirOutput, GetattrOutput, CreateOutput


class HttpFS(Operations):
    def __init__(self, url):
        self.url = url

    # Helpers
    # =======

    def _request(self, endpoint: FuseEndpoints, body: FuseInput, output_type: type = None) -> FuseOutput:
        url = f"{self.url}{endpoint.value}"
        payload = body.model_dump()

        try:
            re = requests.post(url, json=payload)
            re.raise_for_status()

            response: FuseResponse = FuseResponse.from_dict(re.json(), output_type)

            if response.status == "error":
                raise Exception(response.error)

            return response.data

        except Exception as e:
            raise FuseOSError(errno.ECONNRESET) from e

    # Filesystem methods
    # ==================

    def access(self, path: str, mode: int) -> None:
        f_input: fuse_input.AccessInput = fuse_input.AccessInput(path=path, mode=mode)
        self._request(FuseEndpoints.ACCESS, f_input)

    def chmod(self, path: str, mode: int) -> None:
        f_input: fuse_input.ChmodInput = fuse_input.ChmodInput(path=path, mode=mode)
        self._request(FuseEndpoints.CHMOD, f_input)

    def chown(self, path: str, uid: int, gid: int) -> None:
        f_input: fuse_input.ChownInput = fuse_input.ChownInput(path=path, uid=uid, gid=gid)
        self._request(FuseEndpoints.CHOWN, f_input)

    def getattr(self, path: str, fh:int=None) -> dict:
        f_input: fuse_input.GetattrInput = fuse_input.GetattrInput(path=path, fh=fh)
        out: GetattrOutput = self._request(FuseEndpoints.GETATTR, f_input, GetattrOutput)
        return out.model_dump()

    def readdir(self, path: str, fh: int) -> str:
        f_input: fuse_input.ReaddirInput = fuse_input.ReaddirInput(path=path, fh=fh)
        out: ReaddirOutput = self._request(FuseEndpoints.READDIR, f_input, ReaddirOutput)
        for r in out.content:
            yield r

    def readlink(self, path: str) -> str:
        f_input: fuse_input.ReadlinkInput = fuse_input.ReadlinkInput(path=path)
        out: ReadlinkOutput = self._request(FuseEndpoints.READLINK, f_input, ReadlinkOutput)
        return out.path

    def mknod(self, path: str, mode: int, dev: int) -> None:
        f_input: fuse_input.MknodInput = fuse_input.MknodInput(path=path, mode=mode, dev=dev)
        self._request(FuseEndpoints.MKNOD, f_input)

    def rmdir(self, path: str) -> None:
        f_input: fuse_input.RmdirInput = fuse_input.RmdirInput(path=path)
        self._request(FuseEndpoints.RMDIR, f_input)

    def mkdir(self, path: str, mode: int) -> None:
        f_input: fuse_input.MkdirInput = fuse_input.MkdirInput(path=path, mode=mode)
        self._request(FuseEndpoints.MKDIR, f_input)

    def statfs(self, path: str) -> dict:
        f_input: fuse_input.StatfsInput = fuse_input.StatfsInput(path=path)
        out: StatfsOutput = self._request(FuseEndpoints.STATFS, f_input, StatfsOutput)
        return out.model_dump()

    def unlink(self, path: str) -> None:
        f_input: fuse_input.UnlinkInput = fuse_input.UnlinkInput(path=path)
        self._request(FuseEndpoints.UNLINK, f_input)

    def symlink(self, name: str, target: str) -> None:
        f_input: fuse_input.SymlinkInput = fuse_input.SymlinkInput(name=name, target=target)
        self._request(FuseEndpoints.SYMLINK, f_input)

    def rename(self, old: str, new: str) -> None:
        f_input: fuse_input.RenameInput = fuse_input.RenameInput(old=old, new=new)
        self._request(FuseEndpoints.RENAME, f_input)

    def link(self, target: str, name: str) -> None:
        f_input: fuse_input.LinkInput = fuse_input.LinkInput(target=target, name=name)
        self._request(FuseEndpoints.LINK, f_input)

    def utimens(self, path: str, times: tuple[int, int]=None) -> None:
        f_input: fuse_input.UtimensInput = fuse_input.UtimensInput(path=path, times=times)
        self._request(FuseEndpoints.UTIMENS, f_input)

    # File methods
    # ============

    def open(self, path: str, flags: int) -> int:
        f_input: fuse_input.OpenInput = fuse_input.OpenInput(path=path, flags=flags)
        out: OpenOutput = self._request(FuseEndpoints.OPEN, f_input, OpenOutput)
        return out.handle

    def create(self, path: str, mode: int, fi=None) -> int:
        f_input: fuse_input.CreateInput = fuse_input.CreateInput(path=path, mode=mode)
        out: CreateOutput = self._request(FuseEndpoints.CREATE, f_input, CreateOutput)
        return out.handle

    def read(self, path: str, size: int, offset: int, fh: int) -> bytes:
        f_input: fuse_input.ReadInput = fuse_input.ReadInput(path=path, size=size, offset=offset, fh=fh)
        out: output.ReadOutput = self._request(FuseEndpoints.READ, f_input, output.ReadOutput)
        return out.content


    def write(self, path: str, buf: bytes, offset: int, fh: int) -> int:
        f_input: fuse_input.WriteInput = fuse_input.WriteInput(path=path, data=buf, offset=offset, fh=fh)
        out: output.WriteOutput = self._request(FuseEndpoints.WRITE, f_input, output.WriteOutput)
        return out.size


    def truncate(self, path: str, length: int, fh: int=None) -> None:
        f_input: fuse_input.TruncateInput = fuse_input.TruncateInput(path=path, length=length, fh=fh)
        self._request(FuseEndpoints.TRUNCATE, f_input)

    def flush(self, path: str, fh: int) -> None:
        f_input: fuse_input.FlushInput = fuse_input.FlushInput(path=path, fh=fh)
        self._request(FuseEndpoints.FLUSH, f_input)

    def release(self, path: str, fh: int) -> None:
        f_input: fuse_input.ReleaseInput = fuse_input.ReleaseInput(path=path, fh=fh)
        self._request(FuseEndpoints.RELEASE, f_input)

    def fsync(self, path: str, fdatasync: int, fh: int) -> None:
        f_input: fuse_input.FsyncInput = fuse_input.FsyncInput(path=path, fdatasync=fdatasync, fh=fh)
        self._request(FuseEndpoints.FSYNC, f_input)
