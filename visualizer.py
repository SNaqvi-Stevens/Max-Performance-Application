"""
visualizer.py

Matplotlib charts for the project. Each function takes a cleaned
DataFrame, builds a figure, saves it under outputs/, and returns
the Figure so the notebook can show it inline too.
"""

import os
import matplotlib
matplotlib.use("Agg")  # headless backend - works fine in notebooks too
import matplotlib.pyplot as plt
import pandas as pd


_HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULT_OUTPUT_DIR = os.path.join(_HERE, "outputs")


def _resolve_save_path(save_path, default_name):
    """Pick the save path and make sure the parent folder exists."""
    if save_path is None:
        save_path = os.path.join(DEFAULT_OUTPUT_DIR, default_name)
    parent = os.path.dirname(save_path)
    if parent and not os.path.exists(parent):
        os.makedirs(parent, exist_ok=True)
    return save_path


def _require_nonempty_df(df, needed_cols):
    """Raise ValueError if the DataFrame is missing or doesn't have what we need."""
    if not isinstance(df, pd.DataFrame):
        raise ValueError("Expected a pandas DataFrame, got: " + str(type(df)))
    if df.empty:
        raise ValueError("DataFrame is empty - nothing to plot.")
    missing = [c for c in needed_cols if c not in df.columns]
    if missing:
        raise ValueError("DataFrame is missing required columns: " + str(missing))


def plot_calories_by_workout_type(df, save_path=None):
    """Bar chart: average calories burned per workout type."""
    _require_nonempty_df(df, ["exercise_type", "cal_burned"])

    # group by workout type, take mean calories, sort biggest-first
    means = df.groupby("exercise_type")["cal_burned"].mean().sort_values(ascending=False)

    fig, ax = plt.subplots(figsize=(8, 5))
    ax.bar(means.index, means.values, color="#7c6af7")
    ax.set_title("Average Calories Burned by Workout Type")
    ax.set_xlabel("Workout Type")
    ax.set_ylabel("Avg Calories Burned (kcal)")
    ax.grid(axis="y", linestyle="--", alpha=0.4)
    fig.tight_layout()

    # save to outputs/ by default so the notebook can also embed the PNG
    out = _resolve_save_path(save_path, "calories_by_workout_type.png")
    fig.savefig(out, dpi=120)
    return fig


def plot_hr_zone_distribution(tracker_or_df, save_path=None):
    """
    Bar chart of HR zone counts.

    Accepts either a PerformanceTracker (calls hr_zone_distribution() on it)
    or a {zone_name: count} dict directly.
    """
    # accept a tracker (use its method) or a precomputed dict
    if hasattr(tracker_or_df, "hr_zone_distribution"):
        zones = tracker_or_df.hr_zone_distribution()
    elif isinstance(tracker_or_df, dict):
        zones = tracker_or_df
    else:
        raise ValueError("Pass a PerformanceTracker or a dict of {zone: count}.")

    if not zones:
        raise ValueError("No HR zone data to plot.")

    # split the dict into parallel lists for plotting
    labels = list(zones.keys())
    counts = list(zones.values())

    fig, ax = plt.subplots(figsize=(9, 5))
    ax.bar(labels, counts, color="#a6e3a1")
    ax.set_title("Heart Rate Zone Distribution")
    ax.set_xlabel("Zone")
    ax.set_ylabel("Session Count")
    ax.tick_params(axis="x", rotation=20)
    ax.grid(axis="y", linestyle="--", alpha=0.4)
    fig.tight_layout()

    out = _resolve_save_path(save_path, "hr_zone_distribution.png")
    fig.savefig(out, dpi=120)
    return fig


def plot_bmi_by_experience(df, save_path=None):
    """Bar chart: average BMI by experience level (Beginner / Intermediate / Expert)."""
    _require_nonempty_df(df, ["exp_level", "BMI"])

    # mean BMI per experience level, sorted by level number
    grp = df.groupby("exp_level")["BMI"].mean().sort_index()
    label_map = {1: "Beginner", 2: "Intermediate", 3: "Expert"}
    # list comprehension to map numeric levels to readable labels
    labels = [label_map.get(int(k), str(k)) for k in grp.index]

    fig, ax = plt.subplots(figsize=(7, 5))
    ax.bar(labels, grp.values, color="#f9e2af")
    ax.set_title("Average BMI by Experience Level")
    ax.set_xlabel("Experience Level")
    ax.set_ylabel("Average BMI")
    ax.grid(axis="y", linestyle="--", alpha=0.4)
    fig.tight_layout()

    out = _resolve_save_path(save_path, "bmi_by_experience.png")
    fig.savefig(out, dpi=120)
    return fig


def plot_calories_vs_duration(df, save_path=None):
    """Scatter plot of session duration vs calories burned."""
    _require_nonempty_df(df, ["duration_min", "cal_burned"])

    fig, ax = plt.subplots(figsize=(8, 5))
    ax.scatter(df["duration_min"], df["cal_burned"], alpha=0.4, color="#f38ba8", s=14)
    ax.set_title("Session Duration vs Calories Burned")
    ax.set_xlabel("Duration (min)")
    ax.set_ylabel("Calories Burned (kcal)")
    ax.grid(linestyle="--", alpha=0.4)
    fig.tight_layout()

    out = _resolve_save_path(save_path, "calories_vs_duration.png")
    fig.savefig(out, dpi=120)
    return fig


def plot_workout_type_counts(df, save_path=None):
    """Bar chart: how many sessions of each workout type are in the dataset."""
    _require_nonempty_df(df, ["exercise_type"])

    # value_counts returns workout types ordered by frequency
    counts = df["exercise_type"].value_counts()

    fig, ax = plt.subplots(figsize=(8, 5))
    ax.bar(counts.index, counts.values, color="#89b4fa")
    ax.set_title("Workout Type Session Counts")
    ax.set_xlabel("Workout Type")
    ax.set_ylabel("Number of Sessions")
    ax.grid(axis="y", linestyle="--", alpha=0.4)
    fig.tight_layout()

    out = _resolve_save_path(save_path, "workout_type_counts.png")
    fig.savefig(out, dpi=120)
    return fig


if __name__ == "__main__":
    # quick test - load the CSV and render one chart
    from data_loader import load_and_clean

    csv_path = os.path.join(_HERE, "data", "gym_members_exercise_tracking_synthetic_data.csv")
    df = load_and_clean(csv_path)
    fig = plot_calories_by_workout_type(df)
    print("Rendered chart to:", os.path.join(DEFAULT_OUTPUT_DIR, "calories_by_workout_type.png"))
    plt.close(fig)
