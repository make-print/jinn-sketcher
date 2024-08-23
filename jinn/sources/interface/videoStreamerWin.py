import os
import time
from datetime import datetime

import cv2
import ffmpeg
import numpy as np
import pyautogui
import pygetwindow as gw
import yaml

# Load configuration from YAML file
with open("./config.yml", "r") as config_file:
    config = yaml.safe_load(config_file)

# Configuration parameters
window_title: str = config["window_title"]
width: int = config["width"]
height: int = config["height"]
frame_rate: int = config["frame_rate"]
output_url: str = config["output_url"]
local_file: str = config.get("local_file")

# Directories for recordings and screenshots
recordings_dir: str = "recordings"
screenshots_dir: str = "screenshots"
os.makedirs(recordings_dir, exist_ok=True)
os.makedirs(screenshots_dir, exist_ok=True)

# Generate filenames with timestamps
timestamp: str = datetime.now().strftime("%Y%m%d_%H%M%S")
video_filename: str = f"{recordings_dir}/videoStreamer_{timestamp}.mp4"


def find_window(title: str) -> gw.Window:
    """
    Finds a window by its title.

    Args:
        title (str): The title of the window to find.

    Returns:
        gw.Window: The window object that matches the given title.

    Raises:
        Exception: If the window with the specified title is not found.
    """
    window = gw.getWindowsWithTitle(title)
    if window:
        return window[0]
    raise Exception(f"find_window: Window with title '{title}' not found")


def sanitize_filename(name: str) -> str:
    """
    Sanitizes a string to make it safe to use as a filename.

    Args:
        name (str): The name to sanitize.

    Returns:
        str: The sanitized filename.
    """
    return "".join(c for c in name if c.isalnum() or c in (' ', '_')).rstrip()


def capture_window(window_title: str) -> gw.Window:
    """
    Captures a screenshot of the specified window and saves it.

    Args:
        window_title (str): The title of the window to capture.

    Returns:
        gw.Window: The window object that was captured.

    Raises:
        Exception: If the window with the specified title is not found.
    """
    window = find_window(window_title)
    x, y, win_width, win_height = window.left, window.top, window.width, window.height

    # Capture screenshot of the specified window region
    screenshot = pyautogui.screenshot(region=(x, y, win_width, win_height))
    img = np.array(screenshot)
    img = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)
    img = cv2.resize(img, (width, height))

    # Save the screenshot
    sanitized_window_name = sanitize_filename(window_title)
    screenshot_filename = f"{screenshots_dir}/window_{sanitized_window_name}_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}.png"
    cv2.imwrite(screenshot_filename, img)

    return window


def capture_and_stream(window_title: str, width: int, height: int, frame_rate: int, output_url: str,
                       local_file: str) -> None:
    """
    Captures the specified window and streams or saves the video.

    Args:
        window_title (str): The title of the window to capture.
        width (int): The width of the output video.
        height (int): The height of the output video.
        frame_rate (int): The frame rate of the video capture.
        output_url (str): The URL to stream the video to (if applicable).
        local_file (str): The file path to save the video locally (if applicable).
    """
    window = capture_window(window_title)

    ffmpeg_input = ffmpeg.input('pipe:', format='rawvideo', pix_fmt='bgr24', s=f'{width}x{height}',
                                framerate=frame_rate)

    if local_file:
        ffmpeg_output_file = ffmpeg_input.output(local_file, pix_fmt='yuv420p', vcodec='libx264', preset='ultrafast',
                                                 r=frame_rate)
        file_process = ffmpeg_output_file.overwrite_output().run_async(pipe_stdin=True)
    else:
        file_process = None

    frame_interval: float = 1.0 / frame_rate
    next_frame_time: float = time.time() + frame_interval

    while True:
        try:
            # Capture the current frame from the window
            screenshot = pyautogui.screenshot(region=(window.left, window.top, window.width, window.height))
            img = np.array(screenshot)
            img = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)
            img = cv2.resize(img, (width, height))

            # Save the screenshot
            screenshot_filename = f"{screenshots_dir}/screenshot_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}.png"
            cv2.imwrite(screenshot_filename, img)

            # Stream or save the frame
            if file_process:
                file_process.stdin.write(img.tobytes())

            time.sleep(max(0, next_frame_time - time.time()))
            next_frame_time += frame_interval

        except KeyboardInterrupt:
            break

    if file_process:
        file_process.stdin.close()
        file_process.wait()


def main() -> None:
    """
    Main function that sets up the capture and streaming process.
    """
    try:
        window = find_window(window_title)
        capture_and_stream(window_title, width, height, frame_rate, output_url, video_filename)
    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    main()
