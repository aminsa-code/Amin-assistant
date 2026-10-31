
import os
import sys
import time
import shutil
import threading
import subprocess
import webbrowser
import tkinter as tk
from tkinter import messagebox

import customtkinter as ctk
import speech_recognition as sr
import pyttsx3

try:
    from youtubesearchpython import VideosSearch
    YOUTUBE_AVAILABLE = True
except ImportError:
    YOUTUBE_AVAILABLE = False


# =========================
# CONFIGURATION
# =========================

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

APP_TITLE = "Amin Assistant"

running = False
assistant_thread = None
recognizer = sr.Recognizer()

# Initialize speech engine
engine = pyttsx3.init()
engine.setProperty("rate", 175)
engine.setProperty("volume", 1.0)

speech_lock = threading.Lock()


# =========================
# USER INTERFACE
# =========================

root = ctk.CTk()
root.title(APP_TITLE)
root.geometry("550x450")
root.resizable(False, False)

title = ctk.CTkLabel(
    root,
    text="AMIN ASSISTANT",
    font=("Arial", 28, "bold")
)
title.pack(pady=(30, 10))

subtitle = ctk.CTkLabel(
    root,
    text="Your personal voice assistant",
    font=("Arial", 14)
)
subtitle.pack(pady=5)

status_label = ctk.CTkLabel(
    root,
    text="Status: Stopped",
    font=("Arial", 16),
    text_color="#ff5555"
)
status_label.pack(pady=20)

start_button = ctk.CTkButton(
    root,
    text="START LISTENING",
    width=220,
    height=45,
    command=lambda: start_assistant()
)
start_button.pack(pady=10)

stop_button = ctk.CTkButton(
    root,
    text="STOP LISTENING",
    width=220,
    height=45,
    fg_color="#aa3333",
    hover_color="#882222",
    command=lambda: stop_assistant()
)
stop_button.pack(pady=10)

info_label = ctk.CTkLabel(
    root,
    text="Click Start and speak your commands.",
    font=("Arial", 12),
    text_color="gray"
)
info_label.pack(pady=25)


# =========================
# UI HELPERS
# =========================

def update_status(text, color="#ffffff"):
    root.after(
        0,
        lambda: status_label.configure(
            text=f"Status: {text}",
            text_color=color
        )
    )


def show_message(text):
    root.after(
        0,
        lambda: info_label.configure(text=text)
    )


# =========================
# TEXT TO SPEECH
# =========================

def speak(text):
    print("Assistant:", text)

    try:
        with speech_lock:
            engine.say(text)
            engine.runAndWait()
    except Exception as error:
        print("TTS error:", error)


# =========================
# APPLICATION LAUNCHER
# =========================

def launch_app(name):
    """
    Launch native Linux applications or Flatpak applications.
    """

    native_apps = {
        "terminal": ["ptyxis", "kgx", "gnome-terminal"],
        "files": ["nautilus", "dolphin", "thunar"],
        "calculator": ["gnome-calculator", "kcalc"],
        "text editor": [
            "gnome-text-editor",
            "gedit",
            "mousepad"
        ]
    }

    flatpak_apps = {
        "vs code": "com.visualstudio.code",
        "visual studio code": "com.visualstudio.code",
        "vscode": "com.visualstudio.code",
        "lm studio": "ai.lmstudio.lm-studio",
        "lmstudio": "ai.lmstudio.lm-studio",
        "steam": "com.valvesoftware.Steam"
    }

    name = name.lower().strip()

    # Flatpak application
    if name in flatpak_apps:
        app_id = flatpak_apps[name]

        if not shutil.which("flatpak"):
            speak("Flatpak is not installed.")
            return

        check = subprocess.run(
            ["flatpak", "info", app_id],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )

        if check.returncode != 0:
            speak(name + " is not installed.")
            print("Install it using:")
            print("flatpak install flathub", app_id)
            return

        try:
            subprocess.Popen(
                ["flatpak", "run", app_id],
                start_new_session=True
            )
            speak("Opening " + name)
        except Exception as error:
            print("Launch error:", error)
            speak("Could not open " + name)

        return

    # Native Linux application
    if name in native_apps:
        for executable in native_apps[name]:
            path = shutil.which(executable)

            if path:
                try:
                    subprocess.Popen(
                        [path],
                        start_new_session=True
                    )
                    speak("Opening " + name)
                    return
                except Exception as error:
                    print("Launch error:", error)

        speak(name + " is not installed.")
        return

    speak("I do not know this application.")


# =========================
# SCROLL CONTROL
# =========================

def scroll_mouse(direction):
    amount = 5 if direction == "up" else -5

    env = os.environ.copy()
    env["YDOTOOL_SOCKET"] = "/tmp/.ydotool_socket"

    try:
        subprocess.run(
            [
                "ydotool",
                "mousemove",
                "--wheel",
                "--",
                "0",
                str(amount)
            ],
            env=env,
            check=True,
            timeout=5
        )

        print("Scroll", direction, "successful")

    except subprocess.CalledProcessError as error:
        print("Scroll command failed:", error)
        speak("Scrolling failed.")

    except FileNotFoundError:
        speak("Ydotool is not installed.")

    except subprocess.TimeoutExpired:
        speak("Scrolling timed out.")


# =========================
# VOLUME CONTROL
# =========================

