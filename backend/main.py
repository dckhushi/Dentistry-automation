from fastapi import FastAPI, WebSocket, Request, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from twilio.twiml.voice_response import VoiceResponse, Connect, Stream
from backend.core.config import settings
from backend.core.session import session_manager
from backend.agents.receptionist import receptionist_agent
from backend.ivr.navigator import ivr_navigator

app = FastAPI(title="Dentistry Automation Voice AI", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from backend.api.calls import router as calls_router
app.include_router(calls_router)

# ─── Inbound Call Entry Point ───────────────────────────────────────────────

@app.post("/call/inbound")
async def inbound_call(request: Request):
    """
    Twilio calls this webhook when a patient calls the clinic number.
    Returns TwiML to connect the call to our WebSocket audio stream.
    """
    form = await request.form()
    call_sid = form.get("CallSid")
    caller_number = form.get("From")
    to_number = form.get("To")

    # Create Redis session for this call
    await session_manager.create(call_sid, {
        "call_sid": call_sid,
        "caller_number": caller_number,
        "to_number": to_number,
        "agent": "receptionist",
        "status": "active",
        "is_emergency": False,
        "clinic": {
            "name": "Smile Dental",
            "address": "123 Smile Street, Suite 100",
            "hours": "Mon-Fri 9am-6pm, Sat 9am-2pm",
            "dentist_phone": "+1234567890"
        },
        "history": []
    })

    # Return TwiML to stream audio to our WebSocket
    response = VoiceResponse()
    response.say("Thank you for calling Smile Dental. Please hold for a moment.", voice="Polly.Joanna")

    connect = Connect()
    stream = Stream(url=f"wss://{request.headers.get('host')}/ws/audio/{call_sid}")
    connect.append(stream)
    response.append(connect)

    return HTMLResponse(content=str(response), media_type="application/xml")


# ─── WebSocket Audio Stream ──────────────────────────────────────────────────

@app.websocket("/ws/audio/{call_sid}")
async def audio_stream(websocket: WebSocket, call_sid: str):
    """
    Bidirectional audio stream with Twilio Media Streams.
    Receives caller audio, processes with STT+LLM+TTS, sends back.
    """
    await websocket.accept()
    print(f"Audio stream connected: {call_sid}")

    transcript_buffer = ""

    try:
        async for message in websocket.iter_text():
            data = json.loads(message)
            event = data.get("event")

            if event == "connected":
                print(f"Stream connected for call {call_sid}")

            elif event == "media":
                # Audio chunk received from caller
                # In production: pipe to Deepgram STT
                # For demo: we simulate transcript
                pass

            elif event == "stop":
                print(f"Stream stopped for call {call_sid}")
                await session_manager.delete(call_sid)
                break

    except WebSocketDisconnect:
        print(f"WebSocket disconnected: {call_sid}")
        await session_manager.delete(call_sid)


# ─── Demo Endpoint - Simulates Full Call Flow ────────────────────────────────

@app.post("/demo/call")
async def demo_call(request: Request):
    """
    Demo endpoint - simulates a full patient call without real phone.
    Perfect for the assessment demo.
    """
    body = await request.json()
    call_sid = f"DEMO_{body.get('call_sid', 'test123')}"
    user_input = body.get("message", "Hi I need to book an appointment")
    caller_number = body.get("caller_number", "+1234567890")

    # Create session if first message
    session = await session_manager.get(call_sid)
    if not session:
        await session_manager.create(call_sid, {
            "call_sid": call_sid,
            "caller_number": caller_number,
            "agent": "receptionist",
            "status": "active",
            "is_emergency": False,
            "clinic": {
                "name": "Smile Dental",
                "address": "123 Smile Street, Suite 100",
                "hours": "Mon-Fri 9am-6pm, Sat 9am-2pm",
                "dentist_phone": "+1234567890"
            },
            "history": []
        })

    # Process through receptionist agent
    result = await receptionist_agent.respond(call_sid, user_input)

    return {
        "call_sid": call_sid,
        "agent": "receptionist",
        "user_said": user_input,
        "ai_response": result["text"],
        "action": result["action"],
        "sms_sent": result["sms_sent"],
        "emergency": result["action"] == "emergency_escalation"
    }


# ─── IVR Demo Endpoint ───────────────────────────────────────────────────────

@app.post("/demo/ivr")
async def demo_ivr(request: Request):
    """
    Demo endpoint - simulates IVR navigation for insurance verification.
    Shows the learning engine in action.
    """
    body = await request.json()
    call_sid = body.get("call_sid", "IVR_TEST_001")
    payer_id = body.get("payer_id", "aetna_dental")
    task_type = body.get("task_type", "eligibility")
    audio_text = body.get("audio_text", "For eligibility and benefits press 2")

    result = await ivr_navigator.navigate(call_sid, payer_id, task_type, audio_text)

    return {
        "call_sid": call_sid,
        "payer": payer_id,
        "task": task_type,
        "heard": audio_text,
        "action": result
    }


# ─── Health Check ────────────────────────────────────────────────────────────

@app.get("/health")
async def health():
    return {
        "status": "online",
        "service": "Dentistry Automation Voice AI",
        "version": "1.0.0",
        "agents": ["receptionist", "insurance", "claim_followup", "recall", "revenue"],
        "ivr_learning": "active"
    }


# ─── Root ────────────────────────────────────────────────────────────────────

@app.get("/")
async def root():
    return {
        "message": "Dentistry Automation Voice AI Platform",
        "docs": "/docs",
        "health": "/health",
        "demo_call": "/demo/call",
        "demo_ivr": "/demo/ivr"
    }