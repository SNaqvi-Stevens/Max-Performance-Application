"""
athlete.py

Defines the GymMember class. Stores a gym member's profile info
from the dataset and computes fitness metrics from it.

One of our two required classes. Connected to PerformanceTracker
through composition.
"""

class GymMember:
    """
    Stores a gym member's profile and computes basic fitness metrics.

    Attributes: member_id, age, gender, weight_kg, height_m, bmi,
    experience_level, workout_frequency, resting_bpm
    """

    # class attribute: maps experience level number to label
    EXPERIENCE_LABELS = {1: "Beginner", 2: "Intermediate", 3: "Expert"}

    def __init__(self, member_id, age, gender, weight_kg, height_m,
                 bmi, experience_level, workout_frequency, resting_bpm):
        """
        Initialize a GymMember with profile data from the dataset.

        Raises TypeError if member_id is not an int.
        Raises ValueError if any numeric fields are out of realistic range.
        """
        # validate member_id type first
        if not isinstance(member_id, int):
            raise TypeError("member_id has to be an int, got: " + str(type(member_id)))

        # validate ranges: catch bad data before it causes problems later
        if age <= 0 or age > 120:
            raise ValueError("Age has to be a positive number, got: " + str(age))
        if weight_kg <= 0:
            raise ValueError("Weight has to be positive, got: " + str(weight_kg))
        if height_m <= 0:
            raise ValueError("Height has to be positive, got: " + str(height_m))
        if experience_level not in (1, 2, 3):
            raise ValueError("Experience level has to be 1, 2, or 3, got: " + str(experience_level))
        if not (30 <= resting_bpm <= 120):
            raise ValueError("Resting BPM should be between 30 and 120, got: " + str(resting_bpm))

        self.member_id = member_id
        self.age = age
        self.gender = gender.strip()
        self.weight_kg = weight_kg
        self.height_m = height_m
        self.bmi = round(bmi, 2)
        self.experience_level = experience_level
        self.workout_frequency = workout_frequency
        self.resting_bpm = resting_bpm

    @property
    def experience_label(self):
        """Return the text label for this member's experience level."""
        return self.EXPERIENCE_LABELS.get(self.experience_level, "Unknown")

    @property
    def max_heart_rate(self):
        """
        Estimate max heart rate using 220 - age.

        Standard formula used in exercise science.
        """
        return int(220 - self.age)

    @property
    def heart_rate_reserve(self):
        """
        Calculate heart rate reserve (HRR = max HR - resting HR).

        Used in the Karvonen formula to compute target training zones.
        """
        return self.max_heart_rate - int(self.resting_bpm)

    @property
    def bmi_category(self):
        """
        Classify BMI using standard WHO ranges.

        Underweight < 18.5, Normal 18.5-25, Overweight 25-30, Obese 30+
        """
        if self.bmi < 18.5:
            return "Underweight"
        elif self.bmi < 25.0:
            return "Normal"
        elif self.bmi < 30.0:
            return "Overweight"
        else:
            return "Obese"

    def target_hr_zone(self, intensity_pct):
        """
        Compute target heart rate zone using the Karvonen formula.

        Formula: target HR = resting_HR + (HRR * intensity)
        Returns a (lower, upper) tuple using a +/- 5% window around the target.

        Raises ValueError if intensity is not in range (0.0, 1.0].
        """
        if not (0.0 < intensity_pct <= 1.0):
            raise ValueError("Intensity has to be between 0.0 and 1.0, got: " + str(intensity_pct))

        # Karvonen formula with a +/- 5% window around the target intensity
        lower = int(self.resting_bpm + (self.heart_rate_reserve * (intensity_pct - 0.05)))
        upper = int(self.resting_bpm + (self.heart_rate_reserve * (intensity_pct + 0.05)))
        return (lower, upper)

    def weekly_volume_estimate(self):
        """
        Estimate weekly training volume in minutes based on frequency and experience.

        Beginners average ~45 min/session, intermediate ~60, expert ~75.
        Returns estimated total active minutes per week.
        """
        # rough per-session minutes by experience tier
        base_minutes = {1: 45.0, 2: 60.0, 3: 75.0}
        mins_per_session = base_minutes.get(self.experience_level, 60.0)
        # weekly volume = sessions per week * minutes per session
        return round(self.workout_frequency * mins_per_session, 1)

    def __str__(self):
        """Readable summary of this member's profile."""
        return (
            "Member #" + str(self.member_id) + " | " + self.gender +
            ", Age " + str(int(self.age)) + " | Weight: " + str(self.weight_kg) +
            "kg | Height: " + str(self.height_m) + "m | BMI: " + str(self.bmi) +
            " (" + self.bmi_category + ") | " + self.experience_label +
            " | " + str(self.workout_frequency) + "x/week"
        )

    def __eq__(self, other):
        """
        Two members are equal if they have the same member_id.

        Used for deduplication and test assertions.
        """
        if not isinstance(other, GymMember):
            return NotImplemented
        return self.member_id == other.member_id

    def __repr__(self):
        """Developer-friendly string for debugging."""
        return ("GymMember(member_id=" + str(self.member_id) +
                ", age=" + str(self.age) +
                ", gender='" + self.gender + "'" +
                ", experience_level=" + str(self.experience_level) + ")")


if __name__ == "__main__":
    # quick test
    m = GymMember(1, 28, "Female", 65, 1.58, 23, 2, 4, 62)
    print(m)
    print("Max HR:", m.max_heart_rate, "bpm")
    print("HR Reserve:", m.heart_rate_reserve, "bpm")
    print("BMI Category:", m.bmi_category)
    print("Experience:", m.experience_label)
    print("Target 70% zone:", m.target_hr_zone(0.70), "bpm")
    print("Weekly volume estimate:", m.weekly_volume_estimate(), "min")
