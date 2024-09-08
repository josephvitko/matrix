from typing import TypedDict

from winfspy import FILE_ATTRIBUTE


class FileInfo(TypedDict):
    file_name: str
    file_attributes: FILE_ATTRIBUTE
    allocation_size: int
    file_size: int
    creation_time: int
    last_access_time: int
    last_write_time: int
    change_time: int
    index_number: int\
