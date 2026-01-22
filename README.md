🪁 Kite – Focus Timer with Mood Tracking & Personalized Breaks
🪁 Stay focused. Stay balanced. Fly high.

Kite is a sleek, privacy-respecting focus timer built for deep work, wellness, and emotional awareness. Designed with a dark-mode aesthetic and smooth animations, Kite helps you stay productive while tracking your mood on a 1–10 scale and recommending science-backed breaks tailored to your body and energy levels.

Perfect for students, developers, writers, and anyone seeking mindful productivity—without distractions or cloud dependencies.
✨ Features

    🪁 Animated Kite Timer: Visual progress with glowing fill effect and tail animation.
    🧠 1–10 Mood Dial: Rate how you feel (1 = exhausted/stressed, 10 = energized/happy) when pausing.
    ⏸️ Pause & Resume: Seamlessly pause your session, log your mood, and resume where you left off.
    🧬 Personalized Breaks: Break suggestions based on your age, weight, height, and gender using BMR calculations.
    📊 Analytics Dashboard: View daily, weekly, and monthly trends in focus time and mood (with bar graphs).
    💧 Wellness Integration: Auto-calculated daily water goal based on your profile.
    🔒 Fully Offline & Private: No internet required. All data stored locally in kite_logs/.
    🗑️ One-Click Log Clear: Easily reset your history without reinstalling.
    🌙 Dark Theme: Eye-friendly UI with glowing accents and clean typography.
    📦 Standalone Python App: Runs on Windows, macOS, and Linux—no external assets or databases.

🖼️ Screenshots

<img width="857" height="594" alt="image" src="https://github.com/user-attachments/assets/a37c9e97-3010-400f-8403-b68df4d1325b" />

🚀 Quick Start
Prerequisites

    Python 3.7+
    tkinter (usually included with Python)
    Optional: psutil (for clean shutdown; install via pip install psutil)

Installation

    Clone or download this repository:

    bash
    1
    2

    Run the app:

    bash
    1

    Complete your profile on first launch (used for personalized break recommendations).

    💡 No installation needed! Just run the script—everything is self-contained.

🧠 How It Works

    Session Flow:
    Start → Focus → Pause (log mood 1–10) → Resume → Complete → Get break tip.
    Mood Tracking:
    Every pause prompts a 1–10 slider. Data is saved per session for analytics.
    Break Logic:
    Uses your Basal Metabolic Rate (BMR) to suggest hydration, movement, or mindfulness based on session count and energy needs.
    Data Storage:  
        Profile: kite_profile.json  
        Daily Logs: kite_logs/YYYY-MM-DD.json  
        All files are human-readable JSON.

🔒 Privacy & Security

    Zero telemetry
    No network calls
    No cloud sync
    All data stays on your machine
