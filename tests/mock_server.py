from src.data import DriveInstruction, ParameterConfiguration, CarData

import websockets
import asyncio

URL = "localhost"
PORT = "8000"


async def handler(ws, path):
    '''Handles incomming connection.'''

    async for message in ws:
        print("Recieved:", str(message))
        
        if message == "stop":
            await stop()
        elif message == "YO!":
            await send(ws, "YO!")
        else:
            await send(ws, "idk")

async def send(ws, msg: str):
    print("Sending:", msg)
    await ws.send(msg)

async def stop():
    print("Stopping server...")
    global stop_future
    stop_future.set_result(None)
    print("Server stopped")

async def main():
    print("Starting server...")
    global stop_future
    stop_future = asyncio.Future()

    async with websockets.serve(handler, URL, PORT):
        print("Server started")
        await stop_future


if __name__ == "__main__":
    asyncio.run(main())