# import cv2
# import numpy as np
# import ffmpeg
# import yaml
# import time
# import Quartz
# import Quartz.CoreGraphics as CG
# import AppKit
# from PIL import Image
# import os
# from datetime import datetime
# import pyautogui

# # Load configuration from YAML file
# with open("./config.yml", "r") as config_file:
#     config = yaml.safe_load(config_file)

# # Configuration parameters
# window_title = config["window_title"]
# width = config["width"]
# height = config["height"]
# frame_rate = config["frame_rate"]
# output_url = config["output_url"]
# local_file = config.get("local_file")

# # Directories for recordings and screenshots
# recordings_dir = "recordings"
# screenshots_dir = "screenshots"
# os.makedirs(recordings_dir, exist_ok=True)
# os.makedirs(screenshots_dir, exist_ok=True)

# # Generate filenames with timestamps
# timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
# video_filename = f"{recordings_dir}/videoStreamer_{timestamp}.mp4"

# def find_window(title):
#     app = AppKit.NSWorkspace.sharedWorkspace()
#     windows = app.runningApplications()

#     for win in windows:
#         if win.localizedName() == title:
#             return win
#     raise Exception(f"find_window: Window with title '{title}' not found")

# # Directory for saving screenshots of windows
# windows_dir = "windows"
# os.makedirs(windows_dir, exist_ok=True)

# def sanitize_filename(name):
#     # Remove invalid characters from the filename
#     return "".join(c for c in name if c.isalnum() or c in (' ', '_')).rstrip()

# def capture_window(window_title):
#     options = Quartz.kCGWindowListOptionOnScreenOnly
#     window_list = Quartz.CGWindowListCopyWindowInfo(options, Quartz.kCGNullWindowID)
    
#     for win in window_list:
#         window_id = win['kCGWindowNumber']
#         bounds = win['kCGWindowBounds']
#         window_name = win.get('kCGWindowOwnerName', 'UnnamedWindow')
#         sanitized_window_name = sanitize_filename(window_name)
        
#         # Use pyautogui to capture the screenshot
#         screenshot = pyautogui.screenshot(region=(int(bounds['X']), int(bounds['Y']), int(bounds['Width']), int(bounds['Height'])))
#         img = np.array(screenshot)
#         img = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)
#         img = cv2.resize(img, (width, height))  # Resize the image

#         # Save the screenshot
#         screenshot_filename = f"{windows_dir}/window_{window_id}_{sanitized_window_name}_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}.png"
#         cv2.imwrite(screenshot_filename, img)
        
#         # Check if the window matches the criteria
#         if window_title in win.get('kCGWindowOwnerName', '') and win.get('kCGWindowName', '') != '':
#             return window_id, bounds
    
#     raise Exception(f"capture_window: Window with title '{window_title}' not found or has no name")

# def capture_and_stream(window_title, width, height, frame_rate, output_url, local_file):
#     window_id, bounds = capture_window(window_title)
    
#     ffmpeg_input = ffmpeg.input('pipe:', format='rawvideo', pix_fmt='bgr24', s=f'{width}x{height}', framerate=frame_rate)
    
#     if local_file:
#         ffmpeg_output_file = ffmpeg_input.output(local_file, pix_fmt='yuv420p', vcodec='libx264', preset='ultrafast', r=frame_rate)
#         file_process = ffmpeg_output_file.overwrite_output().run_async(pipe_stdin=True)
#     else:
#         file_process = None

#     frame_interval = 1.0 / frame_rate
#     next_frame_time = time.time() + frame_interval

#     while True:
#         try:
#             screenshot = pyautogui.screenshot(region=(int(bounds['X']), int(bounds['Y']), int(bounds['Width']), int(bounds['Height'])))
#             img = np.array(screenshot)
#             img = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)
#             img = cv2.resize(img, (width, height))  # Resize the image

#             screenshot_filename = f"{screenshots_dir}/screenshot_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}.png"
#             cv2.imwrite(screenshot_filename, img)

#             if file_process:
#                 file_process.stdin.write(img.tobytes())

#             time.sleep(max(0, next_frame_time - time.time()))
#             next_frame_time += frame_interval

#         except KeyboardInterrupt:
#             break

#     if file_process:
#         file_process.stdin.close()
#         file_process.wait() 

# def main():
#     try:
#         window = find_window(window_title)
#         capture_and_stream(window_title, width, height, frame_rate, output_url, video_filename)
#     except Exception as e:
#         print(f"Error: {e}")

# if __name__ == "__main__":
#     main()
