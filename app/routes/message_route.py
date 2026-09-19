from fastapi import WebSocket, APIRouter, WebSocketDisconnect
from app.core.verify_token import verify_access_token
from app.services.chat_service import generate_resume_answer
import asyncio
import json
import logging

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Input Message"])


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):

    await websocket.accept()

    try:
        while True:

            data = await websocket.receive_json()

            message = data.get("message")
            access_token = data.get("access_token")

            if not access_token:
                await websocket.send_text(
                    json.dumps({
                        "error": "Access token is required"
                    })
                )
                continue

            try:

                payload = await verify_access_token(
                    access_token
                )

                user_id = payload.get("user_id")

                if not user_id:

                    await websocket.send_text(
                        json.dumps({
                            "error": "User ID missing from token"
                        })
                    )
                    continue

                if not message:

                    await websocket.send_text(
                        json.dumps({
                            "error": "Message is required"
                        })
                    )
                    continue

                result = await asyncio.to_thread(
                    generate_resume_answer,
                    question=message,
                    user_id=user_id
                )

                output = {
                    "output": result["answer"],
                    "sources": result["sources"]
                }

                await websocket.send_text(
                    json.dumps(output)
                )

            except Exception as token_error:

                await websocket.send_text(
                    json.dumps({
                        "error": str(token_error)
                    })
                )

    except WebSocketDisconnect:

        logger.info("Client disconnected")

    except Exception as e:

        logger.error(
            f"Error in websocket: {e}"
        )

        try:

            await websocket.send_text(
                json.dumps({
                    "error": str(e)
                })
            )

        except Exception:
            pass