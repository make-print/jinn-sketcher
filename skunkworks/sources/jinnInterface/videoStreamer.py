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

# Load configuration from YAML file
with open("./config.yml", "r") as config_file:
    config = yaml.safe_load(config_file)

# Configuration parameters
window_title = config["window_title"]
width = config["width"]
height = config["height"]
frame_rate = config["frame_rate"]
output_url = config["output_url"]
local_file = config.get("local_file")

# Directories for recordings and screenshots
recordings_dir = "recordings"
screenshots_dir = "screenshots"
os.makedirs(recordings_dir, exist_ok=True)
os.makedirs(screenshots_dir, exist_ok=True)

# Generate filenames with timestamps
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
video_filename = f"{recordings_dir}/videoStreamer_{timestamp}.mp4"

def find_window(title):
    app = AppKit.NSWorkspace.sharedWorkspace()
    windows = app.runningApplications()

    for win in windows:
        print(win, win.localizedName())
        if win.localizedName() == title:
            return win
    raise Exception(f"find_window: Window with title '{title}' not found")

# Directory for saving screenshots of windows
windows_dir = "windows"
os.makedirs(windows_dir, exist_ok=True)

def sanitize_filename(name):
    # Remove invalid characters from the filename
    return "".join(c for c in name if c.isalnum() or c in (' ', '_')).rstrip()

def capture_window(window_title):
    options = Quartz.kCGWindowListOptionOnScreenOnly
    window_list = Quartz.CGWindowListCopyWindowInfo(options, Quartz.kCGNullWindowID)
    
    for win in window_list:
        print(f"Window: {win}")
        
        # Capture and save the screenshot of each window
        window_id = win['kCGWindowNumber']
        bounds = win['kCGWindowBounds']
        window_name = win.get('kCGWindowOwnerName', 'UnnamedWindow')
        sanitized_window_name = sanitize_filename(window_name)
        rect = CG.CGRectMake(bounds['X'], bounds['Y'], bounds['Width'], bounds['Height'])
        screenshot = CG.CGWindowListCreateImage(rect, CG.kCGWindowListOptionIncludingWindow, window_id, CG.kCGWindowImageDefault)
        
        if screenshot is not None:
            width = CG.CGImageGetWidth(screenshot)
            height = CG.CGImageGetHeight(screenshot)
            provider = CG.CGImageGetDataProvider(screenshot)
            data = CG.CGDataProviderCopyData(provider)
            img_data = bytes(data)

            img = Image.frombytes('RGBA', (width, height), img_data)
            img = img.convert('RGB')  # Convert to RGB format
            img = np.array(img)
            img = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)
            img = cv2.resize(img, (width, height))  # Resize the image

            # Save the screenshot
            screenshot_filename = f"{windows_dir}/window_{window_id}_{sanitized_window_name}_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}.png"
            cv2.imwrite(screenshot_filename, img)
            print(f'Screenshot saved: {screenshot_filename}')
        
        # Check if the window matches the criteria
        if window_title in win.get('kCGWindowOwnerName', '') and win.get('kCGWindowName', '') != '':
            return window_id, bounds
    
    raise Exception(f"capture_window: Window with title '{window_title}' not found or has no name")

def capture_and_stream(window_title, width, height, frame_rate, output_url, local_file):
    window_id, bounds = capture_window(window_title)
    print(f"Window ID: {window_id}")
    print(f"Window bounds: {bounds}")
    
    ffmpeg_input = ffmpeg.input('pipe:', format='rawvideo', pix_fmt='bgr24', s=f'{width}x{height}', framerate=frame_rate)
    
    print(f"Setting up output streams")
    
    if local_file:
        print(f'Local file is defined')
        ffmpeg_output_file = ffmpeg_input.output(local_file, pix_fmt='yuv420p', vcodec='libx264', preset='ultrafast')
        file_process = ffmpeg_output_file.overwrite_output().run_async(pipe_stdin=True)
    else:
        file_process = None

    while True:
        try:
            rect = CG.CGRectMake(bounds['X'], bounds['Y'], bounds['Width'], bounds['Height'])
            print(f"Rect: {rect}")
            screenshot = CG.CGWindowListCreateImage(rect, CG.kCGWindowListOptionIncludingWindow, window_id, CG.kCGWindowImageDefault)
            print(f'Capturing window: {window_title}')
            print(f'Screenshot: {screenshot}')
            if screenshot is None:
                print('Screen shot is None')
                raise Exception(f"Could not capture window '{window_title}'")
            
            width = CG.CGImageGetWidth(screenshot)
            height = CG.CGImageGetHeight(screenshot)
            provider = CG.CGImageGetDataProvider(screenshot)
            data = CG.CGDataProviderCopyData(provider)
            img_data = bytes(data)

            img = Image.frombytes('RGBA', (width, height), img_data)
            img = img.convert('RGB')  # Convert to RGB format
            img = np.array(img)
            img = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)
            img = cv2.resize(img, (width, height))  # Resize the image

            # Save each screenshot
            screenshot_filename = f"{screenshots_dir}/screenshot_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}.png"
            cv2.imwrite(screenshot_filename, img)
            print(f'Screenshot saved: {screenshot_filename}')

            print(f'Captured image: {img.shape}')

            if file_process:
                file_process.stdin.write(img.tobytes())

            time.sleep(1 / frame_rate)

        except KeyboardInterrupt:
            break

    if file_process:
        file_process.stdin.close()
        file_process.wait() 

def main():
    try:
        window = find_window(window_title)
        print(f'Found window: {window}')
        capture_and_stream(window_title, width, height, frame_rate, output_url, video_filename)
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
