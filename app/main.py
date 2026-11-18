import os
from urllib.parse import quote

from dotenv import load_dotenv

load_dotenv()

from fastapi import FastAPI, File, Form, UploadFile  # noqa: E402
from fastapi.concurrency import run_in_threadpool  # noqa: E402
from fastapi.responses import FileResponse, Response  # noqa: E402
from pydantic import BaseModel  # noqa: E402

from . import agent, stt, tts  # noqa: E402

app = FastAPI(title='Masry Voice Agent')
STATIC = os.path.join(os.path.dirname(__file__), 'static')
DIDNT_HEAR = 'مسمعتش حضرتك كويس، ممكن تعيد تاني؟'


class ChatIn(BaseModel):
    session_id: str
    text: str


@app.get('/')
def index():
    return FileResponse(os.path.join(STATIC, 'index.html'))


@app.post('/chat')
async def chat(body: ChatIn):
    reply, tools = await run_in_threadpool(agent.chat, body.session_id, body.text)
    return {'reply': reply, 'tools': tools}


@app.post('/voice')
async def voice(session_id: str = Form(...), audio: UploadFile = File(...)):
    data = await audio.read()
    text = await run_in_threadpool(stt.transcribe, data)
    if text:
        reply, _ = await run_in_threadpool(agent.chat, session_id, text)
    else:
        reply = DIDNT_HEAR
    mp3 = await tts.synthesize(reply)
    return Response(
        content=mp3,
        media_type='audio/mpeg',
        headers={'X-Transcript': quote(text), 'X-Reply': quote(reply)},
    )
