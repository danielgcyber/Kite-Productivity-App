import tkinter as tk
from tkinter import messagebox, ttk
import json
import os
import time
import threading
from datetime import datetime, timedelta
import sys

# Optional safe import
try:
    import psutil
    HAS_PSUTIL = True
except ImportError:
    HAS_PSUTIL = False

# ----------------------------
# CONFIG
# ----------------------------
APP_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH = os.path.join(APP_DIR, "kite_profile.json")
LOGS_DIR = os.path.join(APP_DIR, "kite_logs")
os.makedirs(LOGS_DIR, exist_ok=True)

BG = "#0c0c18"
PANEL = "#1a1a2e"
ACCENT = "#4cc9f0"
TEXT = "#e0e0ff"
MUTED = "#8a8aa8"
RED = "#f72585"
GREEN = "#4ade80"
YELLOW = "#facc15"

# Glow intensity cycle
GLOW_COLORS = [
    "#4cc9f0",  # normal
    "#5fd0f5",
    "#73d8fa",
    "#86dff0",  # peak glow
    "#73d8fa",
    "#5fd0f5",
]
GLOW_CYCLE = len(GLOW_COLORS)

# ----------------------------
# CORE LOGIC
# ----------------------------
def calculate_bmr(gender, weight_lbs, height_ft, height_in, age):
    weight_kg = weight_lbs * 0.453592
    height_cm = (height_ft * 12 + height_in) * 2.54
    if gender == "Male":
        return 10 * weight_kg + 6.25 * height_cm - 5 * age + 5
    else:
        return 10 * weight_kg + 6.25 * height_cm - 5 * age - 161

def get_break_action(session_count, profile):
    bmr = calculate_bmr(
        profile["gender"], profile["weight_lbs"],
        profile["height_ft"], profile["height_in"], profile["age"]
    )
    energy_factor = bmr / 2000

    if session_count % 5 == 0:
        return "🚻 Bathroom break + hydrate + look outside (natural light boosts focus!)"
    elif session_count % 4 == 0:
        if energy_factor > 1.1:
            return "🥜 Protein snack + yerba mate or tea"
        else:
            return "💧 Drink water + 2-min stretch (movement lifts alertness!)"
    elif session_count % 3 == 0:
        return "😊 Smile in mirror + 3 deep breaths (resets mental state!)"
    elif session_count % 2 == 0:
        return "👀 20-20-20 rule: every 20 min, look 20 ft away for 20 sec"
    else:
        if profile["age"] < 30:
            return "⚡ Quick walk + upbeat song (dopamine reset!)"
        else:
            return "🧘‍♂️ 3-min mindfulness (lowers stress, sharpens focus)"

def water_goal(lbs):
    return round((lbs * 0.75) / 33.8, 1)

# ----------------------------
# KITE CANVAS (Pixel-Perfect Fill)
# ----------------------------
class KiteCanvas:
    def __init__(self, parent, width=220, height=220):
        self.canvas = tk.Canvas(parent, width=width, height=height, bg=BG, highlightthickness=0)
        self.width = width
        self.height = height
        self.time_text = ""
        self.percent = 0
        self.glow_index = 0
        self.session_active = False
        self.draw()
        self.canvas.pack()

    def set_active(self, active):
        self.session_active = active
        if active:
            self._animate_glow()

    def _animate_glow(self):
        if not self.session_active:
            return
        self.glow_index = (self.glow_index + 1) % GLOW_CYCLE
        self.draw()
        self.canvas.after(200, self._animate_glow)

    def update(self, seconds_left, total_seconds, time_text):
        self.time_text = time_text
        self.percent = max(0, min(100, 100 - (seconds_left / total_seconds * 100)))
        self.draw()

    def _get_kite_x_bounds(self, y, cx, cy):
        """Return (x_left, x_right) of kite at given y."""
        if y < cy - 60 or y > cy + 60:
            return None, None
        if y <= cy:
            t = (y - (cy - 60)) / 60
            half_width = 40 * t
        else:
            t = ((cy + 60) - y) / 60
            half_width = 40 * t
        return cx - half_width, cx + half_width

    def draw(self):
        self.canvas.delete("all")
        cx, cy = self.width // 2, self.height // 2

        top = (cx, cy - 60)
        right = (cx + 40, cy)
        bottom = (cx, cy + 60)
        left = (cx - 40, cy)
        self.canvas.create_polygon([top, right, bottom, left], outline=MUTED, width=2, fill=BG)

        if self.percent > 0:
            fill_color = GLOW_COLORS[self.glow_index] if self.session_active else ACCENT
            fill_height = (self.percent / 100.0) * 120
            y_start = cy + 60
            y_end = y_start - fill_height

            step = 1
            y = y_start
            while y >= y_end and y >= cy - 60:
                x_left, x_right = self._get_kite_x_bounds(y, cx, cy)
                if x_left is not None and x_right is not None:
                    self.canvas.create_line(x_left, y, x_right, y, fill=fill_color, width=step)
                y -= step

        tail_start_y = cy + 60
        for i in range(6):
            y1 = tail_start_y + i * 7
            y2 = tail_start_y + (i + 1) * 7
            x_offset = 4 if i % 2 == 0 else -4
            self.canvas.create_line(cx, y1, cx + x_offset, y2, fill=MUTED, width=1.5)

        if self.time_text:
            self.canvas.create_text(cx, cy, text=self.time_text, fill=TEXT, font=("Segoe UI", 20, "bold"))

