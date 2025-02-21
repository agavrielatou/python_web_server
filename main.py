""" Author: Anna Gavrielatou
"""
import uvicorn
import os
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from datetime import datetime
from collections import deque
import time
import math
import asyncio
import aiohttp


class Item(BaseModel):
    product_id: str


# global variables
app = FastAPI()
queue = deque()
# capacity and max_seconds define the rate limiter's
# maximum accepted rate (capacity/max_seconds).
CAPACITY = int(os.getenv('CAPACITY', '5'))
MAX_SECONDS = int(os.getenv('MAX_SECONDS', '1'))


async def send_product_request(product_id: str):
    """ Sends a POST request /product to eshop """
    async with aiohttp.ClientSession() as session:
        async with session.post(' http://localhost:8000/product',
            json={'product_id': product_id}):
            pass


@app.post("/product")
async def handle_product_addition(item: Item):
    """ Handles the POST /product_id request based
        on the Item model above. 
        It uses leaky bucket algorithm for rate limiter.
        It raises a HTTP exception if the maximum limit
        of requests is reached.
        Error HTTP codes that are not manually returned
        here are automatically returned by FastAPI. See
        unit tests.
    """
    # first check if the request can be accepted.
    now = datetime.now()
    while queue:
        elapsed = now - queue[0]
        if elapsed.total_seconds() >= MAX_SECONDS:
            queue.popleft()
        else:
            break

    if len(queue) >= CAPACITY:
        print("Too many requests")
        raise HTTPException(status_code=429, detail="Too many requests")

    queue.append(now)


@app.post("/eshop_creation")
async def handle_eshop_creation(item: Item):
    """ Handles POST request /eshop_creation, based on
        the Item model above.
        Error HTTP codes that are not manually returned
        here are automatically returned by FastAPI. See
        unit tests.
        The third-party /product request is launched
        in a separate asyncio task, so this API call
        will return immediately.
    """
    # POST /product in a separate asyncio task,
    # so this API call can return immediately.
    asyncio.create_task(send_product_request(item.product_id))

    # just return True
    return "True"

if __name__ == "__main__":
    uvicorn.run("main:app", reload=True)

