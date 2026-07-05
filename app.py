"""
app.py

Tkinter desktop UI for Max Performance. Allows loading
the dataset, enter a member profile, and explore all the analysis
through a tabbed interface without touching the terminal or notebook.

Tabs:
    1. Member Setup   - enter profile, load dataset, see computed metrics
    2. Performance    - workout stats, calorie breakdown, top sessions
    3. Profiling      - BMI distribution, peer comparison, experience breakdown
    4. Charts         - generate and view all 5 matplotlib charts inline
    5. Run Tests      - run the pytest suite and see results

Imports from the existing project modules so all logic stays there.

Author: Saanie Naqvi
"""

import os
import sys
import subprocess
import threading
import tkinter as tk
from tkinter import ttk, messagebox, filedialog, scrolledtext

# make sure project modules are importable from the same directory
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
from visualizer import (
    plot_calories_by_workout_type,
    plot_bmi_by_experience,
    plot_hr_zone_distribution,
    plot_calories_vs_duration,
)
from data_loader import load_and_clean, build_member_from_row
from recommender import recommend

# -------------------------------------------------------------------
# Styling constants — keeping it clean and readable
# -------------------------------------------------------------------

BG       = "#1e1e2e"   # dark background
PANEL    = "#2a2a3e"   # slightly lighter panel
ACCENT   = "#7c6af7"   # purple accent
TEXT     = "#cdd6f4"   # light text
SUBTEXT  = "#a6adc8"   # muted text
SUCCESS  = "#a6e3a1"   # green
WARNING  = "#f9e2af"   # yellow
ERROR    = "#f38ba8"   # red
FONT     = ("Segoe UI", 10)
FONT_B   = ("Segoe UI", 10, "bold")
FONT_H   = ("Segoe UI", 13, "bold")
FONT_S   = ("Segoe UI", 9)
MONO     = ("Courier New", 9)

DEFAULT_DATA = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "data", "Fitness_Tracker_Dataset.csv"
)


# -------------------------------------------------------------------
# Helper widgets
# -------------------------------------------------------------------

def make_label(parent, text, font=FONT, fg=TEXT, **kw):
    """Create a styled label."""
    return tk.Label(parent, text=text, font=font, fg=fg, bg=PANEL, **kw)


def make_entry(parent, width=22, **kw):
    """Create a styled entry field."""
    e = tk.Entry(parent, width=width, font=FONT,
                 bg="#313244", fg=TEXT, insertbackground=TEXT,
                 relief="flat", bd=4, **kw)
    return e


def make_button(parent, text, command, color=ACCENT, **kw):
    """Create a styled button."""
    return tk.Button(
        parent, text=text, command=command,
        font=FONT_B, bg=color, fg="#1e1e2e",
        activebackground=TEXT, activeforeground="#1e1e2e",
        relief="flat", padx=12, pady=5, cursor="hand2", **kw
    )


def make_output(parent, height=18, width=80):
    """Create a read-only scrolled text box for output."""
    box = scrolledtext.ScrolledText(
        parent, height=height, width=width,
        font=MONO, bg="#181825", fg=TEXT,
        insertbackground=TEXT, relief="flat",
        state="disabled", wrap="word"
    )
    return box


def write_output(box: scrolledtext.ScrolledText, text: str, clear: bool = True):
    """Write text to a read-only ScrolledText widget."""
    box.config(state="normal")
    if clear:
        box.delete("1.0", "end")
    box.insert("end", text + "\n")
    box.see("end")
    box.config(state="disabled")


def append_output(box: scrolledtext.ScrolledText, text: str):
    """Append a line to an output box without clearing it."""
    write_output(box, text, clear=False)


# -------------------------------------------------------------------
# Main application class
# -------------------------------------------------------------------

