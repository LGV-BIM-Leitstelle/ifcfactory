"""
ifcfactory Examples
===================

Example 10 - IfcOpenHouse (Tutorial)
------------------------------------

Port of the classic IfcOpenShell *IfcOpenHouse* (C++) example to *ifcfactory*:

  https://github.com/IfcOpenShell/IfcOpenShell/blob/v0.8.0/src/examples/IfcOpenHouse.cpp

Plan / dimensions reference (Python port):

  https://github.com/cvillagrasa/IfcOpenHouse/blob/master/IfcOpenHouse/core.py


How to read this file
=====================

* **Setup** — ``create_basic_ifc_setup`` (``examples.util``) creates ``IfcProject``,
  units, ``IfcSite``, and ``IfcBuilding``; ``main`` receives ``model``, ``site``,
  ``building``.

* **Constants** — Grouped by topic; derived values chain so roof and gable stay aligned.

* **Tutorial text** — Each build step is explained in a comment block **immediately
  above** the code that implements it in ``main``. Scroll top to bottom.


IFC patterns demonstrated
=========================

* **Type + occurrence** — ``IfcDoorType`` / ``IfcWindowType`` as children of
  ``IfcDoor`` / ``IfcWindow`` (reuse-friendly).
* **Openings in walls** — ``Boolean.Difference`` between wall body and
  ``IfcOpeningElement`` with a deep ``Box`` void.
* **Complex wall shape** — ``Boolean.Difference`` of extrusion + ``HalfSpace`` solids.
* **Roof** — ``Extrusion`` from a 2D profile + ``Transform`` for world alignment.


Copyright (C) 2025 Freie und Hansestadt Hamburg, Landesbetrieb Geoinformation und Vermessung
BIM-Leitstelle, Ahmed Salem <ahmed.salem@gv.hamburg.de>
Developed in collaboration with Thomas Krijnen <mail@thomaskrijnen.com>
"""

import math

import numpy as np

from examples.util import create_basic_ifc_setup
from ifcfactory import (
    BIMFactoryElement,
    Box,
    Extrusion,
    HalfSpace,
    MeshRepresentation,
    Polygon,
    Rect,
    Transform,
    Style,
    Material,
    Boolean,
    BooleanOperationTypes,
)

# --8<-- [start:tutorial_materials]
# ---------------------------------------------------------------------------
# Materials  (see examples/04_styled_elements.py)
# ---------------------------------------------------------------------------
wall_mat = Material(name="WALL", category="concrete", rgb=(191, 186, 173))
footing_mat = Material(name="FOOTING", category="concrete", rgb=(97, 102, 107))
roof_mat = Material(name="ROOF", category="brick", rgb=(61, 20, 10))
stair_mat = Material(name="STAIR", category="concrete", rgb=(115, 120, 143))
door_mat = Material(name="DOOR", category="wood", rgb=(77, 77, 77))
frame_mat = Material(name="FRAME", category="wood", rgb=(77, 77, 77))
glass_mat = Material(name="GLASS", category="glass", rgb=(77, 77, 77), transparency=0.8)
terrain_mat = Material(name="TERRAIN", category="earth", rgb=(38, 64, 13))
# --8<-- [end:tutorial_materials]

# --8<-- [start:tutorial_constants]
# ---------------------------------------------------------------------------
# Building envelope
# ---------------------------------------------------------------------------
WALL_T = 0.36  # wall thickness
WALL_T_HALF = WALL_T / 2.0
STOREY_HEIGHT = 3.0  # floor-to-ceiling height
BUILDING_LENGTH = 10.0  # interior span along X
BUILDING_WIDTH = 5.0  # interior span along Y
BUILDING_SPAN_X = 10.1  # total X span outer face to outer face
INNER_SOUTH_WALL_X = BUILDING_SPAN_X - 2.0 * WALL_T  # south wall inner clear span (9.38 m)
WINDOW_SILL_HEIGHT = 0.4  # sill height above floor
NORTH_WALL_ORIGIN_Y = 5.1  # north wall inner-face Y (IfcOpenHouse C++ port)
WINDOW_REVEAL_Y_NUDGE = 0.04  # south windows: nudge into wall thickness

