#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# PYTHON_ARGCOMPLETE_OK
# from __future__ import annotations
import os
from dataclasses import dataclass, astuple
import itertools
import struct
from typing import BinaryIO
import unittest
import meta_header as MH
import nested as NT

HEADER_BIN = "header.bin"
POLYGON_BIN = "polygon.bin"
PointType = tuple[float, float]
PolyType = list[list[PointType]]
poly3: PolyType = [
    [(1.0, 2.5), (3.5, 4.0), (2.5, 1.5)],
    [(7.0, 1.2), (5.1, 3.0), (0.5, 7.5), (0.8, 9.0)],
    [(3.4, 5.3), (1.2, 0.5), (4.6, 9.2)],
]
point_struct = struct.Struct("<dd")
header_struct = struct.Struct("<iddddi")


@dataclass
class Point:
    x: float
    y: float


def find_bounding_box(poly: PolyType) -> tuple[float, float, float, float]:
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
    code: int  # "file code"
    min_x: float
    min_y: float
    max_x: float
    max_y: float
    npoly: int  # number of polygons


def _make_default_header(poly=poly3) -> PolyHeader:
    return PolyHeader(0x1234, *find_bounding_box(poly), len(poly))


def write_header(f: BinaryIO, ph: PolyHeader = _make_default_header()) -> BinaryIO:
    f.write(
        header_struct.pack(ph.code, ph.min_x, ph.min_y, ph.max_x, ph.max_y, ph.npoly)
    )
    return f


def write_poly(f: BinaryIO) -> None:
    ph = PolyHeader(0x1234, *find_bounding_box(poly3), len(poly3))
    write_header(f, ph)
    polygons = poly3
    poly: list[PointType]
    for poly in polygons:
        f.write(struct.pack("<i", len(poly)))
        pt: PointType
        for pt in poly:
            f.write(point_struct.pack(*pt))


HEADER_SIZE = header_struct.size


def read_header(f: BinaryIO) -> PolyHeader:
    return PolyHeader(*header_struct.unpack(f.read(HEADER_SIZE)))


def read_poly(f: BinaryIO) -> PolyType:
    ph: NT.PolyHeader = NT.PolyHeader.from_file(f)
    polygons: PolyType = []
    for i in range(ph.npoly):
        points: list[NT.Point] = []
        for pt in NT.SizedRecord.from_file(f).iter_as(NT.Point):
            points.append(pt.as_tuple())
        polygons.append(points)
    return polygons


class TestPoly(unittest.TestCase):
    def setUp(self):
        with open(HEADER_BIN, "wb") as f:
            write_header(f, _make_default_header())
        with open(POLYGON_BIN, "wb") as f:
            write_poly(f)

    def tearDown(self):
        os.remove(HEADER_BIN)
        os.remove(POLYGON_BIN)

    def test_10_read_nested_header(self):
        with open(HEADER_BIN, "rb") as f:
            nh: NT.PolyHeader = NT.PolyHeader.from_file(f)
            res = nh.code, *nh.xy1.as_tuple(), *nh.xy2.as_tuple(), nh.npoly
            self.assertEqual(res, astuple(_make_default_header()))

    def test_30_read_header(self):
        with open(HEADER_BIN, "rb") as f:
            self.assertEqual(read_header(f), _make_default_header())

    def test_40_read_poly(self):
        with open(POLYGON_BIN, "rb") as f:
            self.assertEqual(read_poly(f), poly3)


if __name__ == "__main__":
    unittest.main()
