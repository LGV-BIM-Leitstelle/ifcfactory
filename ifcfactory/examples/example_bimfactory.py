"""
ifcfactory Examples
===================

This file contains comprehensive examples demonstrating all the features
of the ifcfactory module as documented in the README.

Copyright (C) 2025 Freie und Hansestadt Hamburg, Landesbetrieb Geoinformation und Vermessung
BIM-Leitstelle, Ahmed Salem <ahmed.salem@gv.hamburg.de>

Developed in collaboration with Thomas Krijnen <mail@thomaskrijnen.com>
"""

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


def create_basic_ifc_setup(project_name: str):
    """Create basic IFC model setup using IfcOpenShell API"""
    # Create IFC model
    model = ifcopenshell.file(schema="IFC4")

    # Create project
    project = ifcopenshell.api.root.create_entity(model, ifc_class="IfcProject", name=project_name)

    # Create units (meters) using pint integration
    ifcopenshell.api.unit.assign_unit(model, length={"is_metric": True, "raw": "METERS"})

    # Create contexts
    model_context = ifcopenshell.api.context.add_context(model, context_type="Model")
    ifcopenshell.api.context.add_context(
        model, context_type="Model", context_identifier="Body", target_view="MODEL_VIEW", parent=model_context
    )

    # Create site
    site = ifcopenshell.api.root.create_entity(model, ifc_class="IfcSite", name="Default Site")
    ifcopenshell.api.aggregate.assign_object(model, relating_object=project, products=[site])

    # Create building
    building = ifcopenshell.api.root.create_entity(model, ifc_class="IfcBuilding", name="Default Building")
    ifcopenshell.api.aggregate.assign_object(model, relating_object=site, products=[building])

    return model, project, site, building


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

# Define materials with RGB colors
wood = Material(name="WOOD01", category="wood", rgb=(0.65, 0.50, 0.30))
steel = Material(name="STEEL01", category="steel", rgb=(0.7, 0.7, 0.7))


