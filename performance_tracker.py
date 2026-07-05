"""
performance_tracker.py

Defines PerformanceTracker class. Loads and analyzes gym
members dataset for a given GymMember

Connected to GymMember through composition

"""

import pandas as pd
import numpy as np
from athlete import GymMember


class PerformanceTracker:
    """
    Loads and analyzes gym workout data for a specific GymMember
    Composition with GymMember, tracker has member
    """

    REQUIRED_COLS = {
        "Age", "Gender", "Weight (kg)", "Height (m)", "Max_BPM",
        "Avg_BPM", "Resting_BPM", "Session_Duration (hours)",
        "Calories_Burned", "Workout_Type", "Fat_Percentage",
        "Water_Intake (liters)", "Workout_Frequency (days/week)",
        "Experience_Level", "BMI"
    }

    INTENSITY_MAP = {1: "low", 2: "moderate", 3: "high"}

    def __init__(self, member):
        """
        Build a tracker around one GymMember. Member is required since
        a lot of the analysis is scoped to that person's experience tier.
        """
        if not isinstance(member, GymMember):
            raise TypeError("member must be a GymMember instance.")

        # composition: tracker has-a member
        self.member = member
        self.df = None
        self.member_df = None
        self._notes = []

    def load_data(self, filepath):
        """
        Read the CSV at filepath, validate columns, clean string fields,
        drop rows missing key columns, and split out a peer subset for
        the member's experience level. Raises FileNotFoundError if the
        path is bad or ValueError if the file is unreadable / missing cols.
        """
        try:
            df = pd.read_csv(filepath)
        except FileNotFoundError:
            raise FileNotFoundError("File not found: " + filepath)
        except Exception as e:
            raise ValueError("Couldn't read the CSV: " + str(e))

        # set difference: which required columns are missing from the file
        missing = self.REQUIRED_COLS - set(df.columns)
        if missing:
            raise ValueError("Missing columns in dataset: " + str(missing))

        # dataset has stray newlines/tabs in some string fields
        for col in ["Workout_Type", "Gender"]:
            df[col] = df[col].astype(str).str.replace(r"[\n\t\r]", "", regex=True).str.strip()

        # only keep rows that have all the columns analysis depends on
        needed = ["Avg_BPM", "Calories_Burned", "Session_Duration (hours)",
                    "Workout_Type", "Experience_Level", "Age", "BMI"]
        df = df.dropna(subset=needed)
        df = df.reset_index(drop=True)

        # convert hours to minutes and label experience levels with intensity strings
        df["duration_min"] = (df["Session_Duration (hours)"] * 60).round(1)
        df["intensity_level"] = df["Experience_Level"].map(self.INTENSITY_MAP)

        df = df.rename(columns={
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
        })

        self.df = df
        self._notes.append("Loaded " + str(len(df)) + " records from " + filepath)

        # peer group = same experience level as this member
        self.member_df = df[df["exp_level"] == self.member.experience_level]
        self.member_df = self.member_df.reset_index(drop=True)
        self._notes.append(
            str(len(self.member_df)) + " peers at exp level " +
            str(self.member.experience_level)
        )

    def performance_summary(self):
        """Overall stats across the dataset."""
        if self.df is None:
            raise RuntimeError("Load data first with load_data().")

        summary = {}

        summary["calories"] = {
            "mean":   round(float(self.df["cal_burned"].mean()), 2),
            "median": round(float(self.df["cal_burned"].median()), 2),
            "min":    round(float(self.df["cal_burned"].min()), 2),
            "max":    round(float(self.df["cal_burned"].max()), 2),
        }
        summary["duration_min"] = {
            "mean":   round(float(self.df["duration_min"].mean()), 2),
            "median": round(float(self.df["duration_min"].median()), 2),
            "min":    round(float(self.df["duration_min"].min()), 2),
            "max":    round(float(self.df["duration_min"].max()), 2),
        }
        summary["avg_hr"] = {
            "mean":   round(float(self.df["avg_heart_rate"].mean()), 2),
            "median": round(float(self.df["avg_heart_rate"].median()), 2),
            "min":    round(float(self.df["avg_heart_rate"].min()), 2),
            "max":    round(float(self.df["avg_heart_rate"].max()), 2),
        }
        return summary

    def calories_by_workout_type(self):
        """Average calories per workout type, sorted descending."""
        if self.df is None:
            raise RuntimeError("Load data first.")

        grp = (
            self.df.groupby("exercise_type")["cal_burned"]
            .agg(["mean", "median", "count"])
            .rename(columns={"mean": "avg_cal", "median": "med_cal", "count": "sessions"})
            .round(2)
            .sort_values("avg_cal", ascending=False)
            .reset_index()
        )
        return grp

    def hr_zone_distribution(self):
        """
        Classifies sessions into HR zones based on this member's max HR.
        Zone 1 (<60%), Zone 2 (60-70%), Zone 3 (70-80%), Zone 4 (80-90%), Zone 5 (>90%)
        """
        if self.df is None:
            raise RuntimeError("Load data first.")

        mhr = self.member.max_heart_rate

        # bucket each session's avg HR into a zone label
        zones = [
            "Zone 1 - Recovery"     if hr < mhr * 0.60 else
            "Zone 2 - Aerobic Base" if hr < mhr * 0.70 else
            "Zone 3 - Aerobic"      if hr < mhr * 0.80 else
            "Zone 4 - Threshold"    if hr < mhr * 0.90 else
            "Zone 5 - Max Effort"
            for hr in self.df["avg_heart_rate"]
        ]

        # count occurrences of each zone label
        zone_counts = {}
        for z in zones:
            zone_counts[z] = zone_counts.get(z, 0) + 1

        # sort by zone name so output order is stable
        return dict(sorted(zone_counts.items()))

    def bmi_by_experience(self):
        """Average BMI grouped by experience level."""
        if self.df is None:
            raise RuntimeError("Load data first.")

        grp = (
            self.df.groupby("exp_level")
            .agg(
                avg_bmi=("BMI", "mean"),
                avg_weight=("weight_kg", "mean"),
                count=("BMI", "count")
            )
            .round(2)
            .reset_index()
        )
        grp["label"] = grp["exp_level"].map({1: "Beginner", 2: "Intermediate", 3: "Expert"})
        return grp

    def top_n_sessions(self, n=5, by="cal_burned"):
        """Top N sessions by a given column."""
        if self.df is None:
            raise RuntimeError("Load data first.")
        if by not in self.df.columns:
            raise ValueError(by + " is not a column in this dataset.")
        return self.df.nlargest(n, by).reset_index(drop=True)

    def workout_type_distribution(self):
        """Session count per workout type."""
        if self.df is None:
            raise RuntimeError("Load data first.")

        # unique workout types as a set (set operation usage)
        types = set(self.df["exercise_type"].dropna().unique())
        # dict comprehension: count rows per type
        counts = {
            wt: sum(1 for t in self.df["exercise_type"] if t == wt)
            for wt in types
        }
        # sort by count descending so the most common type comes first
        return dict(sorted(counts.items(), key=lambda x: x[1], reverse=True))

    def peer_comparison(self):
        """Member stats vs peers at the same experience level."""
        if self.df is None or self.member_df is None:
            raise RuntimeError("Load data first.")

        return {
            "member_experience":  self.member.experience_label,
            "peer_count":         len(self.member_df),
            "peer_avg_cal":       round(float(self.member_df["cal_burned"].mean()), 2),
            "peer_avg_duration":  round(float(self.member_df["duration_min"].mean()), 2),
            "peer_avg_hr":        round(float(self.member_df["avg_heart_rate"].mean()), 2),
            "peer_avg_bmi":       round(float(self.member_df["BMI"].mean()), 2),
            "member_bmi":         self.member.bmi,
            "member_resting_hr":  self.member.resting_bpm,
            "member_wk_freq":     self.member.workout_frequency,
        }

    def add_note(self, note):
        """Append a non-empty trimmed string to the tracker's note log."""
        if isinstance(note, str) and note.strip():
            self._notes.append(note.strip())

    def get_notes(self):
        """Return a copy of the note log so callers can't mutate the internal list."""
        return list(self._notes)

    def __len__(self):
        """Number of records currently loaded (0 if load_data hasn't run yet)."""
        if self.df is None:
            return 0
        return len(self.df)

    def __str__(self):
        """Short status line showing the member id and record count."""
        n = len(self.df) if self.df is not None else 0
        return ("PerformanceTracker for Member #" + str(self.member.member_id) +
                " | Records loaded: " + str(n))

    def __repr__(self):
        """Developer-friendly repr that includes the wrapped member."""
        return "PerformanceTracker(member=" + repr(self.member) + ")"

    def __getattr__(self, name):
        """
        Forward unknown attribute lookups to the underlying member, so
        tracker.bmi works as a shortcut for tracker.member.bmi.
        """
        # don't recurse on our own private attributes
        if name in ("member", "df", "member_df", "_notes"):
            raise AttributeError(name)
        try:
            return getattr(object.__getattribute__(self, "member"), name)
        except AttributeError:
            raise AttributeError("'PerformanceTracker' has no attribute '" + name + "'")


if __name__ == "__main__":
    m = GymMember(1, 28.0, "Female", 65.0, 1.68, 23.0, 2, 4.0, 62.0)
    tracker = PerformanceTracker(m)
    print(tracker)
    print("member BMI via __getattr__:", tracker.bmi)