class MaxPerformanceApp(tk.Tk):
    """
    Root Tkinter window for the Max Performance desktop app.

    Manages the shared state (member, tracker, dataframe) and
    coordinates all five tabs. Each tab is a separate Frame class
    that gets passed a reference to this root so tabs can share data.
    """

    def __init__(self):
        """Set up the root window, apply styling, and build all tabs."""
        super().__init__()

        self.title("Max Performance — Gym Analysis")
        self.geometry("920x640")
        self.minsize(820, 560)
        self.configure(bg=BG)
        self.resizable(True, True)

        # shared state across tabs
        self.member: GymMember | None = None
        self.tracker: PerformanceTracker | None = None
        self.df = None
        self.data_path = tk.StringVar(value=DEFAULT_DATA)

        # style the ttk notebook tabs
        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure("TNotebook",         background=BG, borderwidth=0)
        style.configure("TNotebook.Tab",     background=PANEL, foreground=SUBTEXT,
                        font=FONT_B, padding=[14, 6])
        style.map("TNotebook.Tab",
                  background=[("selected", ACCENT)],
                  foreground=[("selected", "#1e1e2e")])
        style.configure("TFrame", background=PANEL)

        # title bar
        header = tk.Frame(self, bg=ACCENT, height=48)
        header.pack(fill="x", side="top")
        header.pack_propagate(False)
        tk.Label(header, text="  ⚡ Max Performance",
                 font=("Segoe UI", 14, "bold"),
                 bg=ACCENT, fg="#1e1e2e").pack(side="left", pady=8)
        tk.Label(header, text="Gym Member Workout Analysis  ",
                 font=FONT_S, bg=ACCENT, fg="#1e1e2e").pack(side="right", pady=8)

        # notebook
        self.nb = ttk.Notebook(self)
        self.nb.pack(fill="both", expand=True, padx=10, pady=10)

        # build each tab
        self.tab_setup    = SetupTab(self.nb, self)
        self.tab_perf     = PerformanceTab(self.nb, self)
        self.tab_profile  = ProfilingTab(self.nb, self)
        self.tab_charts   = ChartsTab(self.nb, self)
        self.tab_rec      = RecommendationTab(self.nb, self)
        self.tab_tests    = TestsTab(self.nb, self)

        self.nb.add(self.tab_setup,   text="  Member Setup  ")
        self.nb.add(self.tab_perf,    text="  Performance   ")
        self.nb.add(self.tab_profile, text="  Profiling     ")
        self.nb.add(self.tab_charts,  text="  Charts        ")
        self.nb.add(self.tab_rec,     text=" ⚡ Workout Plan ")
        self.nb.add(self.tab_tests,   text="  Run Tests     ")

        # status bar
        self.status_var = tk.StringVar(value="Ready — load a dataset to begin.")
        status = tk.Label(self, textvariable=self.status_var,
                          font=FONT_S, bg=BG, fg=SUBTEXT, anchor="w")
        status.pack(fill="x", padx=14, pady=(0, 6))

    def set_status(self, msg: str):
        """Update the bottom status bar."""
        self.status_var.set(msg)
        self.update_idletasks()

    def load_data(self, filepath: str) -> bool:
        """
        Load and clean the dataset. Returns True on success.

        Called from SetupTab when the user clicks 'Load Dataset'.
        Updates self.df so all other tabs can access it.
        """
        try:
            self.df = load_and_clean(filepath)
            self.set_status(f"Dataset loaded: {len(self.df):,} records from '{os.path.basename(filepath)}'")
            return True
        except FileNotFoundError as e:
            messagebox.showerror("File Not Found", str(e))
            return False
        except Exception as e:
            messagebox.showerror("Load Error", f"Could not load dataset:\n{e}")
            return False

    def build_member_and_tracker(self, member: GymMember) -> bool:
        """
        Store the given GymMember and create a PerformanceTracker for it.

        Called from SetupTab after the user fills in the profile form.
        Returns True on success.
        """
        if self.df is None:
            messagebox.showwarning("No Data", "Load a dataset first.")
            return False
        try:
            self.member = member
            self.tracker = PerformanceTracker(member)
            self.tracker.load_data(self.data_path.get())
            self.set_status(
                f"Member #{member.member_id} loaded | "
                f"{member.experience_label} | "
                f"{len(self.tracker):,} records"
            )
            return True
        except Exception as e:
            messagebox.showerror("Error", f"Could not build tracker:\n{e}")
            return False


# -------------------------------------------------------------------
# Tab 1: Member Setup
# -------------------------------------------------------------------

