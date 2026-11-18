import json
import sys
import uuid

from dotenv import load_dotenv

load_dotenv()

from app import agent  # noqa: E402


def main(path='evals/cases.jsonl'):
    with open(path, encoding='utf-8') as f:
        cases = [json.loads(line) for line in f if line.strip()]
    passed = 0
    for c in cases:
        reply, tools = agent.chat('eval-' + str(uuid.uuid4()), c['text'])
        expected = c['expect_tool']
        ok = (expected in tools) if expected else not tools
        passed += ok
        status = 'PASS' if ok else 'FAIL'
        print(status, '|', c['text'], '| tools =', tools, '|', reply)
    print(passed, '/', len(cases), 'passed')
    sys.exit(0 if passed == len(cases) else 1)


if __name__ == '__main__':
    main()
