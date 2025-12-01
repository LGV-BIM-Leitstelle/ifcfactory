"""
Primitives Base Classes and Utilities
=====================================

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

This module contains the abstract base classes and core functionality
for the BIM factory geometry system, along with helper functions and utilities
for building IFC elements from primitive geometry objects.
"""

from __future__ import annotations

import sys
from abc import ABC, abstractmethod
from typing import Any, Optional, Type, Union

import ifc5d.qto
import ifcopenshell
import ifcopenshell.util.unit
import pint
from pydantic import BaseModel

from .unit_base import pint_to_ifc


class Profile(ABC):
    """Abstract base class for 2D profile definitions used in extrusion operations."""

    @abstractmethod
    def build(self, model: ifcopenshell.file) -> ifcopenshell.entity_instance:
        """
        Build the profile definition in the IFC model.

        Args:
            model: The IFC model instance.

        Returns:
            ifcopenshell.entity_instance: The created profile definition.
        """


class RepresentationItem(ABC):
    """Abstract base class for IFC representation items."""

    @abstractmethod
    def build(self, model: ifcopenshell.file) -> ifcopenshell.entity_instance:
        """
        Build the representation item in the IFC model.

        Args:
            model: The IFC model instance.

        Returns:
            ifcopenshell.entity_instance: The created representation item.
        """


class ElementInterface(ABC):
    """Abstract base class for IFC element interfaces."""

    @abstractmethod
    def build(self, model: ifcopenshell.file) -> ifcopenshell.entity_instance:
        """
        Build the element in the IFC model.

        Args:
            model: The IFC model instance.

        Returns:
            ifcopenshell.entity_instance: The created element.
        """


class Primitive(BaseModel):
    """Base class for all primitive geometry objects."""

    def children_of_type(self, ty: Type):
        """Get all children of a specific type."""
        if isinstance(self, ty):
            yield self
        for child in getattr(self, "children", ()):
            yield from child.children_of_type(ty)
        if child := getattr(self, "item", ()):
            yield from child.children_of_type(ty)


class CachingMixin(ABC):
    """Mixin class that provides caching functionality for IFC building operations."""

    _cache: dict = {}

    @abstractmethod
    def _build(self, model, builder):
        """Abstract method that should be implemented by subclasses."""
        pass

    def build(self, model, builder):
        """Build with caching support."""
        self._cache = getattr(self, "_cache", {})

        # evict cache items for files that have been garbage collected
        cache_key = model.identifier if hasattr(model, "identifier") else model.wrapped_data.file_pointer()
        live_files = sys.modules["ifcopenshell.file"].file_dict
        live_file_ids = (
            ((kk, vv[1]) for kk, vv in live_files.items()) if hasattr(model, "identifier") else live_files.keys()
        )
        for k in list(self._cache.keys()):
            if k not in live_file_ids:
                del self._cache[k]

        if result := self._cache.get(cache_key):
            return model[result]
        else:
            result = self._build(model, builder)
            # We don't actually cache the instance, because that would
            # prevent from freeing the file. We just capture the id
            # that we can use to retrieve the instance from the file
            # later on
            self._cache[cache_key] = result.id()
            return result


def determine_type(
    element: object,
) -> Union[Type[Profile], Type[RepresentationItem], Type[ElementInterface]]:
    """
    Determine the type of geometry element by checking its inheritance.

    This function analyzes an element to determine whether it inherits from
    Profile, RepresentationItem, or ElementInterface. It handles complex cases
    with children and nested items.

    Args:
        element: The geometry element to analyze.

    Returns:
        The type class (Profile, RepresentationItem, or ElementInterface) that the element inherits from.

    Raises:
        TypeError: If the element type cannot be determined or if there are inconsistent child types.
    """
    kinds = (Profile, RepresentationItem, ElementInterface)
    is_ = [isinstance(element, kind) for kind in kinds]
    if sum(is_) == 1:
        return kinds[next(k for k, v in enumerate(is_) if v)]
    elif sum(is_) == 0:
        raise TypeError(f"Element of type {type(element).__name__} not supported")
    elif children := getattr(element, "children", None):
        child_types = set(map(determine_type, children))
        if len(child_types) == 1:
            return next(iter(child_types))
        else:
            raise TypeError(f"Inconsistent child types on {type(element).__name__}")
    elif item := getattr(element, "item", None):
        return determine_type(item)
    else:
        raise TypeError(f"Element of type {type(element).__name__} not supported")


def get_type_bearing_element(element, indent=0) -> Optional[Union[Profile, RepresentationItem, ElementInterface]]:
    """Get the type-bearing element from nested structures."""
    kinds = (Profile, RepresentationItem, ElementInterface)
    is_ = [isinstance(element, kind) for kind in kinds]
    if sum(is_) == 1:
        return element
    elif sum(is_) == 0:
        return None
    elif children := getattr(element, "children", None):
        # Check if element is a Boolean operation by class name to avoid circular imports
        is_boolean = element.__class__.__name__ == "Boolean"

        if len(children) == 1 or is_boolean:
            return get_type_bearing_element(children[0], indent=indent + 4)
        else:
            return None
    elif item := getattr(element, "item", None):
        return get_type_bearing_element(item, indent=indent + 4)
    else:
        return None


def get_qto_rules(model: ifcopenshell.file):
    """Get the appropriate QTO rules based on the model schema."""
    schema_upper = model.schema.upper()
    if schema_upper == "IFC4":
        return ifc5d.qto.rules["IFC4QtoBaseQuantities"]
    elif schema_upper == "IFC4X3":
        return ifc5d.qto.rules["IFC4X3QtoBaseQuantities"]
    else:
        return ifc5d.qto.rules["IFC4QtoBaseQuantities"]


def yield_super_types(declaration: Any):
    """Yield all super types for an IFC declaration."""
    yield declaration.name()
    if hasattr(declaration, "supertype") and (st := declaration.supertype()):
        yield from yield_super_types(st)


def is_hierarchy(inst):
    """Check if an instance is hierarchical (Project or SpatialStructureElement)."""
    return inst.is_a("IfcProject") or inst.is_a("IfcSpatialStructureElement")


def process_quantity(q, model):
    """Process quantity values for IFC property sets."""
    if q is None:
        return None
    elif isinstance(q, pint.Quantity):
        measure_type = pint_to_ifc[q.dimensionality]
        scale_factor = ifcopenshell.util.unit.calculate_unit_scale(
            model, measure_type[3:].replace("Measure", "").upper() + "UNIT"
        )
        value = q.to_base_units().magnitude / scale_factor
        return model.create_entity(measure_type, value)
    elif hasattr(q, "isoformat"):
        return q.isoformat()
    else:
        return q
