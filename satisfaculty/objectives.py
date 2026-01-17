#!/usr/bin/env python3
"""
Example objective classes for schedule optimization.

These demonstrate common scheduling objectives that can be combined
in different orders to create customized optimization strategies.
"""

from .objective_base import ObjectiveBase
from pulp import lpSum, LpVariable
from .scheduler import filter_keys
from .utils import time_to_minutes, expand_days_any
from typing import Optional, List


class MinimizeClassesBefore(ObjectiveBase):
    """
    Minimize classes scheduled before a given time.

    Useful for avoiding early morning classes or accommodating
    instructor preferences.
    """

    def __init__(
        self,
        time: str,
        instructor: Optional[str] = None,
        sense: str = 'minimize',
        tolerance: float = 0.0
    ):
        """
        Args:
            time: Time in HH:MM format (e.g., "9:00")
            instructor: If specified, only count this instructor's classes
            sense: 'minimize' or 'maximize'
            tolerance: Fractional tolerance for lexicographic constraint
        """
        self.time = time
        self.time_minutes = time_to_minutes(time)
        self.instructor = instructor

        name_parts = [f"classes before {time}"]
        if instructor:
            name_parts.append(f"for {instructor}")

        super().__init__(
            name=f"{sense.capitalize()} {' '.join(name_parts)}",
            sense=sense,
            tolerance=tolerance
        )

    def evaluate(self, scheduler):
        def matches_criteria(course, room, time_slot):
            # Check time constraint
            slot_start = scheduler.slot_start_minutes[time_slot]
            if slot_start >= self.time_minutes:
                return False

            # Check instructor constraint
            if self.instructor:
                course_instructor = scheduler.courses_df[
                    scheduler.courses_df['Course'] == course
                ]['Instructor'].values[0]
                if course_instructor != self.instructor:
                    return False

            return True

        filtered = filter_keys(scheduler.keys, predicate=matches_criteria)
        return lpSum(scheduler.x[k] for k in filtered)


class MinimizeClassesAfter(ObjectiveBase):
    """
    Minimize classes scheduled after a given time.

    Useful for avoiding late afternoon/evening classes.
    """

    def __init__(
        self,
        time: str,
        instructor: Optional[str] = None,
        course_type: Optional[str] = None,
        sense: str = 'minimize',
        tolerance: float = 0.0
    ):
        """
        Args:
            time: Time in HH:MM format (e.g., "16:00")
            instructor: If specified, only count this instructor's classes
            course_type: If specified, only count this type ('Lecture' or 'Lab')
            sense: 'minimize' or 'maximize'
            tolerance: Fractional tolerance for lexicographic constraint
        """
        self.time = time
        self.time_minutes = time_to_minutes(time)
        self.instructor = instructor
        self.course_type = course_type

        name_parts = [f"classes after {time}"]
        if instructor:
            name_parts.append(f"for {instructor}")
        if course_type:
            name_parts.append(f"({course_type})")

        super().__init__(
            name=f"{sense.capitalize()} {' '.join(name_parts)}",
            sense=sense,
            tolerance=tolerance
        )

    def evaluate(self, scheduler):
        def matches_criteria(course, room, time_slot):
            # Check time constraint
            slot_start = scheduler.slot_start_minutes[time_slot]
            if slot_start <= self.time_minutes:
                return False

            # Check instructor constraint
            if self.instructor:
                course_instructor = scheduler.courses_df[
                    scheduler.courses_df['Course'] == course
                ]['Instructor'].values[0]
                if course_instructor != self.instructor:
                    return False

            # Check course type constraint
            if self.course_type:
                if scheduler.course_types[course] != self.course_type:
                    return False

            return True

        filtered = filter_keys(scheduler.keys, predicate=matches_criteria)
        return lpSum(scheduler.x[k] for k in filtered)


class MaximizePreferredRooms(ObjectiveBase):
    """
    Maximize use of preferred rooms.

    Useful for assigning courses to rooms with specific equipment,
    better location, or instructor preferences.
    """

    def __init__(
        self,
        preferred_rooms: List[str],
        instructor: Optional[str] = None,
        course_type: Optional[str] = None,
        tolerance: float = 0.0
    ):
        """
        Args:
            preferred_rooms: List of room names to prefer
            instructor: If specified, only for this instructor's classes
            course_type: If specified, only for this type ('Lecture' or 'Lab')
            tolerance: Fractional tolerance for lexicographic constraint
        """
        self.preferred_rooms = set(preferred_rooms)
        self.instructor = instructor
        self.course_type = course_type

        name_parts = [f"preferred rooms ({', '.join(preferred_rooms)})"]
        if instructor:
            name_parts.append(f"for {instructor}")
        if course_type:
            name_parts.append(f"({course_type})")

        super().__init__(
            name=f"Maximize {' '.join(name_parts)}",
            sense='maximize',
            tolerance=tolerance
        )

    def evaluate(self, scheduler):
        def matches_criteria(course, room, time_slot):
            # Check room constraint
            if room not in self.preferred_rooms:
                return False

            # Check instructor constraint
            if self.instructor:
                course_instructor = scheduler.courses_df[
                    scheduler.courses_df['Course'] == course
                ]['Instructor'].values[0]
                if course_instructor != self.instructor:
                    return False

            # Check course type constraint
            if self.course_type:
                if scheduler.course_types[course] != self.course_type:
                    return False

            return True

        filtered = filter_keys(scheduler.keys, predicate=matches_criteria)
        return lpSum(scheduler.x[k] for k in filtered)


