# Satisfaculty

A course scheduling optimization tool using integer linear programming.

## Installation

```bash
pip install satisfaculty
```

## Usage

```python
from satisfaculty import InstructorScheduler, MinimizeClassesBefore

scheduler = InstructorScheduler()
scheduler.load_rooms('rooms.csv')
scheduler.load_courses('courses.csv')
scheduler.load_time_slots('time_slots.csv')

objectives = [MinimizeClassesBefore("9:00")]
scheduler.lexicographic_optimize(objectives)
scheduler.visualize_schedule()
```

This will output a complete schedule:

![Example schedule output](docs/schedule_visual.png)

## Example

Example data files are available in the [`example/`](https://github.com/zsunberg/satisfaculty/tree/main/example) directory of the repository.

## Documentation

- [Objectives Guide](docs/OBJECTIVES_GUIDE.md)
