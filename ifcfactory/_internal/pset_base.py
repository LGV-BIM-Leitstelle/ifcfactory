"""
Property Set Base Classes
========================

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

This module provides base classes for IFC property sets and quantity handling.
"""

import datetime
from typing import ClassVar, Generic, Literal, Optional, TypeVar, get_args

import pint
from pydantic import AliasChoices, BaseModel, Field
from pydantic_core import core_schema

U = pint.UnitRegistry()

# Define a proper TypeVar for the Quantity class
T = TypeVar("T")

# Dimension type literals for pint quantities
Length = Literal["[length]"]
Time = Literal["[time]"]


class PropertySetTemplate(BaseModel):
    pset_name: ClassVar[str]


class Quantity(Generic[T]):
    @classmethod
    def __get_pydantic_core_schema__(cls, source_type, _):
        prescribed = U.get_dimensionality(get_args(get_args(source_type)[0])[0])

        def _validate(val):
            if not isinstance(val, pint.Quantity):
                try:
                    val = U.Quantity(*val) if isinstance(val, (list, tuple)) else U.Quantity(val)
                except Exception as e:
                    raise ValueError(f"Could not parse quantity {val!r}") from e

            if not val.check(prescribed):
                raise ValueError(f"{val!r} does not have dimension {prescribed!r}")

            return val  # .to_base_units()

        return core_schema.no_info_after_validator_function(
            _validate,
            core_schema.any_schema(),
        )


if __name__ == "__main__":

    class PsetTreeInformation(PropertySetTemplate):
        pset_name: ClassVar[str] = "Pset_TreeInformation"

        tree_type: str = Field(
            validation_alias=AliasChoices("tree_type", "_TreeType"),
            serialization_alias="_TreeType",
            default="undefined",
        )

        survey_date: datetime.date = Field(
            validation_alias=AliasChoices("survey_date", "_SurveyDate"),
            serialization_alias="_SurveyDate",
            default_factory=datetime.date.today,
        )

        tree_height: Optional[Quantity[Length]] = Field(
            validation_alias=AliasChoices("tree_height", "_TreeHeight"),
            serialization_alias="_TreeHeight",
            default=None,
        )

        log_level: int = Field(
            validation_alias=AliasChoices("log_level", "_LogLevel"),
            serialization_alias="_LogLevel",
            default=100,
        )

        planting_year: int = Field(
            validation_alias=AliasChoices("planting_year", "_PlantingYear"),
            serialization_alias="_PlantingYear",
            default=9999,
        )

        trunk_diameter: Optional[Quantity[Length]] = Field(
            validation_alias=AliasChoices("trunk_diameter", "_TrunkDiameter"),
            serialization_alias="_TrunkDiameter",
            default=None,
        )
