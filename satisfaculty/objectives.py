#!/usr/bin/env python3
"""
Example objective classes for schedule optimization.

These demonstrate common scheduling objectives that can be combined
in different orders to create customized optimization strategies.
"""

from .objective_base import ObjectiveBase
from pulp import lpSum, LpAffineExpression, LpVariable
from .scheduler import filter_keys
from .utils import time_to_minutes
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
                if self.instructor not in scheduler.course_instructors[course]:
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
            # Check time constraint (use end time to catch classes running past the threshold)
            slot_end = scheduler.slot_end_minutes[time_slot]
            if slot_end <= self.time_minutes:
                return False

            # Check instructor constraint
            if self.instructor:
                if self.instructor not in scheduler.course_instructors[course]:
                    return False

            # Check course type constraint
            if self.course_type:
                if scheduler.course_slot_type[course] != self.course_type:
                    return False

            return True

        filtered = filter_keys(scheduler.keys, predicate=matches_criteria)
        return lpSum(scheduler.x[k] for k in filtered)


class MinimizeMinutesAfter(ObjectiveBase):
    """
    Minimize total minutes of class time scheduled after a given time.

    Unlike MinimizeClassesAfter which counts the number of classes,
    this counts the actual minutes past the threshold. Useful for
    soft preferences where some overage is acceptable but should be minimized.
    """

    def __init__(self, time: str, tolerance: float = 0.0):
        """
        Args:
            time: Time in HH:MM format (e.g., "16:00")
            tolerance: Fractional tolerance for lexicographic constraint
        """
        self.time_minutes = time_to_minutes(time)

        super().__init__(
            name=f"Minimize minutes after {time}",
            sense='minimize',
            tolerance=tolerance
        )

    def evaluate(self, scheduler):
        terms = []
        for course, room, time_slot in scheduler.keys:
            slot_end = scheduler.slot_end_minutes[time_slot]
            if slot_end > self.time_minutes:
                minutes_after = slot_end - self.time_minutes
                num_days = len(scheduler.slot_days[time_slot])
                terms.append(minutes_after * num_days * scheduler.x[(course, room, time_slot)])

        if not terms:
            return LpAffineExpression()
        return lpSum(terms)


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
                if self.instructor not in scheduler.course_instructors[course]:
                    return False

            # Check course type constraint
            if self.course_type:
                if scheduler.course_slot_type[course] != self.course_type:
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
                if self.instructor not in scheduler.course_instructors[course]:
                    return False

            if self.course_type:
                if scheduler.course_slot_type[course] != self.course_type:
                    return False

            return True

        filtered = filter_keys(scheduler.keys, predicate=matches_criteria)
        return lpSum(scheduler.x[k] for k in filtered)


class MinimizeExcessRoomCapacity(ObjectiveBase):
    """
    Minimize assigning courses to rooms larger than necessary.

    Penalizes assignments where a course is placed in a room with capacity
    larger than the smallest available room that can accommodate its enrollment.
    Optionally limit the penalty to "small" courses by enrollment threshold.
    """

    def __init__(
        self,
        max_enrollment: Optional[int] = None,
        tolerance: float = 0.0
    ):
        """
        Args:
            max_enrollment: If set, only penalize courses with enrollment <= this value
            tolerance: Fractional tolerance for lexicographic constraint
        """
        self.max_enrollment = max_enrollment

        name_parts = ["excess room capacity"]
        if max_enrollment is not None:
            name_parts.append(f"(enrollment <= {max_enrollment})")

        super().__init__(
            name=f"Minimize {' '.join(name_parts)}",
            sense='minimize',
            tolerance=tolerance
        )

    def evaluate(self, scheduler):
        # Precompute smallest feasible room capacity for each course
        best_fit_capacity = {}
        for course in scheduler.courses:
            enrollment = scheduler.enrollments[course]
            if self.max_enrollment is not None and enrollment > self.max_enrollment:
                continue

            course_room_type = scheduler.course_room_type[course]
            eligible_capacities = [
                capacity
                for room, capacity in scheduler.capacities.items()
                if course_room_type in scheduler.room_types[room]
                and capacity >= enrollment
            ]
            if eligible_capacities:
                best_fit_capacity[course] = min(eligible_capacities)

        terms = []
        for course, room, time_slot in scheduler.keys:
            if course not in best_fit_capacity:
                continue
            overage = scheduler.capacities[room] - best_fit_capacity[course]
            if overage > 0:
                terms.append(overage * scheduler.x[(course, room, time_slot)])

        if not terms:
            return LpAffineExpression()
        return lpSum(terms)