# ---------------------------------------------------------------------------
# Gable walls
# ---------------------------------------------------------------------------
GABLE_BASE_SPAN = 5.46  # total Y span outer face to outer face
GABLE_RIDGE_PLAN_X = GABLE_BASE_SPAN / 2.0  # ridge centred on gable base span; world-Y of ridge in roof profile

# ---------------------------------------------------------------------------
# Roof
# ---------------------------------------------------------------------------
EAVE_Z = STOREY_HEIGHT  # roof eave sits at wall top
ROOF_OVERHANG = 0.4  # eave overhang past wall face (roof slab eaves use same offset)
ROOF_LEDGE_X = 0.1  # extra ledge along building length
ROOF_LEDGE_Y = 0.22  # extra ledge along building width
ROOF_THICKNESS = WALL_T
ROOF_SIZE_X = BUILDING_LENGTH + 2.0 * (WALL_T + ROOF_LEDGE_X)
ROOF_SIZE_Y = BUILDING_WIDTH + 2.0 * (WALL_T + ROOF_LEDGE_Y)
KNEE_Z = EAVE_Z + ROOF_OVERHANG  # 3.4 m - gable slope starts here
GABLE_RIDGE_Z = KNEE_Z + GABLE_RIDGE_PLAN_X  # eave→ridge run equals half gable span in plan
_SIN45 = math.sin(math.radians(45.0))
# 45° slopes only: inward normal offset from outer eave has |ΔY| = |ΔZ| = t / √2.
_T_PERP = ROOF_THICKNESS * _SIN45
# Vertical (plumb) distance outer ridge to inner ridge for pitch theta: t / sin(theta); here theta = 45°.
ROOF_RIDGE_VERTICAL_THICKNESS = ROOF_THICKNESS / _SIN45
ROOF_INNER_RIDGE_Z = GABLE_RIDGE_Z - ROOF_RIDGE_VERTICAL_THICKNESS


# ---------------------------------------------------------------------------
# Openings - south wall
# ---------------------------------------------------------------------------
SOUTH_OPENING_LARGE_W = 5.55  # large opening width
SOUTH_OPENING_LARGE_LEFT_X = 0.0  # left edge in inner-wall local X
SOUTH_OPENING_SMALL_W = 1.86  # small opening width (C++ x=8.0 centred -> 7.36 here)
SOUTH_OPENING_SMALL_LEFT_X = 7.36
SOUTH_OPENING_LARGE_N_PANELS = 3

# ---------------------------------------------------------------------------
# Openings - west gable window & east gable door
# ---------------------------------------------------------------------------
OPENHOUSE_WINDOW_H = 1.60  # south wall + west gable glazing height
WEST_GABLE_WINDOW_WIDTH = 2.0
WEST_GABLE_WINDOW_TYPE_TRIM = 0.23  # type width = opening width minus frame allowance
DOOR_WIDTH = 1.0
DOOR_HEIGHT = 2.2

# ---------------------------------------------------------------------------
# Windows — IfcWindowType: 4 frame bars + 1 glass pane, each with its own Style.
# All items stay IfcExtrudedAreaSolid → guess_type() returns "SweptSolid" → valid IFC.
# ---------------------------------------------------------------------------
_WINDOW_FRAME_BAR = 0.09  # m, vertical bar section & rail thickness

# ---------------------------------------------------------------------------
# Stair & terrain helpers
# ---------------------------------------------------------------------------
STAIR_FLIGHT_DEPTH = 1.2
TERRAIN_STAIR_FOCUS_Y = 2.5  # mesh ``dist`` target Y (toward stair)

# ---------------------------------------------------------------------------
# Stair profile
# ---------------------------------------------------------------------------
STAIR_PROFILE = Polygon(
    points=[
        (0.00, 0.00),
        (0.25, 0.00),
        (0.25, 0.20),
        (0.50, 0.20),
        (0.50, 0.40),
        (0.00, 0.40),
    ]
)
# --8<-- [end:tutorial_constants]


