#!/usr/bin/env python3
"""
Example script demonstrating lexicographic optimization with configurable constraints.

This shows how to define custom constraints and objective priorities for schedule optimization.
Each user can create their own script with different constraint and objective configurations.
"""

import os
from pathlib import Path

# Avoid matplotlib cache issues in environments where ~ isn't writable.
os.environ.setdefault("MPLCONFIGDIR", "/tmp")

from satisfaculty import *

base_dir = Path(__file__).resolve().parent

scheduler = InstructorScheduler()
scheduler.load_rooms(str(base_dir / 'rooms.csv'))
scheduler.load_courses(str(base_dir / 'courses.csv'))
scheduler.load_time_slots(str(base_dir / 'time_slots.csv'))

# Add constraints (required for a valid schedule)
scheduler.add_constraints([
    AssignAllCourses(),
    NoInstructorOverlap(),
    NoRoomOverlap(),
    RoomCapacity(),
    AvoidRoomsForCourseType(['AERO 141', 'AERO N100'], 'Lecture'),
    ForceRooms(str(base_dir / 'courses.csv')),
    ForceTimeSlots(str(base_dir / 'courses.csv')),
])

# Define lexicographic optimization objectives (in priority order)
objectives = [
    #MinimizeClassesBefore('9:00'),
    MaximizePreferredRooms(['AERO 120']),
    MaximizePreferredRooms(['AERO N100', 'AERO 141'], course_type='Lab110x1'),
    MaximizePreferredRooms(['AERO N100', 'AERO 141'], course_type='Lab110x2'),
    MinimizePreferredRooms(['MAIN 120']),
]

scheduler.lexicographic_optimize(objectives)
scheduler.save_schedule(str(base_dir / 'schedule.csv'))
scheduler.visualize_schedule(str(base_dir / 'schedule_visual.png'))
