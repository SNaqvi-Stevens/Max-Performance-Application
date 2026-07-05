"""
tests/test_max_performance.py

Pytest tests for PerformanceTracker, analytics functions, and data loader.

Run with: pytest tests/test_max_performance.py -v
"""

import sys
import os
import pytest
import pandas as pd
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from athlete import GymMember
from performance_tracker import PerformanceTracker
from analytics import (
    calc_acwr,
    recovery_status,
    exercise_dist,
    trend_analy,
    aggregate_calories,
    describe_series,
)
from data_loader import load_and_clean, build_member_from_row

DATA_PATH = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "data", "gym_members_exercise_tracking_synthetic_data.csv"
)


# ---- fixtures ----

@pytest.fixture
def sample_member():
    return GymMember(1, 28.0, "Female", 65.0, 1.68, 23.0, 2, 4.0, 62.0)

@pytest.fixture
def loaded_tracker(sample_member):
    tracker = PerformanceTracker(sample_member)
    tracker.load_data(DATA_PATH)
    return tracker

@pytest.fixture
def clean_df():
    return load_and_clean(DATA_PATH)


# ---- GymMember (Athlete) ----

class TestAthlete:

    def test_valid_construction(self):
        m = GymMember(7, 28.0, "Female", 65.0, 1.68, 23.0, 2, 4.0, 62.0)
        assert m.member_id == 7
        assert m.age == 28.0
        assert m.gender == "Female"
        assert m.weight_kg == 65.0
        assert m.height_m == 1.68
        assert m.bmi == 23.0
        assert m.experience_level == 2
        assert m.workout_frequency == 4.0
        assert m.resting_bpm == 62.0

    def test_invalid_age_zero(self):
        with pytest.raises(ValueError):
            GymMember(1, 0, "Female", 65.0, 1.68, 23.0, 2, 4.0, 62.0)

    def test_invalid_age_too_high(self):
        with pytest.raises(ValueError):
            GymMember(1, 200, "Female", 65.0, 1.68, 23.0, 2, 4.0, 62.0)

    def test_invalid_weight(self):
        with pytest.raises(ValueError):
            GymMember(1, 28.0, "Female", 0.0, 1.68, 23.0, 2, 4.0, 62.0)

    def test_invalid_height(self):
        with pytest.raises(ValueError):
            GymMember(1, 28.0, "Female", 65.0, -1.0, 23.0, 2, 4.0, 62.0)

    def test_max_heart_rate_formula(self):
        # athlete.py uses 220 - age (cast to int)
        m = GymMember(1, 30.0, "Male", 80.0, 1.80, 24.0, 2, 4.0, 60.0)
        assert m.max_heart_rate == 190

    def test_heart_rate_reserve(self):
        # HRR = max_HR - int(resting_bpm)
        m = GymMember(1, 30.0, "Male", 80.0, 1.80, 24.0, 2, 4.0, 60.0)
        assert m.heart_rate_reserve == m.max_heart_rate - 60

    def test_target_hr_zone_within_bounds(self):
        m = GymMember(1, 30.0, "Male", 80.0, 1.80, 24.0, 2, 4.0, 60.0)
        low, high = m.target_hr_zone(0.70)
        assert isinstance(low, int) and isinstance(high, int)
        assert low <= high
        # zone must lie between resting and max HR
        assert low >= int(m.resting_bpm)
        assert high <= m.max_heart_rate

    def test_bmi_category_boundaries(self):
        # athlete.py thresholds: <18.5 Under, <25.0 Normal, <30.0 Over, else Obese
        cases = [
            (18.4, "Underweight"),
            (18.5, "Normal"),
            (24.9, "Normal"),
            (25.0, "Overweight"),
            (29.9, "Overweight"),
            (30.0, "Obese"),
        ]
        for bmi_val, expected in cases:
            m = GymMember(1, 28.0, "Female", 65.0, 1.68, bmi_val, 2, 4.0, 62.0)
            assert m.bmi_category == expected, f"bmi={bmi_val} expected {expected}, got {m.bmi_category}"

    def test_eq_same_id_true(self):
        a = GymMember(5, 28.0, "Female", 65.0, 1.68, 23.0, 2, 4.0, 62.0)
        b = GymMember(5, 40.0, "Male",   80.0, 1.80, 25.0, 3, 5.0, 70.0)
        # __eq__ keys on member_id only
        assert a == b

    def test_eq_diff_id_false(self):
        a = GymMember(5, 28.0, "Female", 65.0, 1.68, 23.0, 2, 4.0, 62.0)
        b = GymMember(6, 28.0, "Female", 65.0, 1.68, 23.0, 2, 4.0, 62.0)
        assert a != b


