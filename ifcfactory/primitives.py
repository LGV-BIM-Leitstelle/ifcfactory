"""
Primitive Geometry Objects
=========================

Copyright (C) 2025 Freie und Hansestadt Hamburg, Landesbetrieb Geoinformation und Vermessung
BIM-Leitstelle, Ahmed Salem <ahmed.salem@gv.hamburg.de>

Developed in collaboration with Thomas Krijnen <mail@thomaskrijnen.com>

This library is free software; you can redistribute it and/or
modify it under the terms of the GNU Lesser General Public
License as published by the Free Software Foundation; either
version 2.1 of the License, or (at your option) any later version.

This library is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
Lesser General Public License for more details.

You should have received a copy of the GNU Lesser General Public
License along with this library; if not, write to the Free Software
Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301  USA

This module contains all the primitive geometry objects for composable geometry creation.
These classes can be used to build complex geometry arrangements in a
declarative, composable way.
"""

from __future__ import annotations

from typing import Any, List, Tuple, Union

import ifcopenshell
import ifcopenshell.api.aggregate
import ifcopenshell.api.feature
import ifcopenshell.api.geometry
import ifcopenshell.api.material
import ifcopenshell.api.project
import ifcopenshell.api.pset
import ifcopenshell.api.root
import ifcopenshell.api.spatial
import ifcopenshell.api.style
import ifcopenshell.api.type
import ifcopenshell.util.placement
import ifcopenshell.util.representation
import ifcopenshell.util.shape_builder
import ifcopenshell.util.unit
import numpy as np
from icosphere import icosphere as icosphere_lib
from pydantic import Field, PositiveFloat, model_validator

from .operations import Transform
from ._internal.primitives_base import Primitive, Profile, RepresentationItem


class Rect(Primitive, Profile):
    """Rectangular profile definition for extrusion operations."""

    width: PositiveFloat
    height: PositiveFloat

    def build(self, model: ifcopenshell.file) -> ifcopenshell.entity_instance:
        """
        Build a rectangular profile definition.

        Args:
            model: The IFC model instance.

        Returns:
            ifcopenshell.entity_instance: The created rectangular profile.
        """
        builder = ifcopenshell.util.shape_builder.ShapeBuilder(model)
        return builder.rectangle(size=(self.width, self.height))


class Circle(Primitive, Profile):
    """Circular profile definition for extrusion operations."""

    radius: PositiveFloat

    def build(self, model: ifcopenshell.file) -> ifcopenshell.entity_instance:
        """
        Build a circular profile definition.

        Args:
            model: The IFC model instance.

        Returns:
            ifcopenshell.entity_instance: The created circular profile definition.
        """
        return model.createIfcCircleProfileDef(
            "AREA",
            None,
            model.createIfcAxis2Placement2D(model.createIfcCartesianPoint((0.0, 0.0))),
            self.radius,
        )


class Ellipse(Primitive, Profile):
    """Elliptical profile definition for extrusion operations."""

    semi_axis1: PositiveFloat
    semi_axis2: PositiveFloat

    def build(self, model: ifcopenshell.file) -> ifcopenshell.entity_instance:
        """
        Build an elliptical profile definition.

        Args:
            model: The IFC model instance.

        Returns:
            ifcopenshell.entity_instance: The created elliptical profile definition.
        """
        return model.createIfcEllipseProfileDef(
            "AREA",
            None,
            model.createIfcAxis2Placement2D(model.createIfcCartesianPoint((0.0, 0.0))),
            self.semi_axis1,
            self.semi_axis2,
        )