def volume_control(action):
    commands = {
        "up": [
            "wpctl", "set-volume",
            "@DEFAULT_AUDIO_SINK@", "10%+"
        ],
        "down": [
            "wpctl", "set-volume",
            "@DEFAULT_AUDIO_SINK@", "10%-"
        ],
        "mute": [
            "wpctl", "set-mute",
            "@DEFAULT_AUDIO_SINK@", "1"
        ],
        "unmute": [
            "wpctl", "set-mute",
            "@DEFAULT_AUDIO_SINK@", "0"
        ]
    }

    try:
        subprocess.run(
            commands[action],
            check=True,
            timeout=5
        )
        speak("Volume " + action)

    except Exception as error:
        print("Volume error:", error)
        speak("Volume control failed.")


# =========================
# YOUTUBE
# =========================

def play_youtube(query):
    if not YOUTUBE_AVAILABLE:
        speak("YouTube search library is not installed.")
        return

    try:
        videos = VideosSearch(query, limit=1).result()

        results = videos.get("result", [])

        if results:
            url = results[0]["link"]
            webbrowser.open(url)
            speak("Opening " + query + " on YouTube")
        else:
            speak("No video found.")

    except Exception as error:
        print("YouTube error:", error)
        speak("YouTube search failed.")


# =========================
# COMMAND EXECUTION
# =========================

def execute_command(command):
    command = command.lower().strip()

    print("Executing:", command)

    # Stop assistant
    if any(x in command for x in [
        "stop assistant",
        "stop listening",
        "turn off assistant"
    ]):
        stop_assistant()
        speak("Assistant stopped.")
        return

    # Scroll
    if "scroll up" in command:
        scroll_mouse("up")
        return

    if "scroll down" in command:
        scroll_mouse("down")
        return

    # Volume
    if "volume up" in command or "increase volume" in command:
        volume_control("up")
        return

    if "volume down" in command or "decrease volume" in command:
        volume_control("down")
        return

    if "mute" in command:
        volume_control("mute")
        return

    if "unmute" in command:
        volume_control("unmute")
        return

    # Applications
    if any(x in command for x in [
        "open terminal",
        "open the terminal"
    ]):
        launch_app("terminal")
        return

    if any(x in command for x in [
        "open vs code",
        "open vscode",
        "open visual studio code",
        "open code"
    ]):
        launch_app("vs code")
        return

    if "open lm studio" in command or "open lmstudio" in command:
        launch_app("lm studio")
        return

    if "open steam" in command:
        launch_app("steam")
        return

    if "open calculator" in command:
        launch_app("calculator")
        return

    if "open files" in command or "open file manager" in command:
        launch_app("files")
        return

    if "open text editor" in command:
        launch_app("text editor")
        return

    # Websites
    if "open youtube" in command:
        webbrowser.open("https://www.youtube.com")
        speak("Opening YouTube")
        return

    if "open google" in command:
        webbrowser.open("https://www.google.com")
        speak("Opening Google")
        return

    if "open chatgpt" in command:
        webbrowser.open("https://chatgpt.com")
        speak("Opening ChatGPT")
        return

    if "open instagram" in command:
        webbrowser.open("https://www.instagram.com")
        speak("Opening Instagram")
        return

    if "open browser" in command or "open browser" == command:
        webbrowser.open("https://www.google.com")
        speak("Opening browser")
        return

    # YouTube search
    if command.startswith("play "):
        song = command.replace("play ", "", 1).strip()
        play_youtube(song)
        return

    if command.startswith("search youtube for "):
        query = command.replace(
            "search youtube for ", "", 1
        ).strip()
        play_youtube(query)
        return

    # Google search
    if command.startswith("search for "):
        query = command.replace("search for ", "", 1).strip()
        webbrowser.open(
            "https://www.google.com/search?q=" +
            __import__("urllib.parse").parse.quote(query)
        )
        speak("Searching Google")
        return

    speak("Sorry, I did not understand that command.")


# =========================
# MICROPHONE LOOP
# =========================

def assistant_loop():
    global running

    try:
        with sr.Microphone() as source:
            print("Calibrating microphone...")
            update_status("Calibrating microphone...", "#ffaa00")

            recognizer.adjust_for_ambient_noise(
                source,
                duration=1
            )

            print("Microphone ready!")
            update_status("Listening...", "#00dd88")
            speak("I am listening.")

            while running:
                try:
                    audio = recognizer.listen(
                        source,
                        timeout=3,
                        phrase_time_limit=7
                    )

                    if not running:
                        break

                    command = recognizer.recognize_google(
                        audio,
                        language="en-US"
                    ).lower().strip()

                    if command:
                        print("You:", command)
                        show_message("Heard: " + command)
                        execute_command(command)

                except sr.WaitTimeoutError:
                    continue

                except sr.UnknownValueError:
                    continue

                except sr.RequestError as error:
                    print("Speech recognition error:", error)
                    update_status(
                        "Internet / recognition error",
                        "#ff5555"
                    )
                    time.sleep(2)

                except Exception as error:
                    print("Command error:", error)
                    time.sleep(1)

    except Exception as error:
        print("Microphone error:", error)
        update_status("Microphone error", "#ff5555")
        show_message(str(error))

    finally:
        running = False
        update_status("Stopped", "#ff5555")


# =========================
# START / STOP
# =========================

def start_assistant():
    global running, assistant_thread

    if running:
        return

    running = True

    update_status("Starting...", "#ffaa00")
    show_message("Preparing microphone...")

    assistant_thread = threading.Thread(
        target=assistant_loop,
        daemon=True
    )

    assistant_thread.start()


def stop_assistant():
    global running

    running = False

    update_status("Stopping...", "#ffaa00")
    show_message("Listening stopped.")


def close_app():
    global running

    running = False

    try:
        engine.stop()
    except Exception:
        pass

    root.destroy()


root.protocol("WM_DELETE_WINDOW", close_app)

root.mainloop()
