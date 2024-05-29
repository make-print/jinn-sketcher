import requests
from PIL import Image
from huggingface_hub import login
from transformers import AutoProcessor, PaliGemmaForConditionalGeneration

# Login to Hugging Face Hub
login(token="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")

model_id = "google/paligemma-3b-mix-224"
model = PaliGemmaForConditionalGeneration.from_pretrained(model_id)
processor = AutoProcessor.from_pretrained(model_id)

prompt = "What is on the flower?"
image_file = "https://huggingface.co/datasets/huggingface/documentation-images/resolve/main/bee.jpg?download=true"
raw_image = Image.open(requests.get(image_file, stream=True).raw)
inputs = processor(text=prompt, images=raw_image, return_tensors="pt")
output = model.generate(**inputs, max_new_tokens=20)

print(processor.decode(output[0], skip_special_tokens=True)[len(prompt):])
