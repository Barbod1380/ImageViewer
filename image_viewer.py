import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from PIL import Image, ImageTk, ImageOps
import os
import shutil
import platform
import numpy as np
import importlib.util
import inspect


class EnhancedImageViewer:
    """A comprehensive image viewer with editing and file management tools."""

    def __init__(self, root):
        """
        Initialize the EnhancedImageViewer application.

        Args:
            root: The root Tkinter window.
        """
        self.root = root
        self.root.title("Enhanced Image Viewer")
        self.root.geometry("1000x700")
        self.root.minsize(800, 600)

        # Set theme for modern look
        self.style = ttk.Style()
        self.style.theme_use('clam')

        # Configure custom styles
        self.style.configure('TButton', padding=6, font=('Segoe UI', 10))
        self.style.configure(
            'Title.TLabel',
            font=('Segoe UI', 14, 'bold'),
            foreground='#333333'
        )
        self.style.configure(
            'Status.TLabel',
            font=('Segoe UI', 9),
            foreground='#666666'
        )
        self.style.configure('Bold.TLabel', font=('Segoe UI', 9, 'bold'))

        # Initialize variables
        self.image_dir = ""
        self.image_list = []
        self.current_index = 0
        self.output_dir = ""
        self.original_image = None
        self.modified_image = None
        self.current_rotation = 0

        # Create UI elements
        self.create_widgets()

        # Bind keyboard events
        self.root.bind('<Left>', self.prev_image)
        self.root.bind('<Right>', self.next_image)
        self.root.bind('c', self.copy_image)
        self.root.bind('m', self.move_image)
        self.root.bind('d', self.delete_image)
        self.root.bind('r', self.rotate_image)
        self.root.bind('f', self.toggle_fullscreen)
        self.root.bind('<Escape>', self.exit_fullscreen)

        # Handle high DPI displays
        self.scale_factor = self.get_scale_factor()

        # Set initial status
        self.update_status("Select image directory to start")

    def get_scale_factor(self):
        """Get display scaling factor for high DPI displays."""
        if platform.system() == 'Windows':
            from ctypes import windll
            try:
                windll.shcore.SetProcessDpiAwareness(1)
                return windll.shcore.GetScaleFactorForDevice(0) / 100
            except Exception:
                return 1.0
        elif platform.system() == 'Darwin':  # macOS
            return 1.0
        else:  # Linux
            return 1.0

    def create_widgets(self):
        """Create and arrange all UI widgets."""
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        header_frame = ttk.Frame(main_frame)
        header_frame.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(header_frame, text="Enhanced Image Viewer",
                  style='Title.TLabel').pack(side=tk.LEFT)

        btn_frame = ttk.Frame(header_frame)
        btn_frame.pack(side=tk.RIGHT)

        ttk.Button(btn_frame, text="Select Image Directory",
                   command=self.select_image_dir).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Select Output Directory",
                   command=self.select_output_dir).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Apply Function",
                   command=self.apply_py_function).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Fullscreen (F)",
                   command=self.toggle_fullscreen).pack(side=tk.LEFT, padx=5)

        display_frame = ttk.LabelFrame(main_frame, text="Image Preview")
        display_frame.pack(fill=tk.BOTH, expand=True, pady=5)

        self.canvas = tk.Canvas(
            display_frame, bg='#f0f0f0', highlightthickness=0
        )
        self.canvas.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        info_frame = ttk.Frame(main_frame)
        info_frame.pack(fill=tk.X, pady=10)

        nav_frame = ttk.Frame(info_frame)
        nav_frame.pack(side=tk.LEFT, padx=(0, 20))

        ttk.Button(
            nav_frame, text="◀ Previous (←)", command=self.prev_image,
            width=15).pack(side=tk.LEFT, padx=5)
        ttk.Button(
            nav_frame, text="Next (→) ▶", command=self.next_image,
            width=15).pack(side=tk.LEFT, padx=5)

        action_frame = ttk.Frame(info_frame)
        action_frame.pack(side=tk.LEFT, padx=(0, 20))

        ttk.Button(
            action_frame, text="Copy (C)", command=self.copy_image,
            width=12).pack(side=tk.LEFT, padx=5)
        ttk.Button(
            action_frame, text="Move (M)", command=self.move_image,
            width=12).pack(side=tk.LEFT, padx=5)
        ttk.Button(
            action_frame, text="Rotate (R)", command=self.rotate_image,
            width=12).pack(side=tk.LEFT, padx=5)
        ttk.Button(
            action_frame, text="Delete (D)", command=self.delete_image,
            width=12).pack(side=tk.LEFT, padx=5)
        ttk.Button(
            action_frame, text="Save Modified",
            command=self.save_modified_image,
            width=15).pack(side=tk.LEFT, padx=5)

        info_panel = ttk.Frame(info_frame)
        info_panel.pack(side=tk.RIGHT, fill=tk.X, expand=True)

        ttk.Label(info_panel, text="Current Image:",
                  style='Bold.TLabel').grid(row=0, column=0, sticky='w')
        self.current_image_var = tk.StringVar()
        ttk.Label(info_panel, textvariable=self.current_image_var).grid(
            row=0, column=1, sticky='w', padx=(5, 20)
        )

        ttk.Label(info_panel, text="Output Directory:",
                  style='Bold.TLabel').grid(row=0, column=2, sticky='w')
        self.output_dir_var = tk.StringVar()
        ttk.Label(info_panel, textvariable=self.output_dir_var,
                  width=30).grid(row=0, column=3, sticky='w')

        status_frame = ttk.Frame(self.root, relief=tk.SUNKEN)
        status_frame.pack(fill=tk.X, side=tk.BOTTOM)

        self.status_var = tk.StringVar()
        status_label = ttk.Label(status_frame, textvariable=self.status_var,
                                 style='Status.TLabel')
        status_label.pack(side=tk.LEFT, padx=10, pady=2)

        self.progress_var = tk.StringVar()
        ttk.Label(status_frame, textvariable=self.progress_var,
                  style='Status.TLabel').pack(side=tk.RIGHT, padx=10, pady=2)

    def update_status(self, message):
        """
        Update the status bar with a message.

        Args:
            message (str): The message to display.
        """
        self.status_var.set(message)
        self.root.update_idletasks()

    def update_progress(self):
        """Update the progress indicator."""
        if self.image_list:
            self.progress_var.set(
                f"Image {self.current_index + 1} of {len(self.image_list)}"
            )
        else:
            self.progress_var.set("")

    def select_image_dir(self):
        """Open a dialog to select the image directory."""
        self.image_dir = filedialog.askdirectory(
            title="Select Image Directory"
        )
        if self.image_dir:
            self.load_images()
            self.show_image(0)

    def select_output_dir(self):
        """Open a dialog to select the output directory."""
        self.output_dir = filedialog.askdirectory(
            title="Select Output Directory"
        )
        if self.output_dir:
            self.output_dir_var.set(os.path.basename(self.output_dir))
            self.update_status(f"Output directory set to: {self.output_dir}")

    def load_images(self):
        """Load and sort valid image files from the selected directory."""
        valid_extensions = [
            '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp', '.tiff'
        ]
        self.image_list = [
            os.path.join(self.image_dir, f)
            for f in os.listdir(self.image_dir)
            if os.path.splitext(f)[1].lower() in valid_extensions
        ]
        self.image_list.sort()

        if self.image_list:
            self.update_status(
                f"Loaded {len(self.image_list)} images. \n"
                "Navigation: ← → keys. \n"
                "Actions: C=Copy, R=Rotate, D=Delete"
            )
        else:
            self.update_status("No images found in selected directory")

        self.update_progress()

    def show_image(self, index, image_to_show=None):
        """
        Display the image at the specified index or a provided image object.

        Args:
            index (int): The index of the image to display.
            image_to_show (Image, optional): A pre-loaded image to display.
                                             Defaults to None.
        """
        if not self.image_list and not image_to_show:
            return

        # Keep index within bounds
        if index < 0:
            index = 0
        elif index >= len(self.image_list):
            index = len(self.image_list) - 1

        self.current_index = index
        image_path = self.image_list[index]

        try:
            self.canvas.delete("all")

            if image_to_show:
                self.original_image = image_to_show
            else:
                self.original_image = Image.open(image_path)
                self.modified_image = None

            self.current_rotation = 0
            self.original_image = ImageOps.exif_transpose(self.original_image)

            canvas_width = self.canvas.winfo_width()
            canvas_height = self.canvas.winfo_height()

            if canvas_width <= 1 or canvas_height <= 1:
                canvas_width = 800
                canvas_height = 500

            img = self.original_image.copy()
            img.thumbnail(
                (int(canvas_width * 0.95), int(canvas_height * 0.95)),
                Image.Resampling.LANCZOS
            )

            img_tk = ImageTk.PhotoImage(img)

            self.canvas.image = img_tk
            self.canvas.create_image(
                canvas_width // 2,
                canvas_height // 2,
                image=img_tk,
                anchor=tk.CENTER
            )

            filename = os.path.basename(image_path)
            self.current_image_var.set(
                f"{filename} ({img.width}×{img.height})")
            self.update_progress()
        except Exception as e:
            self.update_status(f"Error loading image: {str(e)}")

    def resize_image(self, event):
        """Resize the image when the window size changes."""
        if self.original_image and self.image_list:
            self.show_image(self.current_index)

    def next_image(self, event=None):
        """Show the next image in the list."""
        if self.image_list and self.current_index < len(self.image_list) - 1:
            self.show_image(self.current_index + 1)

    def prev_image(self, event=None):
        """Show the previous image in the list."""
        if self.image_list and self.current_index > 0:
            self.show_image(self.current_index - 1)

    def copy_image(self, event=None):
        """Copy the current image to the output directory."""
        if not self.image_list:
            return

        if not self.output_dir:
            self.update_status("Please select an output directory first!")
            return

        current_image = self.image_list[self.current_index]
        filename = os.path.basename(current_image)
        dest_path = os.path.join(self.output_dir, filename)

        try:
            shutil.copy2(current_image, dest_path)
            self.update_status(f"Copied to output directory: {filename}")
        except Exception as e:
            self.update_status(f"Copy failed: {str(e)}")

    def move_image(self, event=None):
        """Move the current image to the output directory."""
        if not self.image_list:
            return

        if not self.output_dir:
            self.update_status("Please select an output directory first!")
            return

        current_image = self.image_list[self.current_index]
        filename = os.path.basename(current_image)
        dest_path = os.path.join(self.output_dir, filename)

        try:
            shutil.move(current_image, dest_path)
            self.image_list.pop(self.current_index)

            if not self.image_list:
                self.canvas.delete("all")
                self.current_image_var.set("")
                self.update_status("No images remaining")
                self.update_progress()
            else:
                if self.current_index >= len(self.image_list):
                    self.current_index = len(self.image_list) - 1
                self.show_image(self.current_index)
            self.update_status(f"Moved to output directory: {filename}")
        except Exception as e:
            self.update_status(f"Move failed: {str(e)}")

    def delete_image(self, event=None):
        """Delete the current image after confirmation."""
        if not self.image_list:
            return

        current_image = self.image_list[self.current_index]
        filename = os.path.basename(current_image)

        if messagebox.askyesno(
            "Confirm Deletion",
            (f"Are you sure you want to delete:\n{filename}?\n\n"
             "This action cannot be undone!")
        ):
            try:
                os.remove(current_image)
                self.image_list.pop(self.current_index)

                if not self.image_list:
                    self.canvas.delete("all")
                    self.current_image_var.set("")
                    self.update_status("No images remaining")
                    self.update_progress()
                else:
                    if self.current_index >= len(self.image_list):
                        self.current_index = len(self.image_list) - 1
                    self.show_image(self.current_index)
                    self.update_status(f"Deleted: {filename}")

            except Exception as e:
                self.update_status(f"Deletion failed: {str(e)}")

    def rotate_image(self, event=None):
        """Rotate the image 90 degrees clockwise."""
        if self.original_image and self.image_list:
            self.current_rotation = (self.current_rotation + 90) % 360
            rotated = self.original_image.rotate(
                -self.current_rotation, expand=True
            )

            canvas_width = self.canvas.winfo_width()
            canvas_height = self.canvas.winfo_height()

            if canvas_width <= 1 or canvas_height <= 1:
                canvas_width = 800
                canvas_height = 500

            rotated.thumbnail(
                (int(canvas_width * 0.95), int(canvas_height * 0.95)),
                Image.Resampling.LANCZOS
            )

            img_tk = ImageTk.PhotoImage(rotated)

            self.canvas.image = img_tk
            self.canvas.delete("all")
            self.canvas.create_image(
                canvas_width // 2,
                canvas_height // 2,
                image=img_tk,
                anchor=tk.CENTER
            )

            self.update_status(f"Image rotated {self.current_rotation}°")

    def toggle_fullscreen(self, event=None):
        """Toggle fullscreen mode."""
        self.root.attributes(
            "-fullscreen", not self.root.attributes("-fullscreen")
        )
        if self.root.attributes("-fullscreen"):
            self.root.bind("<F11>", self.exit_fullscreen)
        else:
            self.root.unbind("<F11>")

    def exit_fullscreen(self, event=None):
        """Exit fullscreen mode."""
        self.root.attributes("-fullscreen", False)
        self.root.unbind("<F11>")

    def save_modified_image(self):
        """Save the modified image to a new file."""
        if not self.modified_image:
            self.update_status("No modified image to save.")
            return

        save_path = filedialog.asksaveasfilename(
            title="Save Modified Image",
            defaultextension=".png",
            filetypes=[
                ("PNG", "*.png"), ("JPEG", "*.jpg"), ("All files", "*.*")
            ]
        )
        if not save_path:
            return

        try:
            self.modified_image.save(save_path)
            self.update_status(f"Modified image saved to: {save_path}")
        except Exception as e:
            self.update_status(f"Error saving image: {e}")

    def apply_py_function(self):
        """Apply a Python function from a file to the current image."""
        if not self.original_image:
            self.update_status("No image loaded.")
            return

        py_file_path = filedialog.askopenfilename(
            title="Select Python Script",
            filetypes=[("Python files", "*.py")]
        )
        if not py_file_path:
            return

        try:
            spec = importlib.util.spec_from_file_location(
                "custom_module", py_file_path
            )
            custom_module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(custom_module)

            process_function = None
            for name, func in inspect.getmembers(
                custom_module, inspect.isfunction
            ):
                sig = inspect.signature(func)
                if len(sig.parameters) == 1:
                    process_function = func
                    break

            if not process_function:
                self.update_status("No suitable function found in the script.")
                return

            img_array = np.array(self.original_image)
            processed_array = process_function(img_array)

            self.modified_image = Image.fromarray(
                processed_array.astype('uint8')
            )
            self.show_image(
                self.current_index, image_to_show=self.modified_image
            )
            self.update_status(
                f"Applied function: {process_function.__name__}")

        except Exception as e:
            self.update_status(f"Error applying function: {e}")


def main():
    """Create the Tkinter window and run the application."""
    root = tk.Tk()
    app = EnhancedImageViewer(root)
    root.bind("<Configure>", app.resize_image)
    root.mainloop()


if __name__ == "__main__":
    main()
