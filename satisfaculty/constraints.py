#!/usr/bin/env python3
"""
Core constraint classes for schedule optimization.

These define the feasibility requirements that all valid schedules must satisfy.
"""

import pandas as pd
from .constraint_base import ConstraintBase
from pulp import lpSum
from .scheduler import filter_keys


class AssignAllCourses(ConstraintBase):
    """Ensures each course is scheduled exactly once."""

    def __init__(self):
        super().__init__(name="Assign all courses")

    def apply(self, scheduler) -> int:
        count = 0
        for course in scheduler.courses:
            scheduler.prob += (
                lpSum(scheduler.x[k] for k in filter_keys(scheduler.keys, course=course)) == 1,
                f"assign_course_{course}"
            )
            count += 1
        return count


class NoInstructorOverlap(ConstraintBase):
    """Ensures an instructor can only teach one course at a time."""

    def __init__(self):
        super().__init__(name="No instructor overlap")

    def apply(self, scheduler) -> int:
        count = 0
        for instructor in scheduler.instructors:
            for t in scheduler.time_slots:
                scheduler.prob += (
                    lpSum(
                        scheduler.x[k] * scheduler.a[(instructor, k[0])]
                        for k in filter_keys(scheduler.keys, predicate=scheduler.make_overlap_predicate(t))
                    ) <= 1,
                    f"no_instructor_overlap_{instructor}_{t}"
                )
                count += 1
        return count


class NoRoomOverlap(ConstraintBase):
    """Ensures a room can only host one course at a time."""

    def __init__(self):
        super().__init__(name="No room overlap")

    def apply(self, scheduler) -> int:
        # Collect all unique (day, start_time) pairs from all time slots
        day_start_pairs = set()
        for slot in scheduler.time_slots:
            start_minutes = scheduler.slot_start_minutes[slot]
            for day in scheduler.slot_days[slot]:
                day_start_pairs.add((day, start_minutes))

        count = 0
        buffer_minutes = 15
        for room in scheduler.rooms:
            for day, start_minutes in day_start_pairs:
                # Find all slots that contain this day and overlap this start time
                overlapping_keys = []
                for k in scheduler.keys:
                    course, r, slot = k
                    if r != room:
                        continue
                    # Check if this slot contains the specific day
                    if day not in scheduler.slot_days[slot]:
                        continue
                    # Check time overlap
                    slot_start = scheduler.slot_start_minutes[slot]
                    slot_end = scheduler.slot_end_minutes[slot]
                    if slot_start <= start_minutes and slot_end > (start_minutes - buffer_minutes):
                        overlapping_keys.append(k)

                if overlapping_keys:
                    scheduler.prob += (
                        lpSum(scheduler.x[k] for k in overlapping_keys) <= 1,
                        f"no_room_overlap_{room}_{day}_{start_minutes}"
                    )
                    count += 1
        return count


class RoomCapacity(ConstraintBase):
    """Ensures room capacity is not exceeded by course enrollment."""

    def __init__(self):
        super().__init__(name="Room capacity")

    def apply(self, scheduler) -> int:
        count = 0
        for k in scheduler.keys:
            course, room, _ = k
            if scheduler.enrollments[course] > scheduler.capacities[room]:
                scheduler.x[k].upBound = 0
                count += 1
        return count


class AvoidRoomsForCourseType(ConstraintBase):
    """Disallow specific rooms for a given course type."""

    def __init__(self, rooms: list[str], course_type: str):
        self.rooms = set(rooms)
        self.course_type = course_type
        super().__init__(name=f"Avoid rooms ({', '.join(rooms)}) for {course_type}")

    def apply(self, scheduler) -> int:
        count = 0
        for course, room, time_slot in scheduler.keys:
            if scheduler.course_slot_types[course] == self.course_type and room in self.rooms:
                scheduler.x[(course, room, time_slot)].upBound = 0
                count += 1
        return count


class ForceRooms(ConstraintBase):
    """Forces specific courses to be assigned to specific rooms."""

    def __init__(self, column: str = 'Force Room'):
        self.column = column
        super().__init__(name=f"Force rooms ({column})")

    def apply(self, scheduler) -> int:
        df = scheduler.courses_df
        if self.column not in df.columns:
            return 0
        count = 0
        for _, row in df.iterrows():
            course = row['Course']
            forced_room = row[self.column]
            if pd.notna(forced_room) and str(forced_room).strip() != '':
                forced_room = str(forced_room).strip()
                scheduler.prob += (
                    lpSum(scheduler.x[k] for k in filter_keys(scheduler.keys, course=course, room=forced_room)) == 1,
                    f"force_room_{course}"
                )
                count += 1
        return count


class ForceTimeSlots(ConstraintBase):
    """Forces specific courses to be assigned to specific time slots."""

    def __init__(self, column: str = 'Force Time Slot'):
        self.column = column
        super().__init__(name=f"Force time slots ({column})")

    def apply(self, scheduler) -> int:
        df = scheduler.courses_df
        if self.column not in df.columns:
            return 0
        count = 0
        for _, row in df.iterrows():
            course = row['Course']
            forced_slot = row[self.column]
            if pd.notna(forced_slot) and str(forced_slot).strip() != '':
                forced_slot = str(forced_slot).strip()
                scheduler.prob += (
                    lpSum(scheduler.x[k] for k in filter_keys(scheduler.keys, course=course, time_slot=forced_slot)) == 1,
                    f"force_time_slot_{course}"
                )
                count += 1
        return count
