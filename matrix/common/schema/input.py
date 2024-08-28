import base64
from typing import Optional

from pydantic import BaseModel, field_validator

class FuseInput(BaseModel):
    pass

class AccessInput(FuseInput):
    path: str
    mode: int

class ChmodInput(FuseInput):
    path: str
    mode: int

class ChownInput(FuseInput):
    path: str
    uid: int
    gid: int

class GetattrInput(FuseInput):
    path: str
    fh: Optional[int] = None

class ReaddirInput(FuseInput):
    path: str
    fh: int

class ReadlinkInput(FuseInput):
    path: str

class MknodInput(FuseInput):
    path: str
    mode: int
    dev: int

class RmdirInput(FuseInput):
    path: str

class MkdirInput(FuseInput):
    path: str
    mode: int

class StatfsInput(FuseInput):
    path: str

class UnlinkInput(FuseInput):
    path: str

class SymlinkInput(FuseInput):
    name: str
    target: str

class RenameInput(FuseInput):
    old: str
    new: str

class LinkInput(FuseInput):
    target: str
    name: str

class UtimensInput(FuseInput):
    path: str
    times: Optional[tuple[int, int]] = None

class OpenInput(FuseInput):
    path: str
    flags: int

class CreateInput(FuseInput):
    path: str
    mode: int

class ReadInput(FuseInput):
    path: str
    size: int
    offset: int
    fh: int

class WriteInput(FuseInput):
    path: str
    data: bytes
    offset: int
    fh: int

    @field_validator('data', mode='before')
    def decode_base64_data(cls, v):
        if isinstance(v, str):
            try:
                return base64.b64decode(v)
            except Exception as e:
                raise ValueError('Invalid base64 data') from e
        return v

    def model_dump(self, *args, **kwargs):
        data_dict = super().model_dump(*args, **kwargs)
        data_dict['data'] = base64.b64encode(data_dict['data']).decode('utf-8')
        return data_dict

class TruncateInput(FuseInput):
    path: str
    length: int
    fh: Optional[int] = None

class FlushInput(FuseInput):
    path: str
    fh: int

class ReleaseInput(FuseInput):
    path: str
    fh: int

class FsyncInput(FuseInput):
    path: str
    datasync: int
    fh: int