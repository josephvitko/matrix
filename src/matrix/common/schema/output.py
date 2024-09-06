import base64
from typing import Optional

from pydantic import BaseModel, field_validator

class FuseOutput(BaseModel):
    pass


class FuseResponse(BaseModel):
    status: str
    error: Optional[str] = None
    data: Optional[FuseOutput] = None

    def model_dump(self, **kwargs):
        # Use the parent class's model_dump method to handle other fields
        response = super().model_dump(**kwargs)

        # Serialize the `data` field manually if it is an instance of a FuseOutput subclass
        if isinstance(self.data, FuseOutput):
            response['data'] = self.data.model_dump(**kwargs)
        return response

    @classmethod
    def from_dict(cls, data: dict, data_type: type[FuseOutput]) -> "FuseResponse":
        # Deserialize the data field based on the provided data_type
        if 'data' in data and data['data'] is not None:
            data['data'] = data_type.model_validate(data['data'])
        return cls.model_validate(data)


class GetattrOutput(FuseOutput):
    st_atime: float
    st_ctime: float
    st_gid: int
    st_mode: int
    st_mtime: float
    st_nlink: int
    st_size: int
    st_uid: int

class ReaddirOutput(FuseOutput):
    content: list[str]

class ReadlinkOutput(FuseOutput):
    destination_path: str

class StatfsOutput(FuseOutput):
    f_bavail: int
    f_bfree: int
    f_blocks: int
    f_bsize: int
    f_favail: int
    f_ffree: int
    f_files: int
    f_flag: int
    f_frsize: int
    f_namemax: int

class OpenOutput(FuseOutput):
    handle: int

class CreateOutput(FuseOutput):
    handle: int

class ReadOutput(FuseOutput):
    content: bytes

    @field_validator('content', mode='before')
    def decode_base64_content(cls, v):
        if isinstance(v, str):
            try:
                return base64.b64decode(v)
            except Exception as e:
                raise ValueError('Invalid base64 data') from e
        return v

    def model_dump(self, *args, **kwargs):
        data_dict = super().model_dump(*args, **kwargs)
        data_dict['content'] = base64.b64encode(data_dict['content']).decode('utf-8')
        return data_dict

class WriteOutput(FuseOutput):
    bytes_written: int

