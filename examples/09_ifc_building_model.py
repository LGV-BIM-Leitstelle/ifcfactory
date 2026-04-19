"""
ifcfactory Examples
===================

Example 9 - structure Building
--------------------------------

A high-rise office tower: a ground-floor lobby with a central entrance door,
followed by 120 identical office floors each with four south-facing windows.
Follows the same structure as ``10_ifc_open_house.py``:
constants → materials → type-geometry helpers → step-by-step ``main``.


IFC patterns demonstrated
=========================

* **Type + occurrence** — one shared ``IfcWindowType`` / ``IfcDoorType``
  pre-built once and reused by every occurrence via ``BIMFactoryElement``'s
  built-in result cache (``_build_result``).
* **Openings in walls** — ``Boolean.Difference`` between wall ``Box`` and
  ``IfcOpeningElement`` voids.
* **Batch build** — ``BIMFactoryElement.build_in`` assigns all elements of a
  storey in one ``IfcRelContainedInSpatialStructure`` call per floor.
* **Per-storey rotation / twisted tower** — set ``FLOOR_TWIST_DEG`` to a
  non-zero value (e.g. ``1.5``) and each successive floor rotates by that many
  additional degrees around the building centre, producing a helical silhouette.


Copyright (C) 2025 Freie und Hansestadt Hamburg, Landesbetrieb Geoinformation und Vermessung
BIM-Leitstelle, Ahmed Salem <ahmed.salem@gv.hamburg.de>
Developed in collaboration with Thomas Krijnen <mail@thomaskrijnen.com>
"""

import ifcopenshell.api.aggregate
import ifcopenshell.api.root

from examples.util import create_basic_ifc_setup
from ifcfactory import (
    BIMFactoryElement,
    Boolean,
    BooleanOperationTypes,
    Box,
    Material,
    Style,
    Transform,
)

# --8<-- [start:structure_materials]
# ---------------------------------------------------------------------------
# Materials
# ---------------------------------------------------------------------------
concrete_mat = Material(name="CONCRETE", category="concrete", rgb=(210, 210, 205))
glass_mat = Material(name="GLASS", category="glass", rgb=(150, 185, 215), transparency=0.6)
frame_mat = Material(name="FRAME", category="steel", rgb=(55, 55, 60))
door_mat = Material(name="DOOR", category="steel", rgb=(40, 40, 45))
# --8<-- [end:structure_materials]

# --8<-- [start:structure_constants]
# ---------------------------------------------------------------------------
# Building envelope
# ---------------------------------------------------------------------------
WALL_T = 0.30
LOBBY_HEIGHT = 5.0  # ground-floor clear height
STOREY_HEIGHT = 4.0  # typical floor height
NUM_STOREYS = 5  # office floors above lobby
FLOOR_TWIST_DEG = 3.0  # degrees each floor rotates more than the one below, 0.0  → no twist (default)
SLAB_T = 0.30  # floor slab thickness
BUILDING_W = 40.0  # total outer X span
BUILDING_D = 40.0  # total outer Y span
INNER_W = BUILDING_W - 2 * WALL_T

# ---------------------------------------------------------------------------
# South-facade windows (typical floors)
# ---------------------------------------------------------------------------
NUM_WINDOWS = 18
WINDOW_W = 1.6  # window width
WINDOW_H = 2.0  # window height
WINDOW_SILL_Z = 0.8  # sill height above floor level
WINDOW_SPACING = INNER_W / (NUM_WINDOWS + 1)
WINDOW_REVEAL_NUDGE = 0.02  # glass set back from inner wall face

# ---------------------------------------------------------------------------
# Lobby entrance door
# ---------------------------------------------------------------------------
DOOR_W = 1.5
DOOR_H = 3.0
DOOR_REVEAL_NUDGE = 0.02

_BAR = 0.06  # window frame bar section
# --8<-- [end:structure_constants]


