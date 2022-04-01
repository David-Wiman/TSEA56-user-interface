#from src.data import DriveInstruction, ParameterConfiguration, CarData

import asyncio

from websockets import exceptions, serve

URL = "localhost"
PORT = "8000"


async def handler(ws):
    '''Handles incomming connection.'''
    print("Client connected!")

    async for message in ws:
        print("Recieved:", str(message))

        if message == "stop":
            await stop()
        elif message == "YO!":
            await send(ws, "YO!")
        else:
            await send(ws, "idk")

    print("Client disconnected!")


async def send(ws, msg: str):
    print("Sending:", msg)
    try:
        await ws.send(msg)
    except exceptions.ConnectionClosed as e:
        print("Connection was closed: ", str(e))
        await stop()
    except Exception as e:
        print("Error: ", str(e))
        await stop()


async def stop():
    print("Stopping server...")
    global stop_future
    stop_future.set_result(None)


async def main():
    print("Starting server...")
    global stop_future
    stop_future = asyncio.Future()

    async with serve(handler, URL, PORT):
        print("Server started\n")
        await stop_future

    print("Server stopped")


if __name__ == "__main__":
    asyncio.run(main())
