import os
import sys

import ifcopenshell
import ifcopenshell.geom
import numpy as np
import pytest

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if project_root not in map(os.path.abspath, sys.path):
    sys.path.insert(0, project_root)

from ifcfactory import SweptDisk  # noqa: E402

FRAME = [(-0.5, 0.0, 0.0), (-0.5, 0.0, 1.0), (0.5, 0.0, 1.0), (0.5, 0.0, 0.0)]


def bounding_box(model, item):
    settings = ifcopenshell.geom.settings()
    shape = ifcopenshell.geom.create_shape(settings, item)
    vertices = np.array(shape.verts).reshape(-1, 3)
    return vertices.min(axis=0), vertices.max(axis=0)


def test_builds_swept_disk_solid_along_path():
    model = ifcopenshell.file(schema="IFC4")
    solid = SweptDisk(points=FRAME, radius=0.05).build(model)
    assert solid.is_a("IfcSweptDiskSolid")
    assert solid.Radius == pytest.approx(0.05)
    assert [tuple(p) for p in solid.Directrix.Points.CoordList] == FRAME

    low, high = bounding_box(model, solid)
    # The disk is capped flat across the path, so the legs end exactly at z=0.
    assert low == pytest.approx((-0.55, -0.05, 0.0), abs=1e-3)
    assert high == pytest.approx((0.55, 0.05, 1.05), abs=1e-3)


def test_arc_point_becomes_arc_segment():
    model = ifcopenshell.file(schema="IFC4")
    path = [(0.0, 0.0, 0.0), (0.0, 0.0, 0.6), (0.0, 0.4, 1.0), (0.0, 0.6, 1.0), (0.0, 1.0, 1.0)]
    solid = SweptDisk(points=path, radius=0.03, arc_points=[2]).build(model)
    segments = solid.Directrix.Segments
    assert [s.is_a() for s in segments].count("IfcArcIndex") == 1


def test_too_few_points_is_rejected():
    with pytest.raises(ValueError, match="at least 2 points"):
        SweptDisk(points=[(0.0, 0.0, 0.0)], radius=0.05)


@pytest.mark.parametrize("index", [0, 3, 7])
def test_arc_point_at_end_is_rejected(index):
    with pytest.raises(ValueError, match="inner points"):
        SweptDisk(points=FRAME, radius=0.05, arc_points=[index])


def test_non_positive_radius_is_rejected():
    with pytest.raises(ValueError):
        SweptDisk(points=FRAME, radius=0.0)
