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

@create_basic_ifc_setup("Example 2 - Profile Extrusions")
def main(model, _, __, building):
    # Create profiles
    rect_profile = Rect(width=2.0, height=1.0)
    circle_profile = Circle(radius=0.5)
    ellipse_profile = Ellipse(semi_axis1=1.5, semi_axis2=0.8)
    polygon_profile = Polygon(points=[(0, 0), (2, 0), (2, 1), (1, 2), (0, 1)])

    # Create extrusions
    beam_geometry = Extrusion(basis=rect_profile, depth=5.0)
    pipe_geometry = Extrusion(basis=circle_profile, depth=5.0)
    elliptical_beam = Extrusion(basis=ellipse_profile, depth=3.0)
    custom_extrusion = Extrusion(basis=polygon_profile, depth=4.0)

    BIMFactoryElement(
        inst=building,
        children=[
            # Example 2: Row 1 (Y=12) - positions (0,1), (1,1), (2,1), (3,1)
            Translate(
                vec=(0.0, 12.0, 0.0),
                item=BIMFactoryElement(
                    type="IfcBeam",
                    name="Rectangular Beam",
                    children=[beam_geometry],
                ),
            ),
            Translate(
                vec=(12.0, 12.0, 0.0),
                item=BIMFactoryElement(
                    type="IfcFlowSegment",
                    name="Circular Pipe",
                    children=[pipe_geometry],
                ),
            ),
            Translate(
                vec=(24.0, 12.0, 0.0),
                item=BIMFactoryElement(
                    type="IfcBeam",
                    name="Elliptical Beam",
                    children=[elliptical_beam],
                ),
            ),
            Translate(
                vec=(36.0, 12.0, 0.0),
                item=BIMFactoryElement(
                    type="IfcBuildingElementProxy",
                    name="Custom Extrusion",
                    children=[custom_extrusion],
                ),
            ),
        ],
    ).build(model)


if __name__ == "__main__":
    main()