# --8<-- [start:tutorial_window_helper]
def _frame_bar(box: Box) -> Style:
    return Style(item=box, rgb=frame_mat.rgb, transparency=frame_mat.transparency)


# ---------------------------------------------------------------------------
# Terrain — simple flat grid for IfcSite, centred around the building.
# ---------------------------------------------------------------------------
def _openhouse_window_type_geometry(overall_w: float, overall_h: float, n_panels: int = 1) -> list:
    """
    Representation items for ``IfcWindowType``:
    outer frame + ``n_panels - 1`` inner dividers + ``n_panels`` glass panes, each styled.
    All items are ``IfcExtrudedAreaSolid`` → ``guess_type()`` returns "SweptSolid" → valid IFC.
    """
    b = _WINDOW_FRAME_BAR
    v_bar_h = overall_h - 2 * b
    panel_w = (overall_w - (n_panels + 1) * b) / n_panels
    gh = overall_h - 2 * b

    items = []
    # Outer left upright, inner dividers, outer right upright — raised by b to sit on bottom rail
    for i in range(n_panels + 1):
        items.append(
            Transform(
                translation=(i * (panel_w + b), 0.0, b),
                item=_frame_bar(Box(width=b, depth=b, height=v_bar_h)),
            )
        )
    # Bottom and top horizontal rails spanning full width
    items.append(_frame_bar(Box(width=overall_w, depth=b, height=b)))
    items.append(
        Transform(
            translation=(0.0, 0.0, overall_h - b),
            item=_frame_bar(Box(width=overall_w, depth=b, height=b)),
        )
    )
    # Glass panes
    for i in range(n_panels):
        items.append(
            Transform(
                translation=(b + i * (panel_w + b), 0.0, b),
                item=Style(
                    item=Box(width=panel_w, depth=0.01, height=gh),
                    rgb=glass_mat.rgb,
                    transparency=glass_mat.transparency,
                ),
            )
        )
    return items


# --8<-- [end:tutorial_window_helper]


# --8<-- [start:tutorial_door_helper]
# ---------------------------------------------------------------------------
# Door — IfcDoorType + IfcDoor inlined inside the east wall BIMFactoryElement.
# ---------------------------------------------------------------------------
_DOOR_POST_W, _DOOR_POST_D, _DOOR_POST_H = 0.08, 0.08, 2.12
_DOOR_RAIL_W, _DOOR_RAIL_D, _DOOR_RAIL_H = 1.00, 0.08, 0.08
_DOOR_PANEL_W, _DOOR_PANEL_D, _DOOR_PANEL_H = 0.86, 0.03, 2.12
# Type geometry is symmetric about local origin; frame half-thickness in plane normal to wall → ~4 cm gap
# at inner face if placement uses inner face X only. Nudge toward +X (into wall) by half post depth.
_DOOR_INNER_FACE_OFFSET_X = _DOOR_POST_D / 2.0


def _openhouse_door_type_geometry() -> list:
    """Representation items for IfcDoorType: posts, top rail, panel (1.0 m nominal width)."""
    return [
        Transform(
            translation=(0.46, 0.0, 0.0),
            item=Box(width=_DOOR_POST_W, depth=_DOOR_POST_D, height=_DOOR_POST_H),
        ),
        Transform(
            translation=(-0.46, 0.0, 0.0),
            item=Box(width=_DOOR_POST_W, depth=_DOOR_POST_D, height=_DOOR_POST_H),
        ),
        Transform(
            translation=(-0.46, 0.0, _DOOR_POST_H),
            item=Box(width=_DOOR_RAIL_W, depth=_DOOR_RAIL_D, height=_DOOR_RAIL_H),
        ),
        Transform(
            translation=(-0.46 + _DOOR_POST_W, _DOOR_POST_W, 0.0),
            item=Box(width=_DOOR_PANEL_W, depth=_DOOR_PANEL_D, height=_DOOR_PANEL_H),
        ),
    ]


# --8<-- [end:tutorial_door_helper]


