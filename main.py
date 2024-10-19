from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, Response, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from sqlmodel import SQLModel, Session, select
from config.database import create_db_and_tables, engine
from fastapi.middleware.cors import CORSMiddleware
from uuid import uuid4 as uuid
from models.Poll import Poll
from ws import ws_manager
from routes.poll import router as poll_router
import asyncio

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Starting lifespan...")
    try:
        create_db_and_tables()
        print("DB and tables created successfully.")
    except Exception as e:
        print(f"Error during DB setup: {str(e)}")
    yield
    print("Shutting down app...")


app = FastAPI(lifespan=lifespan)
app = FastAPI()
app.title = "Curso de FastAPI"
app.version = "0.0.1"

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(poll_router)

@app.middleware("http")
async def db_session_middleware(request: Request, call_next):
    print("Middleware start")
    session_id = has_session_id = request.cookies.get("fast_vote_session")
    if not has_session_id:
        print("No session ID found, creating one")
        session_id = str(uuid())
    request.cookies.setdefault("fast_vote_session", session_id)
    response: Response = await call_next(request)
    print("Middleware end")
    if has_session_id is None:
        response.set_cookie("fast_vote_session", session_id,path="/", httponly=True)
    return response

@app.websocket("/ws/poll/{poll_id}")
async def websocket_endpoint(websocket: WebSocket, poll_id: str):
    print(f"Opening WebSocket for poll_id: {poll_id}")
    with Session(engine) as session:
        statement = select(Poll).where(Poll.id == poll_id)
        poll = session.exec(statement).first()
        if not poll:
            await websocket.close(code=1008)
            return
    await websocket.accept()
    await ws_manager.connect(poll_id,websocket)
    try:
        while True:
            await asyncio.sleep(0.5)
            await websocket.receive_json()
            # data = await websocket.receive_text()
            # await ws_manager.send_personal_message(data, websocket)
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)
        
@app.get('/', tags = ['home'])
def message ():
    return HTMLResponse('<h2>Hello world</h2>')
