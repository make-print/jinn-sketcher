import base64
import io
import os
from typing import Any, Dict, List, MutableSequence
import traceback

import requests
from PIL import Image
from google.cloud import aiplatform
from google.protobuf import json_format
from google.protobuf.struct_pb2 import Value
from transformers import AutoProcessor

# Set the environment variable for Google Application Credentials
os.environ[
    "GOOGLE_APPLICATION_CREDENTIALS"] = r"C:\Users\the_3\AppData\Roaming\gcloud\application_default_credentials.json"

# Verify the environment variable
credentials_path = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS")
if credentials_path and os.path.isfile(credentials_path):
    print(f"Credentials file found at: {credentials_path}")
else:
    print("Credentials file not found. Please check the GOOGLE_APPLICATION_CREDENTIALS environment variable.")

# Configuration parameters for Google Cloud Vertex AI
PROJECT = "808248687220"
LOCATION = "us-east1"
ENDPOINT_ID = "7694756205129891840"
API_ENDPOINT = "us-east1-aiplatform.googleapis.com"

# Initialize the Vertex AI client
client_options = {"api_endpoint": API_ENDPOINT}
client = aiplatform.gapic.PredictionServiceClient(client_options=client_options)


def preprocess(image_url: str, prompt: str, processor: AutoProcessor) -> List[Dict[str, Any]]:
    """
    Preprocesses the image and prompt for the model input.

    Args:
        image_url (str): URL of the image to be processed.
        prompt (str): Text prompt for the model.
        processor (AutoProcessor): Processor for the model.

    Returns:
        list: Preprocessed inputs including text and image in base64 format.
    """
    print("Starting preprocessing...")
    print(f"Image URL: {image_url}")
    print(f"Prompt: {prompt}")

    # Load and process the image
    raw_image = Image.open(requests.get(image_url, stream=True).raw)
    print("Image downloaded and opened.")

    inputs = processor(images=raw_image, return_tensors="pt")
    print("Inputs processed with processor.")

    # Convert the image tensor to a base64-encoded string
    image_bytes = io.BytesIO()
    raw_image_np = inputs['pixel_values'][0].permute(1, 2, 0).numpy()
    Image.fromarray((raw_image_np * 255).astype('uint8')).save(image_bytes, format='PNG')
    image_base64 = base64.b64encode(image_bytes.getvalue()).decode('utf-8')
    print(f"Image converted to base64 format (first 16 chars): {image_base64[:16]}")

    return [{"data": {"text": prompt, "image_bytes": {"b64": image_base64}}}]


def predict(
        project: str,
        endpoint_id: str,
        instances: List[Dict[str, Any]],
        location: str = "us-east1",
        api_endpoint: str = "us-east1-aiplatform.googleapis.com"
) -> MutableSequence[Any]:
    """
    Sends a prediction request to the Vertex AI endpoint.

    Args:
        project (str): Google Cloud project ID.
        endpoint_id (str): Vertex AI endpoint ID.
        instances (list): Preprocessed input instances for the model.
        location (str): Location of the endpoint.
        api_endpoint (str): API endpoint URL.

    Returns:
        list: List of predictions from the model.
    """
    print("Starting prediction request...")
    print(f"Project: {project}")
    print(f"Endpoint ID: {endpoint_id}")
    print(f"API Endpoint: {api_endpoint}")

    client_options = {"api_endpoint": api_endpoint}
    client = aiplatform.gapic.PredictionServiceClient(client_options=client_options)
    endpoint = client.endpoint_path(project=project, location=location, endpoint=endpoint_id)

    # Ensure instances are wrapped in the correct structure
    request_body = {"instances": instances}
    print(f"Request body (first instance, first 16 chars of image_bytes): {request_body['instances'][0]['data']['image_bytes']['b64'][:16]}")

    instances = [json_format.ParseDict(instance, Value()) for instance in request_body['instances']]
    parameters = json_format.ParseDict({}, Value())

    print("Sending request to Vertex AI endpoint...")
    response = client.predict(endpoint=endpoint, instances=instances, parameters=parameters)
    print("Response received from Vertex AI endpoint.")

    return response.predictions


def main():
    """
    Main function to execute the prediction using a custom Vertex AI endpoint.
    """
    prompt = "What is on the flower?"
    image_url = "https://huggingface.co/datasets/huggingface/documentation-images/resolve/main/bee.jpg?download=true"

    print(f"Prompt: {prompt}")
    print(f"Image URL: {image_url}")

    # Load the processor from Hugging Face
    model_id = "google/paligemma-3b-mix-448"
    print(f"Loading processor for model ID: {model_id}")
    processor = AutoProcessor.from_pretrained(model_id)
    print("Processor loaded.")

    # Preprocess the input
    instances = preprocess(image_url, prompt, processor)
    print(f"Preprocessed instances: {instances}")

    # Get predictions from Vertex AI
    try:
        predictions = predict(PROJECT, ENDPOINT_ID, instances)
        # Decode and print the response
        for prediction in predictions:
            print("Prediction:", dict(prediction))
    except Exception as e:
        print(f"An error occurred: {e}")
        print("Error details:")
        traceback.print_exc()


if __name__ == "__main__":
    main()
