import base64
import os
from openai import OpenAI
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class VisionAnalyzer:
    """
    Analyzes images using a multimodal vision model (e.g., GPT-4 Vision).
    """

    def __init__(self, api_key: str, model: str = "gpt-4-vision-preview"):
        """
        Initializes the VisionAnalyzer with an API key and a model name.

        Args:
            api_key: The API key for the vision model service.
            model: The specific model to use for analysis.
        """
        if not api_key:
            raise ValueError("OpenAI API key is required for VisionAnalyzer.")
        self.client = OpenAI(api_key=api_key)
        self.model = model

    def _encode_image_to_base64(self, image_path: str) -> str:
        """
        Encodes a local image file into a base64 string.

        Args:
            image_path: The file path of the image to encode.

        Returns:
            A base64 encoded string representation of the image.
        """
        try:
            with open(image_path, "rb") as image_file:
                return base64.b64encode(image_file.read()).decode('utf-8')
        except FileNotFoundError:
            logger.error(f"Image file not found at {image_path}")
            raise
        except Exception as e:
            logger.error(f"Error encoding image {image_path}: {str(e)}")
            raise

    def analyze_image(self, image_path: str, prompt: str) -> str:
        """
        Analyzes an image with a given prompt using the vision model.

        Args:
            image_path: The file path of the image to analyze.
            prompt: The text prompt to guide the analysis.

        Returns:
            The textual description of the image from the model.
        """
        logger.info(f"Analyzing image '{image_path}' with model '{self.model}'...")
        try:
            base64_image = self._encode_image_to_base64(image_path)
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{base64_image}"
                                },
                            },
                        ],
                    }
                ],
                max_tokens=300,
            )
            
            if response.choices:
                return response.choices[0].message.content or "No description generated."
            else:
                return "Analysis failed to generate a response."
                
        except Exception as e:
            logger.error(f"Failed to analyze image {image_path}. Error: {str(e)}")
            return f"Error during image analysis: {str(e)}" 