class Polygon(Primitive, Profile):
    """Polygon profile with arbitrary number of points"""

    points: List[Tuple[float, float]]

    @model_validator(mode="after")
    def validate_points(self) -> "Polygon":
        """
        Validate that the polygon has at least 3 points.

        Returns:
            Polygon: The validated polygon instance.

        Raises:
            ValueError: If the polygon has fewer than 3 points.
        """
        if len(self.points) < 3:
            raise ValueError("Polygon must have at least 3 points")
        return self

    def build(self, model: ifcopenshell.file) -> ifcopenshell.entity_instance:
        """
        Build a polygon profile definition.

        Args:
            model: The IFC model instance.

        Returns:
            ifcopenshell.entity_instance: The created polygon profile definition.
        """
        # Create a polyline from the points
        points = [model.createIfcCartesianPoint((float(x), float(y))) for x, y in self.points]
        # Close the polygon by adding the first point at the end
        if points[0].Coordinates != points[-1].Coordinates:
            points.append(points[0])

        polyline = model.createIfcPolyline(points)
        return model.createIfcArbitraryClosedProfileDef("AREA", None, polyline)


# Representation Item Classes
class Extrusion(Primitive, RepresentationItem):
    """Extrusion representation item that creates 3D geometry from 2D profiles."""

    basis: Profile
    depth: PositiveFloat

    # For accepting Profile types
    model_config = {"arbitrary_types_allowed": True}

    def build(self, model: ifcopenshell.file) -> ifcopenshell.entity_instance:
        """
        Build an extrusion representation from a 2D profile.

        Args:
            model: The IFC model instance.

        Returns:
            ifcopenshell.entity_instance: The created extrusion representation.

        Raises:
            TypeError: If the basis is not a valid profile type.
        """
        builder = ifcopenshell.util.shape_builder.ShapeBuilder(model)
        # @todo can we make this type check in pydantic, is it even necessary?
        basis = self.basis.build(model)
        if basis.is_a("IfcCurve"):
            basis = model.createIfcArbitraryClosedProfileDef("AREA", None, basis)
        elif basis.is_a("IfcProfileDef"):
            pass
        else:
            raise TypeError(f"Instance of type {basis.is_a()} not allowed as extrusion basis")
        return builder.extrude(basis, self.depth)


class Box(Primitive, RepresentationItem):
    """Box representation item with width, depth, and height."""

    width: PositiveFloat
    depth: PositiveFloat
    height: PositiveFloat

    def build(self, model: ifcopenshell.file) -> ifcopenshell.entity_instance:
        """
        Build a box representation by extruding a rectangular profile.

        Args:
            model: The IFC model instance.

        Returns:
            ifcopenshell.entity_instance: The created box representation.
        """
        return Extrusion(basis=Rect(width=self.width, height=self.depth), depth=self.height).build(model)


class Cube(Primitive, RepresentationItem):
    """Cube representation item with equal dimensions on all sides."""

    size: PositiveFloat

    def build(self, model: ifcopenshell.file) -> ifcopenshell.entity_instance:
        """
        Build a cube representation with equal width, depth, and height.

        Args:
            model: The IFC model instance.

        Returns:
            ifcopenshell.entity_instance: The created cube representation.
        """
        return Box(width=self.size, height=self.size, depth=self.size).build(model)


class ExtrudedNgonAsMesh(Primitive, RepresentationItem):
    """Extruded N-gon as mesh representation."""

    basis: List[Tuple[float, float, float]] = Field(default_factory=list)
    height: float

    def create_mesh(self):
        """Create a polygonal cylinder mesh (ngon extruded)"""
        basis = self.basis
        if basis[0] == basis[-1]:  # remove duplicate closing point if present
            basis = basis[:-1]

        n_segments = len(basis)
        top = (np.array(basis) + (0.0, 0.0, self.height)).tolist()
        vertices = basis + top
        faces: List[Any] = []

        # Side walls
        for i in range(n_segments):
            next_i = (i + 1) % n_segments
            faces.append((i, next_i, i + n_segments))
            faces.append((next_i, next_i + n_segments, i + n_segments))

        # Bottom face (reverse to face downward)
        faces.append(list(range(n_segments))[::-1])

        # Top face (also reversed to face upward)
        faces.append(list(range(n_segments, 2 * n_segments)))

        return vertices, faces

    def build(self, model):
        vertices, faces = self.create_mesh()
        # Import here to avoid circular imports
        return MeshRepresentation(vertices=vertices, faces=faces).build(model)


