from pathlib import PureWindowsPath

from winfspy import (
    FILE_ATTRIBUTE,
    NTStatusEndOfFile,
)
from winfspy.plumbing.security_descriptor import SecurityDescriptor

from src.win_tests.obj.base_file import BaseFileObj


class FileObj(BaseFileObj):
    allocation_unit: int = 4096
    data: bytearray

    def __init__(self, path: PureWindowsPath, attributes: FILE_ATTRIBUTE, security_descriptor: SecurityDescriptor,
                 allocation_size: int = 0):
        super().__init__(path, attributes, security_descriptor)
        self.data = bytearray(allocation_size)
        self.attributes |= FILE_ATTRIBUTE.FILE_ATTRIBUTE_ARCHIVE
        assert not self.attributes & FILE_ATTRIBUTE.FILE_ATTRIBUTE_DIRECTORY

    @property
    def allocation_size(self) -> int:
        return len(self.data)

    def set_allocation_size(self, allocation_size: int) -> None:
        if allocation_size < self.allocation_size:
            self.data = self.data[:allocation_size]
        if allocation_size > self.allocation_size:
            self.data += bytearray(allocation_size - self.allocation_size)
        assert self.allocation_size == allocation_size
        self.file_size = min(self.file_size, allocation_size)

    def adapt_allocation_size(self, file_size: int) -> None:
        units = (file_size + self.allocation_unit - 1) // self.allocation_unit
        self.set_allocation_size(units * self.allocation_unit)

    def set_file_size(self, file_size: int) -> None:
        if file_size < self.file_size:
            zeros = bytearray(self.file_size - file_size)
            self.data[file_size: self.file_size] = zeros
        if file_size > self.allocation_size:
            self.adapt_allocation_size(file_size)
        self.file_size = file_size

    def read(self, offset: int, length: int) -> bytes:
        if offset >= self.file_size:
            raise NTStatusEndOfFile()
        end_offset = min(self.file_size, offset + length)
        return bytes(self.data[offset:end_offset])

    def write(self, buffer: bytes, offset: int, write_to_end_of_file: bool) -> int:
        if write_to_end_of_file:
            offset = self.file_size
        end_offset = offset + len(buffer)
        if end_offset > self.file_size:
            self.set_file_size(end_offset)
        self.data[offset:end_offset] = buffer
        return len(buffer)

    def constrained_write(self, buffer: bytes, offset: int) -> int:
        if offset >= self.file_size:
            return 0
        end_offset = min(self.file_size, offset + len(buffer))
        transferred_length = end_offset - offset
        self.data[offset:end_offset] = buffer[:transferred_length]
        return transferred_length
