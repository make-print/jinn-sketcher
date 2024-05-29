import base64
import io
from typing import Any, MutableSequence

import requests
from PIL import Image
from google.cloud import aiplatform
from google.protobuf import json_format
from google.protobuf.struct_pb2 import Value
from transformers import AutoProcessor

# Configuration parameters for Google Cloud Vertex AI
PROJECT = "808248687220"
LOCATION = "us-east1"
ENDPOINT_ID = "7694756205129891840"
API_ENDPOINT = "us-east1-aiplatform.googleapis.com"

# Initialize the Vertex AI client
client_options = {"api_endpoint": API_ENDPOINT}
client = aiplatform.gapic.PredictionServiceClient(client_options=client_options)


def preprocess(image_url: str, prompt: str, processor: AutoProcessor) -> dict:
    """
    Preprocesses the image and prompt for the model input.

    Args:
        image_url (str): URL of the image to be processed.
        prompt (str): Text prompt for the model.
        processor (AutoProcessor): Processor for the model.

    Returns:
        dict: Preprocessed inputs including text and image in base64 format.
    """
    raw_image = Image.open(requests.get(image_url, stream=True).raw)
    inputs = processor(text=prompt, images=raw_image, return_tensors="pt")

    # Convert the image tensor to a base64-encoded string
    image_bytes = io.BytesIO()
    raw_image_np = inputs['pixel_values'][0].permute(1, 2, 0).numpy()
    Image.fromarray((raw_image_np * 255).astype('uint8')).save(image_bytes, format='PNG')
    image_base64 = base64.b64encode(image_bytes.getvalue()).decode('utf-8')

    return {"text": prompt, "image": image_base64}


def predict(
        project: str,
        endpoint_id: str,
        instances: dict,
        location: str = "us-east1",
        api_endpoint: str = "us-east1-aiplatform.googleapis.com"
) -> MutableSequence[Any]:
    """
    Sends a prediction request to the Vertex AI endpoint.

    Args:
        project (str): Google Cloud project ID.
        endpoint_id (str): Vertex AI endpoint ID.
        instances (dict): Preprocessed input instances for the model.
        location (str): Location of the endpoint.
        api_endpoint (str): API endpoint URL.

    Returns:
        list: List of predictions from the model.
    """
    client_options = {"api_endpoint": api_endpoint}
    client = aiplatform.gapic.PredictionServiceClient(client_options=client_options)
    endpoint = client.endpoint_path(project=project, location=location, endpoint=endpoint_id)

    instances = [json_format.ParseDict(instances, Value())]
    parameters = json_format.ParseDict({}, Value())

    response = client.predict(endpoint=endpoint, instances=instances, parameters=parameters)
    return response.predictions


def main():
    """
    Main function to execute the prediction using a custom Vertex AI endpoint.
    """
    prompt = "What is on the flower?"
    image_url = "https://huggingface.co/datasets/huggingface/documentation-images/resolve/main/bee.jpg?download=true"

    # Load the processor from Hugging Face
    model_id = "google/paligemma-3b-mix-448"
    processor = AutoProcessor.from_pretrained(model_id)

    # Preprocess the input
    instances = preprocess(image_url, prompt, processor)

    # Get predictions from Vertex AI
    predictions = predict(PROJECT, ENDPOINT_ID, instances)

    # Decode and print the response
    for prediction in predictions:
        print("Prediction:", dict(prediction))


if __name__ == "__main__":
    main()
