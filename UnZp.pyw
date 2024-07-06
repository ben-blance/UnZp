import time
import zipfile
import os
import tkinter as tk
from tkinter import messagebox, ttk
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import pystray
from pystray import MenuItem as item
from PIL import Image, ImageDraw
import threading
import winreg
import sys

class DownloadHandler(FileSystemEventHandler):
    def __init__(self, app):
        super().__init__()
        self.app = app
        self.processing = set()

    def on_created(self, event):
        self.handle_event(event)

    def on_modified(self, event):
        self.handle_event(event)

    def handle_event(self, event):
        if event.is_directory:
            return
        if event.src_path.endswith('.zip') and event.src_path not in self.processing:
            self.processing.add(event.src_path)
            time.sleep(1)  # Wait for the download to complete
            self.unzip_file(event.src_path)
            self.processing.remove(event.src_path)

    def unzip_file(self, zip_path):
        if not os.path.exists(zip_path):
            print(f"File {zip_path} no longer exists. Skipping.")
            return
        extract_path = os.path.splitext(zip_path)[0]
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(extract_path)
        print(f'Unzipped {zip_path} to {extract_path}')

        # Check if the "Automatically delete file after extraction" option is selected
        if self.app.auto_delete_var.get():
            try:
                os.remove(zip_path)
                print(f'Deleted zip file: {zip_path}')
            except Exception as e:
                print(f'Failed to delete zip file: {e}')

class Application(tk.Frame):
    def __init__(self, master=None):
        super().__init__(master)
        self.master = master
        self.master.configure(bg='#f0f0f0')  # Light background color
        self.pack(fill=tk.BOTH, expand=True)
        self.running = False
        self.observer = None  # Initialize observer instance

        self.create_widgets()

        self.download_folder = r'C:\\Users\\Sahil\\Downloads'
        self.event_handler = DownloadHandler(self)

        # Start monitoring automatically
        self.start_monitoring()

        # Start hidden
        self.hide()

        # Check and update startup settings
        self.check_startup_status()
        self.update_startup()

    def create_widgets(self):
        # Configure style for ttk widgets
        style = ttk.Style()
        style.configure('TLabel', font=('Segoe UI', 10))
        style.configure('TButton', font=('Segoe UI', 10))
        style.configure('TCheckbutton', font=('Segoe UI', 10))

        # Frame for the main content
        content_frame = ttk.Frame(self)
        content_frame.pack(padx=20, pady=20, fill=tk.BOTH, expand=True)

        # Status label
        self.status_label = ttk.Label(content_frame, text="Status: running", foreground='green', padding=10)
        self.status_label.pack(pady=10)

        # Stop button
        self.stop_button = ttk.Button(content_frame, text="Stop", command=self.stop_monitoring)
        self.stop_button.pack(pady=5)

        # Hide button
        self.hide_button = ttk.Button(content_frame, text="Hide", command=self.hide)
        self.hide_button.pack(pady=5)

        # Launch on startup checkbox
        self.launch_on_startup_var = tk.BooleanVar()
        self.launch_on_startup_checkbox = ttk.Checkbutton(content_frame, text="Launch when Windows starts",
                                                          variable=self.launch_on_startup_var,
                                                          command=self.update_startup)
        self.launch_on_startup_checkbox.pack(pady=5)

        # Automatically delete file after extraction checkbox
        self.auto_delete_var = tk.BooleanVar()
        self.auto_delete_checkbox = ttk.Checkbutton(content_frame, text="Automatically delete file after extraction",
                                                    variable=self.auto_delete_var)
        self.auto_delete_checkbox.pack(pady=5)

    def start_monitoring(self):
        if not self.running:
            if self.observer is None:
                self.observer = Observer()
                self.observer.schedule(self.event_handler, path=self.download_folder, recursive=False)
            self.observer.start()
            self.running = True
            print(f'Monitoring {self.download_folder} for new zip files...')
        else:
            messagebox.showwarning("Warning", "Already running!")

    def stop_monitoring(self):
        if self.running:
            self.observer.stop()
            self.observer.join()
            self.observer = None  # Reset observer instance
            self.running = False
            self.status_label.config(text="Status: not running", foreground='red')
            print('Monitoring stopped.')
        else:
            messagebox.showwarning("Warning", "Not running!")

    def hide(self):
        self.master.withdraw()
        self.show_tray_icon()

    def show_tray_icon(self):
        def create_image(width, height, color1, color2):
            image = Image.new('RGB', (width, height), color1)
            dc = ImageDraw.Draw(image)
            dc.rectangle(
                (width // 2, 0, width, height // 2),
                fill=color2)
            dc.rectangle(
                (0, height // 2, width // 2, height),
                fill=color2)
            return image

        def on_show_window(icon, item):
            icon.stop()
            self.master.deiconify()

        def on_exit(icon, item):
            icon.stop()
            os._exit(0)

        menu = (item('Show', on_show_window), item('Exit', on_exit))
        icon_image = create_image(64, 64, 'black', 'white')
        icon = pystray.Icon("UnZp", icon_image, "UnZp", menu)
        threading.Thread(target=icon.run).start()

    def check_startup_status(self):
        try:
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Run") as key:
                try:
                    winreg.QueryValueEx(key, "UnZp")
                    self.launch_on_startup_var.set(True)
                except FileNotFoundError:
                    self.launch_on_startup_var.set(False)
        except OSError as e:
            print(f"Error accessing registry: {e}")

    def update_startup(self):
        if self.launch_on_startup_var.get():
            self.add_to_startup()
        else:
            self.remove_from_startup()

    def add_to_startup(self):
        try:
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Run", 0, winreg.KEY_SET_VALUE) as key:
                script_path = os.path.abspath(__file__)
                pythonw_path = os.path.join(os.path.dirname(sys.executable), 'pythonw.exe')
                command = f'"{pythonw_path}" "{script_path}"'
                winreg.SetValueEx(key, "UnZp", 0, winreg.REG_SZ, command)
        except OSError as e:
            messagebox.showerror("Error", f"Failed to add to startup: {e}")

    def remove_from_startup(self):
        try:
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Run", 0, winreg.KEY_SET_VALUE) as key:
                winreg.DeleteValue(key, "UnZp")
        except FileNotFoundError:
            pass
        except OSError as e:
            messagebox.showerror("Error", f"Failed to remove from startup: {e}")

if __name__ == "__main__":
    root = tk.Tk()
    root.title("UnZp")
    app = Application(master=root)
    app.mainloop()



