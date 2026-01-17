#!/usr/bin/env python3
"""
Tests for the ignore_column functionality in load_courses.
"""

import sys
import os
import tempfile

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from satisfaculty import InstructorScheduler, AssignAllCourses, NoRoomOverlap


def test_ignore_column_filters_courses():
    """Test that courses with truthy Ignore values are excluded."""
    with tempfile.TemporaryDirectory() as tmpdir:
        rooms_file = os.path.join(tmpdir, 'rooms.csv')
        with open(rooms_file, 'w') as f:
            f.write('Room,Capacity,Room Type\n')
            f.write('Room1,100,Lecture\n')

        courses_file = os.path.join(tmpdir, 'courses.csv')
        with open(courses_file, 'w') as f:
            f.write('Course,Instructor,Enrollment,Slot Type,Room Type,Ignore\n')
            f.write('Course1,Smith,50,Lecture,Lecture,\n')
            f.write('Course2,Smith,50,Lecture,Lecture,TRUE\n')
            f.write('Course3,Jones,50,Lecture,Lecture,false\n')

        scheduler = InstructorScheduler()
        scheduler.load_rooms(rooms_file)
        df = scheduler.load_courses(courses_file, ignore_column='Ignore')

        # Should have 2 courses (Course1 and Course3), Course2 ignored
        assert len(df) == 2, f'Expected 2 courses, got {len(df)}'
        assert 'Course1' in df['Course'].values
        assert 'Course2' not in df['Course'].values
        assert 'Course3' in df['Course'].values

        print('✓ test_ignore_column_filters_courses passed')


def test_ignore_column_accepts_various_truthy_values():
    """Test that TRUE, 1, yes (case-insensitive) are all recognized."""
    with tempfile.TemporaryDirectory() as tmpdir:
        rooms_file = os.path.join(tmpdir, 'rooms.csv')
        with open(rooms_file, 'w') as f:
            f.write('Room,Capacity,Room Type\n')
            f.write('Room1,100,Lecture\n')

        courses_file = os.path.join(tmpdir, 'courses.csv')
        with open(courses_file, 'w') as f:
            f.write('Course,Instructor,Enrollment,Slot Type,Room Type,Ignore\n')
            f.write('Course1,Smith,50,Lecture,Lecture,TRUE\n')
            f.write('Course2,Smith,50,Lecture,Lecture,true\n')
            f.write('Course3,Smith,50,Lecture,Lecture,1\n')
            f.write('Course4,Smith,50,Lecture,Lecture,yes\n')
            f.write('Course5,Smith,50,Lecture,Lecture,YES\n')
            f.write('Course6,Smith,50,Lecture,Lecture,\n')  # Keep this one

        scheduler = InstructorScheduler()
        scheduler.load_rooms(rooms_file)
        df = scheduler.load_courses(courses_file, ignore_column='Ignore')

        # Should only have Course6
        assert len(df) == 1, f'Expected 1 course, got {len(df)}'
        assert 'Course6' in df['Course'].values

        print('✓ test_ignore_column_accepts_various_truthy_values passed')


def test_default_ignore_column_used_when_exists():
    """Test that the default 'Ignore' column is used automatically."""
    with tempfile.TemporaryDirectory() as tmpdir:
        rooms_file = os.path.join(tmpdir, 'rooms.csv')
        with open(rooms_file, 'w') as f:
            f.write('Room,Capacity,Room Type\n')
            f.write('Room1,100,Lecture\n')

        courses_file = os.path.join(tmpdir, 'courses.csv')
        with open(courses_file, 'w') as f:
            f.write('Course,Instructor,Enrollment,Slot Type,Room Type,Ignore\n')
            f.write('Course1,Smith,50,Lecture,Lecture,TRUE\n')
            f.write('Course2,Smith,50,Lecture,Lecture,\n')

        scheduler = InstructorScheduler()
        scheduler.load_rooms(rooms_file)
        df = scheduler.load_courses(courses_file)  # Uses default ignore_column='Ignore'

        # Should have 1 course (Course1 ignored by default)
        assert len(df) == 1, f'Expected 1 course, got {len(df)}'
        assert 'Course2' in df['Course'].values

        print('✓ test_default_ignore_column_used_when_exists passed')


