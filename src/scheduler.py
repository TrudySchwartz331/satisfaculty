#!/usr/bin/env python3
"""
Instructor Scheduling System with Integer Linear Programming
Optimizes assignment of instructors to rooms considering capacity constraints.
"""

import pandas as pd
import numpy as np
from pulp import *
import csv
from typing import Dict, List, Tuple


class InstructorScheduler:
    def __init__(self, time_slots = range(2)):
        self.time_slots = time_slots
        
    def load_rooms(self, filename: str = 'data/rooms.csv'):
        """Load room data from CSV file."""
        try:
            self.rooms_df = pd.read_csv(filename)

            # Check for duplicate rooms
            rooms = self.rooms_df['Room']
            if len(rooms) != len(rooms.unique()):
                duplicates = rooms[rooms.duplicated()].unique()
                raise ValueError(f"Duplicate rooms found: {list(duplicates)}")

            print(f"Loaded {len(self.rooms_df)} rooms from {filename}")
            return self.rooms_df
        except FileNotFoundError:
            print(f"Error: {filename} not found")
            return None
        except Exception as e:
            print(f"Error loading rooms: {e}")
            return None
    
    def load_courses(self, filename: str = 'data/courses.csv'):
        """Load course data from CSV file."""
        try:
            self.courses_df = pd.read_csv(filename)
            
            # Check for duplicate courses
            courses = self.courses_df['Course']
            if len(courses) != len(courses.unique()):
                duplicates = courses[courses.duplicated()].unique()
                raise ValueError(f"Duplicate courses found: {list(duplicates)}")
            
            print(f"Loaded {len(self.courses_df)} courses from {filename}")
            return self.courses_df
        except FileNotFoundError:
            print(f"Error: {filename} not found")
            return None
        except Exception as e:
            print(f"Error loading courses: {e}")
            return None
    
    def optimize_schedule(self):
        """Solve the instructor scheduling problem using integer linear programming."""
        if self.rooms_df is None or self.courses_df is None:
            print("Error: Room and course data must be loaded first")
            return None
        
        # Create the constraint satisfaction problem
        prob = LpProblem("Instructor_Scheduling", LpMinimize)
        
        # Extract input parameters
        courses = list(self.courses_df['Course'])
        rooms = list(self.rooms_df['Room'])
        time_slots = list(self.time_slots)
        instructors = list(self.courses_df['Instructor'].unique())

        # Create dictionaries for enrollments and capacities
        enrollments = dict(zip(self.courses_df['Course'], self.courses_df['Enrollment']))
        capacities = dict(zip(self.rooms_df['Room'], self.rooms_df['Capacity']))

        # Create matrix a; a[(instructor, course)] = 1 if instructor teaches course
        a = {}
        for instructor in instructors:
            for course in courses:
                if instructor in self.courses_df[self.courses_df['Course'] == course]['Instructor'].values:
                    a[(instructor, course)] = 1
                else:
                    a[(instructor, course)] = 0

        # Create binary decision variables using LpVariable.dicts
        # x[(course, room, time)] = 1 if course is assigned to room at time slot
        indices = [(course, room, t) for course in courses for room in rooms for t in time_slots]
        x = LpVariable.dicts("x", indices, cat='Binary')

        # Course must be taught once
        for course in courses:
            prob += lpSum(x[(course, room, t)] for room in rooms for t in time_slots) == 1

        # Instructor can only be teaching one course at a time
        for instructor in instructors:
            for t in time_slots:
                prob += lpSum(x[(course, room, t)] * a[(instructor, course)] for course in courses for room in rooms) <= 1

        # Room can only have one course at a time
        for room in rooms:
            for t in time_slots:
                prob += lpSum(x[(course, room, t)] for course in courses) <= 1

        # Room capacity constraints
        for room in rooms:
            for t in time_slots:
                prob += lpSum(x[(course, room, t)] * enrollments[course] for course in courses) <= capacities[room]
        
        # Solve the problem
        prob.solve()

        # Check if the problem is solved
        if LpStatus[prob.status] != 'Optimal':
            print("No solution found")
            self.schedule = None
            return

        # Create the schedule (dataframe with course, room, time slot)
        schedule_data = []
        for course in courses:
            for room in rooms:
                for t in time_slots:
                    if x[(course, room, t)].varValue == 1:
                        schedule_data.append({
                            'Course': course,
                            'Room': room,
                            'Time Slot': t,
                            'Instructor': self.courses_df[self.courses_df['Course'] == course]['Instructor'].values[0]
                        })
        self.schedule = pd.DataFrame(schedule_data)

        return self.schedule
    
    def display_schedule(self):
        """Display the optimized schedule."""
        if self.schedule is not None:
            print("\nOptimized Schedule:")
            print(self.schedule)
        else:
            print("No schedule available. Please run optimize_schedule() first.")

    def save_schedule(self, filename: str = 'output/schedule.csv'):
        """Save the optimized schedule to a CSV file."""
        if self.schedule is not None:
            self.schedule.to_csv(filename, index=False)
            print(f"Schedule saved to {filename}")
        else:
            print("No schedule available to save. Please run optimize_schedule() first.")

def main():
    scheduler = InstructorScheduler(time_slots=range(12))
    
    # Load data
    print("Loading room and course data...")
    rooms = scheduler.load_rooms()
    courses = scheduler.load_courses()
    
    if rooms is not None and courses is not None:
        print("\nRoom data preview:")
        print(rooms.head())
        print("\nCourse data preview:")
        print(courses.head())
        
        # Optimize schedule
        scheduler.optimize_schedule()
        scheduler.display_schedule()
        scheduler.save_schedule()
    else:
        print("Failed to load required data files")


if __name__ == "__main__":
    main()