# --8<-- [start:structure_window_helper]
def _window_type_geometry() -> list:
    """
    Representation items for ``IfcWindowType``:
    two vertical posts, top and bottom rails, one glass pane.
    All items are ``Box`` extrusions → SweptSolid representation.
    """
    inner_w = WINDOW_W - 2 * _BAR
    inner_h = WINDOW_H - 2 * _BAR
    return [
        # Left vertical post — at origin
        Style(item=Box(width=_BAR, depth=_BAR, height=WINDOW_H), rgb=frame_mat.rgb),
        # Right vertical post
        Transform(
            translation=(WINDOW_W - _BAR, 0.0, 0.0),
            item=Style(item=Box(width=_BAR, depth=_BAR, height=WINDOW_H), rgb=frame_mat.rgb),
        ),
        # Bottom rail — at origin
        Style(item=Box(width=WINDOW_W, depth=_BAR, height=_BAR), rgb=frame_mat.rgb),
        # Top rail
        Transform(
            translation=(0.0, 0.0, WINDOW_H - _BAR),
            item=Style(item=Box(width=WINDOW_W, depth=_BAR, height=_BAR), rgb=frame_mat.rgb),
        ),
        # Glass pane
        Transform(
            translation=(_BAR, 0.0, _BAR),
            item=Style(
                item=Box(width=inner_w, depth=0.01, height=inner_h),
                rgb=glass_mat.rgb,
                transparency=glass_mat.transparency,
            ),
        ),
    ]


# --8<-- [end:structure_window_helper]


# --8<-- [start:structure_door_helper]
def _door_type_geometry() -> list:
    """
    Representation items for ``IfcDoorType``:
    two side posts, one top rail, one recessed door panel.
    """
    post_w = 0.10
    post_d = 0.08
    panel_w = DOOR_W - 2 * post_w
    panel_d = 0.04
    return [
        # Left post — at origin
        Style(item=Box(width=post_w, depth=post_d, height=DOOR_H), rgb=door_mat.rgb),
        # Right post
        Transform(
            translation=(DOOR_W - post_w, 0.0, 0.0),
            item=Style(item=Box(width=post_w, depth=post_d, height=DOOR_H), rgb=door_mat.rgb),
        ),
        # Top rail
        Transform(
            translation=(0.0, 0.0, DOOR_H - post_w),
            item=Style(item=Box(width=DOOR_W, depth=post_d, height=post_w), rgb=door_mat.rgb),
        ),
        # Door panel
        Transform(
            translation=(post_w, post_d, 0.0),
            item=Style(item=Box(width=panel_w, depth=panel_d, height=DOOR_H), rgb=door_mat.rgb),
        ),
    ]


# --8<-- [end:structure_door_helper]


# --8<-- [start:structure_rotation_helper]
def _rotated(items: list, angle_deg: float) -> list:
    """Wrap every top-level item in a rotation around the building footprint centre.

    The pivot is ``(BUILDING_W / 2, BUILDING_D / 2, 0)``.  Rotation is applied
    in three nested ``Transform`` steps — translate to pivot, rotate, translate
    back — so that the building footprint stays centred on the same XY position
    regardless of angle.

    When ``angle_deg`` is 0 (or within floating-point noise of 0) the list is
    returned as-is, making this a zero-cost no-op for the default
    ``FLOOR_TWIST_DEG = 0.0`` case.

    Usage — progressive twist over ``NUM_STOREYS`` floors::

        BIMFactoryElement.build_in(
            model, inst=storey,
            items=_rotated(floor_items, floor_num * FLOOR_TWIST_DEG)
        )
    """
    if abs(angle_deg) < 1e-9:
        return items
    cx, cy = BUILDING_W / 2.0, BUILDING_D / 2.0
    return [
        Transform(
            translation=(cx, cy, 0.0),
            item=Transform(
                rotation=(angle_deg, "Z"),
                item=Transform(
                    translation=(-cx, -cy, 0.0),
                    item=item,
                ),
            ),
        )
        for item in items
    ]


# --8<-- [end:structure_rotation_helper]


