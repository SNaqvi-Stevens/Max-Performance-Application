"""
recommender.py

Generates personalised workout plans and health advice
based on a GymMember's profile and dataset patterns.
"""

WORKOUT_DB = {
    "Strength": {
        1: ["Bodyweight squats 3x12", "Push-ups 3x10", "Dumbbell rows 3x10", "Glute bridges 3x15", "Plank 3x30s"],
        2: ["Barbell squats 4x8", "Bench press 4x8", "Deadlifts 3x6", "Overhead press 3x10", "Pull-ups 3x8"],
        3: ["Heavy squat 5x5", "Romanian deadlift 4x8", "Weighted pull-ups 4x6", "Incline bench 4x8", "Farmers carry 4x40m"],
    },
    "Cardio": {
        1: ["20-min brisk walk", "Light jog 15 min", "Cycling 20 min (easy)", "Swimming 20 min", "Elliptical 20 min"],
        2: ["5K run", "Cycling 45 min (moderate)", "Rowing 30 min", "Jump rope 20 min", "Swimming 30 min"],
        3: ["10K run", "Tempo run 40 min", "Cycling 60 min (hard)", "Hill sprints 30 min", "Triathlon training set"],
    },
    "HIIT": {
        1: ["20s work / 40s rest · 8 rounds", "Jumping jacks + rest", "Step-ups + bodyweight squats", "Modified burpees 5 rounds", "Marching + rest intervals"],
        2: ["30s work / 30s rest · 10 rounds", "Sprint intervals on bike", "Kettlebell swings + box jumps", "Battle ropes 6 rounds", "Burpees + mountain climbers"],
        3: ["40s work / 20s rest · 12 rounds", "Sprint + plyo combo", "Heavy KB complex", "Assault bike Tabata", "Box jump + barbell complex"],
    },
    "Yoga": {
        1: ["Hatha yoga 30 min", "Gentle flow", "Chair yoga", "Sun salutation x5 slow", "Restorative 30 min"],
        2: ["Vinyasa flow 45 min", "Power yoga 40 min", "Yin yoga 45 min", "Sun salutation x10", "Ashtanga half primary"],
        3: ["Ashtanga primary series", "Power flow 60 min", "Hot yoga 60 min", "Inversions practice", "Advanced vinyasa 60 min"],
    },
}

GOAL_MATRIX = {
    "Underweight": {
        "primary": "Strength",
        "secondary": "Yoga",
        "avoid": "HIIT",
        "freq": (3, 4),
        "duration": (45, 60),
        "hr_zone": "Zone 2-3",
        "goal_label": "Build muscle mass",
        "advice": [
            "Focus on compound lifts — squats, deadlifts, bench press.",
            "Eat in a caloric surplus (add 300-500 kcal/day above maintenance).",
            "Prioritise protein intake: aim for 1.6-2.0g per kg of bodyweight.",
            "Rest 48-72 hours between training the same muscle group.",
            "Avoid excessive cardio — it burns calories you need for gaining weight.",
            "Track your lifts weekly and aim to add weight or reps each session.",
        ],
    },
    "Normal": {
        "primary": "Cardio",
        "secondary": "Strength",
        "avoid": None,
        "freq": (3, 5),
        "duration": (45, 75),
        "hr_zone": "Zone 3-4",
        "goal_label": "Maintain and improve fitness",
        "advice": [
            "You are in a healthy range — focus on performance and consistency.",
            "Mix strength and cardio for a balanced routine.",
            "Aim for 150-300 min of moderate or 75-150 min of vigorous cardio per week (WHO guideline).",
            "Include 2+ strength sessions per week to maintain muscle mass.",
            "Prioritise sleep (7-9h) — it drives recovery and performance.",
            "Stay hydrated: dataset average is 2.4L per session.",
        ],
    },
    "Overweight": {
        "primary": "HIIT",
        "secondary": "Cardio",
        "avoid": None,
        "freq": (4, 5),
        "duration": (40, 60),
        "hr_zone": "Zone 3-4",
        "goal_label": "Reduce body fat, improve cardiovascular health",
        "advice": [
            "HIIT burns ~30% more calories than steady-state cardio in less time.",
            "Start with 2 HIIT sessions/week and build up — recovery matters.",
            "Add 2-3 strength sessions to preserve muscle while losing fat.",
            "Prioritise a moderate caloric deficit (300-500 kcal/day) — not extreme restriction.",
            "Track non-exercise movement (steps) — aim for 8,000-10,000 steps/day.",
            "Yoga sessions improve flexibility and reduce cortisol, which helps fat loss.",
        ],
    },
    "Obese": {
        "primary": "Cardio",
        "secondary": "Strength",
        "avoid": "HIIT",
        "freq": (3, 4),
        "duration": (30, 50),
        "hr_zone": "Zone 2",
        "goal_label": "Safe, sustainable fat loss and cardiovascular improvement",
        "advice": [
            "Start with low-impact cardio (walking, cycling, swimming) to protect joints.",
            "Zone 2 cardio (60-70% max HR) is safest and still highly effective.",
            "Add bodyweight strength work — it builds muscle and burns more calories at rest.",
            "Avoid high-impact HIIT until cardiovascular fitness improves (4-8 weeks in).",
            "Work with a physician to set realistic targets and monitor health markers.",
            "Focus on consistency over intensity — 3 moderate sessions beat 1 brutal one.",
        ],
    },
}

