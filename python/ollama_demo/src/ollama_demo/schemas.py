from __future__ import annotations

from typing import Literal, Optional

from pydantic import BaseModel, Field


class BBox(BaseModel):
    x_min: int = Field(ge=0)
    y_min: int = Field(ge=0)
    x_max: int = Field(ge=0)
    y_max: int = Field(ge=0)


class RobotInImage(BaseModel):
    visible: bool
    bbox: Optional[BBox] = None
    heading_deg: Optional[float] = Field(
        default=None,
        description="Estimated robot heading (yaw) relative to the camera, in degrees.",
    )

class DoorInImage(BaseModel):
    visible: bool
    bbox: Optional[BBox] = None
    heading_deg: Optional[float] = Field(
        default=None,
        description="Estimated door heading (yaw) relative to the camera, in degrees.",
    )


class MotionCommand(BaseModel):
    action: Literal["move", "stop", "turn_left", "turn_right", "unknown"]
    linear_vel_mps: float = Field(
        default=0.0, description="Commanded linear velocity (m/s)."
    )
    angular_vel_rps: float = Field(
        default=0.0, description="Commanded angular velocity (rad/s)."
    )


class PerceptionAndCommand(BaseModel):
    # robot: RobotInImage  # legacy/unused
    door: DoorInImage
    command: MotionCommand
    confidence: float = Field(ge=0.0, le=1.0)
    notes: str = ""
