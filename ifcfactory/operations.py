"""
Geometric Operations
===================

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

This module contains classes for geometric operations like transformations
and boolean operations.
"""

from __future__ import annotations

import warnings
from enum import Enum
from typing import List, Literal, Optional, Tuple, Union

import ifc5d.qto
import ifcopenshell
import ifcopenshell.api.feature
import ifcopenshell.api.geometry
import ifcopenshell.util.placement
import ifcopenshell.util.shape_builder
import numpy as np
from pydantic import model_validator

# Local imports
from .element import BIMFactoryElement
from ._internal.material_base import Style
from ._internal.primitives_base import (
    ElementInterface,
    Primitive,
    Profile,
    RepresentationItem,
    determine_type,
    get_qto_rules,
)


class BooleanOperationTypes(str, Enum):
    """Enumeration of supported boolean operations."""

    Union = "UNION"
    Intersection = "INTERSECTION"
    Difference = "DIFFERENCE"


class Translate(Primitive, RepresentationItem, Profile, ElementInterface):
    """Translation transformation that moves geometry by a specified vector."""

    item: Union[RepresentationItem, Profile, ElementInterface]
    vec: Union[Tuple[float, float], Tuple[float, float, float]]

    model_config = {"arbitrary_types_allowed": True}

    def build(self, model: ifcopenshell.file) -> ifcopenshell.entity_instance:
        """
        Build a translated representation by applying a translation vector.

        Args:
            model: The IFC model instance.

        Returns:
            ifcopenshell.entity_instance: The translated representation.

        Raises:
            Exception: If translation is not supported for the given geometry type.
        """
        # @todo currently not immutable/reentrant
        item = self.item.build(model)
        if item.is_a("IfcProduct"):
            m4 = ifcopenshell.util.placement.get_local_placement(item.ObjectPlacement)
            translation = np.eye(4)
            # Handle both 2D and 3D vectors
            if len(self.vec) == 2:
                translation[0:2, 3] = self.vec
            else:
                translation[0:3, 3] = self.vec
            ifcopenshell.api.geometry.edit_object_placement(model, item, matrix=translation @ m4)
        elif item.is_a("IfcTriangulatedFaceSet"):
            # Handle triangulated face sets by applying translation to vertices
            vertices = list(item.Coordinates.CoordList)
            translated_vertices = []

            # Handle both 2D and 3D vectors
            if len(self.vec) == 2:
                dx, dy = self.vec
                dz = 0.0
            else:
                dx, dy, dz = self.vec

            for i in range(0, len(vertices), 3):
                # Handle vertices as tuples
                if isinstance(vertices[i], tuple):
                    x, y, z = vertices[i]
                else:
                    x, y, z = vertices[i], vertices[i + 1], vertices[i + 2]
                translated_vertices.append([x + dx, y + dy, z + dz])

            # Create new triangulated face set with translated vertices
            coord_list = model.createIfcCartesianPointList3D(translated_vertices)
            return model.createIfcTriangulatedFaceSet(
                coord_list, item.Normals, item.Closed, item.CoordIndex, item.PnIndex
            )
        else:
            try:
                shape_builder = ifcopenshell.util.shape_builder.ShapeBuilder(model)
                shape_builder.translate(item, self.vec)
            except Exception as e:
                # If builder.translate fails, try to handle it as a triangulated face set
                if "is not supported for translate() method" in str(e):
                    raise Exception(
                        f"Translation not supported for {item.is_a()}. Consider using a different geometry type."
                    )
                else:
                    raise
        return item


