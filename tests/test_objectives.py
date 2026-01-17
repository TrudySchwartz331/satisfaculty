#!/usr/bin/env python3
"""
Tests for objective classes.
"""

import sys
import os
import tempfile

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from satisfaculty import (
    InstructorScheduler,
    AssignAllCourses,
    NoRoomOverlap,
    MinimizeMinutesAfter,
)


def create_test_files(tmpdir, rooms_data, courses_data, slots_data):
    """Helper to create test CSV files."""
    rooms_file = os.path.join(tmpdir, 'rooms.csv')
    with open(rooms_file, 'w') as f:
        f.write(rooms_data)

    courses_file = os.path.join(tmpdir, 'courses.csv')
    with open(courses_file, 'w') as f:
        f.write(courses_data)

    slots_file = os.path.join(tmpdir, 'time_slots.csv')
    with open(slots_file, 'w') as f:
        f.write(slots_data)

    return rooms_file, courses_file, slots_file


def test_minimize_minutes_after_prefers_earlier_slot():
    """Test that MinimizeMinutesAfter prefers earlier time slots."""
    with tempfile.TemporaryDirectory() as tmpdir:
        rooms_file, courses_file, slots_file = create_test_files(
            tmpdir,
            rooms_data='Room,Capacity,Room Type\nRoom1,100,Lecture\n',
            courses_data='Course,Instructor,Enrollment,Slot Type,Room Type\nC1,Smith,50,Lecture,Lecture\n',
            # One slot ends at 15:00, another at 17:00
            slots_data='Slot,Days,Start,End,Slot Type\n'
                      'MWF-1400,MWF,14:00,15:00,Lecture\n'
                      'MWF-1600,MWF,16:00,17:00,Lecture\n',
        )

        scheduler = InstructorScheduler()
        scheduler.load_rooms(rooms_file)
        scheduler.load_courses(courses_file)
        scheduler.load_time_slots(slots_file)
        scheduler.add_constraints([AssignAllCourses(), NoRoomOverlap()])

        # Minimize minutes after 16:00
        result = scheduler.lexicographic_optimize([MinimizeMinutesAfter('16:00')])

        assert result is not None
        assert len(result) == 1
        # Should pick the 14:00 slot since it ends at 15:00 (before 16:00)
        assert result.iloc[0]['Start'] == '14:00'


def test_minimize_minutes_after_accounts_for_days():
    """Test that MinimizeMinutesAfter multiplies by number of days."""
    with tempfile.TemporaryDirectory() as tmpdir:
        rooms_file, courses_file, slots_file = create_test_files(
            tmpdir,
            rooms_data='Room,Capacity,Room Type\nRoom1,100,Lecture\n',
            courses_data='Course,Instructor,Enrollment,Slot Type,Room Type\nC1,Smith,50,Lecture,Lecture\n',
            # MWF slot ends 30 min after threshold = 30 * 3 = 90 minutes
            # TTH slot ends 40 min after threshold = 40 * 2 = 80 minutes
            slots_data='Slot,Days,Start,End,Slot Type\n'
                      'MWF-1600,MWF,16:00,16:30,Lecture\n'
                      'TTH-1600,TTH,16:00,16:40,Lecture\n',
        )

        scheduler = InstructorScheduler()
        scheduler.load_rooms(rooms_file)
        scheduler.load_courses(courses_file)
        scheduler.load_time_slots(slots_file)
        scheduler.add_constraints([AssignAllCourses(), NoRoomOverlap()])

        # Minimize minutes after 16:00
        result = scheduler.lexicographic_optimize([MinimizeMinutesAfter('16:00')])

        assert result is not None
        assert len(result) == 1
        # Should pick TTH (80 total minutes) over MWF (90 total minutes)
        assert result.iloc[0]['Days'] == 'TTH'


def test_minimize_minutes_after_zero_when_before_threshold():
    """Test that slots ending before threshold contribute zero."""
    with tempfile.TemporaryDirectory() as tmpdir:
        rooms_file, courses_file, slots_file = create_test_files(
            tmpdir,
            rooms_data='Room,Capacity,Room Type\nRoom1,100,Lecture\n',
            courses_data='Course,Instructor,Enrollment,Slot Type,Room Type\nC1,Smith,50,Lecture,Lecture\n',
            # Both slots end before 17:00
            slots_data='Slot,Days,Start,End,Slot Type\n'
                      'MWF-0800,MWF,08:00,09:00,Lecture\n'
                      'MWF-1400,MWF,14:00,15:00,Lecture\n',
        )

        scheduler = InstructorScheduler()
        scheduler.load_rooms(rooms_file)
        scheduler.load_courses(courses_file)
        scheduler.load_time_slots(slots_file)
        scheduler.add_constraints([AssignAllCourses(), NoRoomOverlap()])

        # Minimize minutes after 17:00 - both slots should have 0 contribution
        result = scheduler.lexicographic_optimize([MinimizeMinutesAfter('17:00')])

        assert result is not None
        # Either slot is valid since both contribute 0 minutes after 17:00


def run_all_tests():
    """Run all tests."""
    print('Running objectives tests...\n')

    test_minimize_minutes_after_prefers_earlier_slot()
    print('✓ test_minimize_minutes_after_prefers_earlier_slot passed')

    test_minimize_minutes_after_accounts_for_days()
    print('✓ test_minimize_minutes_after_accounts_for_days passed')

    test_minimize_minutes_after_zero_when_before_threshold()
    print('✓ test_minimize_minutes_after_zero_when_before_threshold passed')

    print('\n' + '='*50)
    print('All objectives tests passed!')
    print('='*50)


if __name__ == '__main__':
    run_all_tests()
