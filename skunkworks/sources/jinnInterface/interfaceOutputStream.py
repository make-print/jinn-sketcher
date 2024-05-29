import cv2
import numpy as np
import ffmpeg
import yaml
import time
import Quartz
import Quartz.CoreGraphics as CG
import AppKit
from PIL import Image
import os
from datetime import datetime
import pyautogui
import socket
import threading

class InterfaceOutputStream:
    def __init__(self, config_path):
        # Load configuration from YAML file
        with open(config_path, "r") as config_file:
            config = yaml.safe_load(config_file)

        # Configuration parameters
        self.window_title = config["window_title"]
        self.width = config["width"]
        self.height = config["height"]
        self.frame_rate = config["frame_rate"]
        self.output_url = config["output_url"]
        self.local_file = config.get("local_file")

        # Directories for recordings and screenshots
        self.recordings_dir = "recordings"
        self.screenshots_dir = "screenshots"
        os.makedirs(self.recordings_dir, exist_ok=True)
        os.makedirs(self.screenshots_dir, exist_ok=True)

        # Generate filenames with timestamps
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.video_filename = f"{self.recordings_dir}/videoStreamer_{timestamp}.mp4"

    def find_window(self, title):
        app = AppKit.NSWorkspace.sharedWorkspace()
        windows = app.runningApplications()

        for win in windows:
            if win.localizedName() == title:
                return win
        raise Exception(f"find_window: Window with title '{title}' not found")

    def sanitize_filename(self, name):
        # Remove invalid characters from the filename
        return "".join(c for c in name if c.isalnum() or c in (' ', '_')).rstrip()

    def capture_window(self, window_title):
        options = Quartz.kCGWindowListOptionOnScreenOnly
        window_list = Quartz.CGWindowListCopyWindowInfo(options, Quartz.kCGNullWindowID)
        
        for win in window_list:
            window_id = win['kCGWindowNumber']
            bounds = win['kCGWindowBounds']
            window_name = win.get('kCGWindowOwnerName', 'UnnamedWindow')
            sanitized_window_name = self.sanitize_filename(window_name)
            
            # Use pyautogui to capture the screenshot
            screenshot = pyautogui.screenshot(region=(int(bounds['X']), int(bounds['Y']), int(bounds['Width']), int(bounds['Height'])))
            img = np.array(screenshot)
            img = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)
            img = cv2.resize(img, (self.width, self.height))  # Resize the image

            # Save the screenshot
            screenshot_filename = f"{self.screenshots_dir}/window_{window_id}_{sanitized_window_name}_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}.png"
            cv2.imwrite(screenshot_filename, img)
            
            # Check if the window matches the criteria
            if window_title in win.get('kCGWindowOwnerName', '') and win.get('kCGWindowName', '') != '':
                return window_id, bounds
        
        raise Exception(f"capture_window: Window with title '{window_title}' not found or has no name")

    def capture_and_stream(self, window_title, width, height, frame_rate, output_url, local_file, frame_conn):
        window_id, bounds = self.capture_window(window_title)
        
        ffmpeg_input = ffmpeg.input('pipe:', format='rawvideo', pix_fmt='bgr24', s=f'{width}x{height}', framerate=frame_rate)
        
        if local_file:
            ffmpeg_output_file = ffmpeg_input.output(local_file, pix_fmt='yuv420p', vcodec='libx264', preset='ultrafast', r=frame_rate)
            file_process = ffmpeg_output_file.overwrite_output().run_async(pipe_stdin=True)
        else:
            file_process = None

        frame_interval = 1.0 / frame_rate
        next_frame_time = time.time() + frame_interval

        try:
            while True:
                screenshot = pyautogui.screenshot(region=(int(bounds['X']), int(bounds['Y']), int(bounds['Width']), int(bounds['Height'])))
                img = np.array(screenshot)
                img = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)
                img = cv2.resize(img, (width, height))  # Resize the image

                if img.size != width * height * 3:
                    print("Captured frame size does not match expected size.")
                    continue

                screenshot_filename = f"{self.screenshots_dir}/screenshot_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}.png"
                cv2.imwrite(screenshot_filename, img)

                if file_process:
                    file_process.stdin.write(img.tobytes())

                if frame_conn:
                    try:
                        frame_conn.sendall(img.tobytes())
                    except BrokenPipeError:
                        print("Frame connection broken. Exiting.")
                        break

                time.sleep(max(0, next_frame_time - time.time()))
                next_frame_time += frame_interval

        except KeyboardInterrupt:
            pass
        finally:
            if file_process:
                file_process.stdin.close()
                file_process.wait()


    def start(self):
        def prompt_sender(prompt_conn):
            while True:
                user_prompt = input("Enter prompt: ")
                try:
                    prompt_conn.sendall(user_prompt.encode('utf-8'))
                except BrokenPipeError:
                    print("Prompt connection broken. Exiting.")
                    break

        # Initialize frame socket connection
        frame_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        frame_socket.connect(('localhost', 9999))
        threading.Thread(target=self.capture_and_stream, args=(self.window_title, self.width, self.height, self.frame_rate, self.output_url, self.video_filename, frame_socket)).start()

        # Initialize prompt socket connection
        prompt_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        prompt_socket.connect(('localhost', 9998))
        threading.Thread(target=prompt_sender, args=(prompt_socket,)).start()

def main():
    try:
        config_path = "./config.yml"
        out_stream = InterfaceOutputStream(config_path)
        out_stream.start()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
