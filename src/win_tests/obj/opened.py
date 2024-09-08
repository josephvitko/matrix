from typing import Union

from src.win_tests.obj.file import FileObj
from src.win_tests.obj.folder import FolderObj


class OpenedObj:
    file_obj: Union[FileObj, FolderObj]

    def __init__(self, file_obj: Union[FileObj, FolderObj]):
        self.file_obj = file_obj

    def __repr__(self) -> str:
        return f"{type(self).__name__}:{self.file_obj.file_name}"
