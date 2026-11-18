# Masry Voice Agent 🎙️🇪🇬

مساعد صوتي بيتكلم **باللهجة المصرية** ويحجز مواعيد عيادة بالصوت. MVP لحالة استخدام واحدة (حجز / استعلام / إلغاء ميعاد) مع مجموعة اختبارات صغيرة للهجة المصرية.

An Egyptian-Arabic voice agent MVP: speech in, spoken Egyptian Arabic out, with LLM tool-calling for appointment booking.

## Architecture

```
Mic -> faster-whisper (ar) -> Claude + tools -> edge-tts (ar-EG) -> Speaker
                                   |
                              SQLite bookings
```

- **STT**: faster-whisper (Arabic, runs locally)
- **Brain**: Claude with tool calling (`get_available_slots`, `book_appointment`, `find_appointment`, `cancel_appointment`)
- **TTS**: edge-tts with Egyptian voice `ar-EG-SalmaNeural`
- **Backend**: FastAPI, with a tiny web UI to talk to it from the browser
- **Business rules**: Sunday-Thursday, 10:00-18:00, Friday/Saturday off (Egypt weekend)

## Run

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # put your ANTHROPIC_API_KEY
uvicorn app.main:app --reload
```

Open http://localhost:8000 and talk. Or use text only:

```bash
curl -X POST localhost:8000/chat -H 'Content-Type: application/json' \
  -d '{"session_id":"demo","text":"عايز أحجز كشف يوم الحد الجاي"}'
```

## Tests and eval

```bash
pytest                      # booking logic, no API key needed
python -m evals.run_eval    # Egyptian-dialect tool-routing cases (needs API key)
```

`evals/cases.jsonl` is a seed set of Egyptian utterances with the tool the agent is expected to call. Add more dialect cases (Upper Egypt, Alexandrian, slang, code-switching) to grow it into a real benchmark.

## Roadmap

- [ ] Streaming audio over WebSocket for lower latency
- [ ] Phone integration (Twilio / SIP)
- [ ] Barge-in (interrupt the agent while it speaks)
- [ ] Bigger dialect eval set with WER for STT and tool-accuracy for the agent
- [ ] More verticals: banks, telecom, delivery
