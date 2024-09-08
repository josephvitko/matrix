from pathlib import PureWindowsPath

from winfspy import (
    FILE_ATTRIBUTE,
)
from winfspy.plumbing.security_descriptor import SecurityDescriptor

from src.win_tests.obj.base_file import BaseFileObj


class FolderObj(BaseFileObj):
    def __init__(self, path: PureWindowsPath, attributes: FILE_ATTRIBUTE, security_descriptor: SecurityDescriptor):
        super().__init__(path, attributes, security_descriptor)
        self.allocation_size = 0
        assert self.attributes & FILE_ATTRIBUTE.FILE_ATTRIBUTE_DIRECTORY