WEEKLY_TEMPLATES = {
    "Strength_dominant": {
        "Mon": ("Strength", "primary"),
        "Tue": ("Cardio", "light"),
        "Wed": ("Strength", "primary"),
        "Thu": ("Yoga", "recovery"),
        "Fri": ("Strength", "primary"),
        "Sat": ("Cardio", "moderate"),
        "Sun": ("Rest", None),
    },
    "Cardio_dominant": {
        "Mon": ("Cardio", "primary"),
        "Tue": ("Strength", "secondary"),
        "Wed": ("Cardio", "primary"),
        "Thu": ("Rest", None),
        "Fri": ("HIIT", "secondary"),
        "Sat": ("Yoga", "recovery"),
        "Sun": ("Rest", None),
    },
    "HIIT_dominant": {
        "Mon": ("HIIT", "primary"),
        "Tue": ("Strength", "secondary"),
        "Wed": ("Cardio", "light"),
        "Thu": ("HIIT", "primary"),
        "Fri": ("Strength", "secondary"),
        "Sat": ("Yoga", "recovery"),
        "Sun": ("Rest", None),
    },
    "Yoga_dominant": {
        "Mon": ("Yoga", "primary"),
        "Tue": ("Strength", "secondary"),
        "Wed": ("Yoga", "primary"),
        "Thu": ("Cardio", "light"),
        "Fri": ("Strength", "secondary"),
        "Sat": ("Yoga", "primary"),
        "Sun": ("Rest", None),
    },
}


def get_bmi_category(bmi):
    if bmi < 18.5: return "Underweight"
    elif bmi < 25: return "Normal"
    elif bmi < 30: return "Overweight"
    else: return "Obese"


def recommend(member):
    """
    Takes a GymMember and returns a dict with:
      goal, bmi_cat, plan (weekly schedule), exercises, advice, targets
    """
    bmi_cat = get_bmi_category(member.bmi)
    exp = int(member.experience_level)
    goal = GOAL_MATRIX[bmi_cat]
    primary = goal["primary"]

    # pick weekly template based on primary workout
    template_key = primary + "_dominant"
    if template_key not in WEEKLY_TEMPLATES:
        template_key = "Cardio_dominant"
    template = WEEKLY_TEMPLATES[template_key]

    # build week plan with actual exercises
    week = {}
    for day, (wtype, intensity) in template.items():
        if wtype == "Rest":
            week[day] = {"type": "Rest", "exercises": ["Active recovery — walk, stretch, or sleep in"], "duration": 0}
        else:
            exlist = WORKOUT_DB.get(wtype, {}).get(exp, WORKOUT_DB[wtype][1])
            duration_range = goal["duration"]
            dur = duration_range[0] if intensity in ("light", "recovery") else duration_range[1]
            week[day] = {"type": wtype, "exercises": exlist[:3], "duration": dur, "intensity": intensity}

    # hr targets
    mhr = member.max_heart_rate
    hrr = mhr - member.resting_bpm
    targets = {
        "zone2_low":  round(member.resting_bpm + hrr * 0.60),
        "zone2_high": round(member.resting_bpm + hrr * 0.70),
        "zone3_low":  round(member.resting_bpm + hrr * 0.70),
        "zone3_high": round(member.resting_bpm + hrr * 0.80),
        "zone4_low":  round(member.resting_bpm + hrr * 0.80),
        "zone4_high": round(member.resting_bpm + hrr * 0.90),
        "hr_zone":    goal["hr_zone"],
        "mhr":        mhr,
    }

    return {
        "bmi_cat":    bmi_cat,
        "goal_label": goal["goal_label"],
        "primary":    primary,
        "secondary":  goal["secondary"],
        "avoid":      goal["avoid"],
        "freq":       goal["freq"],
        "advice":     goal["advice"],
        "week":       week,
        "targets":    targets,
    }


if __name__ == "__main__":
    import sys, os
    sys.path.insert(0, os.path.dirname(__file__))
    from athlete import GymMember
    m = GymMember(1, 28.0, "Female", 75.0, 1.68, 26.6, 2, 4.0, 62.0)
    r = recommend(m)
    print("Goal:", r["goal_label"])
    print("BMI cat:", r["bmi_cat"])
    print("Primary workout:", r["primary"])
    for day, info in r["week"].items():
        print(f"  {day}: {info['type']} — {info['duration']}min")
