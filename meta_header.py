#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# PYTHON_ARGCOMPLETE_OK
from typing import BinaryIO
import struct


class Chunk:
    def __init__(self, format, offset):
        self.format: str = format  # e.g., "<i"
        self.offset: int = offset

    def __get__(self, instance, owner):
        if instance is None:
            return self
        tup = struct.unpack_from(
            # fmt: off
            self.format, instance._buffer[self.offset:]
            # fmt: on
        )  # always a tupple
        if len(tup) == 1:
            return tup[0]
        else:
            return tup


class MetaHeader(type):
    def __init__(cls, clsname, bases, clsdict):
        offset = 0
        byte_code = ""
        for format, field_name in cls._fields_:
            if format[0] in ("<", ">", "!", "@"):
                byte_code = format[0]
                format = format[1:]
            format = byte_code + format
            setattr(cls, field_name, Chunk(format, offset))
            offset += struct.calcsize(format)
        setattr(cls, "size", offset)


class HeaderBuffer:
    def __init__(self, buffer):
        self._buffer = memoryview(buffer)

    @classmethod
    def from_file(cls, f: BinaryIO):
        return cls(f.read(cls.size))

    def as_tuple(self):
        return (self.code, self.min_x, self.min_y, self.max_x, self.max_y, self.npoly)


class PolyHeader(HeaderBuffer, metaclass=MetaHeader):
    _fields_ = [
        ("<i", "code"),
        ("d", "min_x"),
        ("d", "min_y"),
        ("d", "max_x"),
        ("d", "max_y"),
        ("i", "npoly"),
    ]
