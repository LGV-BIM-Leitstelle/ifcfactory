"""
ifcfactory Examples
===================

This file contains comprehensive examples demonstrating all the features
of the ifcfactory module as documented in the README.

Copyright (C) 2025 Freie und Hansestadt Hamburg, Landesbetrieb Geoinformation und Vermessung
BIM-Leitstelle, Ahmed Salem <ahmed.salem@gv.hamburg.de>

Developed in collaboration with Thomas Krijnen <mail@thomaskrijnen.com>
"""

import numpy as np
from .util import create_basic_ifc_setup
import ifcopenshell
import ifcopenshell.api
import ifcopenshell.api.aggregate
import ifcopenshell.api.context
import ifcopenshell.api.root
import ifcopenshell.api.unit

from ifcfactory import (
    # Base classes
    BIMFactoryElement,
    # 2D Profiles
    Rect,
    Circle,
    Ellipse,
    Polygon,
    # 3D Representations
    Box,
    Cube,
    Cylinder,
    EllipticalCylinder,
    NgonCylinder,
    Sphere,
    Extrusion,
    ExtrudedNgonAsMesh,
    MeshRepresentation,
    # Operations
    Transform,
    Boolean,
    BooleanOperationTypes,
    # Materials and styling
    Style,
    Material,
    # Property sets
    PropertySetTemplate,
)

@create_basic_ifc_setup("Example 8 - Type Objects")
def main(model, _, __, building):
    chair_type = BIMFactoryElement(type="IfcFurnishingElementType", name="CHAIR01", children=[
        Transform(translation=(-0.0500, -0.0500, 0.0000), item=Box(width=0.1000, depth=0.1000, height=0.4000)), 
        Transform(translation=(0.3500, -0.0500, 0.0000), item=Box(width=0.1000, depth=0.1000, height=0.4000)), 
        Transform(translation=(-0.0500, 0.3500, 0.0000), item=Box(width=0.1000, depth=0.1000, height=0.4000)), 
        Transform(translation=(0.3500, 0.3500, 0.0000), item=Box(width=0.1000, depth=0.1000, height=0.4000)), 
        Transform(translation=(-0.0500, -0.0500, 0.4000), item=Box(width=0.5000, depth=0.5000, height=0.0500)), 
        Transform(translation=(-0.0500, 0.3500, 0.4500), item=Box(width=0.1000, depth=0.1000, height=0.5000)), 
        Transform(translation=(0.3500, 0.3500, 0.4500), item=Box(width=0.1000, depth=0.1000, height=0.5000)), 
        Transform(translation=(-0.0500, 0.3000, 0.7500), item=Box(width=0.5000, depth=0.0500, height=0.2000)), 
    ])

    theta = np.linspace(0, 100, 60)
    r = 1. + theta / 8.
    points = np.column_stack((r * np.cos(theta ** 0.6), r * np.sin(theta ** 0.6), np.zeros_like(theta))).tolist()[1:]

    BIMFactoryElement(
        inst=building,
        children=[
            Transform(translation=P, item=BIMFactoryElement(type="IfcFurnishingElement", children=[chair_type])) \
            for P in points
        ],
    ).build(model)

if __name__ == "__main__":
    main()
