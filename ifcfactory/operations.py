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
from typing import List, Optional, Tuple, Union

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


class Transform(Primitive, RepresentationItem, Profile, ElementInterface):
    """Translation and rotation transformation that moves and rotates geometry."""

    item: Union[RepresentationItem, Profile, ElementInterface]
    translation: Optional[Union[Tuple[float, float], Tuple[float, float, float]]] = None
    rotation: Optional[Tuple[Union[int, float], str]] = None  # (angle in degrees, axis: "X", "Y", or "Z")

    # For accepting item
    model_config = {"arbitrary_types_allowed": True}

    @model_validator(mode="after")
    def validate_rotation_axis(self) -> "Transform":
        """Validate that rotation axis is X, Y, or Z."""
        if self.rotation is not None:
            _, axis = self.rotation
            if axis not in ("X", "Y", "Z"):
                raise ValueError(f"Rotation axis must be 'X', 'Y', or 'Z', got '{axis}'")
        return self

    def build(self, model: ifcopenshell.file) -> ifcopenshell.entity_instance:
        """
        Build a translated and/or rotated representation by applying a translation vector and/or optional rotation.
        In terms of order: first rotation is applied (around local origin), then translation.

        Args:
            model: The IFC model instance.

        Returns:
            ifcopenshell.entity_instance: The transformed representation.

        Raises:
            Exception: If transformation is not supported for the given geometry type.
        """
        item = self.item.build(model)
        
        has_rotation = self.rotation is not None and abs(self.rotation[0]) > 1.e-9
        has_translation = self.translation is not None

        transform = np.eye(4)

        if has_rotation:
            angle, axis = self.rotation
            transform = ifcopenshell.util.placement.rotation(angle, axis)

        if has_translation:
            transform[0:len(self.translation), 3] = self.translation

        if item.is_a("IfcProduct"):
            # @todo currently not immutable/reentrant
            m4 = ifcopenshell.util.placement.get_local_placement(item.ObjectPlacement)
            ifcopenshell.api.geometry.edit_object_placement(model, item, matrix=transform @ m4)
        elif item.is_a("IfcTessellatedFaceSet"):
            # Handle triangulated face sets by applying transformation to vertices
            vertices = np.array(list(item.Coordinates.CoordList))
            # Homogenize coordinates (add column of 1s for 4x4 matrix multiplication)
            vertices = np.column_stack((vertices, np.ones(len(vertices))))
            transformed_vertices = np.array([transform @ v for v in vertices]).tolist()
            # Create new triangulated/tessellated face set with transformed vertices
            # with remaining attributes copied over from the original instance
            coord_list = model.createIfcCartesianPointList3D(transformed_vertices)
            return model.create_entity(item.is_a(),
                coord_list, *list(item)[1:]
            )
        else:
            # @todo currently not immutable/reentrant
            shape_builder = ifcopenshell.util.shape_builder.ShapeBuilder(model)
            if has_rotation:
                angle, axis = self.rotation
                if axis == "Z":
                    # NB: May raise Exception(f"{c} is not supported for rotate() method.")
                    shape_builder.rotate(item, angle, counter_clockwise=True)
                else:
                    raise Exception(f"Rotation around axis other than Z not supported for {item.is_a()}")
            if has_translation:
                # NB: May raise Exception(f"{c} is not supported for translate() method.")
                shape_builder.translate(item, self.translation)
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
                # Unwrap Transform and Style wrappers to get the actual element
                current_ch = ch
                while isinstance(current_ch, (Transform, Style)):
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
