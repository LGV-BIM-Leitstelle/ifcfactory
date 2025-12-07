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

@create_basic_ifc_setup("Example 5 - Transformations")
def main(model, _, __, building):
    # Create base geometry
    base_box = Box(width=2.0, depth=2.0, height=2.0)

    # Build structure with transformations
    BIMFactoryElement(
        inst=building,
        children=[
            # Example 5: Row 4 (Y=48) - positions (0,4), (1,4), (2,4), (3,4)
            Translate(
                vec=(0.0, 48.0, 0.0),
                item=BIMFactoryElement(
                    type="IfcBuildingElementProxy",
                    name="Original Box",
                    children=[base_box],
                ),
            ),
            Translate(
                vec=(12.0, 48.0, 0.0),
                item=BIMFactoryElement(
                    type="IfcBuildingElementProxy",
                    name="Moved Box",
                    children=[base_box],
                ),
            ),
            Translate(
                vec=(24.0, 48.0, 0.0),
                item=RotateZ(
                    degrees=45,
                    item=BIMFactoryElement(
                        type="IfcBuildingElementProxy",
                        name="Rotated Box",
                        children=[base_box],
                    ),
                ),
            ),
            Translate(
                vec=(36.0, 48.0, 0.0),
                item=RotateZ(
                    degrees=30,
                    item=BIMFactoryElement(
                        type="IfcBuildingElementProxy",
                        name="Moved and Rotated Box",
                        children=[base_box],
                    ),
                ),
            ),
        ],
    ).build(model)


if __name__ == "__main__":
    main()
