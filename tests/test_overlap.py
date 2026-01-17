#!/usr/bin/env python3
"""
Tests for time overlap logic.
"""

import os

from satisfaculty import scheduler
from satisfaculty.constraints import AssignAllCourses, NoRoomOverlap

def test_time_overlap():
    # Create temporary CSV files for the test
    import tempfile

    sched = scheduler.InstructorScheduler()

    with tempfile.TemporaryDirectory() as tmpdir:
        # Test time slots

        time_slots_file = os.path.join(tmpdir, 'time_slots.csv')
        with open(time_slots_file, 'w') as f:
            f.write('Slot,Days,Start,End,Slot Type\n')
            f.write('T-0830,T,08:30,10:20,Lab\n')
            f.write('TH-0830,TH,08:30,10:20,Lab\n')
            f.write('TTH-0830,TTH,08:30,9:45,Lecture\n')

        # 2 Courses with same instructor
        courses_file = os.path.join(tmpdir, 'courses.csv')
        with open(courses_file, 'w') as f:
            f.write('Course,Instructor,Enrollment,Slot Type,Room Type\n')
            f.write('Lab1,Smith,30,Lab,Lab\n')
            f.write('Lab2,Smith,30,Lab,Lab\n')
            f.write('Course1,Johnson,80,Lecture,Lecture\n')

        # Just 1 room
        rooms_file = os.path.join(tmpdir, 'rooms.csv')
        with open(rooms_file, 'w') as f:
            f.write('Room,Capacity,Room Type\n')
            f.write('Room1,50,Lab\n')
            f.write('Room2,100,Lecture\n')

        sched.load_time_slots(time_slots_file)
        sched.load_courses(courses_file)
        sched.load_rooms(rooms_file)

    sched.add_constraints([
        AssignAllCourses(),
        NoRoomOverlap()
    ])
    sched.setup_problem()

    pred_T_0830 = sched.make_overlap_predicate('T-0830')

    assert pred_T_0830('Lab1', 'Room1', 'T-0830') is True, "Expected overlap for same slot"
    assert pred_T_0830('Lab1', 'Room1', 'TH-0830') is False, "Expected no overlap between T and TH slots"
    assert pred_T_0830('Lab1', 'Room2', 'TTH-0830') is True, "Expected overlap between T and TTH slots"

    pred_TH_0830 = sched.make_overlap_predicate('TH-0830')
    assert pred_TH_0830('Lab1', 'Room1', 'T-0830') is False, "Expected no overlap between TH and T slots"
    assert pred_TH_0830('Lab1', 'Room1', 'TH-0830') is True, "Expected overlap for same slot"
    assert pred_TH_0830('Lab1', 'Room2', 'TTH-0830') is True, "Expected overlap between TH and TTH slots"

    # for name, constraint in sched.prob.constraints.items():
    #     print(f'Constraint: {name} -> {constraint}')

    result = sched.lexicographic_optimize([])
    assert result is not None, "Expected a valid solution"
    # sched.visualize_schedule('test_time_overlap_schedule.png')

def run_all_tests():
    test_time_overlap()

    print('\n' + '='*50)
    print('All overlap tests passed!')
    print('='*50)

if __name__ == '__main__':
    run_all_tests()
