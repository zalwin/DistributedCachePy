from fastapi import FastAPI, Response
from fastapi.responses import StreamingResponse
import memcache
import io
from PIL import Image, ImageDraw
import uvicorn
import random
import pyrqlite.dbapi2 as db

app = FastAPI()

conn = db.connect(host='localhost', port=4001)
num_requests = 0
num_cache_hits = 0
# Assuming Memcached is running on localhost with the default port
cache = memcache.Client(['127.0.0.1:11211'], debug=0)

@app.get("/distcache/stats")
async def stats():
    return {
        "num_requests": num_requests,
        "num_cache_hits": num_cache_hits,
        "hit_ratio": num_cache_hits / num_requests if num_requests > 0 else 0,
    }


async def get_image_from_source(image_id):
    """
    This function simulates getting an image from a source.
    Replace it with actual logic to fetch your image.
    """
    # For demonstration, generate an image dynamically using PIL
    # In practice, you'd fetch the image from disk, an API, etc.
    with conn.cursor() as cur:
        cur.execute("SELECT image FROM images WHERE image_id = ?", (image_id,))
        row = cur.fetchone()
        if row:
            return row[0]
        return None

async def generate_random_image() -> io.BytesIO:
    image_data = io.BytesIO()
    s1, s2 = random.randint(200, 700), random.randint(200, 700)
    r, g, b = random.randint(0, 255), random.randint(0, 255), random.randint(0, 255)
    image = Image.new("RGB", (s1, s2), (r, g, b))
    image.save(image_data, format="PNG")
    image_data.seek(0)
    return image_data

@app.get("/distcache/set_rng_image")
async def set_rng_image():
    image_data = await generate_random_image()
    with conn.cursor() as cur:
        cur.execute("INSERT INTO images (image) VALUES (?) RETURNING image_id", (image_data.read(),))
        image_id = cur.fetchone()[0]
    return {"image_id": image_id}


@app.get("/distcache/update/{image_id}")
async def update_image(image_id : str):
    with conn.cursor() as cur:
        cur.execute("SELECT EXISTS(SELECT 1 FROM images WHERE image_id = ?)", (image_id,))
        row = cur.fetchone()
        if not row:
            return Response(content="Image not found", status_code=404)
        image_data = await generate_random_image()
        cur.execute("UPDATE images SET image = ? WHERE image_id = ?", (image_data.read(), image_id))
    cache.delete(image_id)
    return {"message": "Image updated successfully"}

@app.get("/distcache/image/{image_id}")
async def image(image_id: str):
    # Check if the image is in cache
    image_data = cache.get(image_id)
    if not image_data:
        # If not, fetch the image from the source and cache it
        image_data = await get_image_from_source(image_id)
        if not image_data:
            return Response(content="Image not found", status_code=404)
        cache.set(image_id, image_data)  # Cache for 1 hour
    else:
        global num_cache_hits
        num_cache_hits += 1
    global num_requests
    num_requests += 1
        # If it's cached, wrap the binary data in BytesIO for streaming
        # image_data = io.BytesIO(image_data)
    return Response(image_data, media_type="image/png")


if __name__ == "__main__":
    with conn.cursor() as cur:
        cur.execute("CREATE TABLE IF NOT EXISTS images (image_id integer PRIMARY KEY AUTOINCREMENT, image BLOB)")
    uvicorn.run(app, host="0.0.0.0", port=8002)
