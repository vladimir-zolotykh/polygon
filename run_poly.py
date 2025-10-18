#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# PYTHON_ARGCOMPLETE_OK
from dataclasses import dataclass
import itertools
import struct
from typing import BinaryIO
from typing import TypeAlias, List

poly3 = [
    [(1.0, 2.5), (3.5, 4.0), (2.5, 1.5)],
    [(7.0, 1.2), (5.1, 3.0), (0.5, 7.5), (0.8, 9.0)],
    [(3.4, 5.3), (1.2, 0.5), (4.6, 9.2)],
]


@dataclass
class Point:
    x: float
    y: float


def find_bounding_box(
    poly: list[list[tuple[float, float]]],
) -> tuple[float, float, float, float]:
    """
    >>> find_bounding_box (poly3)
    (0.5, 0.5, 7.0, 9.2)
    """
    flat = list(itertools.chain(*poly))
    min_x = min((x for x, _ in flat))
    min_y = min((y for _, y in flat))
    max_x = max((x for x, _ in flat))
    max_y = max((y for _, y in flat))
    return min_x, min_y, max_x, max_y


@dataclass
class PolyHeader:
    code: str  # "file code"
    min_x: float
    min_y: float
    max_x: float
    max_y: float
    npoly: int  # number of polygons


def write_header(f: BinaryIO, ph: PolyHeader) -> BinaryIO:
    f.write(
        struct.pack(
            "<iddddi", ph.file_code, ph.min_x, ph.min_y, ph.max_x, ph.max_y, ph.npoly
        )
    )
    return f


HEADER_BIN = "header.bin"

PointType = tuple[float, float]
PolyType: TypeAlias = "PolyType | List[PolyType]"


def write_poly(filename=HEADER_BIN):
    with open(filename, "wb") as f:
        ph = PolyHeader(0x1234, *find_bounding_box(poly3), len(poly3))
        write_header(f, ph)
        polygons = poly3
        poly: list[PointType]
        for poly in polygons:
            point_struct = struct.Struct("<dd")
            sz = point_struct.size
            f.write(struct.pack("<i", sz * len(poly) + 4))
            pt: PointType
            for pt in poly:
                f.write(point_struct.pack(*pt))


def read_poly():
    pass


if __name__ == "__main__":
    import doctest

    doctest.testmod()
