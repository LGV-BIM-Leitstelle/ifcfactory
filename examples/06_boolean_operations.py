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

from ifcfactory import (
    # Base classes
    BIMFactoryElement,
    # 2D Profiles
    Rect,
    # 3D Representations
    Box,
    Cube,
    Extrusion,
    # Operations
    Transform,
    Boolean,
    BooleanOperationTypes,
)


@create_basic_ifc_setup("Example 6 - Boolean Operations")
def main(model, _, __, building):
    # Example 1: Wall with rectangular opening
    BIMFactoryElement(
        inst=building,
        children=[
            # Example 6: Row 5 (Y=60) - positions (0,5), (1,5), (2,5)
            Transform(
                translation=(0.0, 60.0, 0.0),
                item=BIMFactoryElement(
                    type="IfcWall",
                    name="Wall with Profile Opening",
                    children=[
                        Extrusion(
                            basis=Boolean(
                                operation=BooleanOperationTypes.Difference,
                                children=[
                                    Rect(width=5.0, height=5.0),
                                    Transform(
                                        translation=(1.0, 1.0),
                                        item=Rect(width=3.0, height=3.0),
                                    ),
                                ],
                            ),
                            depth=5.0,
                        )
                    ],
                ),
            )
        ],
    ).build(model)

    # Example 2: Wall with cubic opening using difference operation
    BIMFactoryElement(
        inst=building,
        children=[
            Transform(
                translation=(12.0, 60.0, 0.0),
                item=Boolean(
                    operation=BooleanOperationTypes.Difference,
                    children=[
                        BIMFactoryElement(type="IfcWall", children=[Cube(size=5.0)]),
                        Transform(
                            translation=(2.0, 2.0, 2.0),
                            item=BIMFactoryElement(type="IfcOpeningElement", children=[Cube(size=1.5)]),
                        ),
                    ],
                ),
            )
        ],
    ).build(model)

    # Example 3: Multiple openings in wall using difference operation
    BIMFactoryElement(
        inst=building,
        children=[
            Transform(
                translation=(24.0, 60.0, 0.0),
                item=Boolean(
                    operation=BooleanOperationTypes.Difference,
                    children=[
                        BIMFactoryElement(
                            type="IfcWall",
                            children=[Box(width=5.0, depth=0.3, height=3.0)],
                        ),
                        Transform(
                            translation=(1.0, 0.0, 1.0),
                            item=BIMFactoryElement(
                                type="IfcOpeningElement",
                                children=[Box(width=1.0, depth=0.5, height=1.0)],
                            ),
                        ),
                        Transform(
                            translation=(3.0, 0.0, 1.0),
                            item=BIMFactoryElement(
                                type="IfcOpeningElement",
                                children=[Box(width=1.0, depth=0.5, height=1.0)],
                            ),
                        ),
                    ],
                ),
            )
        ],
    ).build(model)


if __name__ == "__main__":
    main()
