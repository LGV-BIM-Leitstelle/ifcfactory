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

@create_basic_ifc_setup("Example 3 - Advanced Primitives")
def main(model, _, __, building):
    # Advanced primitive shapes
    elliptical_cylinder = EllipticalCylinder(semi_axis1=1.5, semi_axis2=1.0, height=3.0)

    ngon_cylinder = NgonCylinder(radius=1.2, height=2.5, sides=8)

    # Create hexagon mesh
    extruded_ngon_mesh = ExtrudedNgonAsMesh(
        basis=[
            (1.0, 0.0, 0.0),
            (0.5, 0.87, 0.0),
            (-0.5, 0.87, 0.0),
            (-1.0, 0.0, 0.0),
            (-0.5, -0.87, 0.0),
            (0.5, -0.87, 0.0),
        ],
        height=2.0,
    )

    # Custom mesh (simple pyramid)
    vertices = [
        (0.0, 0.0, 0.0),
        (2.0, 0.0, 0.0),
        (2.0, 2.0, 0.0),
        (0.0, 2.0, 0.0),
        (1.0, 1.0, 3.0),
    ]
    faces = [
        [0, 1, 2, 3],
        [0, 1, 4],
        [1, 2, 4],
        [2, 3, 4],
        [3, 0, 4],
    ]
    custom_mesh = MeshRepresentation(vertices=vertices, faces=faces)

    BIMFactoryElement(
        inst=building,
        children=[
            # Example 3: Row 2 (Y=24) - positions (0,2), (1,2), (2,2), (3,2)
            Translate(
                vec=(0.0, 24.0, 0.0),
                item=BIMFactoryElement(
                    type="IfcColumn",
                    name="Elliptical Column",
                    children=[elliptical_cylinder],
                ),
            ),
            Translate(
                vec=(12.0, 24.0, 0.0),
                item=BIMFactoryElement(
                    type="IfcColumn",
                    name="Octagonal Column",
                    children=[ngon_cylinder],
                ),
            ),
            Translate(
                vec=(24.0, 24.0, 0.0),
                item=BIMFactoryElement(
                    type="IfcBuildingElementProxy",
                    name="Hexagonal Mesh",
                    children=[extruded_ngon_mesh],
                ),
            ),
            Translate(
                vec=(36.0, 24.0, 0.0),
                item=BIMFactoryElement(
                    type="IfcBuildingElementProxy",
                    name="Custom Pyramid",
                    children=[custom_mesh],
                ),
            ),
        ],
    ).build(model)

if __name__ == "__main__":
    main()
