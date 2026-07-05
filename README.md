# Max Performance: A Python-Based Athletic Performance Analysis

A Python program that loads gym workout records, computes fitness metrics for an individual member, and runs cohort-level analytics and visualizations on top of the dataset.

## Team

| Name | Email | Stevens ID |
|---|---|---|
| Saanie Naqvi | snaqvi3@stevens.edu | 20045913 |
| Aaron Nathans | anathans@stevens.edu | 20040170 |
| Azizul Haque | ahaque3@stevens.edu | 20036646 |

**Course:** AAI/CPE/EE 551 WS/WS1
**Submission:** May 6, 2026

## Project Overview

Athletic performance depends on a lot of moving pieces: training intensity, recovery, body composition, and experience all factor in. Most people who track their workouts end up with a spreadsheet they never really analyze. We wanted to build something that takes that kind of data and turns it into actual insights, like which workout types burn the most calories, how often you're training in each heart rate zone, and how you compare to other people at your level.

The program runs on a synthetic dataset of 1,800 gym sessions (15 columns covering things like age, weight, BMI, workout type, calories burned, heart rate, etc.). After cleaning we end up with around 1,629 usable rows. The program then computes per-member metrics (BMI category, max HR, target HR zones using the Karvonen formula), cohort statistics, and saves five matplotlib charts to the `outputs/` folder.

The main program is a Jupyter notebook (`max_performance.ipynb`) that walks through everything step by step. There's also a pytest suite with 70 tests covering the public functions and methods.

## Solution Approach

We split the code into a few focused modules so each one has a clear job:

- `athlete.py` — `GymMember` class. Holds one person's profile and computes their per-member metrics.
- `performance_tracker.py` — `PerformanceTracker` class. Composes a `GymMember` (a tracker has-a member, it isn't a kind of member) and runs cohort analytics on top of the cleaned dataset.
- `analytics.py` — Standalone statistical functions (ACWR, recovery labeling, trend analysis, calorie aggregation, descriptive stats, plus a generator).
- `data_loader.py` — Reads the CSV, cleans it, and provides a factory function for building a `GymMember` from a row.
- `visualizer.py` — Five matplotlib chart functions that save PNGs to `outputs/`.

We went with composition rather than inheritance because a tracker uses a member to scope its analysis; it isn't a specialized type of member.

Quick naming note: the class is called `GymMember` in the code. The proposal used the word "Athlete" but we settled on `GymMember` since it matches the dataset terminology, and we kept it consistent across all the modules and tests.

## Dependencies

- Python 3.12+ (we tested on 3.13)
- pandas
- numpy
- matplotlib
- pytest
- jupyter

### Install

```bash
pip install pandas numpy matplotlib pytest jupyter
```

## File Structure

```
Max_Performance/
├── athlete.py
├── performance_tracker.py
├── analytics.py
├── data_loader.py
├── visualizer.py
├── test_max_performance.py
├── max_performance.ipynb
├── README.md
├── Project_instruction.txt
├── PyCrew - Project Proposal.docx
├── PyCrew_Task_Delegation.docx
├── data/
│   └── gym_members_exercise_tracking_synthetic_data.csv
└── outputs/
    ├── calories_by_workout_type.png
    ├── hr_zone_distribution.png
    ├── bmi_by_experience.png
    ├── calories_vs_duration.png
    └── workout_type_counts.png
```

## How to Run

### Run the notebook (recommended)

From the project root:

```bash
jupyter notebook max_performance.ipynb
```

Then go to Kernel > Restart & Run All. The notebook walks through loading the data, building a member, running the cohort analytics, demoing the generator, rendering all five charts, showing the exception handling, and running the full pytest suite at the end.

### Run the tests directly

```bash
pytest test_max_performance.py -v
```

Should give you 70 passed.

### Run any module standalone

Each `.py` file has an `if __name__ == "__main__":` block:

```bash
python athlete.py
python performance_tracker.py
python analytics.py
python data_loader.py
python visualizer.py
```

## Main Contributions

| Member | Contributions |
|---|---|
| **Saanie Naqvi** (snaqvi3@stevens.edu, 20045913) | `athlete.py` — `GymMember` class with input validation, BMI / max-HR / HR-reserve calculations, Karvonen target HR zone, weekly volume estimate, and operator overloads (`__str__`, `__eq__`, `__repr__`). `performance_tracker.py` — `PerformanceTracker` class composing `GymMember`, with cohort analytics methods and `__len__` / `__str__` / `__getattr__` overloads. `test_max_performance.py` — pytest test suite for `PerformanceTracker`, analytics functions, and data loader. `tests/test_athlete.py` — dedicated pytest suite for the `GymMember` class covering all properties, methods, validation, and operator overloads. `data/gym_members_exercise_tracking_synthetic_data.csv` — sourced and uploaded the dataset from Kaggle. Wrote the main contributions table in `README.md` detailing each team member's files and responsibilities. |
| **Aaron Nathans** (anathans@stevens.edu, 20040170) | `analytics.py` — ACWR, recovery status labeling, exercise distribution, trend analysis with `numpy.polyfit`, reduce + lambda calorie aggregation, `describe_series` using `statistics`, and the `yield_high_calorie_sessions` generator. GitHub repo creation and setup - Created the GitHub repository and shared access with all team members so everyone could collaborate and commit. `outputs/hr_zone_distribution.png`, `outputs/calories_vs_duration.png`, `outputs/workout_type_counts.png` — generated and committed chart outputs. |
| **Azizul Haque** (ahaque3@stevens.edu, 20036646) | `data_loader.py` — CSV ingestion, cleaning, column renaming, and the `GymMember` factory function. `visualizer.py` — five matplotlib chart functions. `README.md` — wrote the full project documentation including project overview, solution approach, dependencies, file structure, setup instructions, and how to run the program (everything except the contributions table). `outputs/calories_by_workout_type.png`, `outputs/bmi_by_experience.png` — generated and committed chart outputs. `max_performance.ipynb` — main Jupyter notebook tying all modules together. Ensured cross-module compatibility across all files — standardized column names (`cal_burned`, `exp_level`, `wk_freq`), verified imports, and resolved integration issues between the data loader, tracker, analytics, and visualizer so the full project runs end to end without errors. |

Each member made at least 5 meaningful commits to the repo across logic, design, testing, data handling, and documentation.

All code was written and tested locally on our individual machines throughout the project. Each team member developed and debugged their assigned files independently, coordinating on column names and function interfaces as we went. Once everything was finalized and working end to end, we uploaded the completed files to the GitHub repository for final submission.
