"""Satisfaculty - A course scheduling optimization tool."""

from .scheduler import InstructorScheduler
from .objectives import (
    MinimizeClassesBefore,
    MinimizeClassesAfter,
    MaximizePreferredRooms,
    MinimizePreferredRooms,
    MaximizeLabRootDayPairs,
)
from .constraints import (
    AssignAllCourses,
    NoInstructorOverlap,
    NoRoomOverlap,
    RoomCapacity,
    AvoidRoomsForCourseType,
    ForceRooms,
    ForceTimeSlots,
)
from .visualize_schedule import visualize_schedule

__all__ = [
    "InstructorScheduler",
    # Objectives
    "MinimizeClassesBefore",
    "MinimizeClassesAfter",
    "MaximizePreferredRooms",
    "MinimizePreferredRooms",
    "MaximizeLabRootDayPairs",
    # Constraints
    "AssignAllCourses",
    "NoInstructorOverlap",
    "NoRoomOverlap",
    "RoomCapacity",
    "AvoidRoomsForCourseType",
    "ForceRooms",
    "ForceTimeSlots",
    # Utilities
    "visualize_schedule",
]
