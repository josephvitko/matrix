from pathlib import PureWindowsPath
from typing import Dict, Union

from winfspy import (
    FILE_ATTRIBUTE,
)
from winfspy.plumbing.security_descriptor import SecurityDescriptor
from winfspy.plumbing.win32_filetime import filetime_now


class BaseFileObj:
    path: PureWindowsPath
    attributes: FILE_ATTRIBUTE
    security_descriptor: SecurityDescriptor
    creation_time: int
    last_access_time: int
    last_write_time: int
    change_time: int
    index_number: int
    file_size: int

    @property
    def name(self) -> str:
        """File name, without the path"""
        return self.path.name

    @property
    def file_name(self) -> str:
        """File name, including the path"""
        return str(self.path)

    def __init__(self, path: PureWindowsPath, attributes: FILE_ATTRIBUTE, security_descriptor: SecurityDescriptor):
        self.path = path
        self.attributes = attributes
        self.security_descriptor = security_descriptor
        now = filetime_now()
        self.creation_time = now
        self.last_access_time = now
        self.last_write_time = now
        self.change_time = now
        self.index_number = 0
        self.file_size = 0

    def get_file_info(self) -> Dict[str, Union[int, FILE_ATTRIBUTE]]:
        return {
            "file_attributes": self.attributes,
            "allocation_size": self.allocation_size,
            "file_size": self.file_size,
            "creation_time": self.creation_time,
            "last_access_time": self.last_access_time,
            "last_write_time": self.last_write_time,
            "change_time": self.change_time,
            "index_number": self.index_number,
        }

    def __repr__(self) -> str:
        return f"{type(self).__name__}:{self.file_name}"