# ----------------------------
# PROFILE SETUP FRAME
# ----------------------------
class ProfileSetupFrame(tk.Frame):
    def __init__(self, parent, on_complete):
        super().__init__(parent, bg=BG)
        self.on_complete = on_complete

        tk.Label(self, text="🪁 Welcome to Kite", font=("Segoe UI", 18, "bold"), fg=ACCENT, bg=BG).pack(pady=(20, 8))
        tk.Label(self, text="Complete your profile for personalized, productivity-optimized breaks",
                 font=("Segoe UI", 10), fg=MUTED, bg=BG, wraplength=380).pack()

        tk.Label(self, text="Gender:", font=("Segoe UI", 11), fg=TEXT, bg=BG).pack(pady=(12, 4))
        self.gender_var = tk.StringVar(value="Male")
        gen_frame = tk.Frame(self, bg=BG)
        for g in ["Male", "Female", "Other"]:
            tk.Radiobutton(gen_frame, text=g, variable=self.gender_var, value=g, bg=BG, fg=TEXT,
                           selectcolor=PANEL, activebackground=BG).pack(side="left", padx=8)
        gen_frame.pack()

        tk.Label(self, text="Age:", font=("Segoe UI", 11), fg=TEXT, bg=BG).pack(pady=(10, 4))
        self.age_var = tk.StringVar(value="25")
        tk.Spinbox(self, from_=13, to=100, textvariable=self.age_var, width=6, font=("Segoe UI", 11)).pack()

        tk.Label(self, text="Height:", font=("Segoe UI", 11), fg=TEXT, bg=BG).pack(pady=(10, 4))
        height_frame = tk.Frame(self, bg=BG)
        self.ft_var = tk.StringVar(value="5")
        self.in_var = tk.StringVar(value="8")
        ft_combo = ttk.Combobox(height_frame, textvariable=self.ft_var, values=[str(i) for i in range(4, 8)], width=5, state="readonly")
        in_combo = ttk.Combobox(height_frame, textvariable=self.in_var, values=[str(i) for i in range(0, 12)], width=5, state="readonly")
        ft_combo.pack(side="left")
        tk.Label(height_frame, text="'", bg=BG, fg=TEXT).pack(side="left")
        in_combo.pack(side="left")
        tk.Label(height_frame, text='"', bg=BG, fg=TEXT).pack(side="left")
        height_frame.pack()

        tk.Label(self, text="Weight (lbs):", font=("Segoe UI", 11), fg=TEXT, bg=BG).pack(pady=(10, 4))
        self.weight_var = tk.StringVar(value="150")
        tk.Entry(self, textvariable=self.weight_var, width=10, font=("Segoe UI", 11)).pack()

        tk.Button(
            self, text="✅ Save & Launch Kite", command=self.save_profile,
            bg=GREEN, fg="#000", font=("Segoe UI", 12, "bold"), padx=20, pady=10
        ).pack(pady=25)

    def save_profile(self):
        try:
            profile = {
                "gender": self.gender_var.get(),
                "age": int(self.age_var.get()),
                "height_ft": int(self.ft_var.get()),
                "height_in": int(self.in_var.get()),
                "weight_lbs": float(self.weight_var.get())
            }
            with open(CONFIG_PATH, 'w') as f:
                json.dump(profile, f, indent=2)
            self.on_complete(profile)
        except Exception as e:
            messagebox.showerror("Input Error", "Please enter valid numbers for age and weight.")