class RotateZ(Primitive, RepresentationItem, Profile, ElementInterface):
    """Z-axis rotation transformation."""

    item: Union[RepresentationItem, Profile, ElementInterface]
    degrees: float

    # For accepting arbitrary types
    model_config = {"arbitrary_types_allowed": True}

    def build(self, model):
        # @todo currently not immutable/reentrant
        item = self.item.build(model)
        if item.is_a("IfcProduct"):
            m4 = ifcopenshell.util.placement.get_local_placement(item.ObjectPlacement)
            theta = np.deg2rad(self.degrees)
            rotation = np.array(
                [
                    [np.cos(theta), -np.sin(theta), 0.0, 0.0],
                    [np.sin(theta), np.cos(theta), 0.0, 0.0],
                    [0.0, 0.0, 1.0, 0.0],
                    [0.0, 0.0, 0.0, 1.0],
                ]
            )
            ifcopenshell.api.geometry.edit_object_placement(model, item, matrix=rotation @ m4)
        else:
            shape_builder = ifcopenshell.util.shape_builder.ShapeBuilder(model)
            shape_builder.rotate(item, angle=self.degrees, counter_clockwise=True)
        return item


class Transform(Primitive, RepresentationItem, Profile, ElementInterface):
    """Translation and rotation transformation that moves and rotates geometry."""

    item: Union[RepresentationItem, Profile, ElementInterface]
    vec: Union[Tuple[float, float], Tuple[float, float, float]]
    rotation: Optional[Tuple[float, Literal["X", "Y", "Z"]]] = None  # (angle, axis) where axis is "X", "Y", or "Z"

    # For accepting item
    model_config = {"arbitrary_types_allowed": True}

    def build(self, model: ifcopenshell.file) -> ifcopenshell.entity_instance:
        """
        Build a translated and/or rotated representation by applying a translation vector and optional rotation.

        Args:
            model: The IFC model instance.

        Returns:
            ifcopenshell.entity_instance: The transformed representation.

        Raises:
            Exception: If transformation is not supported for the given geometry type.
        """
        # @todo currently not immutable/reentrant
        item = self.item.build(model)
        if item.is_a("IfcProduct"):
            m4 = ifcopenshell.util.placement.get_local_placement(item.ObjectPlacement)
            transform = np.eye(4)
            # Handle both 2D and 3D vectors
            if len(self.vec) == 2:
                transform[0:2, 3] = self.vec
            else:
                transform[0:3, 3] = self.vec

            # Apply rotation if specified
            if self.rotation and self.rotation[0] != 0:
                angle, axis = self.rotation
                rotation = ifcopenshell.util.placement.rotation(angle, axis)
                transform = rotation @ transform

            ifcopenshell.api.geometry.edit_object_placement(model, item, matrix=transform @ m4)
        elif item.is_a("IfcTriangulatedFaceSet"):
            # Handle triangulated face sets by applying transformation to vertices
            vertices = list(item.Coordinates.CoordList)
            transformed_vertices = []

            # Handle both 2D and 3D vectors
            if len(self.vec) == 2:
                dx, dy = self.vec
                dz = 0.0
            else:
                dx, dy, dz = self.vec

            # Build transformation matrix for vertices
            transform_matrix = np.eye(4)
            transform_matrix[0:3, 3] = [dx, dy, dz]

            # Apply rotation if specified
            if self.rotation and self.rotation[0] != 0:
                angle, axis = self.rotation
                rotation_matrix = ifcopenshell.util.placement.rotation(angle, axis)
                transform_matrix = rotation_matrix @ transform_matrix

            for i in range(0, len(vertices), 3):
                # Handle vertices as tuples
                if isinstance(vertices[i], tuple):
                    x, y, z = vertices[i]
                else:
                    x, y, z = vertices[i], vertices[i + 1], vertices[i + 2]

                # Apply transformation matrix to vertex
                vertex = np.array([x, y, z, 1.0])
                transformed_vertex = transform_matrix @ vertex
                transformed_vertices.append(
                    [
                        transformed_vertex[0],
                        transformed_vertex[1],
                        transformed_vertex[2],
                    ]
                )

            # Create new triangulated face set with transformed vertices
            coord_list = model.createIfcCartesianPointList3D(transformed_vertices)
            return model.createIfcTriangulatedFaceSet(
                coord_list, item.Normals, item.Closed, item.CoordIndex, item.PnIndex
            )
        else:
            try:
                shape_builder = ifcopenshell.util.shape_builder.ShapeBuilder(model)
                shape_builder.translate(item, self.vec)
                # Note: builder.rotate() might not exist, so we handle rotation separately
                if self.rotation and self.rotation[0] != 0:
                    # For non-IFC products, rotation might need special handling
                    warnings.warn(f"Rotation not fully supported for {item.is_a()}")
            except Exception as e:
                # If builder.translate fails, try to handle it as a triangulated face set
                if "is not supported for translate() method" in str(e):
                    raise Exception(
                        f"Transformation not supported for {item.is_a()}. Consider using a different geometry type."
                    )
                else:
                    raise
        return item


