import json
import os
from datetime import date

from anthropic import Anthropic

from .booking import BookingStore

MODEL = os.getenv('CLAUDE_MODEL', 'claude-sonnet-5-5')
store = BookingStore(os.getenv('DB_PATH', 'bookings.db'))
SESSIONS = {}
_client = None

DAYS_AR = ['الاتنين', 'التلات', 'الأربع', 'الخميس', 'الجمعة', 'السبت', 'الحد']

SYSTEM = '''انتي سلمى، موظفة الاستقبال الصوتية في عيادة. بتتكلمي باللهجة المصرية العامية بشكل طبيعي ودافي.
القواعد:
- ردودك قصيرة (جملة او اتنين) لانها هتتنطق بصوت. من غير رموز او ايموجي او تنسيق.
- اسألي سؤال واحد بس في المرة.
- لازم تعرفي الاسم ورقم الموبايل قبل الحجز، واكدي اليوم والساعة مع العميل قبل ما تحجزي.
- متخترعيش مواعيد: استخدمي الادوات دايما للتأكد من المواعيد الفاضية.
- العيادة شغالة من الحد للخميس من 10 الصبح لـ 6 المغرب. الجمعة والسبت اجازة.
- حولي التواريخ النسبية (بكرة، الحد الجاي) لتاريخ حقيقي بصيغة YYYY-MM-DD.
- لو السؤال برا موضوع المواعيد، اعتذري بلطف وارجعي لموضوع الحجز.
النهاردة: {today} ({weekday}).'''


def _tool(name, desc, props, required):
    return {
        'name': name,
        'description': desc,
        'input_schema': {'type': 'object', 'properties': props, 'required': required},
    }


TOOLS = [
    _tool(
        'get_available_slots',
        'Get free appointment times for a date.',
        {'date': {'type': 'string', 'description': 'YYYY-MM-DD'}},
        ['date'],
    ),
    _tool(
        'book_appointment',
        'Book an appointment after the customer confirmed all details.',
        {
            'name': {'type': 'string'},
            'phone': {'type': 'string'},
            'date': {'type': 'string', 'description': 'YYYY-MM-DD'},
            'time': {'type': 'string', 'description': 'HH:MM, one of the available slots'},
        },
        ['name', 'phone', 'date', 'time'],
    ),
    _tool(
        'find_appointment',
        'Look up upcoming appointments by phone number.',
        {'phone': {'type': 'string'}},
        ['phone'],
    ),
    _tool(
        'cancel_appointment',
        'Cancel an appointment by its booking id.',
        {'booking_id': {'type': 'string'}},
        ['booking_id'],
    ),
]


def dispatch(name, args):
    if name == 'get_available_slots':
        return {'slots': store.available_slots(args.get('date'))}
    if name == 'book_appointment':
        return store.book(args.get('name'), args.get('phone'), args.get('date'), args.get('time'))
    if name == 'find_appointment':
        return {'appointments': store.find(args.get('phone'))}
    if name == 'cancel_appointment':
        return store.cancel(args.get('booking_id', ''))
    return {'error': 'unknown_tool'}


def _system_prompt():
    today = date.today()
    return SYSTEM.format(today=today.isoformat(), weekday=DAYS_AR[today.weekday()])


def chat(session_id, text):
    """Run one user turn. Returns (reply_text, list_of_tool_names_called)."""
    global _client
    if _client is None:
        _client = Anthropic()
    messages = SESSIONS.setdefault(session_id, [])
    messages.append({'role': 'user', 'content': text})
    trace = []
    for _ in range(6):
        resp = _client.messages.create(
            model=MODEL,
            max_tokens=400,
            system=_system_prompt(),
            tools=TOOLS,
            messages=messages,
        )
        messages.append({'role': 'assistant', 'content': resp.content})
        if resp.stop_reason != 'tool_use':
            reply = ''.join(b.text for b in resp.content if b.type == 'text')
            return reply, trace
        results = []
        for block in resp.content:
            if block.type == 'tool_use':
                trace.append(block.name)
                out = dispatch(block.name, block.input)
                results.append({
                    'type': 'tool_result',
                    'tool_use_id': block.id,
                    'content': json.dumps(out, ensure_ascii=False),
                })
        messages.append({'role': 'user', 'content': results})
    return 'حصلت مشكلة صغيرة، ممكن نعيد تاني؟', trace
