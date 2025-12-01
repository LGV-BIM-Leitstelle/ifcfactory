"""
Unit Conversion Utilities
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

This module provides unit conversion utilities for converting between
pint quantities and IFC measure types.
"""

from pint import UnitRegistry

ureg = UnitRegistry()

Dim = ureg.get_dimensionality

L = Dim("[length]")
A = Dim("[length]") ** 2
V = Dim("[length]") ** 3
M = Dim("[mass]")
T = Dim("[time]")
E = Dim("[current]")
K = Dim("[temperature]")
N = Dim("[substance]")
J = Dim("[luminosity]")

rad_dim = ureg.radian.dimensionality
sr_dim = ureg.steradian.dimensionality

P = M / (L * T**2)

pint_to_ifc = {
    L: "IfcLengthMeasure",
    A: "IfcAreaMeasure",
    V: "IfcVolumeMeasure",
    M: "IfcMassMeasure",
    T: "IfcTimeMeasure",
    E: "IfcElectricCurrentMeasure",
    K: "IfcThermodynamicTemperatureMeasure",
    N: "IfcAmountOfSubstanceMeasure",
    J: "IfcLuminousIntensityMeasure",
    rad_dim: "IfcPlaneAngleMeasure",
    sr_dim: "IfcSolidAngleMeasure",
    P: "IfcPressureMeasure",
    ureg.dimensionless: "IfcReal",
}

if __name__ == "__main__":
    assert pint_to_ifc[ureg.meter.dimensionality] == "IfcLengthMeasure"