class MinimizeRoomOrderByCourseRank(ObjectiveBase):
    """
    Minimize room-name order weighted by per-course rank.

    Uses a numeric Rank column from courses.csv (higher rank = stronger preference).
    Rooms are ordered lexicographically by name, and assignments to "later" rooms
    are penalized in proportion to course rank.
    """

    def __init__(
        self,
        rank_column: str = "Rank",
        tolerance: float = 0.0
    ):
        """
        Args:
            rank_column: Column in courses.csv containing numeric ranks
            tolerance: Fractional tolerance for lexicographic constraint
        """
        self.rank_column = rank_column

        super().__init__(
            name=f"Minimize room order by course rank ({rank_column})",
            sense='minimize',
            tolerance=tolerance
        )

    def evaluate(self, scheduler):
        if self.rank_column not in scheduler.courses_df.columns:
            return LpAffineExpression()

        ranks = dict(zip(scheduler.courses_df['Course'], scheduler.courses_df[self.rank_column]))
        room_order = {room: idx for idx, room in enumerate(sorted(scheduler.rooms))}

        def to_weight(value):
            if value is None:
                return 0.0
            try:
                weight = float(value)
            except (TypeError, ValueError):
                return 0.0
            if weight != weight:  # NaN check
                return 0.0
            return weight

        terms = []
        for course, room, time_slot in scheduler.keys:
            weight = to_weight(ranks.get(course))
            if weight > 0:
                terms.append(weight * room_order[room] * scheduler.x[(course, room, time_slot)])

        if not terms:
            return LpAffineExpression()
        return lpSum(terms)


