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
    Translate,
    RotateZ,
    Boolean,
    BooleanOperationTypes,
    # Materials and styling
    Style,
    Material,
    # Property sets
    PropertySetTemplate,
)

# Define materials with RGB colors
wood = Material(name="WOOD01", category="wood", rgb=(0.65, 0.50, 0.30))
steel = Material(name="STEEL01", category="steel", rgb=(0.7, 0.7, 0.7))

@create_basic_ifc_setup("Example 4 - Styled Elements")
def main(model, _, __, building):
    # Create geometry with different materials
    wall_geometry = Box(width=4.0, depth=0.3, height=3.0)
    column_geometry = Cylinder(radius=0.3, height=3.0)
    beam_geometry = Extrusion(basis=Rect(width=0.3, height=0.6), depth=5.0)

    # Build structure with styling
    BIMFactoryElement(
        inst=building,
        children=[
            # Example 4: Row 3 (Y=36) - positions (0,3), (1,3), (2,3)
            Translate(
                vec=(0.0, 36.0, 0.0),
                item=BIMFactoryElement(
                    type="IfcWall",
                    name="Concrete Wall",
                    children=[Style(item=wall_geometry, rgb=(0.8, 0.8, 0.8))],
                ),
            ),
            Translate(
                vec=(12.0, 36.0, 0.0),
                item=BIMFactoryElement(
                    type="IfcColumn",
                    name="Wood Column",
                    children=[column_geometry],
                    material=wood,
                ),
            ),
            Translate(
                vec=(24.0, 36.0, 0.0),
                item=BIMFactoryElement(
                    type="IfcBeam",
                    name="Steel Beam",
                    children=[beam_geometry],
                    material=steel,
                ),
            ),
        ],
    ).build(model)


if __name__ == "__main__":
    main()
