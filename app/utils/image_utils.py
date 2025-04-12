import base64
from typing import Optional
import httpx
import io
from PIL import Image
import logging

logger = logging.getLogger(__name__)

async def download_image(url: str) -> Optional[bytes]:
    """Download an image from URL and return it as bytes."""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url)
            response.raise_for_status()
            return response.content
    except Exception as e:
        logger.error(f"Failed to download image from {url}: {str(e)}")
        return None

def encode_image_to_base64(image_bytes: bytes) -> str:
    """Encode image bytes to base64 string."""
    try:
        base64_encoded = base64.b64encode(image_bytes).decode('utf-8')
        return base64_encoded
    except Exception as e:
        logger.error(f"Failed to encode image to base64: {str(e)}")
        raise

def decode_base64_to_image(base64_string: str) -> Optional[bytes]:
    """Decode base64 string to image bytes."""
    try:
        image_bytes = base64.b64decode(base64_string)
        return image_bytes
    except Exception as e:
        logger.error(f"Failed to decode base64 to image: {str(e)}")
        return None

def validate_image(image_bytes: bytes) -> bool:
    """Validate if bytes represent a valid image."""
    try:
        Image.open(io.BytesIO(image_bytes))
        return True
    except Exception:
        return False 