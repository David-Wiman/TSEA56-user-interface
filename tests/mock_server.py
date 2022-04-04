# Körs med kommandot:
#   python -m tests.mock_server

import asyncio
import json

from src.data import CarData, DriveInstruction, ParameterConfiguration
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
        elif message == "mock_car_data":
            await send(ws, get_mock_car_data())
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


def get_mock_car_data():
    carData = CarData(time=225, throttle=25, steering=25, angle=25)
    return "{" + "\"carData\": " + carData.to_json() + "}"


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Terminating server.")  # Don't print stacktrace when CTRL+C