# --8<-- [start:structure_main_header]
@create_basic_ifc_setup("Example 9 - Building Model")
def main(model, _, __, building):
    # --8<-- [end:structure_main_header]

    # --8<-- [start:structure_step_01_lobby]
    # --- Step 1 · Lobby (ground floor with entrance door) -----------------
    # South wall carries one centred door void (``Boolean.Difference``).
    # The ``IfcDoor`` occurrence with its inline ``IfcDoorType`` sits at the
    # opening on the inner south face.  The remaining three walls are solid
    # boxes.  ``BIMFactoryElement.build_in`` assigns all lobby elements to
    # the storey in a single ``IfcRelContainedInSpatialStructure`` call.
    lobby = ifcopenshell.api.root.create_entity(model, ifc_class="IfcBuildingStorey", name="Lobby")
    lobby.Elevation = 0.0
    ifcopenshell.api.aggregate.assign_object(model, relating_object=building, products=[lobby])

    door_x = (INNER_W - DOOR_W) / 2.0  # centre door on inner south face

    BIMFactoryElement.build_in(
        model,
        inst=lobby,
        items=[
            # Floor slab
            Transform(
                translation=(0.0, 0.0, -SLAB_T),
                item=BIMFactoryElement(
                    type="IfcSlab",
                    name="Lobby_Slab",
                    material=concrete_mat,
                    children=[Box(width=BUILDING_W, depth=BUILDING_D, height=SLAB_T)],
                ),
            ),
            # South wall — door opening
            Transform(
                translation=(WALL_T, 0.0, 0.0),
                item=Boolean(
                    operation=BooleanOperationTypes.Difference,
                    children=[
                        BIMFactoryElement(
                            type="IfcWall",
                            name="Lobby_SouthWall",
                            material=concrete_mat,
                            children=[Box(width=INNER_W, depth=WALL_T, height=LOBBY_HEIGHT)],
                        ),
                        Transform(
                            translation=(door_x, 0.0, 0.0),
                            item=BIMFactoryElement(
                                type="IfcOpeningElement",
                                name="Lobby_DoorOpening",
                                children=[Box(width=DOOR_W, depth=WALL_T + 0.1, height=DOOR_H)],
                            ),
                        ),
                    ],
                ),
            ),
            # North wall — solid
            Transform(
                translation=(WALL_T, BUILDING_D - WALL_T, 0.0),
                item=BIMFactoryElement(
                    type="IfcWall",
                    name="Lobby_NorthWall",
                    material=concrete_mat,
                    children=[Box(width=INNER_W, depth=WALL_T, height=LOBBY_HEIGHT)],
                ),
            ),
            # West wall — solid
            Transform(
                translation=(0.0, 0.0, 0.0),
                item=BIMFactoryElement(
                    type="IfcWall",
                    name="Lobby_WestWall",
                    material=concrete_mat,
                    children=[Box(width=WALL_T, depth=BUILDING_D, height=LOBBY_HEIGHT)],
                ),
            ),
            # East wall — solid
            Transform(
                translation=(BUILDING_W - WALL_T, 0.0, 0.0),
                item=BIMFactoryElement(
                    type="IfcWall",
                    name="Lobby_EastWall",
                    material=concrete_mat,
                    children=[Box(width=WALL_T, depth=BUILDING_D, height=LOBBY_HEIGHT)],
                ),
            ),
            # Door occurrence centred on inner south face
            Transform(
                translation=(WALL_T + door_x, WALL_T - DOOR_REVEAL_NUDGE, 0.0),
                item=BIMFactoryElement(
                    type="IfcDoor",
                    name="Lobby_EntranceDoor",
                    material=door_mat,
                    children=[
                        BIMFactoryElement(
                            type="IfcDoorType",
                            name="structure_DoorType",
                            material=door_mat,
                            children=_door_type_geometry(),
                        )
                    ],
                ),
            ),
        ],
    )
    # --8<-- [end:structure_step_01_lobby]

    # --8<-- [start:structure_step_02_floors]
    # --- Step 2 · Typical floors 1–120 (south windows) --------------------
    # Each floor has ``NUM_WINDOWS`` evenly-spaced openings on the south wall.
    # One shared ``IfcWindowType`` is pre-built here and reused by every
    # occurrence: ``BIMFactoryElement.build()`` caches the IFC entity on the
    # first call and returns the same instance on all subsequent calls, so
    # only one ``IfcWindowType`` (and its geometry) is written to the file
    # instead of 480 duplicate entities.
    #
    # Placement convention for openings vs. occurrences
    # --------------------------------------------------
    # ``IfcOpeningElement`` voids are placed INSIDE a ``Boolean.Difference``.
    # ``ifcopenshell.api.feature.add_feature`` sets the opening's
    # ``PlacementRelTo`` to the wall's ``ObjectPlacement``, so opening
    # translations are in the **wall's local frame** (Z = 0 at the wall base).
    # The outer ``Transform(translation=(WALL_T, 0, z))`` then carries both the
    # wall and its opening to the correct world height automatically.
    # Window *occurrences* live outside the Boolean as independent spatial items
    # and must therefore use world coordinates: ``z + WINDOW_SILL_Z``.
    window_type = BIMFactoryElement(
        type="IfcWindowType",
        name="structure_WindowType",
        material=frame_mat,
        children=_window_type_geometry(),
    )

    for floor_num in range(1, NUM_STOREYS + 1):
        z = LOBBY_HEIGHT + (floor_num - 1) * STOREY_HEIGHT

        storey = ifcopenshell.api.root.create_entity(
            model, ifc_class="IfcBuildingStorey", name=f"Floor {floor_num:03d}"
        )
        storey.Elevation = z
        ifcopenshell.api.aggregate.assign_object(model, relating_object=building, products=[storey])

        openings = [
            Transform(
                translation=((i + 1) * WINDOW_SPACING - WINDOW_W / 2, 0.0, WINDOW_SILL_Z),
                item=BIMFactoryElement(
                    type="IfcOpeningElement",
                    name=f"F{floor_num:03d}_Opening_{i + 1}",
                    qsets=False,
                    children=[Box(width=WINDOW_W, depth=WALL_T + 0.1, height=WINDOW_H)],
                ),
            )
            for i in range(NUM_WINDOWS)
        ]

        windows = [
            Transform(
                translation=(
                    WALL_T + (i + 1) * WINDOW_SPACING - WINDOW_W / 2,
                    WALL_T - WINDOW_REVEAL_NUDGE,
                    z + WINDOW_SILL_Z,
                ),
                item=BIMFactoryElement(
                    type="IfcWindow",
                    name=f"F{floor_num:03d}_Window_{i + 1}",
                    material=frame_mat,
                    children=[window_type],
                ),
            )
            for i in range(NUM_WINDOWS)
        ]

        floor_items = [
            # Floor slab
            Transform(
                translation=(0.0, 0.0, z - SLAB_T),
                item=BIMFactoryElement(
                    type="IfcSlab",
                    name=f"F{floor_num:03d}_Slab",
                    material=concrete_mat,
                    qsets=False,
                    children=[Box(width=BUILDING_W, depth=BUILDING_D, height=SLAB_T)],
                ),
            ),
            # South wall with window openings
            Transform(
                translation=(WALL_T, 0.0, z),
                item=Boolean(
                    operation=BooleanOperationTypes.Difference,
                    children=[
                        BIMFactoryElement(
                            type="IfcWall",
                            name=f"F{floor_num:03d}_SouthWall",
                            material=concrete_mat,
                            qsets=False,
                            children=[Box(width=INNER_W, depth=WALL_T, height=STOREY_HEIGHT - SLAB_T)],
                        ),
                        *openings,
                    ],
                ),
            ),
            # North wall — solid
            Transform(
                translation=(WALL_T, BUILDING_D - WALL_T, z),
                item=BIMFactoryElement(
                    type="IfcWall",
                    name=f"F{floor_num:03d}_NorthWall",
                    material=concrete_mat,
                    qsets=False,
                    children=[Box(width=INNER_W, depth=WALL_T, height=STOREY_HEIGHT - SLAB_T)],
                ),
            ),
            # West wall — solid
            Transform(
                translation=(0.0, 0.0, z),
                item=BIMFactoryElement(
                    type="IfcWall",
                    name=f"F{floor_num:03d}_WestWall",
                    material=concrete_mat,
                    qsets=False,
                    children=[Box(width=WALL_T, depth=BUILDING_D, height=STOREY_HEIGHT - SLAB_T)],
                ),
            ),
            # East wall — solid
            Transform(
                translation=(BUILDING_W - WALL_T, 0.0, z),
                item=BIMFactoryElement(
                    type="IfcWall",
                    name=f"F{floor_num:03d}_EastWall",
                    material=concrete_mat,
                    qsets=False,
                    children=[Box(width=WALL_T, depth=BUILDING_D, height=STOREY_HEIGHT - SLAB_T)],
                ),
            ),
            # Window occurrences
            *windows,
        ]

        BIMFactoryElement.build_in(
            model,
            inst=storey,
            items=_rotated(floor_items, floor_num * FLOOR_TWIST_DEG),
        )
    # --8<-- [end:structure_step_02_floors]


if __name__ == "__main__":
    main()