def test_ignore_column_disabled_with_none():
    """Test that ignore_column=None disables filtering."""
    with tempfile.TemporaryDirectory() as tmpdir:
        rooms_file = os.path.join(tmpdir, 'rooms.csv')
        with open(rooms_file, 'w') as f:
            f.write('Room,Capacity,Room Type\n')
            f.write('Room1,100,Lecture\n')

        courses_file = os.path.join(tmpdir, 'courses.csv')
        with open(courses_file, 'w') as f:
            f.write('Course,Instructor,Enrollment,Slot Type,Room Type,Ignore\n')
            f.write('Course1,Smith,50,Lecture,Lecture,TRUE\n')
            f.write('Course2,Smith,50,Lecture,Lecture,\n')

        scheduler = InstructorScheduler()
        scheduler.load_rooms(rooms_file)
        df = scheduler.load_courses(courses_file, ignore_column=None)

        # Should have both courses (filtering disabled)
        assert len(df) == 2, f'Expected 2 courses, got {len(df)}'

        print('✓ test_ignore_column_disabled_with_none passed')


def test_ignore_column_missing_is_silently_ignored():
    """Test that a non-existent ignore column is silently ignored."""
    with tempfile.TemporaryDirectory() as tmpdir:
        rooms_file = os.path.join(tmpdir, 'rooms.csv')
        with open(rooms_file, 'w') as f:
            f.write('Room,Capacity,Room Type\n')
            f.write('Room1,100,Lecture\n')

        courses_file = os.path.join(tmpdir, 'courses.csv')
        with open(courses_file, 'w') as f:
            f.write('Course,Instructor,Enrollment,Slot Type,Room Type\n')
            f.write('Course1,Smith,50,Lecture,Lecture\n')

        scheduler = InstructorScheduler()
        scheduler.load_rooms(rooms_file)
        result = scheduler.load_courses(courses_file, ignore_column='NonExistent')

        # Should load all courses (column silently ignored)
        assert result is not None, 'Expected courses to load'
        assert len(result) == 1, f'Expected 1 course, got {len(result)}'

        print('✓ test_ignore_column_missing_is_silently_ignored passed')


def test_ignore_makes_infeasible_problem_feasible():
    """Test that ignoring a course can make an infeasible problem feasible.

    Without ignore: 2 courses, 1 room, 1 slot = infeasible
    With ignore: 1 course, 1 room, 1 slot = feasible
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        rooms_file = os.path.join(tmpdir, 'rooms.csv')
        with open(rooms_file, 'w') as f:
            f.write('Room,Capacity,Room Type\n')
            f.write('Room1,100,Lecture\n')

        courses_file = os.path.join(tmpdir, 'courses.csv')
        with open(courses_file, 'w') as f:
            f.write('Course,Instructor,Enrollment,Slot Type,Room Type,Ignore\n')
            f.write('Course1,Smith,50,Lecture,Lecture,\n')
            f.write('Course2,Smith,50,Lecture,Lecture,TRUE\n')  # Ignore this one

        time_slots_file = os.path.join(tmpdir, 'time_slots.csv')
        with open(time_slots_file, 'w') as f:
            f.write('Slot,Days,Start,End,Slot Type\n')
            f.write('MWF-0830,MWF,08:30,09:20,Lecture\n')

        scheduler = InstructorScheduler()
        scheduler.load_rooms(rooms_file)
        scheduler.load_courses(courses_file, ignore_column='Ignore')
        scheduler.load_time_slots(time_slots_file)
        scheduler.add_constraints([
            AssignAllCourses(),
            NoRoomOverlap(),
        ])

        result = scheduler.optimize_schedule()

        # Should find a solution (only 1 course to schedule)
        assert result is not None, 'Expected solution when course is ignored'
        assert len(result) == 1, f'Expected 1 scheduled course, got {len(result)}'
        assert result.iloc[0]['Course'] == 'Course1'

        print('✓ test_ignore_makes_infeasible_problem_feasible passed')


def run_all_tests():
    """Run all tests."""
    print('Running ignore_column tests...\n')

    test_ignore_column_filters_courses()
    test_ignore_column_accepts_various_truthy_values()
    test_default_ignore_column_used_when_exists()
    test_ignore_column_disabled_with_none()
    test_ignore_column_missing_is_silently_ignored()
    test_ignore_makes_infeasible_problem_feasible()

    print('\n' + '='*50)
    print('All ignore_column tests passed!')
    print('='*50)


if __name__ == '__main__':
    run_all_tests()
