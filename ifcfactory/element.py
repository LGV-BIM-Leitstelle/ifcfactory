"""
High-Level BIM Elements
======================

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

This module contains high-level BIM element classes that compose primitive geometry
and operations into complete IFC elements.
"""

from __future__ import annotations

from typing import Any, List, Optional, Union

import ifc5d.qto
import ifcopenshell
import ifcopenshell.api.aggregate
import ifcopenshell.api.geometry
import ifcopenshell.api.material
import ifcopenshell.api.project
import ifcopenshell.api.pset
import ifcopenshell.api.root
import ifcopenshell.api.spatial
import ifcopenshell.api.type
import ifcopenshell.guid
import ifcopenshell.util.representation
import ifcopenshell.util.shape_builder
from pydantic import Field, model_validator

from ._internal.primitives_base import (
    ElementInterface,
    Primitive,
    RepresentationItem,
    determine_type,
    get_qto_rules,
    get_type_bearing_element,
    is_hierarchy,
    process_quantity,
    yield_super_types,
)
from ._internal.pset_base import PropertySetTemplate


class BIMFactoryElement(Primitive, ElementInterface):
    """Factory element that can contain multiple representation items or other elements.

    This class represents a BIM element that can contain multiple representation items
    or other elements. It provides functionality for building IFC entities and managing
    their relationships.

    Attributes:
        guid (str): Unique identifier for the element. Auto-generated if not provided.
        name (Optional[str]): Human-readable name for the element.
        type (Optional[str]): IFC class type name (e.g., "IfcWall", "IfcBeam").
        inst (Optional[ifcopenshell.entity_instance]): Existing IFC entity instance.
        children (List[Union[RepresentationItem, ElementInterface]]): List of child elements
            or representation items that this element contains.
        _build_result (Optional[ifcopenshell.entity_instance]): Cached IFC entity after building.
        material (Optional[Any]): Material assignment for the element.
        psets (List[PropertySetTemplate]): List of property set templates.
        qsets (bool): Whether to generate quantity sets. Defaults to True.
    """

    guid: str = Field(default_factory=ifcopenshell.guid.new)
    name: Optional[str] = None
    type: Optional[str] = None
    inst: Optional[ifcopenshell.entity_instance] = None
    children: List[Union[RepresentationItem, ElementInterface]]
    _build_result: Optional[ifcopenshell.entity_instance] = None
    material: Optional[Any] = None
    psets: List[PropertySetTemplate] = Field(default_factory=list)
    qsets: bool = True

    model_config = {"arbitrary_types_allowed": True}

    def __init__(self, **kwargs):
        """Initialize a new BIMFactoryElement.

        Args:
            **kwargs: Keyword arguments for the element attributes.
                - guid (str): Unique identifier. Auto-generated if not provided.
                - name (str): Human-readable name for the element.
                - type (str): IFC class type name (e.g., "IfcWall", "IfcBeam").
                - inst: Existing IFC entity instance.
                - children: List of child elements or representation items.
                - material: Material assignment for the element.
                - psets: List of property set templates.
                - qsets (bool): Whether to generate quantity sets.
        """
        super().__init__(**kwargs)

    def _get_type_and_occurence_counts(self):
        num_types, num_occurrences = 0, 0
        for child in filter(None, map(get_type_bearing_element, self.children)):
            # @todo hardcoded to ifc4
            schema = ifcopenshell.ifcopenshell_wrapper.schema_by_name("IFC4")  # type: ignore
            ent = schema.declaration_by_name(child.type)  # type: ignore

            if "IfcTypeObject" in yield_super_types(ent):
                num_types += 1
            if "IfcProduct" in yield_super_types(ent):
                num_occurrences += 1
        return num_types, num_occurrences

    @property
    def is_type_container(self):
        return self._get_type_and_occurence_counts()[0] > 0

    @property
    def is_occurrence_container(self):
        return self._get_type_and_occurence_counts()[1] > 0

    @property
    def ifc_type(self):
        return self.inst.is_a() if self.inst else self.type

    @model_validator(mode="after")
    def check_repr_children(self):
        child_types = set(determine_type(ch) for ch in self.children)
        if len(child_types) > 1:
            raise ValueError(
                f"Elements can contain either other elements or representation items, but not both; "
                f"Found {' '.join(type(ch).__name__ for ch in self.children)}"
            )
        if next(iter(child_types)) == ElementInterface:
            if self.is_type_container and self.is_occurrence_container:
                raise ValueError(f"Cannot mix occurences and types")
            if self.is_type_container and self.ifc_type.upper() != "IFCPROJECT" and len(self.children) > 1:
                raise ValueError(f"Only IfcProject can have multiple types as children")
        return self

    @model_validator(mode="after")
    def check_type_inst(self) -> "BIMFactoryElement":
        """
        Validate that type and inst are consistent.

        Returns:
            BIMFactoryElement: The validated element instance.

        Raises:
            ValueError: If neither type nor inst is provided, or if both are provided.
        """
        has_type, has_inst = self.type is not None, self.inst is not None
        if has_type == has_inst:
            raise ValueError(f"Either `type` or `inst` needs to be provided")
        return self

    def build(self, model: ifcopenshell.file) -> ifcopenshell.entity_instance:
        """
        Build the factory element and all its children, caching the created IFC entity.
        If the element has already been built for this model, return the cached
        entity instead of creating a duplicate. This prevents multiple identical
        IFC Type objects from being added to the file when the same
        BIMFactoryElement is reused (e.g. when assigning the same type to many
        instances).
        """
        # Return cached entity if we have already built this element for the
        # given model. This avoids creating duplicate IFC entities with the
        # same GUID when build() is invoked multiple times on the same
        # BIMFactoryElement instance.
        if hasattr(self, "_build_result") and self._build_result is not None:
            return self._build_result

        builder = ifcopenshell.util.shape_builder.ShapeBuilder(model)
        child_type = next(determine_type(ch) for ch in self.children)
        if self.inst:
            element = self.inst
        else:
            element = ifcopenshell.api.root.create_entity(model, ifc_class=self.type)
            element.GlobalId = self.guid
            element.Name = self.name
        ifcopenshell.api.geometry.edit_object_placement(model, product=element)
        if child_type is RepresentationItem:
            body = ifcopenshell.util.representation.get_context(model, "Model", "Body", "MODEL_VIEW")
            rep = builder.get_representation(context=body, items=[ch.build(model) for ch in self.children])
            # works for both occurrences and types
            ifcopenshell.api.geometry.assign_representation(model, product=element, representation=rep)

            # calculate quantities (optional when qsets=True)
            if self.qsets:
                ifc5d.qto.edit_qtos(
                    model,
                    ifc5d.qto.quantify(model, {element}, get_qto_rules(model)),
                )
        if child_type is ElementInterface:
            if self.is_occurrence_container:
                children_instances = [ch.build(model) for ch in self.children]

                if len(set(map(is_hierarchy, children_instances))) != 1:
                    raise ValueError("Cannot mix spatial structure and physical products in children")
                if element.is_a("IfcProject") and not all(map(is_hierarchy, children_instances)):
                    raise ValueError("Cannot assign physical products directly to project")
                if all(map(is_hierarchy, children_instances)) == is_hierarchy(element):
                    ifcopenshell.api.aggregate.assign_object(
                        model, products=children_instances, relating_object=element
                    )
                elif is_hierarchy(element) and not any(map(is_hierarchy, children_instances)):
                    ifcopenshell.api.spatial.assign_container(
                        model, products=children_instances, relating_structure=element
                    )
                else:
                    raise ValueError("Cannot assign spatial container to physical product")
            elif self.is_type_container and self.ifc_type.upper() == "IFCPROJECT":
                ifcopenshell.api.project.assign_declaration(
                    model,
                    definitions=[ch.build(model) for ch in self.children],
                    relating_context=element,
                )
            else:
                ifcopenshell.api.type.assign_type(
                    model,
                    related_objects=[element],
                    relating_type=self.children[0].build(model),
                )
        if self.material:
            ifcopenshell.api.material.assign_material(model, products=[element], material=self.material.build(model))

        for data in self.psets:
            # @todo this means propertyset data is never shared even if it's the same template instance in python
            pset = ifcopenshell.api.pset.add_pset(model, product=element, name=data.pset_name)
            di = data.model_dump(by_alias=True)

            di = dict(zip(di.keys(), map(lambda q: process_quantity(q, model), di.values())))
            # Filter out None values that cause issues
            di = {k: v for k, v in di.items() if v is not None}
            ifcopenshell.api.pset.edit_pset(model, pset=pset, properties=di)

        self._build_result = element
        return element
