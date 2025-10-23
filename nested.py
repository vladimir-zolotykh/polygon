#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# PYTHON_ARGCOMPLETE_OK
from typing import BinaryIO, Self, Iterator, Any
import struct
from meta_header import Chunk


class NestedType:
    """Nested chunk-struct"""

    def __init__(self, name, nested_type, offset):
        self.name = name  # owner attr name
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

                setattr(cls, field_name, Chunk(format, offset))
                offset += struct.calcsize(format)
            else:
                setattr(cls, field_name, NestedType(field_name, nested_type, offset))
                offset += nested_type.size
        setattr(cls, "size", offset)


class NestedBuffer:
    def __init__(self, buffer):
        self._buffer = memoryview(buffer)

    @classmethod
    def from_file(cls, f: BinaryIO) -> Self:
        return cls(f.read(cls.size))


def as_tuple(nested_buffer: NestedBuffer) -> tuple[Any, ...]:
    nb = nested_buffer
    return tuple(getattr(nb, fn) for _, fn in nb._fields_)


class Point(NestedBuffer, metaclass=NestedMeta):
    _fields_ = [
        ("<d", "x"),
        ("d", "y"),
    ]


class PolyHeader(NestedBuffer, metaclass=NestedMeta):
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
        npoints = struct.unpack("<i", f.read(4))[0]
        buf = f.read(Point.size * npoints)
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
        elif isinstance(record_type, type) and issubclass(record_type, NestedBuffer):
            for off in range(0, len(self._buffer), record_type.size):
                # fmt: off
                buf = self._buffer[off:off + record_type.size]
                # fmt: on
                yield record_type(buf)
        else:
            raise TypeError(f"{record_type}: Expected str or NestedBuffer")