class NgonCylinder(ExtrudedNgonAsMesh):
    """Ngon extruded cylinder primitive"""

    radius: float
    segments: int = 8

    def __init__(self, **data):
        super().__init__(**data)
        angle_step = 2 * np.pi / self.segments
        angles = np.arange(self.segments) * angle_step
        x = self.radius * np.cos(angles)
        y = self.radius * np.sin(angles)
        z = np.zeros_like(x)
        self.basis = np.stack((x, y, z), axis=1).tolist()


class Cylinder(Primitive, RepresentationItem):
    """Cylinder representation item created by extruding a circular profile."""

    radius: float
    height: float

    def build(self, model: ifcopenshell.file) -> ifcopenshell.entity_instance:
        """
        Build a cylinder representation by extruding a circular profile.
        Cylinders are automatically centered so their center is at the origin.

        Args:
            model: The IFC model instance.

        Returns:
            ifcopenshell.entity_instance: The created cylinder representation.
        """
        cylinder = Extrusion(basis=Circle(radius=self.radius), depth=self.height)

        # translate it so the base is at z=0 and the center is at the origin
        return Transform(translation=(0.0, 0.0, 0.0), item=cylinder).build(model)


class EllipticalCylinder(Primitive, RepresentationItem):
    """Elliptical cylinder representation item created by extruding an elliptical profile."""

    semi_axis1: float
    semi_axis2: float
    height: float

    def build(self, model: ifcopenshell.file) -> ifcopenshell.entity_instance:
        """
        Build an elliptical cylinder representation by extruding an elliptical profile.
        Elliptical cylinders are automatically centered so their center is at the origin.

        Args:
            model: The IFC model instance.

        Returns:
            ifcopenshell.entity_instance: The created elliptical cylinder representation.
        """
        elliptical_cylinder = Extrusion(
            basis=Ellipse(semi_axis1=self.semi_axis1, semi_axis2=self.semi_axis2),
            depth=self.height,
        )

        # translate it so the base is at z=0 and the center is at the origin
        return Transform(translation=(0.0, 0.0, 0.0), item=elliptical_cylinder).build(model)


class Sphere(Primitive, RepresentationItem):
    """Icosphere representation item with configurable detail level."""

    radius: float
    detail: int = 1

    def create_mesh(self) -> Tuple[List[Tuple[float, float, float]], List[List[int]]]:
        """
        Create an icosphere mesh.

        Returns:
            Tuple containing:
                - List of vertex coordinates as (x, y, z) tuples
                - List of face indices as lists
        """
        vertices, faces = icosphere_lib(self.detail)
        vertices = [tuple(map(float, v)) for v in vertices]
        faces = [list(map(int, f)) for f in faces]
        # Scale vertices to the given radius
        vertices = [(x * self.radius, y * self.radius, z * self.radius) for (x, y, z) in vertices]
        return vertices, faces

    def build(self, model: ifcopenshell.file) -> ifcopenshell.entity_instance:
        """
        Build a sphere representation.

        Args:
            model: The IFC model instance.

        Returns:
            ifcopenshell.entity_instance: The created sphere representation.
        """
        vertices, faces = self.create_mesh()
        return MeshRepresentation(vertices=vertices, faces=faces).build(model)


class MeshRepresentation(Primitive, RepresentationItem):
    """Container for mesh geometry data with vertices and faces."""

    # @todo these are default-initialized so that subclasses can be defined that later overwrite these
    # attributes in model_post_init() without having something passed to their __init__() calls.
    vertices: List[Tuple[float, float, float]] = Field(default_factory=list)
    faces: List[Union[List[int], List[List[int]]]] = Field(default_factory=list)

    def build(self, model: ifcopenshell.file) -> ifcopenshell.entity_instance:
        """
        Build a mesh representation from vertices and faces.

        Args:
            model: The IFC model instance.

        Returns:
            ifcopenshell.entity_instance: The created mesh representation.
        """
        builder = ifcopenshell.util.shape_builder.ShapeBuilder(model)
        return builder.mesh(self.vertices, self.faces)
