from fastapi import FastAPI, Response
from fastapi.responses import StreamingResponse
# import memcache
import io

app = FastAPI()


# Assuming Memcached is running on localhost with the default port
# cache = memcache.Client(['127.0.0.1:11211'], debug=0)

def get_image_from_source(image_id):
    """
    This function simulates getting an image from a source.
    Replace it with actual logic to fetch your image.
    """
    # For demonstration, generate an image dynamically using PIL
    # In practice, you'd fetch the image from disk, an API, etc.
    from PIL import Image, ImageDraw
    image = Image.new('RGB', (100, 100), color=(73, 109, 137))
    d = ImageDraw.Draw(image)
    d.text((10, 10), f"Image ID: {image_id}", fill=(255, 255, 0))
    byte_arr = io.BytesIO()
    image.save(byte_arr, format='PNG')
    byte_arr.seek(0)  # Move to the beginning of the BytesIO buffer
    return byte_arr


@app.get("/distcache/image/{image_id}")
async def image(image_id: str):
    # Check if the image is in cache
    image_data = None  # cache.get(image_id)
    if not image_data:
        # If not, fetch the image from the source and cache it
        image_data = get_image_from_source(image_id).read()
        # cache.set(image_id, image_data, time=60 * 60)  # Cache for 1 hour
    else:
        # If it's cached, wrap the binary data in BytesIO for streaming
        image_data = io.BytesIO(image_data)
    return StreamingResponse(image_data, media_type="image/png")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8002)
