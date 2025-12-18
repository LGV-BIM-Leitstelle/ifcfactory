"""
ifcfactory Examples
===================

This file contains comprehensive examples demonstrating all the features
of the ifcfactory module as documented in the README.

Copyright (C) 2025 Freie und Hansestadt Hamburg, Landesbetrieb Geoinformation und Vermessung
BIM-Leitstelle, Ahmed Salem <ahmed.salem@gv.hamburg.de>

Developed in collaboration with Thomas Krijnen <mail@thomaskrijnen.com>
"""

from examples.util import create_basic_ifc_setup
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

@create_basic_ifc_setup("Example 1 - Complete Building")
def main(model, _, __, building):

    # Create complete project structure using BIMFactoryElement
    BIMFactoryElement(
        inst=building,
        children=[
            # Example 1: Row 0 (Y=0) - positions (0,0), (1,0), (2,0), (3,0), (4,0)
            BIMFactoryElement(
                type="IfcWall",
                name="Box Wall",
                children=[Box(width=5.0, depth=0.3, height=3.0)],
            ),
            Transform(
                translation=(12.0, 0.0, 0.0),
                item=BIMFactoryElement(type="IfcWall", name="Cube Wall", children=[Cube(size=4.0)]),
            ),
            Transform(
                translation=(24.0, 0.0, 0.0),
                item=BIMFactoryElement(
                    type="IfcWall",
                    name="Cylinder Wall",
                    children=[Cylinder(radius=1.5, height=4.0)],
                ),
            ),
            Transform(
                translation=(36.0, 0.0, 0.0),
                item=BIMFactoryElement(
                    type="IfcSlab",
                    name="Extruded Slab",
                    children=[Extrusion(basis=Rect(width=5.0, height=2.5), depth=0.3)],
                ),
            ),
            Transform(
                translation=(48.0, 0.0, 0.0),
                item=BIMFactoryElement(
                    type="IfcBuildingElementProxy",
                    name="Sphere Element",
                    children=[Sphere(radius=1.5, detail=2)],
                ),
            ),
        ],
    ).build(model)

if __name__ == "__main__":
    main()
