"""
ifcfactory Examples
===================

This file contains comprehensive examples demonstrating all the features
of the ifcfactory module as documented in the README.

Copyright (C) 2025 Freie und Hansestadt Hamburg, Landesbetrieb Geoinformation und Vermessung
BIM-Leitstelle, Ahmed Salem <ahmed.salem@gv.hamburg.de>

Developed in collaboration with Thomas Krijnen <mail@thomaskrijnen.com>

Transform Usage
---------------
The Transform class supports both translation and rotation in a single call or as nested operations.

**Single Transform (recommended for most cases):**
    Transform(translation=(x, y, z), rotation=(angle, "Z"), item=element)

    - Rotation is applied first (around local origin), then translation
    - Use when you want to: rotate an object in place, then move it to position

**Nested Transform (for special cases):**
    Transform(translation=(x, y, z), item=Transform(rotation=(angle, "Z"), item=element))

    - Same result as single Transform (rotate first, then translate)

    Transform(rotation=(angle, "Z"), item=Transform(translation=(x, y, z), item=element))

    - Different result: translate first, then rotate around world origin

"""

from examples.util import create_basic_ifc_setup

from ifcfactory import (
    # Base classes
    BIMFactoryElement,
    # 3D Representations
    Box,
    # Operations
    Transform,
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
            Transform(
                translation=(0.0, 48.0, 0.0),
                item=BIMFactoryElement(
                    type="IfcBuildingElementProxy",
                    name="Original Box",
                    children=[base_box],
                ),
            ),
            Transform(
                translation=(12.0, 48.0, 0.0),
                item=BIMFactoryElement(
                    type="IfcBuildingElementProxy",
                    name="Moved Box",
                    children=[base_box],
                ),
            ),
            Transform(
                translation=(24.0, 48.0, 0.0),
                item=Transform(
                    rotation=(45.0, "Z"),
                    item=BIMFactoryElement(
                        type="IfcBuildingElementProxy",
                        name="Rotated Box",
                        children=[base_box],
                    ),
                ),
            ),
            Transform(
                translation=(36.0, 48.0, 0.0),
                item=Transform(
                    rotation=(30.0, "Z"),
                    item=BIMFactoryElement(
                        type="IfcBuildingElementProxy",
                        name="Moved and Rotated Box (nested)",
                        children=[base_box],
                    ),
                ),
            ),
            # Example 5: Row 5 (Y=36) - Same as above but using single Transform operation
            Transform(
                translation=(0.0, 36.0, 0.0),
                item=BIMFactoryElement(
                    type="IfcBuildingElementProxy",
                    name="Original Box (single)",
                    children=[base_box],
                ),
            ),
            Transform(
                translation=(12.0, 36.0, 0.0),
                item=BIMFactoryElement(
                    type="IfcBuildingElementProxy",
                    name="Moved Box (single)",
                    children=[base_box],
                ),
            ),
            Transform(
                translation=(24.0, 36.0, 0.0),
                rotation=(45.0, "Z"),
                item=BIMFactoryElement(
                    type="IfcBuildingElementProxy",
                    name="Rotated Box (single)",
                    children=[base_box],
                ),
            ),
            Transform(
                translation=(36.0, 36.0, 0.0),
                rotation=(30.0, "Z"),
                item=BIMFactoryElement(
                    type="IfcBuildingElementProxy",
                    name="Moved and Rotated Box (single)",
                    children=[base_box],
                ),
            ),
        ],
    ).build(model)


if __name__ == "__main__":
    main()