class MaximizeBackToBackCourses(ObjectiveBase):
    """
    Maximize back-to-back placement for a specified set of courses.

    This objective rewards adjacent time slots (by start time) that are
    assigned to different courses in the specified list. Adjacency is
    evaluated within the same slot type (and optionally the same days set).
    """

    _instance_count = 0

    def __init__(
        self,
        courses: List[str],
        same_days: bool = True,
        same_room: bool = False,
        tolerance: float = 0.0
    ):
        """
        Args:
            courses: List of course names to cluster back-to-back.
            same_days: If True, only count adjacency within the same days set
                       (e.g., MWF with MWF). If False, only slot type is matched.
            same_room: If True, only count adjacency when both courses are in the same room.
            tolerance: Fractional tolerance for lexicographic constraint.
        """
        self.courses = list(courses)
        self.same_days = same_days
        self.same_room = same_room
        self._built = False
        self._objective_expr = None

        MaximizeBackToBackCourses._instance_count += 1
        self._id = MaximizeBackToBackCourses._instance_count

        super().__init__(
            name=f"Maximize back-to-back for {len(self.courses)} course(s)",
            sense='maximize',
            tolerance=tolerance
        )

    def _build(self, scheduler):
        missing = [c for c in self.courses if c not in scheduler.courses]
        if missing:
            raise ValueError(f"Unknown course(s) in MaximizeBackToBackCourses: {missing}")

        # Group time slots by slot type (+ days if requested)
        groups = {}
        for slot in scheduler.time_slots:
            slot_type = scheduler.slot_type[slot]
            if self.same_days:
                days_key = tuple(sorted(scheduler.slot_days[slot]))
                key = (slot_type, days_key)
            else:
                key = (slot_type,)
            groups.setdefault(key, []).append(slot)

        # Build adjacency list of consecutive (slot1, slot2) pairs
        adjacent_slots = []
        for slots in groups.values():
            slots_sorted = sorted(slots, key=lambda s: scheduler.slot_start_minutes[s])
            for i in range(len(slots_sorted) - 1):
                s1 = slots_sorted[i]
                s2 = slots_sorted[i + 1]
                adjacent_slots.append((s1, s2))

        # Precompute course-slot assignment expressions (summing over rooms)
        course_slot_expr = {}
        for course in self.courses:
            for slot in scheduler.time_slots:
                keys = filter_keys(scheduler.keys, course=course, time_slot=slot)
                if keys:
                    course_slot_expr[(course, slot)] = lpSum(scheduler.x[k] for k in keys)

        # Precompute course-slot-room expressions when same_room is required
        course_slot_room_expr = {}
        if self.same_room:
            for course in self.courses:
                for slot in scheduler.time_slots:
                    for room in scheduler.rooms:
                        keys = filter_keys(scheduler.keys, course=course, room=room, time_slot=slot)
                        if keys:
                            course_slot_room_expr[(course, slot, room)] = lpSum(scheduler.x[k] for k in keys)

        adjacency_vars = []
        var_count = 0
        for i, course_a in enumerate(self.courses):
            for course_b in self.courses[i + 1:]:
                for s1, s2 in adjacent_slots:
                    if self.same_room:
                        for room in scheduler.rooms:
                            # course_a in s1 AND course_b in s2 (same room)
                            if (course_a, s1, room) in course_slot_room_expr and (course_b, s2, room) in course_slot_room_expr:
                                y = LpVariable(f"bb_{self._id}_{var_count}", cat='Binary')
                                scheduler.prob += (y <= course_slot_room_expr[(course_a, s1, room)], f"bb_{self._id}_{var_count}_ub1")
                                scheduler.prob += (y <= course_slot_room_expr[(course_b, s2, room)], f"bb_{self._id}_{var_count}_ub2")
                                scheduler.prob += (
                                    y >= course_slot_room_expr[(course_a, s1, room)] + course_slot_room_expr[(course_b, s2, room)] - 1,
                                    f"bb_{self._id}_{var_count}_lb"
                                )
                                adjacency_vars.append(y)
                                var_count += 1

                            # course_a in s2 AND course_b in s1 (same room, reverse)
                            if (course_a, s2, room) in course_slot_room_expr and (course_b, s1, room) in course_slot_room_expr:
                                y = LpVariable(f"bb_{self._id}_{var_count}", cat='Binary')
                                scheduler.prob += (y <= course_slot_room_expr[(course_a, s2, room)], f"bb_{self._id}_{var_count}_ub1")
                                scheduler.prob += (y <= course_slot_room_expr[(course_b, s1, room)], f"bb_{self._id}_{var_count}_ub2")
                                scheduler.prob += (
                                    y >= course_slot_room_expr[(course_a, s2, room)] + course_slot_room_expr[(course_b, s1, room)] - 1,
                                    f"bb_{self._id}_{var_count}_lb"
                                )
                                adjacency_vars.append(y)
                                var_count += 1
                    else:
                        # course_a in s1 AND course_b in s2
                        if (course_a, s1) in course_slot_expr and (course_b, s2) in course_slot_expr:
                            y = LpVariable(f"bb_{self._id}_{var_count}", cat='Binary')
                            scheduler.prob += (y <= course_slot_expr[(course_a, s1)], f"bb_{self._id}_{var_count}_ub1")
                            scheduler.prob += (y <= course_slot_expr[(course_b, s2)], f"bb_{self._id}_{var_count}_ub2")
                            scheduler.prob += (
                                y >= course_slot_expr[(course_a, s1)] + course_slot_expr[(course_b, s2)] - 1,
                                f"bb_{self._id}_{var_count}_lb"
                            )
                            adjacency_vars.append(y)
                            var_count += 1

                        # course_a in s2 AND course_b in s1 (reverse order)
                        if (course_a, s2) in course_slot_expr and (course_b, s1) in course_slot_expr:
                            y = LpVariable(f"bb_{self._id}_{var_count}", cat='Binary')
                            scheduler.prob += (y <= course_slot_expr[(course_a, s2)], f"bb_{self._id}_{var_count}_ub1")
                            scheduler.prob += (y <= course_slot_expr[(course_b, s1)], f"bb_{self._id}_{var_count}_ub2")
                            scheduler.prob += (
                                y >= course_slot_expr[(course_a, s2)] + course_slot_expr[(course_b, s1)] - 1,
                                f"bb_{self._id}_{var_count}_lb"
                            )
                            adjacency_vars.append(y)
                            var_count += 1

        if adjacency_vars:
            self._objective_expr = lpSum(adjacency_vars)
        else:
            self._objective_expr = LpAffineExpression()
        self._built = True

    def evaluate(self, scheduler):
        if not self._built:
            self._build(scheduler)
        return self._objective_expr
