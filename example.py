#!/usr/bin/env python3
"""
Example script demonstrating lexicographic optimization with configurable constraints.

This shows how to define custom constraints and objective priorities for schedule optimization.
Each user can create their own script with different constraint and objective configurations.
"""

from satisfaculty import (
    InstructorScheduler,
    # Constraints
    AssignAllCourses,
    NoInstructorOverlap,
    NoRoomOverlap,
    RoomCapacity,
    ForceRooms,
    ForceTimeSlots,
    # Objectives
    MinimizeClassesBefore,
    MinimizeClassesAfter,
    MaximizePreferredRooms,
)

scheduler = InstructorScheduler()
scheduler.load_rooms('input/rooms.csv')
scheduler.load_courses('input/courses.csv')
scheduler.load_time_slots('input/time_slots.csv')

# Add constraints (required for a valid schedule)
scheduler.add_constraints([
    AssignAllCourses(),
    NoInstructorOverlap(),
    NoRoomOverlap(),
    RoomCapacity(),
    ForceRooms(),
    ForceTimeSlots(),
])

# Define optimization objectives (in priority order)
objectives = [
    MinimizeClassesBefore('9:00'),
]

scheduler.lexicographic_optimize(objectives)
scheduler.save_schedule('output/schedule.csv')
scheduler.visualize_schedule('output/schedule_visual.png')