def main():
    """Run all ifcfactory examples"""
    print("Running ifcfactory Examples...")
    print("=" * 50)

    try:
        # =================================================================
        # EXAMPLE 1: basic object creation
        # =================================================================
        print("Creating complete building example...")

        # Create IFC model and setup
        model, proj, site, building = create_basic_ifc_setup("Example 1 - Complete Building")

        # Create complete project structure using BIMFactoryElement
        BIMFactoryElement(
            inst=building,
            children=[
                # Example 1: Row 0 (Y=0) - positions (0,0), (1,0), (2,0), (3,0), (4,0)
                BIMFactoryElement(type="IfcWall", name="Box Wall", children=[Box(width=5.0, depth=0.3, height=3.0)]),
                Translate(
                    vec=(12.0, 0.0, 0.0),
                    item=BIMFactoryElement(type="IfcWall", name="Cube Wall", children=[Cube(size=4.0)]),
                ),
                Translate(
                    vec=(24.0, 0.0, 0.0),
                    item=BIMFactoryElement(
                        type="IfcWall", name="Cylinder Wall", children=[Cylinder(radius=1.5, height=4.0)]
                    ),
                ),
                Translate(
                    vec=(36.0, 0.0, 0.0),
                    item=BIMFactoryElement(
                        type="IfcSlab",
                        name="Extruded Slab",
                        children=[Extrusion(basis=Rect(width=5.0, height=2.5), depth=0.3)],
                    ),
                ),
                Translate(
                    vec=(48.0, 0.0, 0.0),
                    item=BIMFactoryElement(
                        type="IfcBuildingElementProxy", name="Sphere Element", children=[Sphere(radius=1.5, detail=2)]
                    ),
                ),
            ],
        ).build(model)

        model.write("Example_1_Complete_Building.ifc")
        print("Saved: Example_1_Complete_Building.ifc")

        # =================================================================
        # EXAMPLE 2: Profile-Based Extrusions with All Profile Types
        # =================================================================
        print("Creating profile extrusion examples...")

        model, proj, site, building = create_basic_ifc_setup("Example 2 - Profile Extrusions")

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
                    item=BIMFactoryElement(type="IfcBeam", name="Rectangular Beam", children=[beam_geometry]),
                ),
                Translate(
                    vec=(12.0, 12.0, 0.0),
                    item=BIMFactoryElement(type="IfcFlowSegment", name="Circular Pipe", children=[pipe_geometry]),
                ),
                Translate(
                    vec=(24.0, 12.0, 0.0),
                    item=BIMFactoryElement(type="IfcBeam", name="Elliptical Beam", children=[elliptical_beam]),
                ),
                Translate(
                    vec=(36.0, 12.0, 0.0),
                    item=BIMFactoryElement(
                        type="IfcBuildingElementProxy", name="Custom Extrusion", children=[custom_extrusion]
                    ),
                ),
            ],
        ).build(model)

        model.write("Example_2_Profile_Extrusions.ifc")
        print("Saved: Example_2_Profile_Extrusions.ifc")

        # =================================================================
        # EXAMPLE 3: Advanced Primitives including ExtrudedNgonAsMesh
        # =================================================================
        print("Creating advanced primitives examples...")

        model, proj, site, building = create_basic_ifc_setup("Example 3 - Advanced Primitives")

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
        vertices = [(0.0, 0.0, 0.0), (2.0, 0.0, 0.0), (2.0, 2.0, 0.0), (0.0, 2.0, 0.0), (1.0, 1.0, 3.0)]
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
                    item=BIMFactoryElement(type="IfcColumn", name="Elliptical Column", children=[elliptical_cylinder]),
                ),
                Translate(
                    vec=(12.0, 24.0, 0.0),
                    item=BIMFactoryElement(type="IfcColumn", name="Octagonal Column", children=[ngon_cylinder]),
                ),
                Translate(
                    vec=(24.0, 24.0, 0.0),
                    item=BIMFactoryElement(
                        type="IfcBuildingElementProxy", name="Hexagonal Mesh", children=[extruded_ngon_mesh]
                    ),
                ),
                Translate(
                    vec=(36.0, 24.0, 0.0),
                    item=BIMFactoryElement(
                        type="IfcBuildingElementProxy", name="Custom Pyramid", children=[custom_mesh]
                    ),
                ),
            ],
        ).build(model)

        model.write("Example_3_Advanced_Primitives.ifc")
        print("Saved: Example_3_Advanced_Primitives.ifc")

        # =================================================================
        # EXAMPLE 4: Materials and Styling with Color Utilities
        # =================================================================
        print("Creating styled elements example...")

        model, proj, site, building = create_basic_ifc_setup("Example 4 - Styled Elements")

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

        model.write("Example_4_Styled_Elements.ifc")
        print("Saved: Example_4_Styled_Elements.ifc")

        # =================================================================
        # EXAMPLE 5: Transformations with All Operations
        # =================================================================
        print("Creating transformations example...")

        model, proj, site, building = create_basic_ifc_setup("Example 5 - Transformations")

        # Create base geometry
        base_box = Box(width=2.0, depth=2.0, height=2.0)

        # Build structure with transformations
        BIMFactoryElement(
            inst=building,
            children=[
                # Example 5: Row 4 (Y=48) - positions (0,4), (1,4), (2,4), (3,4)
                Translate(
                    vec=(0.0, 48.0, 0.0),
                    item=BIMFactoryElement(type="IfcBuildingElementProxy", name="Original Box", children=[base_box]),
                ),
                Translate(
                    vec=(12.0, 48.0, 0.0),
                    item=BIMFactoryElement(type="IfcBuildingElementProxy", name="Moved Box", children=[base_box]),
                ),
                Translate(
                    vec=(24.0, 48.0, 0.0),
                    item=RotateZ(
                        degrees=45,
                        item=BIMFactoryElement(type="IfcBuildingElementProxy", name="Rotated Box", children=[base_box]),
                    ),
                ),
                Translate(
                    vec=(36.0, 48.0, 0.0),
                    item=RotateZ(
                        degrees=30,
                        item=BIMFactoryElement(
                            type="IfcBuildingElementProxy", name="Moved and Rotated Box", children=[base_box]
                        ),
                    ),
                ),
            ],
        ).build(model)

        model.write("Example_5_Transformations.ifc")
        print("Saved: Example_5_Transformations.ifc")

        # =================================================================
        # EXAMPLE 6: Boolean Operations (Difference Operations)
        # =================================================================
        print("Creating boolean operations example...")

        model, proj, site, building = create_basic_ifc_setup("Example 6 - Boolean Operations")

        # Example 1: Wall with rectangular opening
        BIMFactoryElement(
            inst=building,
            children=[
                # Example 6: Row 5 (Y=60) - positions (0,5), (1,5), (2,5)
                Translate(
                    vec=(0.0, 60.0, 0.0),
                    item=BIMFactoryElement(
                        type="IfcWall",
                        name="Wall with Profile Opening",
                        children=[
                            Extrusion(
                                basis=Boolean(
                                    operation=BooleanOperationTypes.Difference,
                                    children=[
                                        Rect(width=5.0, height=5.0),
                                        Translate(vec=(1.0, 1.0), item=Rect(width=3.0, height=3.0)),
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
                Translate(
                    vec=(12.0, 60.0, 0.0),
                    item=Boolean(
                        operation=BooleanOperationTypes.Difference,
                        children=[
                            BIMFactoryElement(type="IfcWall", children=[Cube(size=5.0)]),
                            Translate(
                                vec=(2.0, 2.0, 2.0),
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
                Translate(
                    vec=(24.0, 60.0, 0.0),
                    item=Boolean(
                        operation=BooleanOperationTypes.Difference,
                        children=[
                            BIMFactoryElement(type="IfcWall", children=[Box(width=5.0, depth=0.3, height=3.0)]),
                            Translate(
                                vec=(1.0, 0.0, 1.0),
                                item=BIMFactoryElement(
                                    type="IfcOpeningElement", children=[Box(width=1.0, depth=0.5, height=1.0)]
                                ),
                            ),
                            Translate(
                                vec=(3.0, 0.0, 1.0),
                                item=BIMFactoryElement(
                                    type="IfcOpeningElement", children=[Box(width=1.0, depth=0.5, height=1.0)]
                                ),
                            ),
                        ],
                    ),
                )
            ],
        ).build(model)

        model.write("Example_6_Boolean_Operations.ifc")
        print("Saved: Example_6_Boolean_Operations.ifc")

        # =================================================================
        # EXAMPLE 7: Property Sets with Custom Templates
        # =================================================================
        print("Creating property sets example...")

        model, proj, site, building = create_basic_ifc_setup("Example 7 - Property Sets")

        # Create wall geometry with property sets
        wall_geometry = Box(width=4.0, depth=0.3, height=3.0)
        column_geometry = Cylinder(radius=0.25, height=3.0)

        # Build structure with property sets
        BIMFactoryElement(
            inst=building,
            children=[
                # Example 7: Row 6 (Y=72) - positions (0,6), (1,6)
                Translate(
                    vec=(0.0, 72.0, 0.0),
                    item=BIMFactoryElement(
                        type="IfcWall",
                        name="Wall with Properties",
                        children=[wall_geometry],
                        psets=[wall_properties],
                    ),
                ),
                Translate(
                    vec=(12.0, 72.0, 0.0),
                    item=BIMFactoryElement(
                        type="IfcColumn",
                        name="Column with Properties",
                        children=[column_geometry],
                        psets=[column_properties],
                    ),
                ),
            ],
        ).build(model)

        model.write("Example_7_Property_Sets.ifc")
        print("Saved: Example_7_Property_Sets.ifc")

        # =================================================================
        # COMPLETION MESSAGE
        # =================================================================
        print("=" * 50)
        print("All examples completed successfully!")
        print("Generated IFC files in current directory:")
        print("- Example_1_Complete_Building.ifc")
        print("- Example_2_Profile_Extrusions.ifc")
        print("- Example_3_Advanced_Primitives.ifc")
        print("- Example_4_Styled_Elements.ifc")
        print("- Example_5_Transformations.ifc")
        print("- Example_6_Boolean_Operations.ifc")
        print("- Example_7_Property_Sets.ifc")

    except Exception as e:
        print(f"Error running examples: {e}")
        raise


if __name__ == "__main__":
    main()
