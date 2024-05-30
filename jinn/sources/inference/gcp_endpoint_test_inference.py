import base64
import io
import os
import traceback
from typing import Any, Dict, List, MutableSequence

import requests
from PIL import Image
from google.cloud import aiplatform
from google.protobuf import json_format
from google.protobuf.struct_pb2 import Value
from transformers import AutoProcessor


class VertexAIPredictor:
    def __init__(self, project: str, location: str, endpoint_id: str, api_endpoint: str, credentials_path: str):
        """
        Initialize the VertexAIPredictor with necessary configurations.

        Args:
            project (str): Google Cloud project ID.
            location (str): Location of the endpoint.
            endpoint_id (str): Vertex AI endpoint ID.
            api_endpoint (str): API endpoint URL.
            credentials_path (str): Path to the Google Application Credentials file.
        """
        self.project = project
        self.location = location
        self.endpoint_id = endpoint_id
        self.api_endpoint = api_endpoint
        self.credentials_path = credentials_path

        # Set the environment variable for Google Application Credentials
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = credentials_path
        if not os.path.isfile(credentials_path):
            raise FileNotFoundError(f"Credentials file not found at: {credentials_path}")

        # Initialize the Vertex AI client
        client_options = {"api_endpoint": api_endpoint}
        self.client = aiplatform.gapic.PredictionServiceClient(client_options=client_options)
        self.endpoint = self.client.endpoint_path(project=project, location=location, endpoint=endpoint_id)

    def preprocess(self, image_url: str, prompt: str, processor: AutoProcessor) -> List[Dict[str, Any]]:
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
        Image.fromarray((raw_image_np * 255).astype('uint8')).save(image_bytes, format='JPEG')
        image_base64 = base64.b64encode(image_bytes.getvalue()).decode('utf-8')
        # print(f"Image converted to base64 format (first 16 chars): {image_base64[:16]}")

        return [
            {
                "prompt": prompt,
                "image": image_base64,
            }
        ]

    def predict(self, instances: List[Dict[str, Any]]) -> MutableSequence[Any]:
        """
        Sends a prediction request to the Vertex AI endpoint.

        Args:
            instances (list): Preprocessed input instances for the model.

        Returns:
            list: List of predictions from the model.
        """
        print("Starting prediction request...")

        # Ensure instances are wrapped in the correct structure
        request_body = {"instances": instances}

        instances = [json_format.ParseDict(instance, Value()) for instance in request_body['instances']]
        parameters = json_format.ParseDict({}, Value())

        print("Sending request to Vertex AI endpoint...")
        response = self.client.predict(endpoint=self.endpoint, instances=instances, parameters=parameters)
        print("Response received from Vertex AI endpoint.")

        return response.predictions

    def get_prediction(self, image_url: str, prompt: str, model_id: str) -> List[str]:
        """
        Get predictions from the Vertex AI endpoint using the provided image URL and text prompt.

        Args:
            image_url (str): URL of the image to be processed.
            prompt (str): Text prompt for the model.
            model_id (str): Model ID for the processor.

        Returns:
            list: List of decoded predictions from the model.
        """
        print(f"Loading processor for model ID: {model_id}")
        processor = AutoProcessor.from_pretrained(model_id)
        print("Processor loaded.")

        # Preprocess the input
        instances = self.preprocess(image_url, prompt, processor)

        # Get predictions from Vertex AI
        try:
            predictions = self.predict(instances)
            decoded_predictions = [dict(prediction)['response'] for prediction in predictions]
            return decoded_predictions
        except Exception as e:
            print(f"An error occurred: {e}")
            print("Error details:")
            traceback.print_exc()
            return []


if __name__ == "__main__":
    predictor = VertexAIPredictor(
        project="808248687220",
        location="us-east1",
        endpoint_id="7694756205129891840",
        api_endpoint="us-east1-aiplatform.googleapis.com",
        credentials_path=r"C:\Users\the_3\AppData\Roaming\gcloud\application_default_credentials.json"
    )

    image_url = "https://huggingface.co/datasets/huggingface/documentation-images/resolve/main/bee.jpg"
    model_id = "google/paligemma-3b-mix-448"

    while True:
        prompt = input("Enter your prompt (or 'exit' to quit): ")
        if prompt.lower() == 'exit':
            break

        predictions = predictor.get_prediction(image_url, prompt, model_id)
        for prediction in predictions:
            print("Prediction:", prediction)