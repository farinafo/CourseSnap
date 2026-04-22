import os
import sys
import tkinter as tk
from tkinter import filedialog, messagebox

from PIL import Image
from config_manager import get_current_project_dir


# ====== Style configuration (matches the main UI) ======
BG_COLOR = "#F5F5F7"
TEXT_COLOR = "#111111"
SUBTEXT_COLOR = "#8E8E93"

TITLE_FONT = ("Segoe UI", 20, "bold")
STATUS_FONT = ("Segoe UI", 11)
BUTTON_FONT = ("Segoe UI", 12)

selected_mode = None


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


class RoundedButton:
    def __init__(self, canvas, x, y, w, h, text, command):
        self.canvas = canvas
        self.command = command

        self.normal_color = "#FFFFFF"
        self.hover_color = "#FFD60A"
        self.active_color = "#FFD60A"
        self.text_color = "#111111"

        self.is_hovered = False
        self.is_active = False

        self.rect = self.create_rounded_rect(
            x, y, x + w, y + h, 18,
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
        if not self.is_active:
            self.is_hovered = True
            self.canvas.itemconfig(self.rect, fill=self.hover_color)

    def on_leave(self, event):
        if not self.is_active:
            self.is_hovered = False
            self.canvas.itemconfig(self.rect, fill=self.normal_color)

    def on_click(self, event):
        self.is_active = True
        self.canvas.itemconfig(self.rect, fill=self.active_color)
        self.command()


def get_current_project():
    folder = get_current_project_dir().strip()
    if folder and os.path.exists(folder):
        return folder
    return ""


def get_images_from_folder(folder):
    valid_exts = (".png", ".jpg", ".jpeg")
    files = sorted(
        [f for f in os.listdir(folder) if f.lower().endswith(valid_exts)]
    )
    return files


def images_to_pdf(image_folder, output_pdf):
    image_files = get_images_from_folder(image_folder)

    if not image_files:
        raise FileNotFoundError("The selected folder has no PNG/JPG/JPEG images, so a PDF cannot be generated")

    images = []
    opened_images = []

    try:
        for filename in image_files:
            path = os.path.join(image_folder, filename)
            img = Image.open(path).convert("RGB")
            opened_images.append(img)
            images.append(img)

        first_image = images[0]
        rest_images = images[1:]
        first_image.save(output_pdf, save_all=True, append_images=rest_images)

    finally:
        for img in opened_images:
            try:
                img.close()
            except Exception:
                pass


def choose_external_folder():
    folder = filedialog.askdirectory(
        title="Choose the image folder",
        initialdir=os.path.expanduser("~")
    )
    return folder.strip() if folder else ""


def build_output_pdf_path(image_folder, use_current_project=False):
    if use_current_project:
        project_dir = os.path.dirname(image_folder)
        return os.path.join(project_dir, "slides.pdf")

    folder_name = os.path.basename(os.path.normpath(image_folder))
    if not folder_name:
        folder_name = "output"
    return os.path.join(image_folder, f"{folder_name}.pdf")


def run_make_pdf_with_folder(image_folder, use_current_project=False):
    output_pdf = build_output_pdf_path(image_folder, use_current_project=use_current_project)
    images_to_pdf(image_folder, output_pdf)
    return output_pdf


def select_current_project_mode(root, status_var):
    global selected_mode
    selected_mode = "current"
    status_var.set("Loading current project images...")
    root.after(150, root.destroy)


def select_external_mode(root, status_var):
    global selected_mode
    selected_mode = "external"
    status_var.set("Preparing to choose another folder...")
    root.after(150, root.destroy)


def cancel_action(root):
    global selected_mode
    selected_mode = None
    root.destroy()


def show_mode_selector(has_current_project):
    global selected_mode
    selected_mode = None

    root = tk.Tk()
    root.title("CourseSnap - Generate PDF")
    root.geometry("420x270")
    root.configure(bg=BG_COLOR)
    root.resizable(False, False)
    root.protocol("WM_DELETE_WINDOW", lambda: cancel_action(root))
    

    try:
        root.iconbitmap(resource_path("favicon.ico"))
    except Exception:
        pass


    subtitle_text = (
        "Choose an image source"
        if has_current_project
        else "No current project. Choose another image folder."
    )

    subtitle_label = tk.Label(
        root,
        text=subtitle_text,
        font=STATUS_FONT,
        fg=SUBTEXT_COLOR,
        bg=BG_COLOR
    )
    subtitle_label.pack(pady=(28, 12))

    status_var = tk.StringVar(value="Ready")
    status_label = tk.Label(
        root,
        textvariable=status_var,
        font=STATUS_FONT,
        fg=SUBTEXT_COLOR,
        bg=BG_COLOR
    )
    status_label.pack(pady=(0, 6))

    canvas = tk.Canvas(
        root,
        width=420,
        height=150,
        bg=BG_COLOR,
        highlightthickness=0
    )
    canvas.pack()

    if has_current_project:
        RoundedButton(
            canvas, 85, 18, 250, 56,
            "Use Current Project Images",
            lambda: select_current_project_mode(root, status_var)
        )

        RoundedButton(
            canvas, 85, 92, 250, 56,
            "Choose Another Image Folder",
            lambda: select_external_mode(root, status_var)
        )
    else:
        RoundedButton(
            canvas, 85, 55, 250, 56,
            "Choose Another Image Folder",
            lambda: select_external_mode(root, status_var)
        )

    cancel_text = canvas.create_text(
        210, 160,
        text="Cancel",
        font=("Segoe UI", 10),
        fill="#8E8E93"
    )

    def on_cancel_enter(event):
        canvas.itemconfig(cancel_text, fill="#111111")

    def on_cancel_leave(event):
        canvas.itemconfig(cancel_text, fill="#8E8E93")

    canvas.tag_bind(cancel_text, "<Enter>", on_cancel_enter)
    canvas.tag_bind(cancel_text, "<Leave>", on_cancel_leave)
    canvas.tag_bind(cancel_text, "<Button-1>", lambda event: cancel_action(root))

    root.mainloop()
    return selected_mode


def main():
    current_project = get_current_project()
    has_current_project = bool(current_project)

    mode = show_mode_selector(has_current_project)

    if mode is None:
        print("PDF generation canceled")
        sys.exit(2)

    if mode == "current":
        slides_dir = os.path.join(current_project, "slides")

        if not os.path.exists(slides_dir):
            messagebox.showerror("Error", f"The slides folder was not found in the current project:\n{slides_dir}")
            sys.exit(1)

        try:
            output_pdf = run_make_pdf_with_folder(slides_dir, use_current_project=True)
            messagebox.showinfo("Notice", f"PDF generated:\n{output_pdf}")
            print(f"PDF generated: {output_pdf}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to generate PDF:\n{e}")
            print(f"Failed to generate PDF: {e}")
            sys.exit(1)
        return

    if mode == "external":
        folder = choose_external_folder()
        if not folder:
            print("Folder selection canceled")
            sys.exit(2)

        try:
            output_pdf = run_make_pdf_with_folder(folder, use_current_project=False)
            messagebox.showinfo("Notice", f"PDF generated:\n{output_pdf}")
            print(f"PDF generated: {output_pdf}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to generate PDF:\n{e}")
            print(f"Failed to generate PDF: {e}")
            sys.exit(1)
        return


if __name__ == "__main__":
    main()