class MinimizePreferredRooms(ObjectiveBase):
    """
    Minimize use of specific rooms.

    Useful for avoiding overflow rooms or locations that should be last-resort.
    """

    def __init__(
        self,
        preferred_rooms: List[str],
        instructor: Optional[str] = None,
        course_type: Optional[str] = None,
        tolerance: float = 0.0
    ):
        """
        Args:
            preferred_rooms: List of room names to avoid
            instructor: If specified, only for this instructor's classes
            course_type: If specified, only for this type ('Lecture' or 'Lab')
            tolerance: Fractional tolerance for lexicographic constraint
        """
        self.preferred_rooms = set(preferred_rooms)
        self.instructor = instructor
        self.course_type = course_type

        name_parts = [f"preferred rooms ({', '.join(preferred_rooms)})"]
        if instructor:
            name_parts.append(f"for {instructor}")
        if course_type:
            name_parts.append(f"({course_type})")

        super().__init__(
            name=f"Minimize {' '.join(name_parts)}",
            sense='minimize',
            tolerance=tolerance
        )

    def evaluate(self, scheduler):
        def matches_criteria(course, room, time_slot):
            if room not in self.preferred_rooms:
                return False

            if self.instructor:
                course_instructor = scheduler.courses_df[
                    scheduler.courses_df['Course'] == course
                ]['Instructor'].values[0]
                if course_instructor != self.instructor:
                    return False

            if self.course_type:
                if scheduler.course_types[course] != self.course_type:
                    return False

            return True

        filtered = filter_keys(scheduler.keys, predicate=matches_criteria)
        return lpSum(scheduler.x[k] for k in filtered)


class MaximizeLabRootDayPairs(ObjectiveBase):
    """
    Maximize pairing of lab sections sharing a root course number on specific days.
    """

    def __init__(
        self,
        course_types: List[str],
        preferred_days: List[str],
        roots: Optional[List[str]] = None,
        tolerance: float = 0.0
    ):
        """
        Args:
            course_types: Lab course types to include (e.g., ['Lab110x1', 'Lab110x2'])
            preferred_days: Day patterns to pair on (e.g., ['MW', 'TTH'])
            roots: Optional list of root course numbers to include (e.g., ['ASEN 3501'])
            tolerance: Fractional tolerance for lexicographic constraint
        """
        self.course_types = set(course_types)
        self.preferred_days = set(preferred_days)
        self.roots = set(roots) if roots else None

        name = f"Pair lab roots on days ({', '.join(preferred_days)})"
        if roots:
            name = f"{name} for ({', '.join(roots)})"
        super().__init__(name=name, sense='maximize', tolerance=tolerance)

    def _root_key(self, course: str) -> str:
        parts = course.split('-')
        if len(parts) <= 1:
            return course
        return '-'.join(parts[:-1])

    def evaluate(self, scheduler):
        cache_key = ("lab_root_day_pairs", tuple(sorted(self.course_types)), tuple(sorted(self.preferred_days)))
        if not hasattr(scheduler, "_objective_cache"):
            scheduler._objective_cache = {}
        if cache_key in scheduler._objective_cache:
            return scheduler._objective_cache[cache_key]

        # Group lab courses by root.
        root_to_courses = {}
        for course in scheduler.courses:
            if scheduler.course_types.get(course) not in self.course_types:
                continue
            root = self._root_key(course)
            if self.roots is not None and root not in self.roots:
                continue
            root_to_courses.setdefault(root, []).append(course)

        # Build pairing variables and constraints.
        pair_vars = []
        for root, courses in root_to_courses.items():
            if len(courses) < 2:
                continue
            for day in self.preferred_days:
                safe_root = root.replace(" ", "_")
                y = LpVariable(f"pair_{safe_root}_{day}", lowBound=0, upBound=1, cat='Binary')
                pair_vars.append(y)

                # Count how many courses of this root are scheduled on this day pattern.
                count_on_day = lpSum(
                    scheduler.x[k]
                    for k in scheduler.keys
                    if k[0] in courses and scheduler.slot_days[k[2]] == set(expand_days_any(day))
                )
                # y can be 1 only if at least two courses are on this day.
                scheduler.prob += (2 * y <= count_on_day, f"pair_root_{root}_{day}")

        expr = lpSum(pair_vars)
        scheduler._objective_cache[cache_key] = expr
        return expr
