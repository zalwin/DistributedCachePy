from fastapi import FastAPI, Response
from fastapi.responses import StreamingResponse
import memcache
import io
from PIL import Image, ImageDraw
import uvicorn
import random

app = FastAPI()


# Assuming Memcached is running on localhost with the default port
cache = memcache.Client(['192.168.0.21:11211', '192.168.0.22:11211', '192.168.0.23:11211'], debug=0)

def get_image_from_source(image_id):
    """
    This function simulates getting an image from a source.
    Replace it with actual logic to fetch your image.
    """
    # For demonstration, generate an image dynamically using PIL
    # In practice, you'd fetch the image from disk, an API, etc.
    r1, g1, b1 = random.randint(0, 255), random.randint(0, 255), random.randint(0, 255)
    image = Image.new('RGB', (500, 500), color=(r1, g1, b1))
    d = ImageDraw.Draw(image)
    d.text((10, 10), f"Image ID: {image_id}", fill=(255, 255, 0))
    byte_arr = io.BytesIO()
    image.save(byte_arr, format='PNG')
    byte_arr.seek(0)  # Move to the beginning of the BytesIO buffer
    return byte_arr


@app.get("/distcache/image/{image_id}")
async def image(image_id: str):
    # Check if the image is in cache
    image_data = cache.get(image_id)
    if not image_data:
        # If not, fetch the image from the source and cache it
        image_data = get_image_from_source(image_id).read()
        cache.set(image_id, image_data)  # Cache for 1 hour
    else:
        pass
        # If it's cached, wrap the binary data in BytesIO for streaming
        # image_data = io.BytesIO(image_data)
    return Response(image_data, media_type="image/png")


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8002)
