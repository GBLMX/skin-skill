"""Body poses for 3D rendering (borrowed from Blockbench's mature poses).

Each pose defines per-part transforms (rotation/translation) applied to the
body-part cubes before orthographic projection. Rotations are in degrees on
the standard Minecraft body axes, mimicking Blockbench's pose system.

Pose keys: natural, walking, sitting, crouching, jumping, aiming.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Tuple


@dataclass(frozen=True)
class PartPose:
    """Per-part rotation (degrees) and translation (voxel units)."""
    rx: float = 0.0   # pitch (rotate around X)
    ry: float = 0.0   # yaw (rotate around Y)
    rz: float = 0.0   # roll (rotate around Z)
    dx: float = 0.0   # translation X
    dy: float = 0.0   # translation Y
    dz: float = 0.0   # translation Z


# Part names as used in renderer
PART_KEYS = ("head", "body", "right_arm", "left_arm", "right_leg", "left_leg")


def _pose(**overrides) -> Dict[str, PartPose]:
    base = {k: PartPose() for k in PART_KEYS}
    base.update(overrides)
    return base


# ---------------------------------------------------------------------------
# Pose library (angles chosen for recognizable silhouettes)
# ---------------------------------------------------------------------------
POSES: Dict[str, Dict[str, PartPose]] = {
    "natural": _pose(),

    "walking": _pose(
        right_arm=PartPose(rx=-30),
        left_arm=PartPose(rx=30),
        right_leg=PartPose(rx=20),
        left_leg=PartPose(rx=-20),
    ),

    "sitting": _pose(
        head=PartPose(dy=-2),
        body=PartPose(dy=-2),
        right_arm=PartPose(dy=-2),
        left_arm=PartPose(dy=-2),
        right_leg=PartPose(rx=90, dy=-4, dz=-2),
        left_leg=PartPose(rx=90, dy=-4, dz=2),
    ),

    "crouching": _pose(
        body=PartPose(rx=15, dy=-2),
        head=PartPose(dy=-4),
        right_leg=PartPose(rx=45, dy=-2),
        left_leg=PartPose(rx=45, dy=-2),
        right_arm=PartPose(rx=-15),
        left_arm=PartPose(rx=-15),
    ),

    "jumping": _pose(
        right_arm=PartPose(rx=-160),
        left_arm=PartPose(rx=-160),
        right_leg=PartPose(rx=-30, dy=2),
        left_leg=PartPose(rx=30, dy=2),
        head=PartPose(ry=10),
    ),

    "aiming": _pose(
        right_arm=PartPose(rx=-90, ry=20),
        left_arm=PartPose(rx=-60, ry=-10),
        head=PartPose(ry=-15),
    ),
}


def get_pose(name: str) -> Dict[str, PartPose]:
    """Return a pose by name (falls back to natural)."""
    if name not in POSES:
        raise ValueError(f"unknown pose {name!r}; choices: {sorted(POSES)}")
    return POSES[name]
