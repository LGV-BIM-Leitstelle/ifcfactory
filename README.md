# ifcfactory

[![PyPI version](https://badge.fury.io/py/ifcfactory.svg)](https://pypi.org/project/ifcfactory/)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-LGPL--2.1-blue.svg)](LICENSE)

A modular geometry system for creating BIM elements with composable geometry creation.

## Quick Install

```bash
pip install ifcfactory
```

## Overview

ifcfactory offers a declarative, composable framework for creating complex BIM geometry.
It leverages Pydantic models for strong type safety and validation, 
while providing seamless integration with IfcOpenShell for reliable IFC file generation.

The declarative structures in Python are automatically mapped to the most appropriate IFC mechanisms, for example:

 - `Boolean(operation, children)`:
   - In case of: *subtraction of element from element* -> `IfcRelVoidsElement` + `IfcOpeningElement`
   - In case of: *subtraction of profile from profile* -> `IfcProfileDefWithVoids`
   - In case of: *any item to item* -> `IfcBooleanResult`
 - `Transform(item, translation, rotation)`:
   - In case of: *element* -> Factored into `ObjectPlacement`
   - In case of: *tesselation* -> Applied to coordinates
   - Other cases: defer to `shape_builder` translate() and rotate() [when along "Z" axis]

## Structure

```
ifcfactory/
├── __init__.py                 # Main public API
├── element.py                  # High-level BIM elements
├── primitives.py               # Geometric shapes (Box, Cylinder, Sphere, etc.)
├── operations.py               # Transformations and Boolean operations
├── _internal/                  # Internal implementation (not for direct user access)
│   ├── __init__.py            # Internal package marker
│   ├── primitives_base.py     # Base classes and helper functions
│   ├── material_base.py       # Materials and styling
│   ├── unit_base.py           # Unit conversion utilities (pint ↔ IFC)
│   └── pset_base.py           # Property set templates
├── examples/
│   └── example_bimfactory.py
└── README.md
```

## Public API

### High-Level Elements

- **`BIMFactoryElement`**: Container for complete BIM elements with IFC integration

### 2D Profiles

- **`Rect(width, height)`**: Rectangular profile
- **`Circle(radius)`**: Circular profile
- **`Ellipse(semi_axis1, semi_axis2)`**: Elliptical profile
- **`Polygon(points)`**: Arbitrary polygon from list of 2D points

### 3D Representations

- **`Box(width, depth, height)`**: Rectangular box
- **`Cube(size)`**: Cube with equal dimensions
- **`Cylinder(radius, height)`**: Circular cylinder
- **`EllipticalCylinder(semi_axis1, semi_axis2, height)`**: Elliptical cylinder
- **`NgonCylinder(radius, height, sides)`**: N-sided cylinder
- **`Sphere(radius, detail=1)`**: Icosphere with configurable detail
- **`Extrusion(basis, depth)`**: Extrude any 2D profile
- **`ExtrudedNgonAsMesh(basis, height)`**: N-sided extrusion as mesh
- **`MeshRepresentation(vertices, faces)`**: Custom mesh geometry

### Operations

- **`Transform(item, translation, rotation)`**: Apply a transformation (translation and/or rotation)
- **`Boolean(operation, children)`**: Boolean operations (union, difference, intersection)
- **`BooleanOperationTypes`**: Enum for boolean operation types

### Materials & Styling

- **`Style`**: Visual styling with colors and transparency
- **`Material`**: Physical material properties

### Property Sets

- **`PropertySetTemplate`**: Template for creating property sets

### Units

- Dimension variables: `L` (length), `A` (area), `V` (volume), `M` (mass), `T` (time), `E` (current), `K` (temperature),
  `N` (force), `J` (energy), `P` (power)
- **`pint_to_ifc`**: Mapping dictionary for unit conversion
- **`ureg`**: Pint unit registry
- **`Dim`**: Dimension class

## Key Features

- **Type Safety**: Built on Pydantic for runtime type checking and validation
- **Composable**: Mix and match primitives to create complex geometry
- **Cacheable**: Built elements are cached to prevent duplication
- **Unit Aware**: Automatic unit conversion between pint and IFC types
- **Material Support**: Visual styling and material assignment
- **Property Sets**: Support for IFC property sets and quantities
- **API**: Internal implementation hidden in `_internal` module

## Complete Working Example

Here's a complete example that creates a simple building with multiple wall types:

```python
import ifcopenshell
import ifcopenshell.api
import ifcopenshell.api.aggregate
import ifcopenshell.api.context
import ifcopenshell.api.root
import ifcopenshell.api.unit

from ifcfactory import (
    BIMFactoryElement, Box, Cube, Cylinder, Extrusion, Rect, Sphere
)


def create_basic_ifc_setup(project_name: str):
    """Create basic IFC model setup using IfcOpenShell API"""
    # Create IFC model
    ifc_model = ifcopenshell.file(schema="IFC4")

    # Create project
    project_entity = ifcopenshell.api.root.create_entity(ifc_model, ifc_class="IfcProject", name=project_name)

    # Create units (meters)
    ifcopenshell.api.unit.assign_unit(ifc_model, length={"is_metric": True, "raw": "METERS"})

    # Create contexts
    model_context = ifcopenshell.api.context.add_context(ifc_model, context_type="Model")
    ifcopenshell.api.context.add_context(
            ifc_model, context_type="Model", context_identifier="Body", target_view="MODEL_VIEW", parent=model_context
    )

    # Create site
    site_entity = ifcopenshell.api.root.create_entity(ifc_model, ifc_class="IfcSite", name="Default Site")
    ifcopenshell.api.aggregate.assign_object(ifc_model, relating_object=project_entity, products=[site_entity])

    # Create building
    building_entity = ifcopenshell.api.root.create_entity(ifc_model, ifc_class="IfcBuilding", name="Default Building")
    ifcopenshell.api.aggregate.assign_object(ifc_model, relating_object=site_entity, products=[building_entity])

    return ifc_model, project_entity, site_entity, building_entity


# Create IFC model and setup
model, proj, site, building = create_basic_ifc_setup("Example Building")

# Create complete project structure using BIMFactoryElement
BIMFactoryElement(
        inst=building,
        children=[
                # Box wall positioned at origin
                BIMFactoryElement(type="IfcWall", name="Box Wall", children=[Box(width=5.0, depth=0.3, height=3.0)]),
                # Cube wall
                BIMFactoryElement(type="IfcWall", name="Cube Wall", children=[Cube(size=4.0)]),
                # Cylinder wall
                BIMFactoryElement(type="IfcWall", name="Cylinder Wall", children=[Cylinder(radius=1.5, height=4.0)]),
                # Extruded slab
                BIMFactoryElement(
                        type="IfcSlab",
                        name="Extruded Slab",
                        children=[Extrusion(basis=Rect(width=5.0, height=2.5), depth=0.3)],
                ),
                # Sphere element
                BIMFactoryElement(
                        type="IfcBuildingElementProxy",
                        name="Sphere Element",
                        children=[Sphere(radius=1.5, detail=2)]
                ),
        ],
).build(model)

# Save the model
model.write("example_building.ifc")
print("Saved: example_building.ifc")
```

This example demonstrates:

- Setting up a proper IFC model with project hierarchy
- Creating various geometric primitives (Box, Cube, Cylinder, Sphere)
- Using profile-based extrusions (Rect → Extrusion)
- Organizing elements in a hierarchical BIM structure
- Saving the result as an IFC file

For more comprehensive examples, see the sections below which demonstrate all features including
transformations, boolean operations, materials, and property sets.

## Other examples

You can run all examples with `python -m examples` or an individual examples as `python -m examples.05_transformations`. The examples are all written to disk as .ifc files and are validated using `ifcopenshell.validate`.

### Example 1 - Complete Building

![](img/Example_1_Complete_Building.png)

### Example 2 - Profile Extrusions

![](img/Example_2_Profile_Extrusions.png)

### Example 3 - Advanced Primitives

![](img/Example_3_Advanced_Primitives.png)

### Example 4 - Styled Elements

![](img/Example_4_Styled_Elements.png)

### Example 5 - Transformations

![](img/Example_5_Transformations.png)

### Example 6 - Boolean Operations

![](img/Example_6_Boolean_Operations.png)

### Example 7 - Property Sets

![](img/Example_7_Property_Sets.png)

### Example 8 - Type Objects

![](img/Example_8_Type_Objects.png)

## Links

- **PyPI**: https://pypi.org/project/ifcfactory/
- **GitHub**: https://github.com/LGV-BIM-Leitstelle/ifcfactory
- **Issues**: https://github.com/LGV-BIM-Leitstelle/ifcfactory/issues

## License

This project is licensed under the GNU Lesser General Public License v2.1 (LGPL-2.1).

**Copyright (C) 2025 Freie und Hansestadt Hamburg, Landesbetrieb Geoinformation und Vermessung**
**BIM-Leitstelle, Ahmed Salem**