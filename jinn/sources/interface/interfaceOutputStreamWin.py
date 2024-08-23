import os
import socket
import threading
import time
from datetime import datetime

import cv2
import ffmpeg
import numpy as np
import pyautogui
import pygetwindow as gw
import yaml


class InterfaceOutputStreamWin:
    """
    A class to capture the content of a specified window, stream it, save it locally, or send it via a socket connection.

    Attributes:
        window_title (str): The title of the window to capture.
        width (int): The width of the captured video frames.
        height (int): The height of the captured video frames.
        frame_rate (int): The frame rate for capturing video.
        output_url (str): The URL to stream the video to (if applicable).
        local_file (str): The path to save the video locally (if applicable).
        recordings_dir (str): Directory where video recordings are saved.
        screenshots_dir (str): Directory where screenshots are saved.
        video_filename (str): The filename for the recorded video with a timestamp.
    """

    def __init__(self, config_path: str) -> None:
        """
        Initializes the InterfaceOutputStreamWin class with configuration parameters loaded from a YAML file.

        Args:
            config_path (str): The path to the configuration YAML file.
        """
        # Load configuration from YAML file
        with open(config_path, "r") as config_file:
            config = yaml.safe_load(config_file)

        # Configuration parameters
        self.window_title: str = config["window_title"]
        self.width: int = config["width"]
        self.height: int = config["height"]
        self.frame_rate: int = config["frame_rate"]
        self.output_url: str = config["output_url"]
        self.local_file: str = config.get("local_file")

        # Directories for recordings and screenshots
        self.recordings_dir: str = "recordings"
        self.screenshots_dir: str = "screenshots"
        os.makedirs(self.recordings_dir, exist_ok=True)
        os.makedirs(self.screenshots_dir, exist_ok=True)

        # Generate filenames with timestamps
        timestamp: str = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.video_filename: str = f"{self.recordings_dir}/videoStreamer_{timestamp}.mp4"

    def find_window(self, title: str) -> gw.Window:
        """
        Finds a window by its title.

        Args:
            title (str): The title of the window to find.

        Returns:
            gw.Window: The window object that matches the given title.

        Raises:
            Exception: If the window with the specified title is not found.
        """
        windows = gw.getWindowsWithTitle(title)
        if windows:
            return windows[0]
        raise Exception(f"find_window: Window with title '{title}' not found")

    @staticmethod
    def sanitize_filename(name: str) -> str:
        """
        Sanitizes a string to make it safe to use as a filename.

        Args:
            name (str): The name to sanitize.

        Returns:
            str: The sanitized filename.
        """
        return "".join(c for c in name if c.isalnum() or c in (' ', '_')).rstrip()

    def capture_window(self, window_title: str) -> gw.Box:
        """
        Captures a screenshot of the specified window and saves it.

        Args:
            window_title (str): The title of the window to capture.

        Returns:
            gw.Box: The bounding box of the captured window.
        """
        window = self.find_window(window_title)
        bounds = window.box

        # Capture the screenshot of the specified window region
        screenshot = pyautogui.screenshot(
            region=(bounds.left, bounds.top, bounds.width, bounds.height)
        )
        img = np.array(screenshot)
        img = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)
        img = cv2.resize(img, (self.width, self.height))  # Resize the image

        # Save the screenshot
        sanitized_window_name = self.sanitize_filename(window_title)
        screenshot_filename = f"{self.screenshots_dir}/window_{sanitized_window_name}_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}.png"
        cv2.imwrite(screenshot_filename, img)

        return bounds

    def capture_and_stream(
            self,
            window_title: str,
            width: int,
            height: int,
            frame_rate: int,
            output_url: str,
            local_file: str,
            frame_conn: socket.socket
    ) -> None:
        """
        Continuously captures the window content, optionally streams or saves the video, and sends frames over a socket connection.

        Args:
            window_title (str): The title of the window to capture.
            width (int): The width of the output video.
            height (int): The height of the output video.
            frame_rate (int): The frame rate of the video capture.
            output_url (str): The URL to stream the video to (if applicable).
            local_file (str): The file path to save the video locally (if applicable).
            frame_conn (socket.socket): A socket connection to send frames to a server.
        """
        bounds = self.capture_window(window_title)

        ffmpeg_input = ffmpeg.input(
            'pipe:', format='rawvideo', pix_fmt='bgr24', s=f'{width}x{height}', framerate=frame_rate
        )

        if local_file:
            ffmpeg_output_file = ffmpeg_input.output(
                local_file, pix_fmt='yuv420p', vcodec='libx264', preset='ultrafast', r=frame_rate
            )
            file_process = ffmpeg_output_file.overwrite_output().run_async(pipe_stdin=True)
        else:
            file_process = None

        frame_interval: float = 1.0 / frame_rate
        next_frame_time: float = time.time() + frame_interval

        try:
            while True:
                # Capture the current frame from the window
                screenshot = pyautogui.screenshot(
                    region=(bounds.left, bounds.top, bounds.width, bounds.height)
                )
                img = np.array(screenshot)
                img = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)
                img = cv2.resize(img, (width, height))  # Resize the image

                if img.size != width * height * 3:
                    print("Captured frame size does not match expected size.")
                    continue

                # Save the screenshot
                screenshot_filename = f"{self.screenshots_dir}/screenshot_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}.png"
                cv2.imwrite(screenshot_filename, img)

                # Stream or save the frame
                if file_process:
                    file_process.stdin.write(img.tobytes())

                # Send the frame over the socket connection
                if frame_conn:
                    try:
                        frame_conn.sendall(img.tobytes())
                    except BrokenPipeError:
                        print("Frame connection broken. Exiting.")
                        break

                # Sleep to maintain the correct frame rate
                time.sleep(max(0, next_frame_time - time.time()))
                next_frame_time += frame_interval

        except KeyboardInterrupt:
            pass
        finally:
            if file_process:
                file_process.stdin.close()
                file_process.wait()

    def start(self) -> None:
        """
        Starts the capture and streaming process and initiates the prompt-sending process via socket connections.
        """

        def prompt_sender(prompt_conn: socket.socket) -> None:
            """
            Continuously prompts the user for input and sends the input to a server via a socket connection.

            Args:
                prompt_conn (socket.socket): A socket connection for sending user prompts.
            """
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
        threading.Thread(
            target=self.capture_and_stream, args=(
                self.window_title, self.width, self.height, self.frame_rate, self.output_url, self.video_filename,
                frame_socket
            )
        ).start()

        # Initialize prompt socket connection
        prompt_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        prompt_socket.connect(('localhost', 9998))
        threading.Thread(target=prompt_sender, args=(prompt_socket,)).start()


def main() -> None:
    """
    Main function that sets up the capture and streaming process.
    """
    try:
        config_path = "./config.yml"
        out_stream = InterfaceOutputStreamWin(config_path)
        out_stream.start()
    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    main()
