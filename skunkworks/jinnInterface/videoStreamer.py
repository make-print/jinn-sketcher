import cv2
import numpy as np
import pygetwindow as gw
import ffmpeg
import yaml
import time

# Load configuration from YAML file
with open("config.yaml", "r") as config_file:
    config = yaml.safe_load(config_file)

# Configuration parameters
window_title = config["window_title"]
width = config["width"]
height = config["height"]
frame_rate = config["frame_rate"]
output_url = config["output_url"]

def find_window(title):
    windows = gw.getWindowsWithTitle(title)
    if windows:
        return windows[0]
    else:
        raise Exception(f"Window with title '{title}' not found")

def capture_and_stream(window, width, height, frame_rate, output_url):
    # Define the command for FFmpeg to stream the video
    process = (
        ffmpeg
        .input('pipe:', format='rawvideo', pix_fmt='bgr24', s=f'{width}x{height}', framerate=frame_rate)
        .output(output_url, pix_fmt='yuv420p', vcodec='libx264', preset='ultrafast', f='flv')
        .overwrite_output()
        .run_async(pipe_stdin=True)
    )

    while True:
        try:
            # Capture the window
            img = np.array(window.screenshot())
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
        capture_and_stream(window, width, height, frame_rate, output_url)
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
