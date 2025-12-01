"""
Style and Material Classes
==========================

Copyright (C) 2025 Freie und Hansestadt Hamburg, Landesbetrieb Geoinformation und Vermessung
BIM-Leitstelle, Ahmed Salem <ahmed.salem@gv.hamburg.de>

Developed in collaboration with Thomas Krijnen <mail@thomaskrijnen.com>

This library is free software; you can redistribute it and/or
modify it under the terms of the GNU Lesser General Public
License as published by the Free Software Foundation; either
version 2.1 of the License, or (at your option) any later version.

This library is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
Lesser General Public License for more details.

You should have received a copy of the GNU Lesser General Public
License along with this library; if not, write to the Free Software
Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301  USA

This module contains classes for styling and material definitions
for IFC elements.
"""

from typing import Optional, Tuple

import ifcopenshell
import ifcopenshell.api.material
import ifcopenshell.api.style

from .primitives_base import Primitive, RepresentationItem


class Style(Primitive, RepresentationItem):
    """Styling wrapper that applies color, transparency, and optionally a CAD layer to representation items."""

    item: RepresentationItem
    rgb: str | Tuple[float, float, float]
    transparency: Optional[float] = None
    cad_layer: Optional[str] = None

    model_config = {"arbitrary_types_allowed": True}

    def build(self, model: ifcopenshell.file) -> ifcopenshell.entity_instance:
        """
        Build a styled representation with color, transparency, and optional CAD layer assignment.

        Args:
            model: The IFC model instance.

        Returns:
            ifcopenshell.entity_instance: The styled representation.
        """
        inst = self.item.build(model)
        # assign_color_to_representation(model, inst, self.rgb, self.transparency)

        if self.cad_layer:
            # Use rgb (converted to tuple if needed) for the layer color
            if isinstance(self.rgb, tuple):
                color = self.rgb
            elif isinstance(self.rgb, str):
                color = tuple(float(x.strip()) for x in self.rgb.split(","))
            else:
                color = (1.0, 1.0, 1.0)
            assign_layer_to_representation(model, inst, self.cad_layer, color)

        assign_color_to_element(model, inst, self.rgb, self.transparency)

        return inst


class Material(Primitive):
    """
    Material definition for IFC elements.

    Args:
        name (str): Name of the material.
        category (Optional[str]): Category of the material.
        rgb (Tuple[float, float, float]): Normalized RGB color as floats in [0, 1].
        transparency (Optional[float]): Transparency value (0.0 = opaque, 1.0 = fully transparent).
    """

    name: str
    category: Optional[str] = None
    rgb: Tuple[float, float, float]  # Normalized RGB in [0, 1]
    transparency: Optional[float] = None
    _build_result: Optional[ifcopenshell.entity_instance] = None

    def build(self, model):
        if res := getattr(self, "_build_result", None):
            # build it only once
            return res
        inst = ifcopenshell.api.material.add_material(
            model,
            name=self.name,
            **({"category": self.category} if model.schema != "IFC2X3" else {}),
        )

        style = ifcopenshell.api.style.add_style(model)
        ifcopenshell.api.style.add_surface_style(
            model,
            style=style,
            ifc_class=("IfcSurfaceStyleShading" if model.schema != "IFC2X3" else "IfcSurfaceStyleRendering"),
            attributes={
                "SurfaceColour": {
                    "Name": None,
                    "Red": self.rgb[0],
                    "Green": self.rgb[1],
                    "Blue": self.rgb[1],
                },
                "Transparency": self.transparency,
            },
        )
        context = [x for x in model.by_type("IfcGeometricRepresentationContext") if x.ContextIdentifier == "Body"][0]
        ifcopenshell.api.style.assign_material_style(model, material=inst, style=style, context=context)
        self._build_result = inst
        return inst


def ifc_normalise_color(rgb_color_str: str) -> list[float]:
    """
    Normalize RGB color string to IFC-compatible values in range [0.1, 1].

    Args:
        rgb_color_str (str): RGB color string in format "r,g,b" (e.g., "255,0,0").

    Returns:
        list[float]: Normalized RGB values as a list of three floats.

    Raises:
        ValueError: If rgb_color_str is not in the expected format.
    """
    rgb_color = rgb_color_str.split(",")
    r, g, b = (float(rgb_color[0]), float(rgb_color[1]), float(rgb_color[2]))

    # Normalizing RGB values to the range [0.1, 1]
    normalized_rgb = [
        round(r / 255 * (1 - 0.1) + 0.1, 2),
        round(g / 255 * (1 - 0.1) + 0.1, 2),
        round(b / 255 * (1 - 0.1) + 0.1, 2),
    ]

    return normalized_rgb


