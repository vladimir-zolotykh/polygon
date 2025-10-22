#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# PYTHON_ARGCOMPLETE_OK
from typing import BinaryIO, Self, Iterator, Any
import struct
from meta_header import Chunk


class NestedType:
    """Nested chunk-struct"""

    def __get_name__(self, owner, name):
        self.name = "_" + name

    def __init__(self, nested_type, offset):
        self.nested_type = nested_type
        self.offset = offset

    def __get__(self, instance, owner):
        if instance is None:
            return self
        # fmt: off
        buf = instance._buffer[self.offset:self.offset + self.nested_type.size]
        # fmt: on
        val = self.nested_type(buf)
        setattr(instance, self.name, self.nested_type(buf))
        return val


class NestedMeta(type):
    def __init__(cls, clsname, bases, clsdict):
        byte_code = ""
        offset: int = 0
        for nested_type, field_name in cls._fields_:
            if isinstance(nested_type, str):
                format = nested_type
                if format[0] in ("<", ">", "!", "@"):
                    byte_code = format[0]
                    format = format[1:]
                format = byte_code + format

                # fmt: off
                dat = cls._buffer[offset:offset + struct.calcsize(format)]
                # fmt: on
                setattr(cls, field_name, Chunk(format, dat))
                offset += struct.calcsize(format)
            else:
                setattr(cls, field_name, NestedType(nested_type, offset))
                offset += nested_type.size
        setattr(cls, "size", offset)


class NestedBuffer(metaclass=NestedMeta):
    def __init__(self, buffer):
        self._buffer = memoryview(buffer)

    @classmethod
    def from_file(cls, f: BinaryIO) -> Self:
        return cls(cls(f.read(cls.size)))


class Point(NestedBuffer):
    _fields_ = [
        ("<d", "x"),
        ("d", "y"),
    ]


class PolyHeader(NestedBuffer):
    _fields_ = [
        ("<i", "code"),
        (Point, "xy1"),
        (Point, "xy2"),
        ("i", "npoly"),
    ]


class SizedRecord:
    def __init__(self, bytedata):
        self._buffer = memoryview(bytedata)

    @classmethod
    def from_file(cls, f: BinaryIO):
        size = struct.unpack("<i", f.read(4))
        buf = f.read(size)
        return cls(buf)

    def iter_as(
        self,
        record_type,
    ) -> Iterator[tuple[Any, ...] | NestedBuffer]:
        if isinstance(record_type, str):
            format: str = record_type
            u = struct.Struct(format)
            for off in range(0, len(self._buffer), u.size):
                # fmt: off
                buf = self._buffer[off:off + u.size]
                # fmt: on
                yield u.unpack_from(buf)
        elif isinstance(record_type, NestedBuffer):
            for off in range(0, len(self._buffer), record_type.size):
                # fmt: off
                buf = self._buffer[off:off + record_type.size]
                # fmt: on
                yield record_type(buf)
