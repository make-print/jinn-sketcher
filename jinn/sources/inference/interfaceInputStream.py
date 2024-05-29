import socket
import threading

import cv2
import numpy as np


class InterfaceInputStream:
    def __init__(self, frame_host, frame_port, prompt_host, prompt_port, width, height):
        self.frame_host = frame_host
        self.frame_port = frame_port
        self.prompt_host = prompt_host
        self.prompt_port = prompt_port
        self.width = width
        self.height = height
        self.last_prompt = None
        self.latest_frames = []

    def start_prompt_server(self):
        def receive_prompts(conn):
            while True:
                try:
                    prompt = conn.recv(1024).decode('utf-8')
                    if prompt:
                        self.last_prompt = prompt
                        print(f"Received prompt: {prompt}")
                except Exception as e:
                    print(f"Error receiving prompt: {e}")
                    break

        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind((self.prompt_host, self.prompt_port))
            s.listen(1)
            print(f"Listening for prompts on {self.prompt_host}:{self.prompt_port}")

            conn, addr = s.accept()
            with conn:
                print(f"Connected to prompt sender at {addr}")
                receive_prompts(conn)

    def start_frame_server(self):
        def receive_frames(conn):
            frame_size = self.width * self.height * 3
            while True:
                try:
                    frame_data = conn.recv(frame_size)
                    if not frame_data or len(frame_data) != frame_size:
                        break
                    frame = np.frombuffer(frame_data, dtype=np.uint8).reshape((self.height, self.width, 3))
                    if len(self.latest_frames) >= self.n_frames:
                        self.latest_frames.pop(0)
                    self.latest_frames.append(frame)
                    # cv2.imshow('Frame', frame)
                    if cv2.waitKey(1) & 0xFF == ord('q'):
                        break
                except Exception as e:
                    print(f"Error receiving frame: {e}")
                    break
            cv2.destroyAllWindows()

        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind((self.frame_host, self.frame_port))
            s.listen(1)
            print(f"Listening for frames on {self.frame_host}:{self.frame_port}")

            conn, addr = s.accept()
            with conn:
                print(f"Connected to frame sender at {addr}")
                receive_frames(conn)

    def get_prompt(self):
        return self.last_prompt

    def get_latest_frames(self, n):
        if len(self.latest_frames) < n:
            return self.latest_frames[:]
        return self.latest_frames[-n:]


if __name__ == "__main__":
    frame_host = 'localhost'
    frame_port = 9999
    prompt_host = 'localhost'
    prompt_port = 9998

    in_stream = InterfaceInputStream(frame_host, frame_port, prompt_host, prompt_port, 1280, 720)
    threading.Thread(target=in_stream.start_frame_server).start()
    threading.Thread(target=in_stream.start_prompt_server).start()
