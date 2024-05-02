from start_application import start_application
from fastapi import FastAPI, Response, Request
from fastapi.responses import StreamingResponse
import memcache
import io
from PIL import Image, ImageDraw
import uvicorn
import random
import pyrqlite.dbapi2 as db
import json
import datetime
from sse_starlette.sse import EventSourceResponse
from queue import Queue
import asyncio

own_host = start_application()

with open('config.json') as f:
    config = json.load(f)

app = FastAPI()

conn = db.connect(host=own_host, port=config['db_port'])
num_requests = 0
num_cache_hits = 0
num_images_genarated = 0
# Assuming Memcached is running on localhost with the default port
cache = memcache.Client(config["cache_hosts"], debug=0)
updated_images = Queue()
current_cache_hits = []

@app.get("/distcache/stats")
async def stats():
    return {
        "num_requests": num_requests,
        "num_cache_hits": num_cache_hits,
        "hit_ratio": num_cache_hits / num_requests if num_requests > 0 else 0,
        "num_images_generated": num_images_genarated,
        "cache_hits": current_cache_hits
    }

@app.get("/distcache/reset_stats")
async def reset_stats():
    global num_cache_hits, num_requests, num_images_genarated, current_cache_hits
    num_requests, num_cache_hits, num_images_genarated = 0,0,0
    current_cache_hits = []
    return Response(content="Stats reset", status_code=200)

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
    global num_images_genarated
    num_images_genarated += 1
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
    updated_images.put(image_id)
    return Response(image_data, media_type="image/png")


@app.get("/distcache/image/{image_id}")
async def image(image_id: str):
    # Check if the image is in cache
    image_data = cache.get(image_id)
    global num_cache_hits
    if not image_data:
        # If not, fetch the image from the source and cache it
        image_data = await get_image_from_source(image_id)
        if not image_data:
            return Response(content="Image not found", status_code=404)
        cache.set(image_id, image_data)  # Cache for 1 hour
    else:

        num_cache_hits += 1
    global num_requests, current_cache_hits
    if num_requests < 9999:
        current_cache_hits.append(num_cache_hits)
    num_requests += 1
    # If it's cached, wrap the binary data in BytesIO for streaming
    # image_data = io.BytesIO(image_data)
    return Response(image_data, media_type="image/png")

@app.get('/distcache/skip_cache/{image_id}')
async def skip_cache(image_id: str):
    with conn.cursor() as cur:
        cur.execute("SELECT image FROM images WHERE image_id = ?", (image_id,))
        row = cur.fetchone()
        if not row:
            return Response(content="Image not found", status_code=404)
        image_data = row[0]
    return Response(image_data, media_type="image/png")

@app.get('/distcache/events')
async def update_stream(request: Request):
    async def update_generator():
        global updated_images
        while True:
            if await request.is_disconnected():
                break
            if not updated_images.empty():
                yield f"{updated_images.get()}\n\n"
        await asyncio.sleep(0.1)
    return EventSourceResponse(update_generator())

if __name__ == "__main__":
    with conn.cursor() as cur:
        cur.execute("CREATE TABLE IF NOT EXISTS images (image_id integer PRIMARY KEY AUTOINCREMENT, image BLOB)")
    uvicorn.run(app, host="0.0.0.0", port=config["own_port"])
