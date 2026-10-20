import math
import os
import sys

import ifcopenshell
import numpy as np
import pytest
import shapely

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if project_root not in map(os.path.abspath, sys.path):
    sys.path.insert(0, project_root)

from ifcfactory import PolylineOffset  # noqa: E402


def centerline_length(points):
    return sum(math.dist(a, b) for a, b in zip(points, points[1:]))


def test_l_shape_outline():
    outer, voids = PolylineOffset(points=[(0.0, 0.0), (4.0, 0.0), (4.0, 3.0)], offset=0.15).rings()
    assert voids == []
    expected = [(0.0, 0.15), (3.85, 0.15), (3.85, 3.0), (4.15, 3.0), (4.15, -0.15), (0.0, -0.15)]
    assert shapely.Polygon(outer).equals(shapely.Polygon(expected))


def test_mitered_area_is_length_times_thickness():
    points = [(0.0, 0.0), (4.0, 0.0), (4.0, 3.0), (7.0, 5.0), (4.0, 7.0)]
    outer, _ = PolylineOffset(points=points, offset=0.15).rings()
    assert len(outer) == 2 * len(points)
    assert shapely.Polygon(outer).area == pytest.approx(centerline_length(points) * 0.30)


def test_sharp_corner_is_cut_off_at_miter_limit():
    corner, incoming, outgoing = np.array([4.0, 0.0]), np.array([1.0, 0.0]), np.array([-4.0, 0.35])
    wall = PolylineOffset(points=[(0.0, 0.0), tuple(corner), (0.0, 0.35)], offset=0.15)
    outer, _ = wall.rings()
    bisector = incoming - outgoing / np.linalg.norm(outgoing)
    bisector /= np.linalg.norm(bisector)
    reach = max(float(np.dot(np.array(p) - corner, bisector)) for p in outer)
    assert reach == pytest.approx(wall.miter_limit * wall.offset)


def test_reversal_gives_single_strip():
    outer, voids = PolylineOffset(points=[(0.0, 0.0), (4.0, 0.0), (0.0, 0.0)], offset=0.15).rings()
    assert voids == []
    assert shapely.Polygon(outer).area == pytest.approx(4.0 * 0.30)


def test_too_few_points_is_rejected():
    with pytest.raises(ValueError, match="at least 2 points"):
        PolylineOffset(points=[(0.0, 0.0)], offset=0.15)


def test_degenerate_centerline_is_rejected():
    with pytest.raises(ValueError, match="single wall outline"):
        PolylineOffset(points=[(1.0, 1.0), (1.0, 1.0)], offset=0.15)


@pytest.mark.parametrize("clockwise", [False, True])
def test_closed_centerline_gives_ring_with_void(clockwise):
    square = [(0.0, 0.0), (4.0, 0.0), (4.0, 3.0), (0.0, 3.0), (0.0, 0.0)]
    if clockwise:
        square = square[::-1]
    wall = PolylineOffset(points=square, offset=0.15)
    outer, voids = wall.rings()
    assert len(voids) == 1
    assert shapely.Polygon(outer).area == pytest.approx(4.3 * 3.3)
    assert shapely.Polygon(voids[0]).area == pytest.approx(3.7 * 2.7)

    profile = wall.build(ifcopenshell.file(schema="IFC4"))
    assert profile.is_a("IfcArbitraryProfileDefWithVoids")
    assert len(profile.InnerCurves) == 1