class Boolean(Primitive, RepresentationItem, Profile, ElementInterface):
    """Boolean operation that combines multiple geometry elements."""

    operation: BooleanOperationTypes
    children: List[Union[RepresentationItem, Profile, ElementInterface]]
    qsets: bool = False

    # For accepting children types
    model_config = {"arbitrary_types_allowed": True}

    @model_validator(mode="after")
    def valid_operands(self) -> "Boolean":
        """
        Validate that all children are of consistent types for boolean operations.

        Returns:
            Boolean: The validated boolean operation instance.

        Raises:
            ValueError: If children contain mixed types that cannot be combined.
        """
        ty = determine_type(self)
        if ty is None:
            raise ValueError("Invalid type configuration")
        if ty is Profile and self.operation == BooleanOperationTypes.Intersection:
            raise ValueError("Intersections not support on profiles")
        if ty is ElementInterface:
            if self.operation != BooleanOperationTypes.Difference:
                raise ValueError("Only difference supported on elements")
            for ch in self.children[1:]:
                # Unwrap Translate and Style wrappers to get the actual element
                current_ch = ch
                while isinstance(current_ch, (Translate, Style)):
                    current_ch = current_ch.item

                # Now check if it's a BIMFactoryElement with the correct type
                if not isinstance(current_ch, BIMFactoryElement) or current_ch.type != "IfcOpeningElement":
                    raise ValueError("Only opening elements are supported as second operand element children")
        return self

    def build(self, model: ifcopenshell.file) -> ifcopenshell.entity_instance:
        """
        Build a boolean operation representation.

        Args:
            model: The IFC model instance.

        Returns:
            ifcopenshell.entity_instance: The created boolean operation representation.
        """
        ty = determine_type(self)
        chs = [ch.build(model) for ch in self.children]
        if ty == Profile:
            if self.operation == BooleanOperationTypes.Difference:
                # @todo this discards inner curves and ignores other profile types
                chs = [(inst.OuterCurve if inst.is_a("IfcArbitraryClosedProfileDef") else inst) for inst in chs]
                return model.createIfcArbitraryProfileDefWithVoids("AREA", None, chs[0], chs[1:])
            else:
                chs = [
                    (model.createIfcArbitraryClosedProfileDef("AREA", None, inst) if inst.is_a("IfcCurve") else inst)
                    for inst in chs
                ]
                return model.createIfcCompositeProfileDef("AREA", None, chs, None)
        if ty == ElementInterface:
            element = chs[0]
            for op in chs[1:]:
                ifcopenshell.api.feature.add_feature(model, feature=op, element=element)

            # calculate quantities (optional when qsets=True)
            if self.qsets:
                ifc5d.qto.edit_qtos(
                    model,
                    ifc5d.qto.quantify(model, {element}, get_qto_rules(model)),
                )
            return element
        if ty == RepresentationItem:
            left = chs.pop(0)
            while chs:
                left = model.createIfcBooleanResult(self.operation.value, left, chs.pop(0))
            return left

        # This should never be reached, but ensures the method always returns the correct type
        raise ValueError(f"Unsupported boolean operation type: {ty}")
