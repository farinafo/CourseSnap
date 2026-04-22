import tkinter as tk
from tkinter import messagebox, simpledialog, filedialog
import threading
import os
import subprocess
import sys
from datetime import datetime

from config_manager import (
    get_api_key,
    set_api_key,
    get_last_parent_dir,
    set_last_parent_dir,
    get_current_project_dir,
    set_current_project_dir,
)


capture_process = None

# ====== Paths / packaging compatibility ======
def is_frozen():
    return getattr(sys, "frozen", False)


def app_dir():
    if is_frozen():
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))


def resource_path(relative_path):
    if is_frozen():
        return os.path.join(os.path.dirname(sys.executable), relative_path)
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), relative_path)


def run_target(py_name, exe_name):
    base = app_dir()
    if is_frozen():
        target = os.path.join(base, exe_name)
        return subprocess.run([target])
    else:
        target = os.path.join(base, py_name)
        return subprocess.run([sys.executable, target])


# ====== Style configuration ======
BG_COLOR = "#F5F5F7"
TEXT_COLOR = "#111111"
SUBTEXT_COLOR = "#8E8E93"

TITLE_FONT = ("Segoe UI", 28, "bold")
STATUS_FONT = ("Segoe UI", 14)
BUTTON_FONT = ("Segoe UI", 13)

all_buttons = []


class RoundedButton:
    def __init__(self, canvas, x, y, w, h, text, command):
        self.canvas = canvas
        self.command = command

        self.normal_color = "#FFFFFF"
        self.hover_color = "#FFD60A"
        self.active_color = "#FFD60A"
        self.text_color = "#111111"

        self.is_working = False
        self.is_hovered = False

        self.rect = self.create_rounded_rect(
            x, y, x + w, y + h, 20,
            fill=self.normal_color,
            outline=""
        )

        self.label = canvas.create_text(
            x + w / 2,
            y + h / 2,
            text=text,
            font=BUTTON_FONT,
            fill=self.text_color
        )

        for item in (self.rect, self.label):
            self.canvas.tag_bind(item, "<Enter>", self.on_enter)
            self.canvas.tag_bind(item, "<Leave>", self.on_leave)
            self.canvas.tag_bind(item, "<Button-1>", self.on_click)

        all_buttons.append(self)

    def create_rounded_rect(self, x1, y1, x2, y2, r, **kwargs):
        points = [
            x1 + r, y1,
            x2 - r, y1,
            x2, y1,
            x2, y1 + r,
            x2, y2 - r,
            x2, y2,
            x2 - r, y2,
            x1 + r, y2,
            x1, y2,
            x1, y2 - r,
            x1, y1 + r,
            x1, y1
        ]
        return self.canvas.create_polygon(points, smooth=True, **kwargs)

    def on_enter(self, event):
        self.is_hovered = True
        if not self.is_working:
            self.canvas.itemconfig(self.rect, fill=self.hover_color)

    def on_leave(self, event):
        self.is_hovered = False
        if not self.is_working:
            self.canvas.itemconfig(self.rect, fill=self.normal_color)

    def on_click(self, event):
        self.command()

    def set_working(self):
        self.is_working = True
        self.canvas.itemconfig(self.rect, fill=self.active_color)

    def reset(self):
        self.is_working = False
        if self.is_hovered:
            self.canvas.itemconfig(self.rect, fill=self.hover_color)
        else:
            self.canvas.itemconfig(self.rect, fill=self.normal_color)


def reset_all_buttons(except_button=None):
    for btn in all_buttons:
        if btn is not except_button:
            btn.reset()


def update_status(text):
    status_var.set(text)
    root.update_idletasks()


def prompt_for_api_key(is_change=False):
    title = "Change API Key" if is_change else "Enter API Key"
    prompt = (
        "Enter the new DashScope API Key:"
        if is_change
        else "Enter your DashScope API Key to use the summary feature:"
    )

    user_input = simpledialog.askstring(title, prompt, show="*")

    if user_input is None:
        return False

    user_input = user_input.strip()
    if not user_input:
        messagebox.showwarning("Notice", "API Key cannot be empty")
        return False

    set_api_key(user_input)

    if is_change:
        messagebox.showinfo("Notice", "API Key updated")
        update_status("API Key updated")
    else:
        update_status("API Key saved")

    return True


def change_api_key():
    prompt_for_api_key(is_change=True)


