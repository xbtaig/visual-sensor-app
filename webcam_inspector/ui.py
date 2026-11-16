import tkinter as tk
from tkinter import messagebox, ttk

import cv2
from PIL import Image, ImageTk

from webcam_inspector.inspection import InspectionResult, compare_images
from webcam_inspector.storage import (
    DEFAULT_DATA_DIR,
    ensure_data_dirs,
    load_master,
    save_inspection,
    save_master,
)


class InspectorApp:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("Visual Sensor App")
        self.root.minsize(900, 600)
        self.camera: cv2.VideoCapture | None = None
        self._camera_after_id: str | None = None
        self.current_frame = None
        self.last_result: InspectionResult | None = None
        self.master = load_master()
        self.camera_index = tk.IntVar(value=0)
        self.tolerance = tk.IntVar(value=35)
        self.allowed_difference = tk.DoubleVar(value=2.0)
        self._photos: list[ImageTk.PhotoImage | None] = [None, None]

        ensure_data_dirs()
        self._build_ui()
        self._update_master_label()
        self.root.protocol("WM_DELETE_WINDOW", self.close)

    def _build_ui(self) -> None:
        controls = ttk.Frame(self.root, padding=10)
        controls.pack(fill="x")
        ttk.Label(controls, text="Camera index:").pack(side="left")
        ttk.Spinbox(
            controls, from_=0, to=10, width=4, textvariable=self.camera_index
        ).pack(side="left", padx=(4, 12))
        self.camera_button = ttk.Button(
            controls, text="Start camera", command=self.toggle_camera
        )
        self.camera_button.pack(side="left")
        ttk.Button(
            controls, text="Capture master", command=self.capture_master
        ).pack(side="left", padx=6)
        self.save_button = ttk.Button(
            controls, text="Save inspection", command=self.save_current_inspection
        )
        self.save_button.pack(side="left")

        settings = ttk.Frame(self.root, padding=(10, 0, 10, 8))
        settings.pack(fill="x")
        ttk.Label(settings, text="Pixel tolerance:").pack(side="left")
        tk.Scale(
            settings,
            from_=0,
            to=100,
            orient="horizontal",
            variable=self.tolerance,
            length=180,
            showvalue=True,
        ).pack(side="left", padx=(4, 16))
        ttk.Label(settings, text="Allowed changed area (%):").pack(side="left")
        tk.Scale(
            settings,
            from_=0,
            to=20,
            resolution=0.1,
            orient="horizontal",
            variable=self.allowed_difference,
            length=180,
            showvalue=True,
        ).pack(side="left", padx=4)
        self.master_label = ttk.Label(settings, text="")
        self.master_label.pack(side="right")

        self.status = tk.Label(
            self.root,
            text="Capture a master sample, then start inspection.",
            font=("Segoe UI", 18, "bold"),
            bg="#e8e8e8",
            fg="#333333",
            pady=10,
        )
        self.status.pack(fill="x", padx=10, pady=(0, 8))

        previews = ttk.Frame(self.root, padding=(10, 0, 10, 8))
        previews.pack(fill="both", expand=True)
        self.preview_labels: list[ttk.Label] = []
        for column, title in enumerate(("Live camera", "Difference highlight")):
            panel = ttk.Frame(previews)
            panel.grid(row=0, column=column, sticky="nsew", padx=5)
            ttk.Label(panel, text=title, font=("Segoe UI", 11, "bold")).pack(
                anchor="w", pady=(0, 4)
            )
            preview = ttk.Label(panel, text="Camera preview", anchor="center")
            preview.pack(fill="both", expand=True)
            self.preview_labels.append(preview)
        previews.columnconfigure(0, weight=1)
        previews.columnconfigure(1, weight=1)
        previews.rowconfigure(0, weight=1)

        ttk.Label(
            self.root,
            text=f"Samples and saved inspections are stored in: {DEFAULT_DATA_DIR}",
            padding=(10, 0, 10, 10),
        ).pack(anchor="w")

    def _update_master_label(self) -> None:
        if self.master is None:
            self.master_label.configure(text="Master: not set")
        else:
            height, width = self.master.shape[:2]
            self.master_label.configure(text=f"Master: {width} x {height}")

    def toggle_camera(self) -> None:
        if self.camera is not None:
            if self._camera_after_id is not None:
                self.root.after_cancel(self._camera_after_id)
                self._camera_after_id = None
            self.camera.release()
            self.camera = None
            self.camera_button.configure(text="Start camera")
            self.status.configure(text="Camera stopped", bg="#e8e8e8", fg="#333333")
            return

        camera = cv2.VideoCapture(self.camera_index.get())
        if not camera.isOpened():
            camera.release()
            messagebox.showerror(
                "Camera unavailable",
                "Could not open that camera. Check the camera index and permissions.",
            )
            return
        self.camera = camera
        self.camera_button.configure(text="Stop camera")
        self._read_camera()

    def _read_camera(self) -> None:
        self._camera_after_id = None
        if self.camera is None:
            return
        ok, frame = self.camera.read()
        if not ok:
            self.camera.release()
            self.camera = None
            self.camera_button.configure(text="Start camera")
            messagebox.showerror("Camera error", "The camera stopped returning frames.")
            return

        self.current_frame = frame
        self.last_result = None
        self._show_image(0, frame)
        if self.master is not None:
            height, width = self.master.shape[:2]
            aligned_frame = cv2.resize(frame, (width, height))
            self.last_result = compare_images(
                self.master,
                aligned_frame,
                tolerance=self.tolerance.get(),
                max_difference_percent=self.allowed_difference.get(),
            )
            self._show_image(1, self.last_result.overlay)
            result = "OK" if self.last_result.ok else "NG"
            color = "#188038" if self.last_result.ok else "#c5221f"
            self.status.configure(
                text=f"{result}  |  Changed area: {self.last_result.difference_percent:.2f}%",
                bg=color,
                fg="white",
            )
        else:
            self._show_image(1, frame)
            self.status.configure(
                text="Capture a master sample to enable comparison.",
                bg="#e8e8e8",
                fg="#333333",
            )
        self._camera_after_id = self.root.after(30, self._read_camera)

    def _show_image(self, index: int, frame) -> None:
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        image = Image.fromarray(rgb)
        image.thumbnail((600, 400))
        photo = ImageTk.PhotoImage(image=image)
        self._photos[index] = photo
        self.preview_labels[index].configure(image=photo, text="")

    def capture_master(self) -> None:
        if self.current_frame is None:
            messagebox.showinfo("No camera frame", "Start the camera before capturing a master.")
            return
        try:
            path = save_master(self.current_frame)
            self.master = self.current_frame.copy()
            self._update_master_label()
            messagebox.showinfo("Master saved", f"Master sample saved to:\n{path}")
        except OSError as error:
            messagebox.showerror("Could not save master", str(error))

    def save_current_inspection(self) -> None:
        if self.current_frame is None or self.last_result is None:
            messagebox.showinfo(
                "No inspection result",
                "Start the camera and capture a master before saving an inspection.",
            )
            return
        height, width = self.master.shape[:2]
        aligned_frame = cv2.resize(self.current_frame, (width, height))
        try:
            path = save_inspection(
                aligned_frame,
                self.last_result,
                tolerance=self.tolerance.get(),
                max_difference_percent=self.allowed_difference.get(),
            )
            messagebox.showinfo("Inspection saved", f"Inspection data saved to:\n{path}")
        except OSError as error:
            messagebox.showerror("Could not save inspection", str(error))

    def close(self) -> None:
        if self._camera_after_id is not None:
            self.root.after_cancel(self._camera_after_id)
            self._camera_after_id = None
        if self.camera is not None:
            self.camera.release()
            self.camera = None
        self.root.destroy()


def run() -> None:
    root = tk.Tk()
    InspectorApp(root)
    root.mainloop()