# ----------------------------
# MAIN APP FRAME
# ----------------------------
class KiteAppFrame(tk.Frame):
    def __init__(self, parent, profile):
        super().__init__(parent, bg=BG)
        self.profile = profile
        self.session_active = False
        self.session_paused = False
        self.timer_thread = None
        self.seconds_left = 0
        self.total_seconds = 600
        self.log_data = self.load_log()

        tk.Label(self, text="🪁 Kite", font=("Segoe UI", 26, "bold"), fg=ACCENT, bg=BG).pack(pady=(15, 5))
        tk.Label(self, text="Optimized for productivity", font=("Segoe UI", 11), fg=MUTED, bg=BG).pack()

        dur_frame = tk.Frame(self, bg=BG)
        dur_frame.pack(pady=10)
        tk.Label(dur_frame, text="Session Length:", fg=MUTED, bg=BG, font=("Segoe UI", 11)).pack(side="left")
        self.duration_var = tk.StringVar(value="10")
        for val in ["10", "20", "30"]:
            tk.Radiobutton(dur_frame, text=f"{val} min", variable=self.duration_var, value=val,
                           bg=BG, fg=TEXT, selectcolor=PANEL, activebackground=BG).pack(side="left", padx=10)

        self.kite_canvas = KiteCanvas(self)

        self.status_label = tk.Label(
            self, text="Select duration and start your focus session.",
            font=("Segoe UI", 12), fg=TEXT, bg=BG, wraplength=580
        )
        self.status_label.pack(pady=10)

        btn_frame = tk.Frame(self, bg=BG)
        btn_frame.pack(pady=15)
        self.start_btn = tk.Button(btn_frame, text="▶ Start Focus", command=self.start_session,
                                   font=("Segoe UI", 12, "bold"), bg=GREEN, fg="#000", padx=20, pady=8)
        self.start_btn.pack(side="left", padx=8)

        # Pause/Resume button (replaces "Break Now")
        self.pause_btn = tk.Button(btn_frame, text="⏸ Pause", command=self.toggle_pause,
                                   font=("Segoe UI", 12, "bold"), bg=YELLOW, fg="#000", padx=20, pady=8, state="disabled")
        self.pause_btn.pack(side="left", padx=8)

        self.report_btn = tk.Button(btn_frame, text="📊 Analytics", command=self.show_analytics,
                                    font=("Segoe UI", 12, "bold"), bg=ACCENT, fg="#000", padx=20, pady=8)
        self.report_btn.pack(side="left", padx=8)

        self.end_btn = tk.Button(btn_frame, text="⏹ End Day", command=self.end_session,
                                 font=("Segoe UI", 12, "bold"), bg=RED, fg="#fff", padx=20, pady=8)
        self.end_btn.pack(side="left", padx=8)

        water = water_goal(self.profile["weight_lbs"])
        ht = f"{self.profile['height_ft']}′{self.profile['height_in']}″"
        footer_text = f"Profile: {self.profile['gender']}, {self.profile['age']}y | {ht}, {int(self.profile['weight_lbs'])} lbs | Water Goal: {water}L"
        tk.Label(self, text=footer_text, font=("Segoe UI", 9), fg=MUTED, bg=BG).pack(side="bottom", pady=10)

    def load_log(self):
        path = os.path.join(LOGS_DIR, f"{datetime.now().strftime('%Y-%m-%d')}.json")
        if os.path.exists(path):
            try:
                with open(path, 'r') as f:
                    return json.load(f)
            except:
                pass
        return {"date": datetime.now().strftime("%Y-%m-%d"), "sessions": [], "moods": []}

    def save_log(self, data):
        path = os.path.join(LOGS_DIR, f"{datetime.now().strftime('%Y-%m-%d')}.json")
        try:
            temp = path + ".tmp"
            with open(temp, 'w') as f:
                json.dump(data, f, indent=2)
            os.replace(temp, path)
        except:
            pass

    def start_session(self):
        if self.session_active:
            return
        try:
            mins = int(self.duration_var.get())
            self.total_seconds = mins * 60
            self.seconds_left = self.total_seconds
            self.session_active = True
            self.session_paused = False
            self.kite_canvas.set_active(True)
            self.start_btn.config(state="disabled", bg="#555")
            self.pause_btn.config(state="normal", bg=YELLOW, text="⏸ Pause")
            self.status_label.config(text=f"Focusing for {mins} minutes... Use Pause to take a break.")
            
            self.kite_canvas.time_text = f"{mins:02}:00"
            self.kite_canvas.percent = 0
            self.kite_canvas.draw()
            
            self.timer_thread = threading.Thread(target=self.run_timer, daemon=True)
            self.timer_thread.start()
        except Exception as e:
            messagebox.showerror("Error", f"Invalid input: {e}")

    def run_timer(self):
        while self.seconds_left > 0 and self.session_active and not self.session_paused:
            time.sleep(1)
            if not self.session_paused and self.session_active:
                self.seconds_left -= 1
                mins, secs = divmod(self.seconds_left, 60)
                time_str = f"{mins:02}:{secs:02}"
                self.after(0, lambda t=time_str: self.update_kite(t))
        if self.session_active and not self.session_paused:
            self.after(0, self.complete_session)

    def update_kite(self, time_str):
        self.kite_canvas.update(self.seconds_left, self.total_seconds, time_str)

    def complete_session(self):
        self._record_session()
        self._show_completion()

    def toggle_pause(self):
        if not self.session_active:
            return
        if self.session_paused:
            # Resume
            self.session_paused = False
            self.pause_btn.config(text="⏸ Pause", bg=YELLOW)
            self.status_label.config(text="Session resumed.")
            self.kite_canvas.set_active(True)
            # Restart timer thread
            self.timer_thread = threading.Thread(target=self.run_timer, daemon=True)
            self.timer_thread.start()
        else:
            # Pause → prompt mood
            self.session_paused = True
            self.kite_canvas.set_active(False)
            self.pause_btn.config(text="▶ Resume", bg=GREEN)
            self.status_label.config(text="Session paused. How are you feeling?")
            self.ask_mood_on_pause()

    def ask_mood_on_pause(self):
        mood_win = tk.Toplevel(self)
        mood_win.title("How are you feeling?")
        mood_win.geometry("360x200")
        mood_win.configure(bg=PANEL)
        mood_win.transient(self)
        mood_win.grab_set()

        tk.Label(mood_win, text="Rate your current mood:\n1 = Exhausted/Stressed ←→ 10 = Energized/Happy",
                 font=("Segoe UI", 11), fg=TEXT, bg=PANEL, justify="center").pack(pady=15)

        mood_var = tk.IntVar(value=5)
        mood_scale = tk.Scale(
            mood_win, from_=1, to=10, orient="horizontal",
            variable=mood_var, length=300,
            bg=PANEL, fg=TEXT, highlightthickness=0,
            troughcolor=BG, activebackground=ACCENT
        )
        mood_scale.pack(pady=10)

        def submit_mood():
            mood_score = mood_var.get()
            self.log_data["moods"].append({
                "time": datetime.now().isoformat(),
                "mood_score": mood_score  # 1-10
            })
            self.save_log(self.log_data)
            mood_win.destroy()

        tk.Button(
            mood_win, text="✅ Submit & Continue", command=submit_mood,
            bg=GREEN, fg="#000", font=("Segoe UI", 10, "bold"), padx=15, pady=5
        ).pack(pady=10)

    def _record_session(self):
        session_mins = (self.total_seconds - self.seconds_left) // 60
        if session_mins == 0:
            session_mins = 1
        self.log_data["sessions"].append({
            "duration_min": session_mins,
            "completed_at": datetime.now().isoformat()
        })
        self.save_log(self.log_data)

    def _show_completion(self):
        session_count = len(self.log_data["sessions"])
        action = get_break_action(session_count, self.profile)
        self.status_label.config(text=f"✅ Session #{session_count} complete!\n\n{action}")
        self._reset_ui()

    def _reset_ui(self):
        self.session_active = False
        self.session_paused = False
        self.kite_canvas.set_active(False)
        self.start_btn.config(state="normal", bg=GREEN)
        self.pause_btn.config(state="disabled", bg="#555", text="⏸ Pause")
        self.kite_canvas.time_text = ""
        self.kite_canvas.percent = 0
        self.kite_canvas.draw()

    def load_all_logs(self, period="daily"):
        now = datetime.now()
        if period == "daily":
            dates = [now.strftime("%Y-%m-%d")]
        elif period == "weekly":
            dates = [(now - timedelta(days=i)).strftime("%Y-%m-%d") for i in range(7)]
        elif period == "monthly":
            dates = [(now - timedelta(days=i)).strftime("%Y-%m-%d") for i in range(30)]
        else:
            dates = [now.strftime("%Y-%m-%d")]

        all_sessions = []
        all_moods = []

        for date_str in dates:
            path = os.path.join(LOGS_DIR, f"{date_str}.json")
            if os.path.exists(path):
                try:
                    with open(path, 'r') as f:
                        data = json.load(f)
                        all_sessions.extend(data.get("sessions", []))
                        all_moods.extend(data.get("moods", []))
                except:
                    continue

        all_sessions.sort(key=lambda x: x["completed_at"])
        all_moods.sort(key=lambda x: x["time"])
        return all_sessions, all_moods

    def show_analytics(self):
        chart_win = tk.Toplevel(self)
        chart_win.title("Kite Analytics")
        chart_win.geometry("700x500")
        chart_win.configure(bg=BG)

        control_frame = tk.Frame(chart_win, bg=BG)
        control_frame.pack(pady=10, fill="x", padx=20)

        period_var = tk.StringVar(value="daily")
        for p, txt in [("daily", "Today"), ("weekly", "Last 7 Days"), ("monthly", "Last 30 Days")]:
            tk.Radiobutton(control_frame, text=txt, variable=period_var, value=p,
                           bg=BG, fg=TEXT, selectcolor=PANEL, activebackground=BG,
                           command=lambda: self._refresh_analytics(canvas_frame, period_var.get())).pack(side="left", padx=10)

        clear_btn = tk.Button(control_frame, text="🗑️ Clear All Logs", command=self._confirm_clear_logs,
                              bg=RED, fg="white", font=("Segoe UI", 9), padx=8, pady=2)
        clear_btn.pack(side="right")

        canvas_frame = tk.Frame(chart_win, bg=PANEL)
        canvas_frame.pack(fill="both", expand=True, padx=20, pady=(0, 20))

        self._refresh_analytics(canvas_frame, "daily")

    def _refresh_analytics(self, parent, period):
        for widget in parent.winfo_children():
            widget.destroy()

        sessions, moods = self.load_all_logs(period)

        if not sessions:
            tk.Label(parent, text="No session data yet.", fg=MUTED, bg=PANEL, font=("Segoe UI", 14)).pack(expand=True)
            return

        # Map mood_score (1-10) to graph Y (0-3)
        def score_to_graph_level(score):
            if score <= 2:
                return 0  # angry
            elif score <= 4:
                return 1  # tired
            elif score <= 7:
                return 2  # neutral
            else:
                return 3  # happy

        session_data = []
        mood_index = 0
        moods_sorted = sorted(moods, key=lambda x: x["time"])

        for sess in sessions:
            sess_time = datetime.fromisoformat(sess["completed_at"])
            mood_val = 5  # default mid
            while mood_index < len(moods_sorted) and datetime.fromisoformat(moods_sorted[mood_index]["time"]) <= sess_time:
                raw_score = moods_sorted[mood_index].get("mood_score", 5)
                mood_val = score_to_graph_level(raw_score)
                mood_index += 1
            session_data.append((mood_val, sess["duration_min"]))

        canvas = tk.Canvas(parent, bg=PANEL, highlightthickness=0)
        canvas.pack(fill="both", expand=True, padx=20, pady=20)

        parent.update_idletasks()
        width = canvas.winfo_reqwidth()
        height = canvas.winfo_reqheight()
        if width <= 1 or height <= 1:
            width, height = 640, 400

        left_pad = 90
        right_pad = 70
        top_pad = 40
        bottom_pad = 60
        plot_w = width - left_pad - right_pad
        plot_h = height - top_pad - bottom_pad

        if plot_w <= 0 or plot_h <= 0:
            canvas.create_text(width//2, height//2, text="Graph area too small", fill=MUTED)
            return

        n = len(session_data)
        if n == 0:
            return

        time_vals = [item[1] for item in session_data]
        max_time = max(time_vals) if time_vals else 1

        # Left Y-axis: Mood levels
        MOOD_LABELS_GRAPH = ["😠 Low", "😴 Tired", "😐 Okay", "😊 Great"]
        for i in range(4):
            y = top_pad + plot_h - (i / 3) * plot_h
            canvas.create_line(left_pad - 10, y, left_pad, y, fill=MUTED)
            canvas.create_text(left_pad - 15, y, text=MOOD_LABELS_GRAPH[i], fill=TEXT, anchor="e", font=("Segoe UI", 9))

        # Right Y-axis: Time
        time_ticks = min(5, max(2, max_time // 5 + 1))
        for i in range(time_ticks + 1):
            t_val = int((i / time_ticks) * max_time)
            y = top_pad + plot_h - (i / time_ticks) * plot_h
            canvas.create_line(width - right_pad, y, width - right_pad + 10, y, fill=MUTED)
            canvas.create_text(width - right_pad + 15, y, text=f"{t_val}m", fill=ACCENT, anchor="w", font=("Segoe UI", 9))

        # X-axis labels
        if n == 1:
            x_positions = [left_pad + plot_w // 2]
            labels = ["#1"]
        else:
            max_x_labels = min(n, 8)
            step = max(1, (n - 1) // (max_x_labels - 1))
            x_positions = []
            labels = []
            for i in range(0, n, step):
                x = left_pad + (i / (n - 1)) * plot_w
                x_positions.append(x)
                labels.append(f"#{i+1}")
            if n > 1 and (n-1) not in range(0, n, step):
                x_positions.append(left_pad + plot_w)
                labels.append(f"#{n}")

        for x, label in zip(x_positions, labels):
            canvas.create_line(x, top_pad + plot_h, x, top_pad + plot_h + 5, fill=MUTED)
            canvas.create_text(x, top_pad + plot_h + 20, text=label, fill=TEXT, font=("Segoe UI", 8))

        # Plot data
        mood_points = []
        time_points = []

        MOOD_COLORS_GRAPH = {0: RED, 1: YELLOW, 2: MUTED, 3: GREEN}

        for i, (mood, dur) in enumerate(session_data):
            x = left_pad + (i / (n - 1 if n > 1 else 1)) * plot_w
            y_mood = top_pad + plot_h - (mood / 3) * plot_h
            y_time = top_pad + plot_h - (dur / max_time) * plot_h

            mood_points.extend([x, y_mood])
            time_points.extend([x, y_time])

            color = MOOD_COLORS_GRAPH[mood]
            canvas.create_oval(x-5, y_mood-5, x+5, y_mood+5, fill=color, outline="")

            tri_size = 6
            canvas.create_polygon(
                x, y_time - tri_size,
                x - tri_size, y_time + tri_size,
                x + tri_size, y_time + tri_size,
                fill=ACCENT, outline=""
            )

        # Connect mood points
        if len(mood_points) >= 4:
            for i in range(0, len(mood_points)-2, 2):
                x1, y1 = mood_points[i], mood_points[i+1]
                x2, y2 = mood_points[i+2], mood_points[i+3]
                canvas.create_line(x1, y1, x2, y2, fill="#a0a0ff", width=2)

        # Connect time points (dashed)
        if len(time_points) >= 4:
            for i in range(0, len(time_points)-2, 2):
                x1, y1 = time_points[i], time_points[i+1]
                x2, y2 = time_points[i+2], time_points[i+3]
                canvas.create_line(x1, y1, x2, y2, fill=ACCENT, width=1, dash=(3,3))

        canvas.create_text(width//2, 15, text="Mood & Time Studied per Session", fill=ACCENT, font=("Segoe UI", 12, "bold"))

        legend_y = height - 30
        canvas.create_oval(20, legend_y-5, 30, legend_y+5, fill=GREEN, outline="")
        canvas.create_text(35, legend_y, text="Mood", anchor="w", fill=TEXT, font=("Segoe UI", 9))
        canvas.create_polygon(90, legend_y-4, 85, legend_y+4, 95, legend_y+4, fill=ACCENT, outline="")
        canvas.create_text(100, legend_y, text="Time (min)", anchor="w", fill=ACCENT, font=("Segoe UI", 9))

    def _confirm_clear_logs(self):
        if messagebox.askyesno("Clear All Logs?", "This will permanently delete all recorded sessions and moods. Continue?"):
            try:
                for file in os.listdir(LOGS_DIR):
                    os.remove(os.path.join(LOGS_DIR, file))
                messagebox.showinfo("Success", "All logs cleared.")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to clear logs:\n{e}")

    def end_session(self):
        if not self.log_data["sessions"]:
            messagebox.showinfo("No Activity", "No sessions recorded.")
            return

        total_min = sum(s["duration_min"] for s in self.log_data["sessions"])
        mood_counts = {"1-2": 0, "3-4": 0, "5-7": 0, "8-10": 0}
        for m in self.log_data["moods"]:
            score = m.get("mood_score", 5)
            if score <= 2:
                mood_counts["1-2"] += 1
            elif score <= 4:
                mood_counts["3-4"] += 1
            elif score <= 7:
                mood_counts["5-7"] += 1
            else:
                mood_counts["8-10"] += 1

        report = f"""🪁 Kite Daily Report — {datetime.now().strftime('%Y-%m-%d')}
{"="*50}
⏱️  Total Focused Time: {total_min} minutes
🎯 Sessions: {len(self.log_data['sessions'])}

😌 Mood Summary (1-10 scale):"""
        report += f"\n   😠 Low (1-2): {mood_counts['1-2']}"
        report += f"\n   😴 Tired (3-4): {mood_counts['3-4']}"
        report += f"\n   😐 Okay (5-7): {mood_counts['5-7']}"
        report += f"\n   😊 Great (8-10): {mood_counts['8-10']}"

        water = water_goal(self.profile["weight_lbs"])
        report += f"\n\n💡 Wellness:\n   • Water Goal: {water}L\n   • Profile: {self.profile['gender']}, {self.profile['age']}y"

        messagebox.showinfo("Daily Report", report)
        self.cleanup()
        self.quit_app()

    def cleanup(self):
        self.session_active = False
        self.session_paused = False
        self.kite_canvas.set_active(False)
        if HAS_PSUTIL:
            try:
                current = psutil.Process()
                for child in current.children(recursive=True):
                    child.kill()
            except:
                pass

    def quit_app(self):
        self.master.destroy()

# ----------------------------
# MAIN APPLICATION CONTROLLER
# ----------------------------
class KiteApplication:
    def __init__(self, root):
        self.root = root
        self.root.title("🪁 Kite")
        self.root.geometry("640x600")
        self.root.configure(bg=BG)
        self.root.resizable(False, False)
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

        if os.path.exists(CONFIG_PATH):
            try:
                with open(CONFIG_PATH, 'r') as f:
                    profile = json.load(f)
                    required = ["gender", "age", "height_ft", "height_in", "weight_lbs"]
                    if all(k in profile for k in required):
                        self.show_main_app(profile)
                        return
            except:
                pass

        self.show_setup()

    def show_setup(self):
        self.current_frame = ProfileSetupFrame(self.root, self.on_profile_saved)
        self.current_frame.pack(fill="both", expand=True)

    def on_profile_saved(self, profile):
        self.current_frame.destroy()
        self.show_main_app(profile)

    def show_main_app(self, profile):
        self.current_frame = KiteAppFrame(self.root, profile)
        self.current_frame.pack(fill="both", expand=True)

    def on_closing(self):
        frame = self.current_frame
        if hasattr(frame, 'session_active') and frame.session_active and not frame.session_paused:
            messagebox.showwarning("Focus Active", "Please pause or complete your session before closing.")
        else:
            if hasattr(frame, 'cleanup'):
                frame.cleanup()
            self.root.destroy()

# ==============================
# Run
# ==============================
if __name__ == "__main__":
    try:
        root = tk.Tk()
        app = KiteApplication(root)
        root.mainloop()
    except Exception as e:
        root = tk.Tk()
        root.withdraw()
        messagebox.showerror("Startup Failed", f"Error:\n{str(e)}")
        root.destroy()
