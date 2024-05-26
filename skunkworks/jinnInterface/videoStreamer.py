import cv2
import numpy as np
import ffmpeg
import yaml
import time
import Quartz
import AppKit

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

def find_window(title):
    app = AppKit.NSWorkspace.sharedWorkspace()
    windows = app.runningApplications()
    for win in windows:
        if win.localizedName() == title:
            return win
    raise Exception(f"Window with title '{title}' not found")

def capture_window(window):
    options = Quartz.kCGWindowListOptionOnScreenOnly
    window_list = Quartz.CGWindowListCopyWindowInfo(options, Quartz.kCGNullWindowID)
    for win in window_list:
        if window_title in win.get('kCGWindowName', ''):
            window_id = win['kCGWindowNumber']
            bounds = win['kCGWindowBounds']
            return window_id, bounds
    raise Exception(f"Window with title '{window_title}' not found")

def capture_and_stream(window, width, height, frame_rate, output_url, local_file):
    window_id, bounds = capture_window(window)
    # Define the command for FFmpeg to stream the video
    ffmpeg_input = ffmpeg.input('pipe:', format='rawvideo', pix_fmt='bgr24', s=f'{width}x{height}', framerate=frame_rate)
    
    # Chain the output streams correctly
    ffmpeg_output = ffmpeg_input.output(output_url, pix_fmt='yuv420p', vcodec='libx264', preset='ultrafast', f='flv')
    if local_file:
        ffmpeg_output = ffmpeg_output.output(local_file, pix_fmt='yuv420p', vcodec='libx264', preset='ultrafast')
    
    process = ffmpeg_output.overwrite_output().run_async(pipe_stdin=True)

    while True:
        try:
            screenshot = Quartz.CGWindowListCreateImage(bounds, Quartz.kCGWindowListOptionIncludingWindow, window_id, Quartz.kCGWindowImageDefault)
            if screenshot is None:
                raise Exception(f"Could not capture window '{window_title}'")
            
            img = np.array(Quartz.CGImageToImageRef(screenshot))
            img = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)
            img = cv2.resize(img, (width, height))

            # Write to FFmpeg's stdin
            process.stdin.write(img.tobytes())

            # Control the frame rate
            time.sleep(1 / frame_rate)

        except KeyboardInterrupt:
            break

    process.stdin.close()
    process.wait()

def main():
    try:
        window = find_window(window_title)
        capture_and_stream(window, width, height, frame_rate, output_url, local_file)
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
