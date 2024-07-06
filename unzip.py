import time
import zipfile
import os
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

class DownloadHandler(FileSystemEventHandler):
    def __init__(self):
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

if __name__ == "__main__":
    download_folder = r'C:\\Users\\Sahil\\Downloads'
    event_handler = DownloadHandler()
    observer = Observer()
    observer.schedule(event_handler, path=download_folder, recursive=False)
    observer.start()
    print(f'Monitoring {download_folder} for new zip files...')
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()
  