def get_current_project():
    folder = get_current_project_dir().strip()
    if folder and os.path.exists(folder):
        return folder
    return ""


def ensure_project_ready():
    folder = get_current_project()
    if not folder:
        messagebox.showwarning("Notice", "Click \"Start Recording\" first to create this project")
        return ""
    return folder


def choose_project_parent_dir():
    initial_dir = get_last_parent_dir().strip()
    if not initial_dir or not os.path.exists(initial_dir):
        initial_dir = os.path.expanduser("~")

    folder = filedialog.askdirectory(
        title="Choose where to save this project",
        initialdir=initial_dir
    )
    if not folder:
        return ""

    set_last_parent_dir(folder)
    return folder


def create_new_project():
    parent_dir = choose_project_parent_dir()
    if not parent_dir:
        return ""

    project_name = simpledialog.askstring(
        "Project Name",
        "Enter the course/project name:"
    )

    if project_name is None:
        return ""

    project_name = project_name.strip()
    if not project_name:
        messagebox.showwarning("Notice", "Project name cannot be empty")
        return ""

    safe_name = project_name.replace("/", "_").replace("\\", "_").replace(":", "_")
    timestamp = datetime.now().strftime("%Y%m%d_%H%M")
    project_dir = os.path.join(parent_dir, f"{safe_name}_{timestamp}")
    slides_dir = os.path.join(project_dir, "slides")

    os.makedirs(slides_dir, exist_ok=True)
    set_current_project_dir(project_dir)

    update_status(f"Current project: {os.path.basename(project_dir)}")
    return project_dir


def start_capture():
    global capture_process

    if capture_process is not None and capture_process.poll() is None:
        messagebox.showwarning("Notice", "Recording is already in progress")
        return

    project_dir = create_new_project()
    if not project_dir:
        update_status("Project creation canceled")
        return

    try:
        stop_flag_path = os.path.join(app_dir(), "stop.flag")
        if os.path.exists(stop_flag_path):
            os.remove(stop_flag_path)

        reset_all_buttons(except_button=btn_start)
        btn_start.set_working()
        update_status("Recording...")

        if is_frozen():
            target = os.path.join(app_dir(), "capture.exe")
            capture_process = subprocess.Popen([target])
        else:
            target = os.path.join(app_dir(), "capture.py")
            capture_process = subprocess.Popen([sys.executable, target])

    except Exception as e:
        btn_start.reset()
        messagebox.showerror("Error", f"Failed to start recording:\n{e}")
        update_status("Failed to start recording")


def stop_capture():
    global capture_process

    if capture_process is None or capture_process.poll() is not None:
        messagebox.showwarning("Notice", "No recording is currently in progress")
        return

    try:
        reset_all_buttons(except_button=btn_stop)
        btn_stop.set_working()

        stop_flag_path = os.path.join(app_dir(), "stop.flag")
        with open(stop_flag_path, "w", encoding="utf-8") as f:
            f.write("stop")

        update_status("Stopping recording...")
        root.after(1200, check_capture_stopped)

    except Exception as e:
        btn_stop.reset()
        messagebox.showerror("Error", f"Failed to stop recording:\n{e}")
        update_status("Failed to stop recording")


def check_capture_stopped():
    global capture_process

    if capture_process is not None and capture_process.poll() is None:
        root.after(800, check_capture_stopped)
    else:
        reset_all_buttons()
        update_status("Recording stopped")
        messagebox.showinfo("Notice", "Recording stopped")


def run_pdf():
    def task():
        try:
            root.after(0, lambda: reset_all_buttons(except_button=btn_pdf))
            root.after(0, btn_pdf.set_working)
            root.after(0, lambda: update_status("Generating PDF..."))

            result = run_target("make_pdf.py", "make_pdf.exe")

            if result.returncode == 0:
                root.after(0, lambda: update_status("PDF generated"))
                root.after(0, lambda: messagebox.showinfo("Notice", "PDF generated"))

            elif result.returncode == 2:
                root.after(0, lambda: update_status("PDF generation canceled"))

            else:
                root.after(0, lambda: update_status("PDF generation failed"))
                root.after(0, lambda: messagebox.showerror("Error", "PDF generation failed"))

        except Exception as e:
            root.after(0, lambda: update_status("PDF generation failed"))
            root.after(0, lambda: messagebox.showerror("Error", f"PDF process error:\n{e}"))

        finally:
            root.after(0, reset_all_buttons)

    threading.Thread(target=task, daemon=True).start()


