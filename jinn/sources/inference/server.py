import argparse
import threading

from PIL import Image
from huggingface_hub import login
from transformers import AutoProcessor, PaliGemmaForConditionalGeneration

import interfaceInputStream

# Login to Hugging Face Hub
login(token="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")


class InferenceServer:
    def __init__(self, model_id, frame_host, frame_port, prompt_host, prompt_port, width, height, n_frames):
        self.model_id = model_id
        self.processor = AutoProcessor.from_pretrained(model_id)
        self.model = PaliGemmaForConditionalGeneration.from_pretrained(model_id)
        self.in_stream = interfaceInputStream.InterfaceInputStream(
            frame_host,
            frame_port,
            prompt_host,
            prompt_port,
            width, height)
        self.n_frames = n_frames

    def run_inference(self):
        while True:
            prompt = self.in_stream.get_prompt()
            frames = self.in_stream.get_latest_frames(self.n_frames)

            if prompt and len(frames) == self.n_frames:
                images = [Image.fromarray(f) for f in frames]
                inputs = self.processor(text=prompt, images=images, return_tensors="pt")
                output = self.model.generate(**inputs, max_new_tokens=20)
                result = self.processor.decode(output[0], skip_special_tokens=True)[len(prompt):]
                print(f"Prompt: {prompt}\nResult: {result}")

    def start(self):
        threading.Thread(target=self.in_stream.start_frame_server).start()
        threading.Thread(target=self.in_stream.start_prompt_server).start()
        self.run_inference()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Inference Server")
    parser.add_argument(
        '--in_frames',
        type=int,
        default=5,
        help='Number of frames for rolling window input to the model')

    args = parser.parse_args()

    server = InferenceServer(
        model_id="google/paligemma-3b-mix-224",
        frame_host='localhost',
        frame_port=9999,
        prompt_host='localhost',
        prompt_port=9998,
        width=1280,
        height=720,
        n_frames=args.in_frames)

    server.start()
