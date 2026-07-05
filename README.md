# Max Performance: Gym Member Workout Analysis & Recommendation System

A Python program and interactive web application that loads gym workout records, computes personalised fitness metrics, generates weekly workout plans, and runs cohort-level analytics and visualisations on top of the dataset.

## 🌐 Live Web App

**[Launch Max Performance →](https://snaqvi-stevens.github.io/Max-Performance-Application/)**
The full app runs in any browser — no Python or installation required. Enter a member profile to get a personalised weekly workout plan, heart rate targets, health coaching tips, and dataset-driven comparisons.

## Team

| Name | Email | Stevens ID |
|---|---|---|
| Saanie Naqvi | snaqvi3@stevens.edu | 20045913 |
| Aaron Nathans | anathans@stevens.edu | 20040170 |
| Azizul Haque | ahaque3@stevens.edu | 20036646 |

**Course:** AAI/CPE/EE 551 WS/WS1  
**Submission:** May 6, 2026

---

## Project Overview

Athletic performance depends on a lot of moving pieces: training intensity, recovery, body composition, and experience all factor in. Most people who track their workouts end up with a spreadsheet they never really analyse. We wanted to build something that takes that kind of data and turns it into actual insights — which workout types burn the most calories, how often you are training in each heart rate zone, how you compare to other members at your experience level, and most importantly, what you should actually be doing to reach your goals.

The program runs on a synthetic dataset of 1,800 gym sessions (15 columns covering age, weight, BMI, workout type, calories burned, heart rate, water intake, and more). After cleaning we end up with around 1,576 usable rows. The program computes per-member metrics (BMI category, max HR, target HR zones using the Karvonen formula), cohort statistics, and generates personalised weekly workout plans and health advice based on BMI category and experience level. It also saves five matplotlib charts to the `outputs/` folder.

The main program is a Jupyter notebook (`max_performance.ipynb`) that walks through everything step by step. There is also a Tkinter desktop application (`app.py`) with a full GUI, a browser-based web application (`index.html`) that runs without any installation, and a pytest suite with 70 tests covering the public functions and methods.

---

## Solution Approach

We split the code into focused modules so each one has a clear job:

- `athlete.py` — `GymMember` class. Holds one person's profile and computes their per-member metrics.
- `performance_tracker.py` — `PerformanceTracker` class. Composes a `GymMember` (a tracker has-a member, it is not a kind of member) and runs cohort analytics on top of the cleaned dataset.
- `analytics.py` — Standalone statistical functions (ACWR, recovery labelling, trend analysis, calorie aggregation, descriptive stats, plus a generator).
- `data_loader.py` — Reads the CSV, cleans it, and provides a factory function for building a `GymMember` from a row.
- `visualizer.py` — Five matplotlib chart functions that save PNGs to `outputs/`.
- `recommender.py` — Recommendation engine that maps a member's BMI category and experience level to a personalised weekly workout schedule, specific exercises, heart rate zone targets, and health coaching advice derived from dataset patterns.
- `app.py` — Full Tkinter desktop GUI with five tabs: Member Setup (with kg/m and lbs/ft unit toggle), Performance Analysis, Member Profiling, Charts, and a Workout Plan tab powered by the recommendation engine.
- `index.html` — Standalone browser-based web application. No Python or server required — open it directly or visit the GitHub Pages URL above. Includes the full recommendation engine rebuilt in JavaScript with the same BMI/experience logic, interactive unit conversion, Chart.js visualisations, ACWR calculator, and dataset comparison tools.

We went with composition rather than inheritance because a tracker uses a member to scope its analysis; it is not a specialised type of member.

Quick naming note: the class is called `GymMember` in the code. The proposal used the word "Athlete" but we settled on `GymMember` since it matches the dataset terminology, and we kept it consistent across all modules and tests.

---

## Features

### Desktop app (`app.py`)
- **Member Setup** — enter a profile with kg/m or lbs/ft, auto-calculates BMI and HR zones
- **Performance Analysis** — overall stats, calories by workout type, top 10 sessions, trend analysis
- **Member Profiling** — BMI distribution, experience-level breakdown, peer comparison, HR zone classification
- **Charts** — five matplotlib chart previews rendered inline
- **⚡ Workout Plan** — personalised weekly schedule, specific exercises, health advice, and Karvonen HR targets

### Web app (`index.html`)
- All of the above, runs in any browser
- Unit toggle (kg/m ↔ lbs/ft) with automatic conversion
- Interactive ACWR injury risk calculator
- Dataset comparison — you vs peers at your experience level with visual BMI progress bar
- Chart.js charts for calories, session counts, BMI by experience, HR zones, and a scatter plot

### Recommendation engine (`recommender.py`)
Generates workout plans based on BMI category and experience level using patterns from the dataset:

| BMI Category | Primary workout | Goal | Dataset-backed reasoning |
|---|---|---|---|
| Underweight | Strength | Build muscle mass | Preserve calories, compound lifts |
| Normal | Cardio | Maintain and improve fitness | Balanced 3–5x/week approach |
| Overweight | HIIT | Reduce body fat | Burns ~30% more than steady-state cardio |
| Obese | Low-impact Cardio | Safe fat loss | Protects joints, Zone 2 HR targeting |

Each plan includes day-by-day exercises scaled to the member's experience level, Karvonen formula HR zones, and six data-informed coaching tips.

---

## Dependencies

- Python 3.12+ (tested on 3.13)
- pandas
- numpy
- matplotlib
- pytest
- jupyter
- tkinter (built into Python — no install needed)

### Install

```bash
pip install pandas numpy matplotlib pytest jupyter
```

---

## File Structure

```
Max_Performance/
├── athlete.py                  ← GymMember class
├── performance_tracker.py      ← PerformanceTracker class
├── analytics.py                ← standalone stats functions
├── data_loader.py              ← CSV ingestion and cleaning
├── visualizer.py               ← matplotlib chart functions
├── recommender.py              ← workout plan & advice engine
├── app.py                      ← Tkinter desktop GUI
├── index.html                  ← browser web app (GitHub Pages)
├── test_max_performance.py     ← pytest suite (70 tests)
├── max_performance.ipynb       ← main Jupyter notebook
├── README.md
├── data/
│   └── gym_members_exercise_tracking_synthetic_data.csv
└── outputs/
    ├── calories_by_workout_type.png
    ├── hr_zone_distribution.png
    ├── bmi_by_experience.png
    ├── calories_vs_duration.png
    └── workout_type_counts.png
```

---

## How to Run

### Option 1 — Live web app (no installation)

Visit: **[[[https://snaqvi3.github.io/Max-Performance-Application/](https://snaqvi-stevens.github.io/Max-Performance-Application/)]
](https://snaqvi-stevens.github.io/Max-Performance-Application/)
Or open `index.html` directly in any browser.

### Option 2 — Tkinter desktop app

```bash
pip install pandas numpy matplotlib
python3 app.py
```

1. Click **Browse** to locate the CSV or confirm the default path
2. Click **Load Dataset**
3. Fill in a member profile and click **Create Member**
4. Navigate tabs — use **⚡ Workout Plan** for personalised recommendations

### Option 3 — Jupyter notebook (recommended for code walkthrough)

```bash
jupyter notebook max_performance.ipynb
```

Go to Kernel > Restart & Run All.

### Option 4 — Run tests

```bash
pytest test_max_performance.py -v
```

Should give you 70 passed.

### Option 5 — Run any module standalone

Each `.py` file has an `if __name__ == "__main__":` block:

```bash
python athlete.py
python performance_tracker.py
python analytics.py
python data_loader.py
python visualizer.py
python recommender.py
```

---

## Main Contributions

| Member | Contributions |
|---|---|
| **Saanie Naqvi** (snaqvi3@stevens.edu, 20045913) | `athlete.py` — `GymMember` class with input validation, BMI, max-HR, HR-reserve calculations, Karvonen target HR zone, weekly volume estimate, and operator overloads (`__str__`, `__eq__`, `__repr__`). `performance_tracker.py` — `PerformanceTracker` class composing `GymMember`, with cohort analytics methods and `__len__`, `__str__`, `__getattr__` overloads. `test_max_performance.py` — pytest suite for `PerformanceTracker`, analytics functions, and data loader. `tests/test_athlete.py` — dedicated pytest suite for `GymMember` covering all properties, methods, validation, and operator overloads. `recommender.py` — full recommendation engine mapping BMI category and experience level to personalised weekly workout plans, exercise libraries scaled by experience, Karvonen HR zone targets, and dataset-backed coaching advice for all four BMI groups. `app.py` — complete Tkinter desktop GUI including all five analysis tabs, a full ⚡ Workout Plan tab with four sub-views (weekly schedule, health advice, HR targets), and a kg/m ↔ lbs/ft unit toggle with automatic conversion. `index.html` — full browser-based web application built without any backend; includes the complete recommendation engine rebuilt in JavaScript, interactive unit conversion, Chart.js visualisations (calories, session counts, BMI by experience, HR zones, scatter), ACWR calculator, BMI checker, dataset comparison with peer group, and BMI progress bar. Published to GitHub Pages. Dataset sourced from Kaggle and uploaded to the repository. Wrote the main contributions table in `README.md`. |
| **Aaron Nathans** (anathans@stevens.edu, 20040170) | `analytics.py` — ACWR, recovery status labelling, exercise distribution, trend analysis with `numpy.polyfit`, reduce + lambda calorie aggregation, `describe_series` using `statistics`, and the `yield_high_calorie_sessions` generator. GitHub repo creation and setup — created the repository and shared access with all team members. `outputs/hr_zone_distribution.png`, `outputs/calories_vs_duration.png`, `outputs/workout_type_counts.png` — generated and committed chart outputs. |
| **Azizul Haque** (ahaque3@stevens.edu, 20036646) | `data_loader.py` — CSV ingestion, cleaning, column renaming, and the `GymMember` factory function. `visualizer.py` — five matplotlib chart functions. `README.md` — wrote the full project documentation including project overview, solution approach, dependencies, file structure, and setup instructions. `outputs/calories_by_workout_type.png`, `outputs/bmi_by_experience.png` — generated and committed chart outputs. `max_performance.ipynb` — main Jupyter notebook tying all modules together. Ensured cross-module compatibility — standardised column names (`cal_burned`, `exp_level`, `wk_freq`), verified imports, and resolved integration issues between the data loader, tracker, analytics, and visualiser so the full project runs end to end without errors. |

Each member made at least 5 meaningful commits to the repo across logic, design, testing, data handling, and documentation.

All code was written and tested locally on our individual machines throughout the project. Each team member developed and debugged their assigned files independently, coordinating on column names and function interfaces as we went. Once everything was finalised and working end to end, we uploaded the completed files to the GitHub repository for final submission.