def assign_color_to_element(
    model: ifcopenshell.file,
    representation,
    color_rgb: str | tuple[float, ...],
    transparency: float | None,
) -> None:
    """
    Assign a color to the IFC element representation or item.

    Args:
        model (ifcopenshell.file): The IFC model instance.
        representation: The IFC representation or representation item.
        color_rgb (str | tuple[float, ...]): Color as RGB string or tuple.
        transparency (float | None): Transparency value (0.0 to 1.0).

    Raises:
        TypeError: If representation is not a valid IFC representation type.
    """
    value = ifc_normalise_color(color_rgb) if isinstance(color_rgb, str) else color_rgb

    # Creating a new style
    style_ifc = ifcopenshell.api.style.add_style(model, name="Style")

    ifcopenshell.api.style.add_surface_style(
        model,
        style=style_ifc,
        ifc_class="IfcSurfaceStyleShading",
        attributes={
            "SurfaceColour": {
                "Name": None,
                "Red": value[0],
                "Green": value[1],
                "Blue": value[2],
            },
            **({"Transparency": transparency} if transparency is not None else {}),
        },
    )
    if representation.is_a("IfcRepresentation"):
        ifcopenshell.api.style.assign_representation_styles(
            model, shape_representation=representation, styles=[style_ifc]
        )
    elif representation.is_a("IfcRepresentationItem"):
        ifcopenshell.api.style.assign_item_style(model, item=representation, style=style_ifc)
    else:
        raise TypeError(f"Unable to assign style to instance of type {representation.is_a()}")


def assign_layer_to_representation(
    model,
    representation: ifcopenshell.entity_instance,
    layer_name: str,
    color: tuple = (1.0, 1.0, 1.0),
    transparency: float = 0.0,
) -> None:
    """
    Assign a layer to the given representation, reusing or creating IfcPresentationLayerWithStyle.

    Args:
        model: The IFC model instance.
        representation: The representation to assign to the layer.
        layer_name: Name of the layer.
        color: Normalized RGB tuple for the layer style (default: white).
        transparency: Transparency for the layer style (default: 0.0).
    """
    try:
        items_to_assign = []

        # Assign the representation itself if it's a geometric solid
        if hasattr(representation, "is_a") and representation.is_a() in [
            "IfcExtrudedAreaSolid",
            "IfcTriangulatedFaceSet",
            "IfcPolygonalFaceSet",
            "IfcMappedItem",
            "IfcSweptDiskSolid",
        ]:
            items_to_assign.append(representation)

        # Add geometry items from the representation if present
        if hasattr(representation, "Items") and representation.Items:
            for item in representation.Items:
                items_to_assign.append(item)
                if hasattr(item, "is_a") and item.is_a("IfcMappedItem"):
                    items_to_assign.append(item)

        # Add the representation itself if it's a mapped representation
        if hasattr(representation, "is_a") and representation.is_a("IfcShapeRepresentation"):
            if getattr(representation, "RepresentationType", "") == "MappedRepresentation":
                items_to_assign.append(representation)

        # Remove duplicates
        items_to_assign = list(dict.fromkeys(items_to_assign))

        # Don't create layer if no items to assign (prevents BricsCAD errors)
        if not items_to_assign:
            return

        # Create surface style for the layer
        layer_color = model.create_entity(
            "IfcColourRgb",
            Name="LayerColor",
            Red=color[0],
            Green=color[1],
            Blue=color[2],
        )
        surface_style_shading = model.create_entity(
            "IfcSurfaceStyleShading",
            SurfaceColour=layer_color,
            Transparency=transparency,
        )
        surface_style = model.create_entity(
            "IfcSurfaceStyle",
            Name="LayerStyle",
            Side="POSITIVE",
            Styles=[surface_style_shading],
        )

        # Check if layer already exists
        existing_layer = None
        for layer in model.by_type("IfcPresentationLayerWithStyle"):
            if layer.Name == layer_name:
                existing_layer = layer
                break

        if existing_layer:
            existing_items = list(existing_layer.AssignedItems) if existing_layer.AssignedItems else []
            existing_items.extend(items_to_assign)
            existing_layer.AssignedItems = list(dict.fromkeys(existing_items))
        else:
            model.create_entity(
                "IfcPresentationLayerWithStyle",
                Name=layer_name,
                Description=None,
                AssignedItems=items_to_assign,
                LayerOn=True,
                LayerFrozen=False,
                LayerBlocked=False,
                LayerStyles=[surface_style],
            )

        # Also assign mapped items to the layer
        if hasattr(representation, "Items") and representation.Items:
            for item in representation.Items:
                if hasattr(item, "is_a") and item.is_a("IfcMappedItem"):
                    # Handle mapped items recursively
                    if hasattr(item, "MappingSource") and item.MappingSource:
                        mapped_rep = item.MappingSource.MappedRepresentation
                        if mapped_rep:
                            assign_layer_to_representation(model, mapped_rep, layer_name, color, transparency)

    except Exception as e:
        print(f"Warning: Could not assign layer '{layer_name}' to representation: {e}")
