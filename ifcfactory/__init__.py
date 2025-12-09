"""
BIM Factory Module
==================

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

Main Components:
- Base classes and helper functions (_internal/primitives_base.py)
- Primitive geometry objects (primitives.py)
- Geometric operations (operations.py)
- Material and styling definitions (_internal/material_base.py)
- Unit conversion utilities (_internal/unit_base.py)
- Property set base classes (_internal/pset_base.py)
"""

# Import high-level BIM elements
from .element import BIMFactoryElement

# Import styles and materials
from ._internal.material_base import Material, Style

# Import operations
from .operations import Boolean, BooleanOperationTypes, Transform
from .primitives import (
    Box,  # Profile classes; Representation item classes
    Circle,
    Cube,
    Cylinder,
    Ellipse,
    EllipticalCylinder,
    ExtrudedNgonAsMesh,
    Extrusion,
    MeshRepresentation,
    NgonCylinder,
    Polygon,
    Rect,
    Sphere,
)

# Import property set base
from ._internal.pset_base import PropertySetTemplate

# Import units
from ._internal.unit_base import A, Dim, E, J, L, M, N, P, T, V, K, pint_to_ifc, ureg

# Import base classes for advanced usage
from ._internal.primitives_base import ElementInterface, Primitive, Profile, RepresentationItem

__all__ = [
    # Element classes
    "BIMFactoryElement",
    # Profile classes
    "Rect",
    "Circle",
    "Ellipse",
    "Polygon",
    # Representation item classes
    "Extrusion",
    "Box",
    "Cube",
    "ExtrudedNgonAsMesh",
    "NgonCylinder",
    "Cylinder",
    "EllipticalCylinder",
    "Sphere",
    "MeshRepresentation",
    # Operations
    "BooleanOperationTypes",
    "Boolean",
    "Transform",
    # Styles and materials
    "Style",
    "Material",
    # Property sets
    "PropertySetTemplate",
    # Units
    "ureg",
    "Dim",
    "L",
    "A",
    "V",
    "M",
    "T",
    "E",
    "K",
    "N",
    "J",
    "P",
    "pint_to_ifc",
    # Base classes (for advanced usage)
    "ElementInterface",
    "Primitive",
    "Profile",
    "RepresentationItem",
]