# ---- PerformanceTracker ----

class TestPerformanceTracker:

    def test_valid_creation(self, sample_member):
        t = PerformanceTracker(sample_member)
        assert t.member == sample_member

    def test_non_member_raises(self):
        with pytest.raises(TypeError):
            PerformanceTracker("not a member")

    def test_missing_file_raises(self, sample_member):
        t = PerformanceTracker(sample_member)
        with pytest.raises(FileNotFoundError):
            t.load_data("/nonexistent/path.csv")

    def test_data_loads(self, loaded_tracker):
        assert loaded_tracker.df is not None
        assert len(loaded_tracker) > 0

    def test_row_count(self, loaded_tracker):
        # dataset should have well over 1000 entries
        assert len(loaded_tracker) > 1000

    def test_summary_keys(self, loaded_tracker):
        s = loaded_tracker.performance_summary()
        assert "calories" in s
        assert "duration_min" in s
        assert "avg_hr" in s

    def test_calories_by_type_cols(self, loaded_tracker):
        res = loaded_tracker.calories_by_workout_type()
        assert "exercise_type" in res.columns
        assert "avg_cal" in res.columns

    def test_hr_zones_dict(self, loaded_tracker):
        zones = loaded_tracker.hr_zone_distribution()
        assert isinstance(zones, dict)
        assert len(zones) > 0

    def test_bmi_exp_levels(self, loaded_tracker):
        res = loaded_tracker.bmi_by_experience()
        assert len(res) == 3

    def test_top5(self, loaded_tracker):
        top = loaded_tracker.top_n_sessions(n=5)
        assert len(top) == 5

    def test_bad_col_raises(self, loaded_tracker):
        with pytest.raises(ValueError):
            loaded_tracker.top_n_sessions(by="fake_col")

    def test_workout_dist(self, loaded_tracker):
        dist = loaded_tracker.workout_type_distribution()
        assert isinstance(dist, dict)
        assert len(dist) > 0

    def test_peer_comparison_keys(self, loaded_tracker):
        res = loaded_tracker.peer_comparison()
        assert "peer_avg_cal" in res
        assert "member_bmi" in res

    def test_len_matches_df(self, loaded_tracker):
        assert len(loaded_tracker) == len(loaded_tracker.df)

    def test_str_has_id(self, loaded_tracker):
        assert "1" in str(loaded_tracker)

    def test_getattr_delegation(self, loaded_tracker):
        assert loaded_tracker.bmi == loaded_tracker.member.bmi

    def test_bad_attr_raises(self, loaded_tracker):
        with pytest.raises(AttributeError):
            _ = loaded_tracker.nonexistent_xyz

    def test_notes(self, loaded_tracker):
        loaded_tracker.add_note("checked session data")
        assert any("checked session" in n for n in loaded_tracker.get_notes())

    def test_summary_before_load_raises(self, sample_member):
        t = PerformanceTracker(sample_member)
        with pytest.raises(RuntimeError):
            t.performance_summary()

    def test_bad_csv_raises(self, sample_member, tmp_path):
        # CSV with wrong columns should fail loudly
        bad = pd.DataFrame({"date": ["2024-01-01"], "exercise_type": ["Running"]})
        p = tmp_path / "bad.csv"
        bad.to_csv(p, index=False)
        t = PerformanceTracker(sample_member)
        with pytest.raises(ValueError):
            t.load_data(str(p))


# ---- analytics ----

class TestCalcAcwr:

    def test_returns_float(self):
        result = calc_acwr([100, 120, 110], [90, 95, 100, 105])
        assert isinstance(result, float)

    def test_balanced_load(self):
        # both sum to 2800, ratio should sit near 1.0
        result = calc_acwr([400] * 7, [100] * 28)
        assert 0.8 <= result <= 1.3

    def test_zero_chronic(self):
        # no chronic load recorded, shouldn't crash
        result = calc_acwr([100, 200], [0, 0, 0])
        assert result == 0

    def test_overtraining_flag(self):
        # acute way higher than chronic, classic overtraining signal
        result = calc_acwr([500] * 7, [50] * 28)
        assert result > 1.3

    def test_undertrained(self):
        result = calc_acwr([20] * 7, [100] * 28)
        assert result < 0.8


