from start_application import start_application
from fastapi import FastAPI, Response
from fastapi.responses import StreamingResponse
import memcache
import io
from PIL import Image, ImageDraw
import uvicorn
import random
import pyrqlite.dbapi2 as db
import json
import datetime

own_host = start_application()

with open('config.json') as f:
    config = json.load(f)

app = FastAPI()

conn = db.connect(host=own_host, port=config['db_port'])
num_requests = 0
num_cache_hits = 0
# Assuming Memcached is running on localhost with the default port
cache = memcache.Client(config["cache_hosts"], debug=0)


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
    If no image is found, generate a new image.
    """
    # For demonstration, generate an image dynamically using PIL
    # In practice, you'd fetch the image from disk, an API, etc.
    with conn.cursor() as cur:
        cur.execute("SELECT image FROM images WHERE image_id = ?", (image_id,))
        row = cur.fetchone()
        if row:
            return row[0]
        new_image = await generate_random_image()
        cur.execute("INSERT INTO images (image) VALUES (?)", (new_image,))
        return new_image


async def generate_random_image() -> bytes:
    image_data = io.BytesIO()
    s1, s2 = random.randint(200, 700), random.randint(200, 700)
    r, g, b = random.randint(0, 255), random.randint(0, 255), random.randint(0, 255)
    image = Image.new("RGB", (s1, s2), (r, g, b))
    draw = ImageDraw.Draw(image)
    draw.text((s1 // 2, s2 // 2), f"{datetime.datetime.utcnow()}", fill=(255 - r, 255 - g, 255 - b))
    image.save(image_data, format="PNG")
    image_data.seek(0)
    return image_data.read()



@app.get("/distcache/update/{image_id}")
async def update_image(image_id: str):
    with conn.cursor() as cur:
        cur.execute("SELECT EXISTS(SELECT 1 FROM images WHERE image_id = ?)", (image_id,))
        row = cur.fetchone()
        if not row:
            return Response(content="Image not found", status_code=404)
        image_data = await generate_random_image()
        cur.execute("UPDATE images SET image = ? WHERE image_id = ?", (image_data, image_id))
    cache.delete(image_id)
    return Response(image_data, media_type="image/png")


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
    uvicorn.run(app, host="0.0.0.0", port=config["own_port"])
