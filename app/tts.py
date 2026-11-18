import os

import edge_tts

VOICE = os.getenv('TTS_VOICE', 'ar-EG-SalmaNeural')


async def synthesize(text):
    chunks = []
    async for chunk in edge_tts.Communicate(text, VOICE).stream():
        if chunk['type'] == 'audio':
            chunks.append(chunk['data'])
    return b''.join(chunks)
