#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# PYTHON_ARGCOMPLETE_OK


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