# --8<-- [start:tutorial_main_header]
# ---------------------------------------------------------------------------
# main — tutorial steps 1–9 follow the ``.build(model)`` order below.
# ---------------------------------------------------------------------------
@create_basic_ifc_setup("Example 10 - IfcOpenHouse")
def main(model, _, site, building):

    # --8<-- [end:tutorial_main_header]
    # --8<-- [start:tutorial_step_01_footing]
    # --- Step 1 · Footing -------------------------------------------------
    # Place a strip footing under the full building footprint. The ``Transform``
    # shifts the box down by 2 m so the top of the footing sits at Z = 0 (roughly
    # grade). Dimensions match ``BUILDING_SPAN_X`` × ``GABLE_BASE_SPAN`` from the
    # constants section.
    BIMFactoryElement(
        inst=building,
        children=[
            Transform(
                translation=(0.0, 0.0, -2.0),
                item=BIMFactoryElement(
                    type="IfcFooting",
                    name="Footing",
                    material=footing_mat,
                    children=[Box(width=BUILDING_SPAN_X, depth=GABLE_BASE_SPAN, height=2.0)],
                ),
            ),
        ],
    ).build(model)
    # --8<-- [end:tutorial_step_01_footing]

    # --8<-- [start:tutorial_step_02_north_wall]
    # --- Step 2 · North wall ----------------------------------------------
    # Simple ``IfcWall``: one ``Box`` extrusion, no boolean. Placed at inner-face
    # offset ``WALL_T`` in X; ``NORTH_WALL_ORIGIN_Y`` / ``STOREY_HEIGHT`` match the C++ house.
    BIMFactoryElement(
        inst=building,
        children=[
            Transform(
                translation=(WALL_T, NORTH_WALL_ORIGIN_Y, 0.0),
                item=BIMFactoryElement(
                    type="IfcWall",
                    name="NorthWall",
                    material=wall_mat,
                    children=[Box(width=INNER_SOUTH_WALL_X, depth=WALL_T, height=STOREY_HEIGHT)],
                ),
            ),
        ],
    ).build(model)
    # --8<-- [end:tutorial_step_02_north_wall]

    # --8<-- [start:tutorial_step_03_south_wall]
    # --- Step 3 · South wall ----------------------------------------------
    # One outer ``BIMFactoryElement`` groups wall and both windows. First child:
    # ``Transform(translation=(WALL_T,0,0))`` shifts the wall to the inner south face, then
    # ``Boolean.Difference`` — wall ``Box`` minus two ``IfcOpeningElement`` voids
    # (historic names "WestOpening", "SouthOpening"). Next: two ``IfcWindow`` siblings
    # with inline ``IfcWindowType`` geometry from ``_openhouse_window_type_geometry``.
    BIMFactoryElement(
        inst=building,
        children=[
            Transform(
                translation=(WALL_T, 0.0, 0.0),
                item=Boolean(
                    operation=BooleanOperationTypes.Difference,
                    children=[
                        BIMFactoryElement(
                            type="IfcWall",
                            name="SouthWall",
                            material=wall_mat,
                            children=[Box(width=INNER_SOUTH_WALL_X, depth=WALL_T, height=STOREY_HEIGHT)],
                        ),
                        Transform(
                            translation=(SOUTH_OPENING_LARGE_LEFT_X, 0.0, WINDOW_SILL_HEIGHT),
                            item=BIMFactoryElement(
                                type="IfcOpeningElement",
                                name="WestOpening",
                                children=[
                                    Box(
                                        width=SOUTH_OPENING_LARGE_W,
                                        depth=0.5,
                                        height=OPENHOUSE_WINDOW_H,
                                    ),
                                ],
                            ),
                        ),
                        Transform(
                            translation=(SOUTH_OPENING_SMALL_LEFT_X, 0.0, WINDOW_SILL_HEIGHT),
                            item=BIMFactoryElement(
                                type="IfcOpeningElement",
                                name="SouthOpening",
                                children=[
                                    Box(
                                        width=SOUTH_OPENING_SMALL_W,
                                        depth=0.5,
                                        height=OPENHOUSE_WINDOW_H,
                                    ),
                                ],
                            ),
                        ),
                    ],
                ),
            ),
            Transform(
                translation=(
                    WALL_T_HALF + SOUTH_OPENING_LARGE_LEFT_X,
                    WALL_T_HALF - WINDOW_REVEAL_Y_NUDGE,
                    WINDOW_SILL_HEIGHT,
                ),
                item=BIMFactoryElement(
                    type="IfcWindow",
                    name="Window_South_Large",
                    material=frame_mat,
                    children=[
                        BIMFactoryElement(
                            type="IfcWindowType",
                            name="OpenHouse_Window_SouthLarge",
                            material=frame_mat,
                            qsets=False,
                            children=_openhouse_window_type_geometry(
                                SOUTH_OPENING_LARGE_W + WALL_T_HALF,
                                OPENHOUSE_WINDOW_H,
                                SOUTH_OPENING_LARGE_N_PANELS,
                            ),
                        )
                    ],
                ),
            ),
            Transform(
                translation=(
                    WALL_T + SOUTH_OPENING_SMALL_LEFT_X,
                    WALL_T_HALF - WINDOW_REVEAL_Y_NUDGE,
                    WINDOW_SILL_HEIGHT,
                ),
                item=BIMFactoryElement(
                    type="IfcWindow",
                    name="Window_South_Small",
                    material=frame_mat,
                    children=[
                        BIMFactoryElement(
                            type="IfcWindowType",
                            name="OpenHouse_Window_SouthSmall",
                            material=frame_mat,
                            qsets=False,
                            children=_openhouse_window_type_geometry(SOUTH_OPENING_SMALL_W, OPENHOUSE_WINDOW_H, 1),
                        )
                    ],
                ),
            ),
        ],
    ).build(model)
    # --8<-- [end:tutorial_step_03_south_wall]

    # --8<-- [start:tutorial_step_04_gable_prep]
    # --- Step 4 · Gable wall body + roof edge helpers ---------------------
    # (a) Clip normals for the gable: derived from ridge height vs. knee so the wall
    # top matches the roof slope. (b) ``south_eave_y`` / ``north_eave_y`` are reused
    # when building the merged roof profile in step 7. (c) ``_gable_solid`` is a tall
    # rectangle extrusion minus two ``HalfSpace`` solids — shared by east and west
    # gable walls in steps 5–6.
    _dy_ridge = GABLE_RIDGE_Z - KNEE_Z
    _len_south = math.hypot(GABLE_RIDGE_PLAN_X, _dy_ridge)
    _GABLE_CLIP_SOUTH_N = (-_dy_ridge / _len_south, GABLE_RIDGE_PLAN_X / _len_south, 0.0)
    _dx_north = GABLE_RIDGE_PLAN_X - GABLE_BASE_SPAN
    _len_north = math.hypot(_dx_north, _dy_ridge)
    _GABLE_CLIP_NORTH_N = (-_dy_ridge / _len_north, _dx_north / _len_north, 0.0)
    south_eave_y = -ROOF_OVERHANG
    north_eave_y = GABLE_BASE_SPAN + ROOF_OVERHANG

    _gable_solid = Boolean(
        operation=BooleanOperationTypes.Difference,
        children=[
            Extrusion(basis=Rect(width=GABLE_BASE_SPAN, height=GABLE_RIDGE_Z), depth=WALL_T),
            HalfSpace(position=(0.0, KNEE_Z, 0.0), normal=_GABLE_CLIP_SOUTH_N, flip=False),
            HalfSpace(position=(GABLE_BASE_SPAN, KNEE_Z, 0.0), normal=_GABLE_CLIP_NORTH_N, flip=True),
        ],
    )
    # --8<-- [end:tutorial_step_04_gable_prep]

    # --8<-- [start:tutorial_step_05_east_gable]
    # --- Step 5 · East gable wall + door ----------------------------------
    # ``Boolean.Difference`` subtracts an ``IfcOpeningElement`` void from the wall
    # body (``_gable_solid`` from step 4). R_z(90°) then R_y(90°) maps wall native axes
    # to world. Sibling ``Transform``: ``IfcDoor`` + inline ``IfcDoorType`` from
    # ``_openhouse_door_type_geometry``; extra rotations align local +Z (up) with world.
    BIMFactoryElement(
        inst=building,
        children=[
            Transform(
                translation=(BUILDING_SPAN_X - WALL_T, 0.0, 0.0),
                rotation=[(90.0, "Z"), (90.0, "Y")],
                item=Boolean(
                    operation=BooleanOperationTypes.Difference,
                    children=[
                        BIMFactoryElement(
                            type="IfcWall",
                            name="EastWall",
                            material=wall_mat,
                            qsets=False,
                            children=[_gable_solid],
                        ),
                        Transform(
                            translation=(GABLE_RIDGE_PLAN_X - DOOR_WIDTH / 2, 0.0, 0.0),
                            item=BIMFactoryElement(
                                type="IfcOpeningElement",
                                name="EastDoorOpening",
                                children=[
                                    Box(
                                        width=DOOR_WIDTH,
                                        depth=DOOR_HEIGHT,
                                        height=0.5,
                                    )
                                ],
                            ),
                        ),
                    ],
                ),
            ),
            Transform(
                translation=(
                    BUILDING_SPAN_X - WALL_T_HALF,
                    GABLE_RIDGE_PLAN_X - _DOOR_POST_W / 2,
                    0.0,
                ),
                rotation=[(-90.0, "X"), (90.0, "Z"), (90.0, "Y")],
                item=BIMFactoryElement(
                    type="IfcDoor",
                    name="Door",
                    material=door_mat,
                    children=[
                        BIMFactoryElement(
                            type="IfcDoorType",
                            name="OpenHouse_DoorType",
                            material=door_mat,
                            children=_openhouse_door_type_geometry(),
                        )
                    ],
                ),
            ),
        ],
    ).build(model)
    # --8<-- [end:tutorial_step_05_east_gable]

    # --8<-- [start:tutorial_step_06_west_gable]
    # --- Step 6 · West gable wall + window --------------------------------
    # Same wall orientation and shared ``_gable_solid`` as east. Opening is a tall
    # ``Box`` void for the window. ``IfcWindow`` + inline ``IfcWindowType`` use
    # ``_openhouse_window_type_geometry`` (frame bars + glazed pane with transparency).
    BIMFactoryElement(
        inst=building,
        children=[
            Transform(
                translation=(0.0, 0.0, 0.0),
                rotation=[(90.0, "Z"), (90.0, "Y")],
                item=Boolean(
                    operation=BooleanOperationTypes.Difference,
                    children=[
                        BIMFactoryElement(
                            type="IfcWall",
                            name="WestWall",
                            material=wall_mat,
                            qsets=False,
                            children=[_gable_solid],
                        ),
                        Transform(
                            translation=(
                                0.0,
                                WINDOW_SILL_HEIGHT,
                                0.0,
                            ),
                            item=BIMFactoryElement(
                                type="IfcOpeningElement",
                                name="WestWindowOpening",
                                children=[
                                    Box(
                                        width=WEST_GABLE_WINDOW_WIDTH,
                                        depth=OPENHOUSE_WINDOW_H,
                                        height=0.5,
                                    )
                                ],
                            ),
                        ),
                    ],
                ),
            ),
            Transform(
                translation=(WALL_T_HALF, WEST_GABLE_WINDOW_WIDTH, WINDOW_SILL_HEIGHT),
                rotation=(-90, "Z"),
                item=BIMFactoryElement(
                    type="IfcWindow",
                    name="Window_West_1",
                    material=frame_mat,
                    children=[
                        BIMFactoryElement(
                            type="IfcWindowType",
                            name="OpenHouse_Window_2000x1600",
                            material=frame_mat,
                            children=_openhouse_window_type_geometry(
                                WEST_GABLE_WINDOW_WIDTH - WEST_GABLE_WINDOW_TYPE_TRIM,
                                OPENHOUSE_WINDOW_H,
                                1,
                            ),
                        )
                    ],
                ),
            ),
        ],
    ).build(model)
    # --8<-- [end:tutorial_step_06_west_gable]

    # --8<-- [start:tutorial_step_07_roof]
    # --- Step 7 · Roof slab -----------------------------------------------
    # Closed hexagon in (world Z, world Y): outer ridge → north eave → north inner eave
    # → inner ridge (plumb under outer ridge) → south inner eave → south outer eave →
    # (closes back to ridge). Inner eaves use ``_T_PERP`` = t/√2 (45° slopes: cut ⟂ slope).
    # Extruded along local Z, R_y(-90°) → world −X;
    # ``translation=(ROOF_SIZE_X, 0, ROOF_RIDGE_VERTICAL_THICKNESS)`` as before.

    BIMFactoryElement(
        inst=building,
        children=[
            Transform(
                translation=(ROOF_SIZE_X, 0.0, ROOF_RIDGE_VERTICAL_THICKNESS),
                rotation=(-90.0, "Y"),
                item=BIMFactoryElement(
                    type="IfcSlab",
                    name="RoofSlab",
                    material=roof_mat,
                    children=[
                        Extrusion(
                            basis=Polygon(
                                points=[
                                    (GABLE_RIDGE_Z, GABLE_RIDGE_PLAN_X),
                                    (EAVE_Z, north_eave_y),
                                    (EAVE_Z - _T_PERP, north_eave_y - _T_PERP),
                                    (ROOF_INNER_RIDGE_Z, GABLE_RIDGE_PLAN_X),
                                    (EAVE_Z - _T_PERP, south_eave_y + _T_PERP),
                                    (EAVE_Z, south_eave_y),
                                ]
                            ),
                            depth=ROOF_SIZE_X,
                        )
                    ],
                ),
            ),
        ],
    ).build(model)
    # --8<-- [end:tutorial_step_07_roof]

    # --8<-- [start:tutorial_step_08_stair]
    # --- Step 8 · Stair flight --------------------------------------------
    # ``STAIR_PROFILE`` (defined with the constants) is extruded ``STAIR_FLIGHT_DEPTH`` in local Z.
    # ``R_x(-90°)`` turns that extrusion direction into world +Y. Placed at the east
    # end of the building so the flight reads like the original example.
    BIMFactoryElement(
        inst=building,
        children=[
            Transform(
                translation=(
                    BUILDING_SPAN_X,
                    GABLE_RIDGE_PLAN_X - STAIR_FLIGHT_DEPTH / 2,
                    0.0,
                ),
                rotation=(-90.0, "X"),
                item=BIMFactoryElement(
                    type="IfcStairFlight",
                    name="Stair",
                    material=stair_mat,
                    children=[Extrusion(basis=STAIR_PROFILE, depth=STAIR_FLIGHT_DEPTH)],
                ),
            )
        ],
    ).build(model)
    # --8<-- [end:tutorial_step_08_stair]

    # --8<-- [start:tutorial_step_09_terrain]
    # --- Step 9 · Terrain -------------------------------------------------
    # Ground on ``IfcSite`` (not the building). A 20×20 grid is built inline: vertices
    # from ``numpy`` mesh + Z = base + slope from distance to the stair + light sine
    # undulation; ``MeshRepresentation`` + ``Material`` for colour. `

    n = 20
    xx, yy = np.meshgrid(np.linspace(-5.0, 15.0, n), np.linspace(-5.0, 10.0, n))
    dist = np.sqrt((xx - BUILDING_SPAN_X) ** 2 + (yy - TERRAIN_STAIR_FOCUS_Y) ** 2)

    zz = -0.15 - 0.15 * dist + 0.2 * np.sin(xx * 0.4) * np.cos(yy * 0.5)
    vertices = list(zip(xx.ravel().tolist(), yy.ravel().tolist(), zz.ravel().tolist()))
    faces = []
    for i in range(n - 1):
        for j in range(n - 1):
            a, b = i * n + j, i * n + j + 1
            c, d = (i + 1) * n + j, (i + 1) * n + j + 1
            faces.append([a, b, d])
            faces.append([a, d, c])

    BIMFactoryElement(
        inst=site,
        children=[
            Style(
                item=MeshRepresentation(vertices=vertices, faces=faces),
                rgb=terrain_mat.rgb,
                transparency=terrain_mat.transparency,
            )
        ],
    ).build(model)
    # --8<-- [end:tutorial_step_09_terrain]


if __name__ == "__main__":
    main()
