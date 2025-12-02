import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from PIL import Image, ImageTk, ImageOps
import os
import shutil
import platform

class EnhancedImageViewer:
    def __init__(self, root):
        self.root = root
        self.root.title("Enhanced Image Viewer")
        self.root.geometry("1000x700")
        self.root.minsize(800, 600)
        
        # Set theme for modern look
        self.style = ttk.Style()
        self.style.theme_use('clam')
        
        # Configure custom styles
        self.style.configure('TButton', padding=6, font=('Segoe UI', 10))
        self.style.configure('Title.TLabel', font=('Segoe UI', 14, 'bold'), foreground='#333333')
        self.style.configure('Status.TLabel', font=('Segoe UI', 9), foreground='#666666')
        self.style.configure('Bold.TLabel', font=('Segoe UI', 9, 'bold'))
        
        # Initialize variables
        self.image_dir = ""
        self.image_list = []
        self.current_index = 0
        self.output_dir = ""
        self.original_image = None
        self.current_rotation = 0
        
        # Create UI elements
        self.create_widgets()
        
        # Bind keyboard events
        self.root.bind('<Left>', self.prev_image)
        self.root.bind('<Right>', self.next_image)
        self.root.bind('c', self.copy_image)
        self.root.bind('d', self.delete_image)
        self.root.bind('r', self.rotate_image)
        self.root.bind('f', self.toggle_fullscreen)
        self.root.bind('<Escape>', self.exit_fullscreen)
        
        # Handle high DPI displays
        self.scale_factor = self.get_scale_factor()
        
        # Set initial status
        self.update_status("Select image directory to start")
        
    def get_scale_factor(self):
        """Get display scaling factor for high DPI displays"""
        if platform.system() == 'Windows':
            from ctypes import windll
            try:
                windll.shcore.SetProcessDpiAwareness(1)
                return windll.shcore.GetScaleFactorForDevice(0) / 100
            except:
                return 1.0
        elif platform.system() == 'Darwin':  # macOS
            return 1.0  # Tkinter handles scaling automatically on macOS
        else:  # Linux
            return 1.0
    
    def create_widgets(self):
        # Create main frame
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Header with title and buttons
        header_frame = ttk.Frame(main_frame)
        header_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(header_frame, text="Enhanced Image Viewer", style='Title.TLabel').pack(side=tk.LEFT)
        
        # Action buttons
        btn_frame = ttk.Frame(header_frame)
        btn_frame.pack(side=tk.RIGHT)
        
        ttk.Button(btn_frame, text="Select Image Directory", command=self.select_image_dir).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Select Output Directory", command=self.select_output_dir).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Fullscreen (F)", command=self.toggle_fullscreen).pack(side=tk.LEFT, padx=5)
        
        # Image display area with shadow effect
        display_frame = ttk.LabelFrame(main_frame, text="Image Preview")
        display_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # Canvas for image display with scrollbars
        self.canvas = tk.Canvas(display_frame, bg='#f0f0f0', highlightthickness=0)
        self.canvas.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Navigation and info panel
        info_frame = ttk.Frame(main_frame)
        info_frame.pack(fill=tk.X, pady=10)
        
        # Navigation buttons
        nav_frame = ttk.Frame(info_frame)
        nav_frame.pack(side=tk.LEFT, padx=(0, 20))
        
        ttk.Button(nav_frame, text="◀ Previous (←)", command=self.prev_image, width=15).pack(side=tk.LEFT, padx=5)
        ttk.Button(nav_frame, text="Next (→) ▶", command=self.next_image, width=15).pack(side=tk.LEFT, padx=5)
        
        # Action buttons
        action_frame = ttk.Frame(info_frame)
        action_frame.pack(side=tk.LEFT, padx=(0, 20))
        
        ttk.Button(action_frame, text="Copy (C)", command=self.copy_image, width=12).pack(side=tk.LEFT, padx=5)
        ttk.Button(action_frame, text="Rotate (R)", command=self.rotate_image, width=12).pack(side=tk.LEFT, padx=5)
        ttk.Button(action_frame, text="Delete (D)", command=self.delete_image, width=12).pack(side=tk.LEFT, padx=5)
        
        # Image info
        info_panel = ttk.Frame(info_frame)
        info_panel.pack(side=tk.RIGHT, fill=tk.X, expand=True)
        
        ttk.Label(info_panel, text="Current Image:", style='Bold.TLabel').grid(row=0, column=0, sticky='w')
        self.current_image_var = tk.StringVar()
        ttk.Label(info_panel, textvariable=self.current_image_var).grid(row=0, column=1, sticky='w', padx=(5, 20))
        
        ttk.Label(info_panel, text="Output Directory:", style='Bold.TLabel').grid(row=0, column=2, sticky='w')
        self.output_dir_var = tk.StringVar()
        ttk.Label(info_panel, textvariable=self.output_dir_var, width=30).grid(row=0, column=3, sticky='w')
        
        # Status bar
        status_frame = ttk.Frame(self.root, relief=tk.SUNKEN)
        status_frame.pack(fill=tk.X, side=tk.BOTTOM)
        
        self.status_var = tk.StringVar()
        status_label = ttk.Label(status_frame, textvariable=self.status_var, style='Status.TLabel')
        status_label.pack(side=tk.LEFT, padx=10, pady=2)
        
        # Progress indicator
        self.progress_var = tk.StringVar()
        ttk.Label(status_frame, textvariable=self.progress_var, style='Status.TLabel').pack(side=tk.RIGHT, padx=10, pady=2)
    
    def update_status(self, message):
        """Update status bar with message"""
        self.status_var.set(message)
        self.root.update_idletasks()
    
    def update_progress(self):
        """Update progress indicator"""
        if self.image_list:
            self.progress_var.set(f"Image {self.current_index + 1} of {len(self.image_list)}")
        else:
            self.progress_var.set("")
    
    def select_image_dir(self):
        """Select directory containing images"""
        self.image_dir = filedialog.askdirectory(title="Select Image Directory")
        if self.image_dir:
            self.load_images()
            self.show_image(0)
    
    def select_output_dir(self):
        """Select directory for output images"""
        self.output_dir = filedialog.askdirectory(title="Select Output Directory")
        if self.output_dir:
            self.output_dir_var.set(os.path.basename(self.output_dir))
            self.update_status(f"Output directory set to: {self.output_dir}")
    
    def load_images(self):
        """Load valid image files from selected directory"""
        valid_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp', '.tiff']
        self.image_list = [
            os.path.join(self.image_dir, f) 
            for f in os.listdir(self.image_dir) 
            if os.path.splitext(f)[1].lower() in valid_extensions
        ]
        self.image_list.sort()
        
        if self.image_list:
            self.update_status(f"Loaded {len(self.image_list)} images. Navigation: ← → keys. Actions: C=Copy, R=Rotate, D=Delete")
        else:
            self.update_status("No images found in selected directory")
        
        self.update_progress()
    
    def show_image(self, index):
        """Display image at specified index"""
        if not self.image_list:
            return
            
        # Keep index within bounds
        if index < 0:
            index = 0
        elif index >= len(self.image_list):
            index = len(self.image_list) - 1
            
        self.current_index = index
        image_path = self.image_list[index]
        
        try:
            # Clear canvas before loading new image
            self.canvas.delete("all")
            
            # Open image
            self.original_image = Image.open(image_path)
            self.current_rotation = 0  # Reset rotation
            
            # Rotate based on EXIF orientation
            self.original_image = ImageOps.exif_transpose(self.original_image)
            
            # Get canvas dimensions
            canvas_width = self.canvas.winfo_width()
            canvas_height = self.canvas.winfo_height()
            
            # Calculate dimensions if canvas is too small
            if canvas_width <= 1 or canvas_height <= 1:
                canvas_width = 800
                canvas_height = 500
            
            # Resize image while maintaining aspect ratio
            img = self.original_image.copy()
            img.thumbnail(
                (int(canvas_width * 0.95), int(canvas_height * 0.95)), 
                Image.Resampling.LANCZOS
            )
            
            # Convert for Tkinter
            img_tk = ImageTk.PhotoImage(img)
            
            # Display image on canvas
            self.canvas.image = img_tk  # Keep reference
            self.canvas.create_image(
                canvas_width // 2, 
                canvas_height // 2, 
                image=img_tk, 
                anchor=tk.CENTER
            )
            
            # Update image info
            filename = os.path.basename(image_path)
            self.current_image_var.set(f"{filename} ({img.width}×{img.height})")
            
            # Update status
            self.update_progress()
        except Exception as e:
            self.update_status(f"Error loading image: {str(e)}")
    
    def resize_image(self, event):
        """Resize image when window size changes"""
        if self.original_image and self.image_list:
            self.show_image(self.current_index)
    
    def next_image(self, event=None):
        """Show next image"""
        if self.image_list and self.current_index < len(self.image_list) - 1:
            self.show_image(self.current_index + 1)
    
    def prev_image(self, event=None):
        """Show previous image"""
        if self.image_list and self.current_index > 0:
            self.show_image(self.current_index - 1)
    
    def copy_image(self, event=None):
        """Copy current image to output directory"""
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
    
    def delete_image(self, event=None):
        """Delete current image after confirmation"""
        if not self.image_list:
            return
            
        current_image = self.image_list[self.current_index]
        filename = os.path.basename(current_image)
        
        if messagebox.askyesno(
            "Confirm Deletion", 
            f"Are you sure you want to delete:\n{filename}?\n\nThis action cannot be undone!"
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
                    # Show next image if available, otherwise previous
                    if self.current_index >= len(self.image_list):
                        self.current_index = len(self.image_list) - 1
                    self.show_image(self.current_index)
                    self.update_status(f"Deleted: {filename}")
                
            except Exception as e:
                self.update_status(f"Deletion failed: {str(e)}")
    
    def rotate_image(self, event=None):
        """Rotate image 90 degrees clockwise"""
        if self.original_image and self.image_list:
            self.current_rotation = (self.current_rotation + 90) % 360
            rotated = self.original_image.rotate(-self.current_rotation, expand=True)
            
            # Get canvas dimensions
            canvas_width = self.canvas.winfo_width()
            canvas_height = self.canvas.winfo_height()
            
            # Calculate dimensions if canvas is too small
            if canvas_width <= 1 or canvas_height <= 1:
                canvas_width = 800
                canvas_height = 500
            
            # Resize rotated image
            rotated.thumbnail(
                (int(canvas_width * 0.95), int(canvas_height * 0.95)), 
                Image.Resampling.LANCZOS
            )
            
            # Convert for Tkinter
            img_tk = ImageTk.PhotoImage(rotated)
            
            # Display rotated image
            self.canvas.image = img_tk  # Keep reference
            self.canvas.delete("all")
            self.canvas.create_image(
                canvas_width // 2, 
                canvas_height // 2, 
                image=img_tk, 
                anchor=tk.CENTER
            )
            
            self.update_status(f"Image rotated {self.current_rotation}°")
    
    def toggle_fullscreen(self, event=None):
        """Toggle fullscreen mode"""
        self.root.attributes("-fullscreen", not self.root.attributes("-fullscreen"))
        if self.root.attributes("-fullscreen"):
            self.root.bind("<F11>", self.exit_fullscreen)
        else:
            self.root.unbind("<F11>")
    
    def exit_fullscreen(self, event=None):
        """Exit fullscreen mode"""
        self.root.attributes("-fullscreen", False)
        self.root.unbind("<F11>")

if __name__ == "__main__":
    root = tk.Tk()
    app = EnhancedImageViewer(root)
    
    # Bind resize event for responsive image display
    root.bind("<Configure>", app.resize_image)
    
    root.mainloop()