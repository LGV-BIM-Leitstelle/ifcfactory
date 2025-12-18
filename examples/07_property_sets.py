"""
ifcfactory Examples
===================

This file contains comprehensive examples demonstrating all the features
of the ifcfactory module as documented in the README.

Copyright (C) 2025 Freie und Hansestadt Hamburg, Landesbetrieb Geoinformation und Vermessung
BIM-Leitstelle, Ahmed Salem <ahmed.salem@gv.hamburg.de>

Developed in collaboration with Thomas Krijnen <mail@thomaskrijnen.com>
"""

from ifcfactory import (
    # Base classes
    BIMFactoryElement,
    # 3D Representations
    Box,
    Cylinder,
    # Operations
    Transform,
    # Property sets
    PropertySetTemplate,
)
from .util import create_basic_ifc_setup


class PsetWallExample(PropertySetTemplate):
    """Example property set for walls"""

    pset_name = "Pset_WallExample"
    wall_type: str = "Exterior"
    material_type: str = "Concrete"
    fire_rating: str = "120min"
    thermal_transmittance: float = 0.25


wall_properties = PsetWallExample(
    wall_type="Exterior",
    material_type="Reinforced Concrete",
    fire_rating="120min",
    thermal_transmittance=0.22,
)


class PsetColumnExample(PropertySetTemplate):
    """Example property set for columns"""

    pset_name = "Pset_ColumnExample"
    column_type: str = "Structural"
    material_grade: str = "C30/37"
    load_bearing: bool = True
    fire_rating: str = "90min"


column_properties = PsetColumnExample(
    column_type="Load Bearing",
    material_grade="C35/45",
    load_bearing=True,
    fire_rating="90min",
)


@create_basic_ifc_setup("Example 7 - Property Sets")
def main(model, _, __, building):
    # Create wall geometry with property sets
    wall_geometry = Box(width=4.0, depth=0.3, height=3.0)
    column_geometry = Cylinder(radius=0.25, height=3.0)

    # Build structure with property sets
    BIMFactoryElement(
        inst=building,
        children=[
            # Example 7: Row 6 (Y=72) - positions (0,6), (1,6)
            Transform(
                translation=(0.0, 72.0, 0.0),
                item=BIMFactoryElement(
                    type="IfcWall",
                    name="Wall with Properties",
                    children=[wall_geometry],
                    psets=[wall_properties],
                ),
            ),
            Transform(
                translation=(12.0, 72.0, 0.0),
                item=BIMFactoryElement(
                    type="IfcColumn",
                    name="Column with Properties",
                    children=[column_geometry],
                    psets=[column_properties],
                ),
            ),
        ],
    ).build(model)


if __name__ == "__main__":
    main()