class TestRecoveryStatus:

    def test_low_ratio(self):
        assert recovery_status(0.5) == "Undertrained"

    def test_at_1(self):
        assert recovery_status(1.0) == "Optimal"

    def test_lower_bound(self):
        assert recovery_status(0.8) == "Optimal"

    def test_upper_bound(self):
        assert recovery_status(1.3) == "Optimal"

    def test_over_threshold(self):
        assert recovery_status(1.5) == "Overtrained"

    def test_very_high(self):
        assert recovery_status(2.0) == "Overtrained"


class TestExerciseDist:

    def test_returns_dict(self):
        res = exercise_dist(["Running", "Cycling", "Running"])
        assert isinstance(res, dict)

    def test_proportions_add_up(self):
        res = exercise_dist(["Running", "Cycling", "Running", "Yoga"])
        assert abs(sum(res.values()) - 1.0) < 0.001

    def test_empty(self):
        assert exercise_dist([]) == {}

    def test_one_type_full_share(self):
        res = exercise_dist(["Running", "Running", "Running"])
        assert res["Running"] == 1.0

    def test_split_proportions(self):
        res = exercise_dist(["A", "A", "B"])
        assert abs(res["A"] - 2/3) < 0.001
        assert abs(res["B"] - 1/3) < 0.001


class TestTrendAnaly:

    def test_output_length(self):
        result = trend_analy(list(range(10)), [2*i+1 for i in range(10)])
        assert len(result) == 3

    def test_positive_slope(self):
        slope, _, _ = trend_analy(list(range(10)), [i*3 for i in range(10)])
        assert slope > 0

    def test_negative_slope(self):
        slope, _, _ = trend_analy(list(range(10)), [100 - i*5 for i in range(10)])
        assert slope < 0

    def test_perfect_linear_r2(self):
        _, _, r2 = trend_analy(list(range(10)), [2*i+3 for i in range(10)])
        assert abs(r2 - 1.0) < 0.001

    def test_slope_value(self):
        slope, _, _ = trend_analy(list(range(5)), [i*2 for i in range(5)])
        assert abs(slope - 2.0) < 0.01


class TestAggregateCalories:

    def test_basic_sum(self):
        assert aggregate_calories([100, 200, 300]) == 600

    def test_empty(self):
        assert aggregate_calories([]) == 0

    def test_single(self):
        assert aggregate_calories([500]) == 500

    def test_floats(self):
        assert abs(aggregate_calories([100.5, 200.5]) - 301.0) < 0.01


class TestDescribeSeries:

    def test_returns_dict(self):
        assert isinstance(describe_series([1, 2, 3, 4, 5]), dict)

    def test_has_expected_keys(self):
        res = describe_series([1, 2, 3, 4, 5])
        for k in ("mean", "median", "stdev"):
            assert k in res

    def test_mean_val(self):
        assert describe_series([10, 20, 30])["mean"] == 20.0

    def test_median_val(self):
        assert describe_series([1, 2, 3, 4, 5])["median"] == 3

    def test_single_val_stdev(self):
        assert describe_series([42])["stdev"] == 0


# ---- data loader ----

class TestDataLoader:

    def test_returns_df(self, clean_df):
        assert isinstance(clean_df, pd.DataFrame)

    def test_size(self, clean_df):
        assert len(clean_df) > 1000

    def test_expected_cols(self, clean_df):
        for col in ["exercise_type", "cal_burned", "duration_min",
                    "avg_heart_rate", "exp_level", "BMI"]:
            assert col in clean_df.columns

    def test_no_nulls_in_key_cols(self, clean_df):
        for col in ["exercise_type", "cal_burned", "avg_heart_rate"]:
            assert clean_df[col].isnull().sum() == 0

    def test_duration_range(self, clean_df):
        # sessions under 20 min or over 3 hrs would be data issues
        assert clean_df["duration_min"].min() >= 20
        assert clean_df["duration_min"].max() <= 180

    def test_no_whitespace_in_types(self, clean_df):
        for wt in clean_df["exercise_type"].dropna():
            assert wt == wt.strip()

    def test_missing_file(self):
        with pytest.raises(FileNotFoundError):
            load_and_clean("/nonexistent/path.csv")

    def test_build_member(self, clean_df):
        m = build_member_from_row(clean_df, member_id=1, row_idx=0)
        assert isinstance(m, GymMember)
        assert m.member_id == 1

    def test_bad_row_idx(self, clean_df):
        with pytest.raises(IndexError):
            build_member_from_row(clean_df, row_idx=99999)