def find_transcript_file(project_dir):
    for f in os.listdir(project_dir):
        if f.lower().endswith((".txt", ".docx")):
            return os.path.join(project_dir, f)
    return None


def run_summary():
    project_dir = ensure_project_ready()
    if not project_dir:
        return

    pdf_path = os.path.join(project_dir, "slides.pdf")
    transcript_path = find_transcript_file(project_dir)

    if not os.path.exists(pdf_path):
        messagebox.showwarning(
            "Missing File",
            "slides.pdf was not found.\nClick \"Generate PDF\" first."
        )
        return

    if not transcript_path:
        messagebox.showwarning(
            "Missing File",
            "No transcript was found (txt or docx).\nPlace it in the project folder."
        )
        return

    api_key = get_api_key()

    if not api_key:
        ok = prompt_for_api_key(is_change=False)
        if not ok:
            update_status("Summary canceled")
            return

    def task():
        try:
            root.after(0, lambda: reset_all_buttons(except_button=btn_summary))
            root.after(0, btn_summary.set_working)
            root.after(0, lambda: update_status("Generating summary..."))

            result = run_target("summarize.py", "summarize.exe")

            if result.returncode == 0:
                root.after(0, lambda: update_status("Summary complete"))
                root.after(0, lambda: messagebox.showinfo("Notice", "Summary complete. Word notes have been generated."))
            else:
                root.after(0, lambda: update_status("Summary failed"))
                root.after(0, lambda: messagebox.showerror("Error", "Summary failed"))

        except Exception as e:
            root.after(0, lambda: update_status("Summary failed"))
            root.after(0, lambda: messagebox.showerror("Error", f"Summary process error:\n{e}"))

        finally:
            root.after(0, reset_all_buttons)

    threading.Thread(target=task, daemon=True).start()


def open_output_folder():
    project_dir = ensure_project_ready()
    if not project_dir:
        return

    try:
        reset_all_buttons(except_button=btn_folder)
        btn_folder.set_working()
        os.startfile(project_dir)

    except Exception as e:
        messagebox.showerror("Error", f"Could not open folder:\n{e}")

    finally:
        root.after(200, reset_all_buttons)


# ====== Main window ======
root = tk.Tk()

try:
    root.iconbitmap(resource_path("favicon.ico"))
except Exception:
    pass

root.title("CourseSnap")
root.geometry("460x560")
root.configure(bg=BG_COLOR)
root.resizable(False, False)

title_label = tk.Label(
    root,
    text="CourseSnap",
    font=TITLE_FONT,
    fg=TEXT_COLOR,
    bg=BG_COLOR
)
title_label.pack(pady=(28, 8))

status_var = tk.StringVar(value="Ready")
status_label = tk.Label(
    root,
    textvariable=status_var,
    font=STATUS_FONT,
    fg=SUBTEXT_COLOR,
    bg=BG_COLOR
)
status_label.pack(pady=(0, 20))

canvas = tk.Canvas(
    root,
    width=460,
    height=380,
    bg=BG_COLOR,
    highlightthickness=0
)
canvas.pack()

btn_start = RoundedButton(canvas, 55, 25, 150, 60, "Start Recording", start_capture)
btn_stop = RoundedButton(canvas, 245, 25, 150, 60, "Stop Recording", stop_capture)

btn_pdf = RoundedButton(canvas, 55, 115, 150, 60, "Generate PDF", run_pdf)
btn_summary = RoundedButton(canvas, 245, 115, 150, 60, "Summarize", run_summary)

btn_folder = RoundedButton(canvas, 120, 210, 220, 60, "Open Current Project Folder", open_output_folder)

change_key_text = canvas.create_text(
    230, 300,
    text="Change API Key",
    font=("Segoe UI", 10),
    fill="#8E8E93"
)


def on_link_click(event):
    change_api_key()


def on_link_enter(event):
    canvas.itemconfig(change_key_text, fill="#111111")


def on_link_leave(event):
    canvas.itemconfig(change_key_text, fill="#8E8E93")


canvas.tag_bind(change_key_text, "<Button-1>", on_link_click)
canvas.tag_bind(change_key_text, "<Enter>", on_link_enter)
canvas.tag_bind(change_key_text, "<Leave>", on_link_leave)

root.mainloop()
