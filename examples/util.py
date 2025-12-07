import functools
import re
import ifcopenshell
import ifcopenshell.api

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
            filename = re.sub(r'\s*-\s*|\s+', '_', project_name) + '.ifc'
            model.write(filename)

            return model

        return inner
    return decorator

