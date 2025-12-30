from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List
import asyncio
from telegram_service import TelegramService

app = FastAPI()

# Allow CORS for Next.js frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize with credentials from tool.py
API_ID = 33238695
API_HASH = "1a0c36b4f211274c65a9733df5df65a7"

telegram_service = TelegramService(API_ID, API_HASH)

class LoginRequest(BaseModel):
    phone: str

class AuthRequest(BaseModel):
    phone: str
    code: str
    hash: str
    password: Optional[str] = None

class StartRequest(BaseModel):
    source_group: str
    target_group: str
    delay: int = 40

@app.on_event("startup")
async def startup():
    await telegram_service.connect()

@app.get("/status")
async def get_status():
    authorized = await telegram_service.is_authorized()
    return {
        "authorized": authorized,
        "is_running": telegram_service.is_running,
        "stats": telegram_service.stats,
        "logs": telegram_service.logs[-20:] # Return last 20 logs
    }

@app.get("/history")
async def get_history():
    return {"history": list(telegram_service.invited_cache)}

@app.post("/login/send-code")
async def send_code(req: LoginRequest):
    try:
        sent_code = await telegram_service.send_code(req.phone)
        return {"hash": sent_code.phone_code_hash}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/login/verify")
async def verify_code(req: AuthRequest):
    result = await telegram_service.sign_in(req.phone, req.code, req.hash, req.password)
    if result == "2FA_REQUIRED":
        return {"status": "2FA_REQUIRED"}
    elif result:
        return {"status": "SUCCESS"}
    else:
        raise HTTPException(status_code=400, detail="Invalid code or error during sign in")

@app.post("/start")
async def start_inviting(req: StartRequest):
    if telegram_service.is_running:
        return {"status": "ALREADY_RUNNING"}
    
    # Run invitation in background
    asyncio.create_task(telegram_service.start_inviting(req.source_group, req.target_group, req.delay))
    return {"status": "STARTED"}

@app.post("/stop")
async def stop_inviting():
    await telegram_service.stop()
    return {"status": "STOPPING"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
