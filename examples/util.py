import functools
import re
import subprocess
import sys
import ifcopenshell
import ifcopenshell.api
import ifcopenshell.api.aggregate
import ifcopenshell.api.context
import ifcopenshell.api.root
import ifcopenshell.api.unit
import ifcopenshell.geom
import numpy as np

from ifcfactory import BIMFactoryElement, Box, Style, Transform

GROUND_PLANE_NAME = "Ground Plane"
GROUND_MARGIN = 2.0
# A shadow is height / tan(sun elevation) long; 2 × height keeps it on the plane down to ~27°.
GROUND_SHADOW_FACTOR = 2.0
GROUND_THICKNESS = 0.01


def add_ground_plane(model: ifcopenshell.file, site: ifcopenshell.entity_instance) -> None:
    """Lay a thin slab under the model so viewers have a surface to cast shadows on.

    Its top is ground level, z=0, where the example objects stand; anything below z=0, such as
    a foundation slab, is sunk into it. On every side it reaches past the model by
    ``GROUND_SHADOW_FACTOR`` times the model height, so shadows from any direction land on it,
    and by at least ``GROUND_MARGIN``. Skipped when the site already has its own terrain.
    """
    if site.Representation:
        return
    products = [
        p
        for p in model.by_type("IfcProduct")
        if p.Representation and not p.is_a("IfcSpatialElement") and not p.is_a("IfcOpeningElement")
    ]
    if not products:
        return

    settings = ifcopenshell.geom.settings()
    settings.set("use-world-coords", True)
    low, high = np.full(3, np.inf), np.full(3, -np.inf)
    for product in products:
        shape = ifcopenshell.geom.create_shape(settings, product)
        vertices = np.array(list(shape.geometry.verts), dtype=float).reshape(-1, 3)
        low, high = np.minimum(low, vertices.min(axis=0)), np.maximum(high, vertices.max(axis=0))

    margin = max(GROUND_MARGIN, GROUND_SHADOW_FACTOR * float(high[2]))
    width, depth = high[:2] - low[:2] + 2 * margin
    BIMFactoryElement(
        inst=site,
        children=[
            Transform(
                translation=(low[0] - margin, low[1] - margin, -GROUND_THICKNESS),
                item=BIMFactoryElement(
                    type="IfcGeographicElement",
                    name=GROUND_PLANE_NAME,
                    children=[
                        Style(
                            item=Box(width=float(width), depth=float(depth), height=GROUND_THICKNESS),
                            rgb=(0.85, 0.85, 0.85),
                        )
                    ],
                ),
            )
        ],
    ).build(model)


def create_basic_ifc_setup(project_name: str):
    def decorator(fn):
        @functools.wraps(fn)
        def inner():
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
                model,
                context_type="Model",
                context_identifier="Body",
                target_view="MODEL_VIEW",
                parent=model_context,
            )

            # Create site
            site = ifcopenshell.api.root.create_entity(model, ifc_class="IfcSite", name="Default Site")
            ifcopenshell.api.aggregate.assign_object(model, relating_object=project, products=[site])

            # Create building
            building = ifcopenshell.api.root.create_entity(model, ifc_class="IfcBuilding", name="Default Building")
            ifcopenshell.api.aggregate.assign_object(model, relating_object=site, products=[building])

            print(f"Running example: {project_name}")
            fn(model, project, site, building)
            add_ground_plane(model, site)
            filename = re.sub(r"\s*-\s*|\s+", "_", project_name) + ".ifc"
            model.write(filename)

            # validate the model for any schema errors
            subprocess.run([sys.executable, "-m", "ifcopenshell.validate", "--rules", filename], check=True)

            return model

        return inner

    return decorator
