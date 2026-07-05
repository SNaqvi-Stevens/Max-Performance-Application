"""
data_loader.py

Loads and cleans the gym members CSV. Returns a tidy DataFrame
with short column names that the rest of the project uses.
"""

import os
import pandas as pd

from athlete import GymMember


# raw columns we expect from the CSV
REQUIRED_RAW_COLS = {
    "Age", "Gender", "Weight (kg)", "Height (m)", "Max_BPM",
    "Avg_BPM", "Resting_BPM", "Session_Duration (hours)",
    "Calories_Burned", "Workout_Type", "Fat_Percentage",
    "Water_Intake (liters)", "Workout_Frequency (days/week)",
    "Experience_Level", "BMI",
}

# raw -> short names so the rest of the code isn't full of "Workout_Frequency (days/week)"
RENAME_MAP = {
    "Avg_BPM":                       "avg_heart_rate",
    "Calories_Burned":               "cal_burned",
    "Workout_Type":                  "exercise_type",
    "Water_Intake (liters)":         "water_liters",
    "Workout_Frequency (days/week)": "wk_freq",
    "Experience_Level":              "exp_level",
    "Weight (kg)":                   "weight_kg",
    "Height (m)":                    "height_m",
    "Resting_BPM":                   "resting_bpm",
    "Max_BPM":                       "max_bpm",
    "Fat_Percentage":                "fat_pct",
}

# columns that have to be present (non-null) for a row to be useful
KEY_COLS = [
    "exercise_type", "cal_burned", "avg_heart_rate",
    "duration_min", "exp_level", "BMI", "Age",
]

# session duration limits in minutes (anything outside is probably bad data)
DURATION_MIN = 20
DURATION_MAX = 180

INTENSITY_MAP = {1: "low", 2: "moderate", 3: "high"}


def load_and_clean(path):
    """
    Read the CSV and return a cleaned DataFrame.

    Handles a few annoying things in the source data: Max_BPM is stored
    as a string, Workout_Type has stray whitespace and literal '\\n' / '\\t'
    sequences, and there are NaNs scattered through almost every column.
    """
    if not os.path.exists(path):
        raise FileNotFoundError("Dataset not found at: " + str(path))

    try:
        df = pd.read_csv(path)
    except Exception as e:
        raise ValueError("Failed to read CSV at " + str(path) + ": " + str(e))

    # check columns first so the error message is useful
    missing = REQUIRED_RAW_COLS - set(df.columns)
    if missing:
        raise ValueError("CSV is missing required columns: " + str(sorted(missing)))

    # Workout_Type has two kinds of pollution: real \n/\t/\r chars AND
    # literal backslash-letter pairs (the data was probably exported badly).
    # Strip both, then trim.
    df["Workout_Type"] = (
        df["Workout_Type"].astype(str)
        .str.replace(r"\\[ntr]", "", regex=True)
        .str.replace(r"[\n\t\r]", "", regex=True)
        .str.strip()
    )
    df["Gender"] = df["Gender"].astype(str).str.strip()

    # Max_BPM is stored as object (string). Coerce to numeric, NaN if it can't parse.
    df["Max_BPM"] = pd.to_numeric(df["Max_BPM"], errors="coerce")

    df = df.rename(columns=RENAME_MAP)

    # convert hours -> minutes, drop the hours col since we don't need it anymore
    df["duration_min"] = (df["Session_Duration (hours)"] * 60).round(1)
    df = df.drop(columns=["Session_Duration (hours)"])

    df["intensity_level"] = df["exp_level"].map(INTENSITY_MAP)

    # drop rows missing any of the columns we actually need for analysis
    df = df.dropna(subset=KEY_COLS)

    # clamp duration to a reasonable range
    df = df[(df["duration_min"] >= DURATION_MIN) & (df["duration_min"] <= DURATION_MAX)]

    df = df.reset_index(drop=True)
    return df


def build_member_from_row(df, member_id=1, row_idx=0):
    """
    Make a GymMember from one row of a cleaned DataFrame.

    member_id defaults to 1 since the dataset itself doesn't have IDs.
    row_idx defaults to 0.
    """
    if not isinstance(df, pd.DataFrame):
        raise TypeError("df must be a pandas DataFrame, got: " + str(type(df)))

    # explicit bounds check so we get IndexError (pandas would raise something else)
    if row_idx < 0 or row_idx >= len(df):
        raise IndexError("row_idx " + str(row_idx) + " is out of range for df of length " + str(len(df)))

    row = df.iloc[row_idx]

    return GymMember(
        member_id=int(member_id),
        age=float(row["Age"]),
        gender=str(row["Gender"]),
        weight_kg=float(row["weight_kg"]),
        height_m=float(row["height_m"]),
        bmi=float(row["BMI"]),
        experience_level=int(row["exp_level"]),
        workout_frequency=float(row["wk_freq"]),
        resting_bpm=float(row["resting_bpm"]),
    )


if __name__ == "__main__":
    # quick sanity check
    here = os.path.dirname(os.path.abspath(__file__))
    csv_path = os.path.join(here, "data", "gym_members_exercise_tracking_synthetic_data.csv")
    cleaned = load_and_clean(csv_path)
    print("Loaded:", csv_path)
    print("Shape:", cleaned.shape)
    print("Dtypes:")
    print(cleaned.dtypes)
    print("First member from row 0:")
    print(build_member_from_row(cleaned, member_id=1, row_idx=0))
