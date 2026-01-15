#!/usr/bin/env python3
"""
Tests for infeasibility detection and constraint violation reporting.
"""

import sys
import os
import io
from contextlib import redirect_stdout

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from satisfaculty import InstructorScheduler, AssignAllCourses, NoRoomOverlap


def test_infeasible_two_courses_one_slot():
    """Test that violated constraints are printed when problem is infeasible.

    Creates a scenario with 2 courses, 1 room, and 1 time slot - impossible to satisfy.
    """
    # Create temporary CSV files for the test
    import tempfile

    with tempfile.TemporaryDirectory() as tmpdir:
        # 1 room
        rooms_file = os.path.join(tmpdir, 'rooms.csv')
        with open(rooms_file, 'w') as f:
            f.write('Room,Capacity\n')
            f.write('Room1,100\n')

        # 2 courses (same instructor to keep it simple)
        courses_file = os.path.join(tmpdir, 'courses.csv')
        with open(courses_file, 'w') as f:
            f.write('Course,Instructor,Enrollment,Type\n')
            f.write('Course1,Smith,50,Lecture\n')
            f.write('Course2,Smith,50,Lecture\n')

        # 1 time slot
        time_slots_file = os.path.join(tmpdir, 'time_slots.csv')
        with open(time_slots_file, 'w') as f:
            f.write('Slot,Days,Start,End,Type\n')
            f.write('MWF-0830,MWF,08:30,09:20,Lecture\n')

        scheduler = InstructorScheduler()
        scheduler.load_rooms(rooms_file)
        scheduler.load_courses(courses_file)
        scheduler.load_time_slots(time_slots_file)
        scheduler.add_constraints([
            AssignAllCourses(),
            NoRoomOverlap(),
        ])

        # Capture stdout
        output = io.StringIO()
        with redirect_stdout(output):
            result = scheduler.optimize_schedule()

        stdout_text = output.getvalue()

        # Should return None (no solution)
        assert result is None, 'Expected no solution for infeasible problem'

        # Should print violated constraints
        assert 'Violated constraints:' in stdout_text, f'Expected violation output, got: {stdout_text}'

        # The room overlap or assign constraint should be violated
        assert 'no_room_overlap_' in stdout_text or 'assign_course_' in stdout_text, \
            f'Expected constraint violation, got: {stdout_text}'

        print('✓ test_infeasible_two_courses_one_slot passed')


def run_all_tests():
    """Run all tests."""
    print('Running infeasibility tests...\n')

    test_infeasible_two_courses_one_slot()

    print('\n' + '='*50)
    print('All infeasibility tests passed!')
    print('='*50)


if __name__ == '__main__':
    run_all_tests()