class SetupTab(ttk.Frame):
    """
    Tab for loading the dataset and entering a member profile.

    Shows all computed metrics (max HR, HR zones, BMI category, etc.)
    after the member is created. Users can either fill in manual values
    or use the 'Load from Dataset Row' shortcut.
    """

    def __init__(self, parent, app: MaxPerformanceApp):
        """Set up the layout: left panel for inputs, right panel for output."""
        super().__init__(parent)
        self.app = app
        self.configure(style="TFrame")
        self._build()

    def _build(self):
        """Build the two-column layout for this tab."""
        # left column: inputs
        left = tk.Frame(self, bg=PANEL, padx=16, pady=12)
        left.pack(side="left", fill="y")

        make_label(left, "Dataset", font=FONT_H).grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 6))

        make_label(left, "CSV Path:").grid(row=1, column=0, sticky="w", pady=3)
        path_entry = tk.Entry(left, textvariable=self.app.data_path,
                              width=28, font=FONT_S, bg="#313244",
                              fg=TEXT, insertbackground=TEXT, relief="flat", bd=4)
        path_entry.grid(row=2, column=0, columnspan=2, sticky="ew", pady=2)

        btn_row = tk.Frame(left, bg=PANEL)
        btn_row.grid(row=3, column=0, columnspan=2, sticky="w", pady=4)
        make_button(btn_row, "Browse", self._browse).pack(side="left", padx=(0, 6))
        make_button(btn_row, "Load Dataset", self._load_dataset, color=SUCCESS).pack(side="left")

        ttk.Separator(left, orient="horizontal").grid(
            row=4, column=0, columnspan=2, sticky="ew", pady=10)

        make_label(left, "Member Profile", font=FONT_H).grid(
            row=5, column=0, columnspan=2, sticky="w", pady=(0, 6))

        # unit toggle — metric (kg/m) vs imperial (lbs/ft+in)
        self._use_metric = True
        unit_row = tk.Frame(left, bg=PANEL)
        unit_row.grid(row=5, column=1, sticky="e", pady=(0, 6))
        self._unit_btn = make_button(unit_row, "Switch to lbs/ft", self._toggle_units)
        self._unit_btn.pack()

        # input fields
        fields = [
            ("Member ID (int):",     "member_id",  "1"),
            ("Age (years):",         "age",         "28"),
            ("Gender:",              "gender",      "Female"),
            ("Weight (kg):",         "weight_kg",   "65.0"),
            ("Height (m):",          "height_m",    "1.68"),
            ("BMI:",                 "bmi",         "23.0"),
            ("Experience (1/2/3):",  "exp_level",   "2"),
            ("Workouts/week:",       "freq",        "4.0"),
            ("Resting HR (bpm):",    "resting",     "62.0"),
        ]
        self._vars = {}
        self._field_labels = {}
        for i, (label, key, default) in enumerate(fields):
            lbl = make_label(left, label)
            lbl.grid(row=6 + i, column=0, sticky="w", pady=2)
            self._field_labels[key] = lbl
            var = tk.StringVar(value=default)
            self._vars[key] = var
            make_entry(left, textvariable=var, width=14).grid(
                row=6 + i, column=1, sticky="w", padx=(6, 0), pady=2)

        # extra field for feet+inches when imperial
        self._ht_in_label = make_label(left, "Height (in):")
        self._ht_in_var = tk.StringVar(value="2")
        self._ht_in_entry = make_entry(left, textvariable=self._ht_in_var, width=14)

        btn_row2 = tk.Frame(left, bg=PANEL)
        btn_row2.grid(row=6 + len(fields) + 1, column=0, columnspan=2, sticky="w", pady=10)
        make_button(btn_row2, "Create Member", self._create_member, color=ACCENT).pack(side="left", padx=(0,6))
        make_button(btn_row2, "From Row 0", self._load_from_row, color=WARNING).pack(side="left")

        # right column: output
        right = tk.Frame(self, bg=PANEL, padx=10, pady=12)
        right.pack(side="left", fill="both", expand=True)

        make_label(right, "Member Metrics", font=FONT_H).pack(anchor="w", pady=(0, 6))
        self.output = make_output(right, height=28, width=55)
        self.output.pack(fill="both", expand=True)

        write_output(self.output,
            "Welcome to Max Performance!\n\n"
            "Steps to get started:\n"
            "  1. Confirm the CSV path or click Browse\n"
            "  2. Click 'Load Dataset'\n"
            "  3. Fill in a member profile\n"
            "  4. Click 'Create Member'\n"
            "  5. Explore the other tabs\n\n"
            "Tip: 'From Row 0' auto-fills the form\n"
            "from the first row of the dataset."
        )

    def _toggle_units(self):
        """Switch between metric (kg/m) and imperial (lbs/ft+in)."""
        # read current values before switching
        try:
            cur_wt = float(self._vars["weight_kg"].get())
            cur_ht = float(self._vars["height_m"].get())
        except ValueError:
            cur_wt = 65.0
            cur_ht = 1.68

        if self._use_metric:
            # switching TO imperial
            self._use_metric = False
            self._unit_btn.config(text="Switch to kg/m")
            self._field_labels["weight_kg"].config(text="Weight (lbs):")
            self._field_labels["height_m"].config(text="Height (ft):")
            # convert kg -> lbs
            lbs = round(cur_wt * 2.20462, 1)
            self._vars["weight_kg"].set(str(lbs))
            # convert m -> ft and inches
            total_in = cur_ht * 39.3701
            ft = int(total_in // 12)
            inches = round(total_in % 12, 1)
            self._vars["height_m"].set(str(ft))
            self._ht_in_var.set(str(inches))
            # show the inches entry
            self._ht_in_label.grid(row=10, column=0, sticky="w", pady=2)
            self._ht_in_entry.grid(row=10, column=1, sticky="w", padx=(6, 0), pady=2)
        else:
            # switching TO metric
            self._use_metric = True
            self._unit_btn.config(text="Switch to lbs/ft")
            self._field_labels["weight_kg"].config(text="Weight (kg):")
            self._field_labels["height_m"].config(text="Height (m):")
            # convert lbs -> kg
            kg = round(cur_wt / 2.20462, 1)
            self._vars["weight_kg"].set(str(kg))
            # convert ft+in -> m
            try:
                ft = float(self._vars["height_m"].get())
                inches = float(self._ht_in_var.get())
            except ValueError:
                ft, inches = 5.0, 6.0
            total_in = ft * 12 + inches
            m = round(total_in * 0.0254, 2)
            self._vars["height_m"].set(str(m))
            # hide inches entry
            self._ht_in_label.grid_remove()
            self._ht_in_entry.grid_remove()

    def _browse(self):
        """Open a file dialog to pick the CSV file."""
        path = filedialog.askopenfilename(
            title="Select dataset CSV",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
        )
        if path:
            self.app.data_path.set(path)

    def _load_dataset(self):
        """Load the dataset from the current path."""
        success = self.app.load_data(self.app.data_path.get())
        if success:
            write_output(self.output,
                f"Dataset loaded successfully!\n\n"
                f"  Records : {len(self.app.df):,}\n"
                f"  Columns : {len(self.app.df.columns)}\n"
                f"  Workout types: {', '.join(self.app.df['exercise_type'].unique())}\n\n"
                "Now enter a member profile and click 'Create Member'."
            )

    def _load_from_row(self):
        """Auto-fill the form from row 0 of the loaded dataset."""
        if self.app.df is None:
            messagebox.showwarning("No Data", "Load the dataset first.")
            return
        row = self.app.df.iloc[0]
        self._vars["age"].set(str(round(float(row["Age"]), 1)))
        self._vars["gender"].set(str(row["Gender"]))
        wt_kg = round(float(row["weight_kg"]), 1)
        ht_m = round(float(row["height_m"]), 2)
        if self._use_metric:
            self._vars["weight_kg"].set(str(wt_kg))
            self._vars["height_m"].set(str(ht_m))
        else:
            # convert to imperial for display
            self._vars["weight_kg"].set(str(round(wt_kg * 2.20462, 1)))
            total_in = ht_m * 39.3701
            ft = int(total_in // 12)
            inches = round(total_in % 12, 1)
            self._vars["height_m"].set(str(ft))
            self._ht_in_var.set(str(inches))
        self._vars["bmi"].set(str(round(float(row["BMI"]), 2)))
        self._vars["exp_level"].set(str(int(row["exp_level"])))
        self._vars["freq"].set(str(round(float(row["wk_freq"]), 1)))
        resting = row.get("resting_bpm", 65.0)
        self._vars["resting"].set(str(round(float(resting) if str(resting) != "nan" else 65.0, 1)))
        append_output(self.output, "\nForm filled from dataset row 0.")

    def _create_member(self):
        """Read the form fields and create a GymMember object."""
        try:
            # get weight and height, convert from imperial if needed
            if self._use_metric:
                weight_kg = float(self._vars["weight_kg"].get())
                height_m = float(self._vars["height_m"].get())
            else:
                # lbs -> kg
                weight_kg = round(float(self._vars["weight_kg"].get()) / 2.20462, 2)
                # ft + in -> m
                ft = float(self._vars["height_m"].get())
                inches = float(self._ht_in_var.get())
                height_m = round((ft * 12 + inches) * 0.0254, 3)

            member = GymMember(
                member_id=int(self._vars["member_id"].get()),
                age=float(self._vars["age"].get()),
                gender=self._vars["gender"].get(),
                weight_kg=weight_kg,
                height_m=height_m,
                bmi=float(self._vars["bmi"].get()),
                exp_level=int(self._vars["exp_level"].get()),
                wk_freq=float(self._vars["freq"].get()),
                resting_bpm=float(self._vars["resting"].get()),
            )
        except (ValueError, TypeError) as e:
            messagebox.showerror("Input Error", f"Check your inputs:\n{e}")
            return

        ok = self.app.build_member_and_tracker(member)
        if not ok:
            return

        m = self.app.member
        z65 = m.target_hr_zone(0.65)
        z70 = m.target_hr_zone(0.70)
        z80 = m.target_hr_zone(0.80)
        z85 = m.target_hr_zone(0.85)

        lines = [
            "Member Created Successfully!",
            "=" * 38,
            str(m),
            "",
            "Computed Metrics",
            "-" * 38,
            f"  Max Heart Rate    : {m.max_heart_rate} bpm",
            f"  HR Reserve        : {m.heart_rate_reserve} bpm",
            f"  BMI Category      : {m.bmi_category}",
            f"  Experience Level  : {m.experience_label}",
            f"  Weekly Vol. Est.  : {m.weekly_volume_estimate()} min/week",
            "",
            "Target HR Zones (Karvonen Formula)",
            "-" * 38,
            f"  65% intensity     : {z65[0]} - {z65[1]} bpm",
            f"  70% intensity     : {z70[0]} - {z70[1]} bpm",
            f"  80% intensity     : {z80[0]} - {z80[1]} bpm",
            f"  85% intensity     : {z85[0]} - {z85[1]} bpm",
            "",
            f"Tracker loaded with {len(self.app.tracker):,} records.",
            f"Peer group: {len(self.app.tracker.member_df)} members at same level.",
            "",
            "Head to the other tabs to explore the analysis.",
        ]
        write_output(self.output, "\n".join(lines))


# -------------------------------------------------------------------
# Tab 2: Performance Analysis
# -------------------------------------------------------------------

class PerformanceTab(ttk.Frame):
    """
    Tab for workout performance analysis.

    Shows overall stats, calories by workout type, top sessions,
    high-calorie session count, and a trend analysis.
    """

    def __init__(self, parent, app: MaxPerformanceApp):
        """Set up button row and output area."""
        super().__init__(parent)
        self.app = app
        self.configure(style="TFrame")
        self._build()

    def _build(self):
        """Build the layout for the performance tab."""
        top = tk.Frame(self, bg=PANEL, padx=12, pady=10)
        top.pack(fill="x")

        make_label(top, "Workout Performance Analysis", font=FONT_H).pack(side="left")

        btn_frame = tk.Frame(top, bg=PANEL)
        btn_frame.pack(side="right")
        make_button(btn_frame, "Overall Stats",     self._show_stats).pack(side="left", padx=3)
        make_button(btn_frame, "By Workout Type",   self._show_by_type).pack(side="left", padx=3)
        make_button(btn_frame, "Top 10 Sessions",   self._show_top).pack(side="left", padx=3)
        make_button(btn_frame, "Trend Analysis",    self._show_trend).pack(side="left", padx=3)

        self.output = make_output(self, height=30, width=90)
        self.output.pack(fill="both", expand=True, padx=12, pady=(0, 10))
        write_output(self.output, "Create a member in the Setup tab first, then use the buttons above.")

    def _check_ready(self) -> bool:
        """Return True if tracker is loaded, show warning otherwise."""
        if self.app.tracker is None:
            messagebox.showwarning("Not Ready", "Set up a member in the Setup tab first.")
            return False
        return True

    def _show_stats(self):
        """Show overall performance statistics."""
        if not self._check_ready(): return
        tracker = self.app.tracker

        lines = [
            "Overall Performance Statistics",
            "=" * 42,
        ]

        # use describe_series for each metric
        for col, label in [
            ("cal_burned", "Calories Burned"),
            ("duration_min",    "Session Duration (min)"),
            ("avg_heart_rate",  "Avg Heart Rate (bpm)"),
        ]:
            lines.append(describe_series(tracker.df[col], label))
            lines.append("")

        # water intake summary
        lines.append(f"Avg Water Intake : {tracker.df['water_liters'].mean():.2f} liters/session")

        # high-calorie sessions via generator
        high_cal = list(yield_high_calorie_sessions(tracker.df, threshold=1000.0))
        lines.append(f"Sessions > 1000 kcal : {len(high_cal)}")
        lines.append("")

        write_output(self.output, "\n".join(lines))

    def _show_by_type(self):
        """Show calorie and session breakdown by workout type."""
        if not self._check_ready(): return
        tracker = self.app.tracker

        cal_by_type = tracker.calories_by_workout_type()
        dist = tracker.workout_type_distribution()

        # total calories using aggregate_calories (reduce-based)
        total_cal = aggregate_calories(list(tracker.df["cal_burned"].dropna()))

        # exercise distribution proportions
        exercises = list(tracker.df["exercise_type"].dropna())
        dist_pct = exercise_dist(exercises)

        lines = [
            "Breakdown by Workout Type",
            "=" * 42,
            "",
            "Avg Calories per Session:",
            "-" * 28,
        ]
        for _, row in cal_by_type.iterrows():
            lines.append(
                "  " + str(row["exercise_type"]).ljust(20) +
                str(round(row["avg_cal"])).rjust(7) + " kcal avg   (" +
                str(int(row["sessions"])) + " sessions)"
            )

        lines += ["", "Total Calories (all sessions): " + str(round(total_cal, 0)) + " kcal"]

        lines += ["", "Exercise Distribution:", "-" * 28]
        for wtype, pct in dist_pct.items():
            bar = "|" * int(pct * 30)
            lines.append("  " + str(wtype).ljust(20) + " " + bar + " (" + str(round(pct * 100, 1)) + "%)")

        write_output(self.output, "\n".join(lines))

    def _show_top(self):
        """Show the top 10 highest-calorie sessions."""
        if not self._check_ready(): return
        tracker = self.app.tracker

        top = tracker.top_n_sessions(n=10, by="cal_burned")

        lines = ["Top 10 Sessions by Calories Burned", "=" * 42, ""]
        lines.append(f"  {'#':<4} {'Type':<22} {'Dur (min)':<12} {'Calories':<12} {'Avg HR':<10} {'Intensity'}")
        lines.append("  " + "-" * 66)

        for i, row in top.iterrows():
            lines.append(
                f"  {i+1:<4} {str(row['exercise_type']):<22} "
                f"{row['duration_min']:<12.1f} "
                f"{row['cal_burned']:<12.0f} "
                f"{row['avg_heart_rate']:<10.0f} "
                f"{str(row['intensity_level'])}"
            )

        write_output(self.output, "\n".join(lines))

    def _show_trend(self):
        """Show linear trend analysis across the dataset."""
        if not self._check_ready(): return
        tracker = self.app.tracker

        lines = ["Trend Analysis", "=" * 42, ""]

        for col, label in [
            ("cal_burned", "Calories Burned"),
            ("duration_min",    "Session Duration"),
            ("avg_heart_rate",  "Avg Heart Rate"),
            ("BMI",             "BMI"),
        ]:
            trend = compute_progress_trend(tracker.df[col])
            direction_icon = "↑" if trend["direction"] == "improving" else "↓" if trend["direction"] == "declining" else "→"
            lines.append(f"{label}")
            lines.append(f"  Direction : {direction_icon} {trend['direction'].title()}")
            lines.append(f"  Slope     : {trend['slope']}")
            lines.append(f"  R²        : {trend['r_squared']}")
            lines.append("")

        write_output(self.output, "\n".join(lines))


# -------------------------------------------------------------------
# Tab 3: Member Profiling
# -------------------------------------------------------------------

class ProfilingTab(ttk.Frame):
    """
    Tab for member profiling analysis.

    Shows BMI distribution, experience-level breakdown, peer comparison,
    and HR zone classification.
    """

    def __init__(self, parent, app: MaxPerformanceApp):
        """Set up button row and output area."""
        super().__init__(parent)
        self.app = app
        self.configure(style="TFrame")
        self._build()

    def _build(self):
        """Build the layout for the profiling tab."""
        top = tk.Frame(self, bg=PANEL, padx=12, pady=10)
        top.pack(fill="x")

        make_label(top, "Member Profiling", font=FONT_H).pack(side="left")

        btn_frame = tk.Frame(top, bg=PANEL)
        btn_frame.pack(side="right")
        make_button(btn_frame, "BMI Distribution",  self._show_bmi).pack(side="left", padx=3)
        make_button(btn_frame, "By Experience",     self._show_exp).pack(side="left", padx=3)
        make_button(btn_frame, "Peer Comparison",   self._show_peer).pack(side="left", padx=3)
        make_button(btn_frame, "HR Zones",          self._show_zones).pack(side="left", padx=3)

        self.output = make_output(self, height=30, width=90)
        self.output.pack(fill="both", expand=True, padx=12, pady=(0, 10))
        write_output(self.output, "Create a member in the Setup tab first, then use the buttons above.")

    def _check_ready(self) -> bool:
        if self.app.tracker is None:
            messagebox.showwarning("Not Ready", "Set up a member in the Setup tab first.")
            return False
        return True

    def _show_bmi(self):
        """Show BMI category distribution."""
        if not self._check_ready(): return
        tracker = self.app.tracker

        # compute BMI categories manually without importing bmi_category_distribution
        def categorize(bmi):
            if bmi < 18.5: return "Underweight"
            elif bmi < 25.0: return "Normal"
            elif bmi < 30.0: return "Overweight"
            else: return "Obese"

        all_cats = [categorize(b) for b in tracker.df["BMI"].dropna()]
        unique_cats = set(all_cats)
        cats = {cat: all_cats.count(cat) for cat in unique_cats}
        cats = dict(sorted(cats.items(), key=lambda x: x[1], reverse=True))
        total = sum(cats.values())

        lines = [
            "BMI Category Distribution",
            "=" * 42,
            f"  Total members : {total:,}",
            "",
        ]

        # visual bar for each category
        bar_colors = {
            "Underweight": "░",
            "Normal":      "█",
            "Overweight":  "▓",
            "Obese":       "▒",
        }
        for cat, count in cats.items():
            pct  = count / total * 100
            bar  = bar_colors.get(cat, "█") * int(pct / 2)
            lines.append(f"  {cat:<15} {bar:<30} {count:>5} ({pct:.1f}%)")

        lines += [
            "",
            "WHO Ranges:",
            "  Underweight : BMI < 18.5",
            "  Normal      : 18.5 – 24.9",
            "  Overweight  : 25.0 – 29.9",
            "  Obese       : BMI ≥ 30.0",
            "",
            f"This member's BMI: {self.app.member.bmi} ({self.app.member.bmi_category})",
        ]
        write_output(self.output, "\n".join(lines))

    def _show_exp(self):
        """Show average stats by experience level."""
        if not self._check_ready(): return
        tracker = self.app.tracker

        bmi_exp = tracker.bmi_by_experience()

        lines = [
            "Profile Breakdown by Experience Level",
            "=" * 42,
            "",
            f"  {'Level':<16} {'Avg BMI':<12} {'Avg Weight (kg)':<18} {'Members'}",
            "  " + "-" * 54,
        ]
        for _, row in bmi_exp.iterrows():
            lines.append(
                f"  {str(row['label']):<16} "
                f"{row['avg_bmi']:<12.2f} "
                f"{row['avg_weight']:<18.1f} "
                f"{int(row['count'])}"
            )

        intensity_labels = {1: "Beginner (Low)", 2: "Intermediate (Moderate)", 3: "Expert (High)"}
        lines += ["", "Intensity Labels:", "-" * 28]
        for level in [1, 2, 3]:
            lines.append("  Level " + str(level) + ": " + intensity_labels[level])

        write_output(self.output, "\n".join(lines))

    def _show_peer(self):
        """Show peer comparison for the current member."""
        if not self._check_ready(): return

        peer = self.app.tracker.peer_comparison()
        m    = self.app.member

        lines = [
            f"Peer Comparison — {peer['member_experience']}s",
            "=" * 42,
            f"  Peers in group     : {peer['peer_count']}",
            "",
            f"  {'Metric':<22} {'This Member':>14}  {'Peer Avg':>10}",
            "  " + "-" * 50,
            f"  {'BMI':<22} {peer['member_bmi']:>14.2f}  {peer['peer_avg_bmi']:>10.2f}",
            f"  {'Resting HR (bpm)':<22} {peer['member_resting_hr']:>14.1f}  {'—':>10}",
            f"  {'Workouts / week':<22} {peer['member_workout_freq']:>14.1f}  {'—':>10}",
            f"  {'Avg calories':<22} {'—':>14}  {peer['peer_avg_calories']:>10.0f}",
            f"  {'Avg duration (min)':<22} {'—':>14}  {peer['peer_avg_duration']:>10.1f}",
            f"  {'Avg heart rate':<22} {'—':>14}  {peer['peer_avg_hr']:>10.1f}",
            "",
            f"Weekly volume estimate: {m.weekly_volume_estimate()} min/week",
        ]

        # simple flag if BMI is above peer average
        if peer["member_bmi"] > peer["peer_avg_bmi"]:
            lines.append(f"\n  Note: Member BMI is above peer average by "
                         f"{peer['member_bmi'] - peer['peer_avg_bmi']:.2f} points.")
        else:
            lines.append(f"\n  Note: Member BMI is below peer average by "
                         f"{peer['peer_avg_bmi'] - peer['member_bmi']:.2f} points.")

        write_output(self.output, "\n".join(lines))

    def _show_zones(self):
        """Show HR zone distribution across all sessions."""
        if not self._check_ready(): return

        zones = self.app.tracker.hr_zone_distribution()
        m     = self.app.member
        total = sum(zones.values())

        lines = [
            f"Heart Rate Zone Distribution",
            f"(Based on member max HR: {m.max_heart_rate} bpm)",
            "=" * 42,
            "",
        ]
        zone_colors = ["░", "▒", "▓", "█", "■"]
        for i, (zone, count) in enumerate(zones.items()):
            pct = count / total * 100 if total > 0 else 0
            bar = zone_colors[min(i, 4)] * int(pct / 2)
            lines.append(f"  {zone:<28} {bar:<20} {count:>5} ({pct:.1f}%)")

        lines += [
            "",
            "Zone Definitions:",
            "  Zone 1 - Recovery    : < 60% max HR",
            "  Zone 2 - Aerobic Base: 60-70% max HR",
            "  Zone 3 - Aerobic     : 70-80% max HR",
            "  Zone 4 - Threshold   : 80-90% max HR",
            "  Zone 5 - Max Effort  : > 90% max HR",
        ]
        write_output(self.output, "\n".join(lines))


# -------------------------------------------------------------------
# Tab 4: Charts
# -------------------------------------------------------------------

class ChartsTab(ttk.Frame):
    """
    Tab for generating and viewing matplotlib charts.

    Each button generates a chart (saved to outputs/) and then
    displays a preview of it inline using a Tkinter Canvas.
    """

    def __init__(self, parent, app: MaxPerformanceApp):
        """Set up chart selector and preview area."""
        super().__init__(parent)
        self.app = app
        self.configure(style="TFrame")
        self._build()

    def _build(self):
        """Build the chart selector on the left and preview on the right."""
        left = tk.Frame(self, bg=PANEL, width=210, padx=14, pady=12)
        left.pack(side="left", fill="y")
        left.pack_propagate(False)

        make_label(left, "Charts", font=FONT_H).pack(anchor="w", pady=(0, 8))

        charts = [
            ("Calories by Workout Type", self._chart_calories),
            ("BMI Distribution",         self._chart_bmi),
            ("HR Zone Distribution",     self._chart_zones),
            ("Duration vs Calories",     self._chart_scatter),
            ("BMI by Experience Level",  self._chart_bmi_exp),
            ("Generate All Charts",      self._chart_all),
        ]
        for label, cmd in charts:
            make_button(left, label, cmd).pack(fill="x", pady=3)

        self._status = make_label(left, "", fg=SUBTEXT, font=FONT_S)
        self._status.pack(anchor="w", pady=(10, 0))

        # right side: image preview
        right = tk.Frame(self, bg="#181825", padx=6, pady=6)
        right.pack(side="left", fill="both", expand=True)

        self._canvas = tk.Canvas(right, bg="#181825", highlightthickness=0)
        self._canvas.pack(fill="both", expand=True)
        self._img_ref = None  # hold a reference to prevent garbage collection

    def _check_ready(self) -> bool:
        if self.app.tracker is None:
            messagebox.showwarning("Not Ready", "Set up a member in the Setup tab first.")
            return False
        return True

    def _show_chart(self, path: str):
        """Load a PNG and display it on the canvas."""
        try:
            from PIL import Image, ImageTk
            img = Image.open(path)
            canvas_w = self._canvas.winfo_width()
            canvas_h = self._canvas.winfo_height()
            if canvas_w < 10 or canvas_h < 10:
                canvas_w, canvas_h = 660, 440
            img.thumbnail((canvas_w, canvas_h), Image.LANCZOS)
            photo = ImageTk.PhotoImage(img)
            self._canvas.delete("all")
            self._canvas.create_image(canvas_w // 2, canvas_h // 2,
                                       image=photo, anchor="center")
            self._img_ref = photo
            self._status.config(text=f"Saved: {os.path.basename(path)}", fg=SUCCESS)
        except ImportError:
            # PIL not available - show a text message instead
            self._canvas.delete("all")
            self._canvas.create_text(
                300, 200,
                text=f"Chart saved to:\n{path}\n\n"
                     "(Install Pillow for inline preview:\n pip install Pillow)",
                fill=TEXT, font=FONT, justify="center"
            )
            self._status.config(text=f"Saved: {os.path.basename(path)}", fg=SUCCESS)

    def _chart_calories(self):
        if not self._check_ready(): return
        cal = self.app.tracker.calories_by_workout_type()
        path = plot_calories_by_workout_type(cal)
        self._show_chart(path)

    def _chart_bmi(self):
        if not self._check_ready(): return
        path = plot_bmi_by_experience(self.app.tracker.df)
        self._show_chart(path)

    def _chart_zones(self):
        if not self._check_ready(): return
        zones = self.app.tracker.hr_zone_distribution()
        path  = plot_hr_zone_distribution(zones)
        self._show_chart(path)

    def _chart_scatter(self):
        if not self._check_ready(): return
        path = plot_calories_vs_duration(self.app.tracker.df)
        self._show_chart(path)

    def _chart_bmi_exp(self):
        if not self._check_ready(): return
        bmi_exp = self.app.tracker.bmi_by_experience()
        path    = plot_bmi_by_experience(bmi_exp)
        self._show_chart(path)

    def _chart_all(self):
        """Generate all 5 charts in sequence."""
        if not self._check_ready(): return
        self._status.config(text="Generating all charts...", fg=WARNING)
        self.update()
        self._chart_calories()
        self._chart_bmi()
        self._chart_zones()
        self._chart_scatter()
        self._chart_bmi_exp()
        self._status.config(text="All 5 charts generated.", fg=SUCCESS)


# -------------------------------------------------------------------
# -------------------------------------------------------------------
# Tab 5: Workout Recommendations
# -------------------------------------------------------------------

class RecommendationTab(ttk.Frame):
    """
    Generates a personalised weekly workout plan and health advice
    based on the member's BMI, experience level, and HR metrics.
    """

    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app
        self.configure(style="TFrame")
        self._build()

    def _build(self):
        top = tk.Frame(self, bg=PANEL, padx=12, pady=10)
        top.pack(fill="x")

        make_label(top, "⚡ Personalised Workout Plan", font=FONT_H).pack(side="left")

        btn_frame = tk.Frame(top, bg=PANEL)
        btn_frame.pack(side="right")
        make_button(btn_frame, "Generate Plan", self._generate, color=ACCENT).pack(side="left", padx=3)
        make_button(btn_frame, "Weekly Schedule", self._show_week, color=SUCCESS).pack(side="left", padx=3)
        make_button(btn_frame, "Health Advice", self._show_advice, color=WARNING).pack(side="left", padx=3)
        make_button(btn_frame, "HR Targets", self._show_hr).pack(side="left", padx=3)

        self.output = make_output(self, height=32, width=90)
        self.output.pack(fill="both", expand=True, padx=12, pady=(0, 10))
        write_output(self.output,
            "Create a member profile in the Setup tab first.\n\n"
            "Then click 'Generate Plan' to get a personalised\n"
            "weekly workout schedule and health advice based\n"
            "on your BMI, experience level, and heart rate metrics."
        )
        self._rec = None

    def _check_ready(self):
        if self.app.member is None:
            messagebox.showwarning("Not Ready", "Set up a member in the Setup tab first.")
            return False
        return True

    def _generate(self):
        if not self._check_ready(): return
        self._rec = recommend(self.app.member)
        m = self.app.member
        r = self._rec

        DAY_ICONS = {"Strength": "🏋", "Cardio": "🏃", "HIIT": "⚡", "Yoga": "🧘", "Rest": "💤"}

        lines = [
            "PERSONALISED WORKOUT PLAN",
            "=" * 55,
            f"  Member        : #{m.member_id} · {m.gender} · Age {int(m.age)}",
            f"  BMI           : {m.bmi} ({r['bmi_cat']})",
            f"  Experience    : {m.experience_label}",
            f"  Goal          : {r['goal_label']}",
            "",
            "WEEKLY PLAN SUMMARY",
            "-" * 55,
        ]

        for day, info in r["week"].items():
            icon = DAY_ICONS.get(info["type"], "·")
            if info["type"] == "Rest":
                lines.append(f"  {day:<10} {icon}  Rest day — active recovery recommended")
            else:
                lines.append(f"  {day:<10} {icon}  {info['type']:<12} {info['duration']} min  ({info.get('intensity','').title()})")

        lines += [
            "",
            f"  Primary focus   : {r['primary']}",
            f"  Secondary       : {r['secondary']}",
            f"  Recommended freq: {r['freq'][0]}–{r['freq'][1]} sessions/week",
            "",
            "Click 'Weekly Schedule' for exercises · 'Health Advice' for tips · 'HR Targets' for zones",
        ]
        write_output(self.output, "\n".join(lines))

    def _show_week(self):
        if not self._check_ready(): return
        if self._rec is None:
            self._generate()
            return

        r = self._rec
        lines = [
            "WEEKLY WORKOUT SCHEDULE",
            "=" * 55,
            "",
        ]
        for day, info in r["week"].items():
            lines.append(f"── {day.upper()} ──────────────────────────────────────")
            if info["type"] == "Rest":
                lines.append(f"  REST DAY")
                lines.append(f"  · Light walk or stretching only")
                lines.append(f"  · Focus on sleep and hydration")
            else:
                lines.append(f"  {info['type'].upper()} · {info['duration']} min · {info.get('intensity','').title()} intensity")
                for ex in info["exercises"]:
                    lines.append(f"    › {ex}")
            lines.append("")

        write_output(self.output, "\n".join(lines))

    def _show_advice(self):
        if not self._check_ready(): return
        if self._rec is None:
            self._generate()
            return

        r = self._rec
        m = self.app.member
        lines = [
            "HEALTH ADVICE & COACHING TIPS",
            "=" * 55,
            f"  Tailored for BMI category: {r['bmi_cat']}",
            f"  Goal: {r['goal_label']}",
            "",
        ]
        for i, tip in enumerate(r["advice"], 1):
            lines.append(f"  {i}. {tip}")
            lines.append("")

        lines += [
            "DATASET BENCHMARKS (1,576 members)",
            "-" * 55,
            f"  Avg calories/session : 1,038 kcal",
            f"  Avg session duration : 83.5 min",
            f"  Avg heart rate       : 146 bpm",
            f"  Avg water intake     : 2.4 L/session",
            "",
            "  Your targets:",
            f"    Calories/session   : {int(900 + m.experience_level * 80)}–{int(1050 + m.experience_level * 100)} kcal",
            f"    Duration           : {r['freq'][0] * 45}–{r['freq'][1] * 60} min/week total",
            f"    Water intake       : 2.0–3.0 L/session",
        ]
        write_output(self.output, "\n".join(lines))

    def _show_hr(self):
        if not self._check_ready(): return
        if self._rec is None:
            self._generate()
            return

        r = self._rec
        t = r["targets"]
        m = self.app.member
        lines = [
            "HEART RATE TARGETS (Karvonen Formula)",
            "=" * 55,
            f"  Max HR (220 - age)   : {t['mhr']} bpm",
            f"  Resting HR           : {m.resting_bpm} bpm",
            f"  HR Reserve           : {t['mhr'] - int(m.resting_bpm)} bpm",
            "",
            "  ZONES",
            "  " + "-" * 40,
            f"  Zone 2 (Aerobic base)   : {t['zone2_low']}–{t['zone2_high']} bpm  ← fat burning",
            f"  Zone 3 (Aerobic)        : {t['zone3_low']}–{t['zone3_high']} bpm  ← cardio fitness",
            f"  Zone 4 (Threshold)      : {t['zone4_low']}–{t['zone4_high']} bpm  ← performance",
            "",
            f"  RECOMMENDED ZONE FOR YOUR GOAL",
            "  " + "-" * 40,
            f"  Target zone  : {t['hr_zone']}",
            "",
            "  WHAT THIS MEANS",
            "  " + "-" * 40,
            "  Zone 2: Long steady sessions, burns fat, builds aerobic base.",
            "  Zone 3: Moderate effort, improves cardiovascular fitness.",
            "  Zone 4: Hard effort, increases VO2 max and performance.",
            "",
            "  TIP: Buy a HR monitor or use smartwatch — training",
            "  in the right zone is the #1 factor in results.",
        ]
        write_output(self.output, "\n".join(lines))


# -------------------------------------------------------------------
# Tab 6: Run Tests
# -------------------------------------------------------------------

class TestsTab(ttk.Frame):
    """
    Tab for running the pytest test suite directly from the UI.

    Runs tests in a background thread so the UI doesn't freeze.
    Shows pass/fail counts and highlights any failures.
    """

    def __init__(self, parent, app: MaxPerformanceApp):
        """Set up the run button and output area."""
        super().__init__(parent)
        self.app = app
        self.configure(style="TFrame")
        self._build()

    def _build(self):
        """Build the run button and scrolled output area."""
        top = tk.Frame(self, bg=PANEL, padx=12, pady=10)
        top.pack(fill="x")

        make_label(top, "Pytest Test Suite", font=FONT_H).pack(side="left")

        btn_frame = tk.Frame(top, bg=PANEL)
        btn_frame.pack(side="right")
        make_button(btn_frame, "Run All Tests",
                    self._run_tests, color=SUCCESS).pack(side="left", padx=3)
        make_button(btn_frame, "GymMember Tests Only",
                    self._run_athlete_tests, color=ACCENT).pack(side="left", padx=3)

        self.output = make_output(self, height=32, width=90)
        self.output.pack(fill="both", expand=True, padx=12, pady=(0, 10))
        write_output(self.output,
            "Click 'Run All Tests' to run the full test suite.\n"
            "Or 'GymMember Tests Only' to run just tests/test_athlete.py.\n\n"
            "Tests run in the background so the UI stays responsive."
        )

    def _run_tests(self):
        """Run the full pytest suite in a background thread."""
        self._start_run(["python", "-m", "pytest", "tests/", "-v", "--tb=short"])

    def _run_athlete_tests(self):
        """Run only test_athlete.py in a background thread."""
        self._start_run(["python", "-m", "pytest", "tests/test_athlete.py", "-v", "--tb=short"])

    def _start_run(self, cmd: list):
        """Kick off a subprocess in a daemon thread so the UI doesn't block."""
        write_output(self.output, "Running tests...\n")
        self.app.set_status("Running test suite...")

        def _run():
            """Run pytest and stream output back to the text box."""
            project_dir = os.path.dirname(os.path.abspath(__file__))
            result = subprocess.run(
                cmd, capture_output=True, text=True, cwd=project_dir
            )
            output = result.stdout + (result.stderr if result.stderr else "")

            # color code the summary line
            lines = output.split("\n")
            summary = next((l for l in reversed(lines) if "passed" in l or "failed" in l), "")

            self.output.after(0, lambda: write_output(self.output, output))

            if "failed" in summary:
                self.app.after(0, lambda: self.app.set_status(f"Tests done — {summary.strip()}"))
            else:
                self.app.after(0, lambda: self.app.set_status(f"Tests done — {summary.strip()}"))

        t = threading.Thread(target=_run, daemon=True)
        t.start()


# -------------------------------------------------------------------
# Entry point
# -------------------------------------------------------------------

if __name__ == "__main__":
    app = MaxPerformanceApp()
    app.mainloop()
