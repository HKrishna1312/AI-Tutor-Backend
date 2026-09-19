from fastapi import WebSocket, APIRouter, WebSocketDisconnect
from app.core.llm_manager import LLMManger
from app.core.verify_token import verify_access_token
import json
import logging

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Input Message"])

@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    llm_manager = LLMManger()
    
    try:
        while True:
            data = await websocket.receive_json()
            message = data.get("message")
            access_token = data.get("access_token")
            
            # Check if access_token is provided
            if not access_token:
                await websocket.send_text(json.dumps({"error": "Access token is required"}))
                continue
            
            # Verify the token
            try:
                payload = await verify_access_token(access_token)
                
                # Check if token is valid and has user_id
                if payload and payload.get("user_id"): #user_id is present in the payload
                    if message:
                        response = llm_manager.invoke(message)
                        output = {"output": response.content}
                        await websocket.send_text(json.dumps(output))
                    else:
                        await websocket.send_text(json.dumps({"error": "Message is required"}))
                else:
                    await websocket.send_text(json.dumps({"error": "Invalid token or session expired"}))
                    
            except Exception as token_error:
                await websocket.send_text(json.dumps({"error": f"Token verification failed: {str(token_error)}"}))
                continue
                
    except WebSocketDisconnect:
        logger.info("Client disconnected")
    except Exception as e:
        logger.error(f"Error in websocket: {e}")
        try:
            await websocket.send_text(json.dumps({"error": str(e)}))
        except:
            pass