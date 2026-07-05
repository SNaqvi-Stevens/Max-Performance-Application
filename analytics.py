"""
analytics.py

Standalone functions for fatigue, recovery, and performance trend
calculations used across the project.
"""

import os
import numpy as np
from functools import reduce
import statistics


def calc_acwr(recent, long):
    """
    Acute:Chronic Workload Ratio.

    recent = short-term workload (~7 days), long = long-term (~28 days).
    Returns 0 if the chronic load is zero so we don't divide by zero.
    """
    # guard against an empty/zero chronic window
    if sum(long) == 0:
        return 0
    # ratio of acute load over chronic load
    return sum(recent) / sum(long)


def recovery_status(acwr):
    """
    Label an ACWR value as Undertrained / Optimal / Overtrained.

    Sweet spot is roughly 0.8 to 1.3 based on sports science research.
    """
    if acwr < 0.8:
        return "Undertrained"
    elif acwr <= 1.3:
        return "Optimal"
    else:
        return "Overtrained"


def exercise_dist(exercises):
    """
    Take a list of exercise names and return the share of each as a dict.
    Values add up to 1.0. Empty input -> empty dict.
    """
    if not exercises:
        return {}

    total = len(exercises)
    counts = {}

    # tally how many times each exercise name shows up
    for ex in exercises:
        if ex in counts:
            counts[ex] += 1
        else:
            counts[ex] = 1

    # convert raw counts to proportions of the total
    result = {}
    for ex in counts:
        result[ex] = counts[ex] / total

    return result


def trend_analy(x, y):
    """
    Linear trend on (x, y). Returns slope, intercept, R^2.

    Uses numpy.polyfit and computes R^2 manually from residuals.
    """
    x = np.array(x)
    y = np.array(y)

    # degree-1 polyfit returns coefficients of a straight line
    slope, intercept = np.polyfit(x, y, 1)
    y_pred = slope * x + intercept

    # standard R^2 = 1 - SS_res / SS_tot
    residual_ss = np.sum((y - y_pred) ** 2)
    total_ss = np.sum((y - np.mean(y)) ** 2)

    r2 = 1 - (residual_ss / total_ss)

    return slope, intercept, r2


def aggregate_calories(calories):
    """Sum calorie values using reduce + lambda. Returns 0 for empty input."""
    if not calories:
        return 0
    return reduce(lambda a, b: a + b, calories)


def describe_series(data):
    """Return mean, median, and stdev for a numeric sequence."""
    mean_val = statistics.mean(data)
    median_val = statistics.median(data)

    # stdev needs at least 2 data points
    if len(data) > 1:
        stdev_val = statistics.stdev(data)
    else:
        stdev_val = 0

    return {
        "mean": mean_val,
        "median": median_val,
        "stdev": stdev_val,
    }


def yield_high_calorie_sessions(df, threshold):
    """
    Generator. Yields each row (as dict) where cal_burned >= threshold.

    Streams rows one at a time so we don't have to copy the whole filtered
    DataFrame into memory.
    """
    # itertuples is faster than iterrows for read-only iteration
    for row in df.itertuples(index=False):
        cal = getattr(row, "cal_burned", None)
        if cal is None:
            continue
        if cal >= threshold:
            yield row._asdict()


if __name__ == "__main__":
    # quick demo of each function on the real dataset
    from data_loader import load_and_clean

    here = os.path.dirname(os.path.abspath(__file__))
    csv_path = os.path.join(here, "data", "gym_members_exercise_tracking_synthetic_data.csv")
    df = load_and_clean(csv_path)

    print("calc_acwr([400]*7, [100]*28) =", calc_acwr([400] * 7, [100] * 28))
    print("recovery_status(1.0)         =", recovery_status(1.0))
    print("exercise_dist (top 4)        =", dict(list(exercise_dist(list(df['exercise_type'])).items())[:4]))

    cal_list = list(df["cal_burned"])
    print("aggregate_calories total     =", round(aggregate_calories(cal_list), 1))
    print("describe_series(cal_burned)  =", {k: round(v, 2) for k, v in describe_series(cal_list).items()})

    slope, intercept, r2 = trend_analy(list(range(len(cal_list))), cal_list)
    print("trend slope/intercept/r2     =", round(slope, 4), round(intercept, 2), round(r2, 4))

    high_cal_iter = yield_high_calorie_sessions(df, threshold=1500)
    first_two = [next(high_cal_iter, None), next(high_cal_iter, None)]
    print("first 2 high-cal sessions    =", [r.get("cal_burned") if r else None for r in first_two])
