import asyncio
import json
import websockets


ACCESS_TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoiMiIsInR5cGUiOiJhY2Nlc3MiLCJleHAiOjE3OTA3MDM2NTR9.gG8nKU4IQvGobLgpnqbzi-awPoO2k2qFeB4R9GTreV8"


async def main():
    uri = "ws://127.0.0.1:8000/ws"

    async with websockets.connect(uri) as websocket:

        await websocket.send(json.dumps({
            "message": "Tell me about my Salesforce Developer Agent project",
            "access_token": ACCESS_TOKEN
        }))

        response = await websocket.recv()

        print("\n========== CHATBOT RESPONSE ==========")
        print(response)
        print("======================================\n")


asyncio.run(main())