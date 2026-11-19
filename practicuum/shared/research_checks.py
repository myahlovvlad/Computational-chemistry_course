"""Limited public numerical checks, never a scientific reasoning grade."""
import json
import math
from pathlib import Path


def check(lesson_id, answer):
    contracts = json.loads(Path(__file__).with_name('research_contracts.json').read_text(encoding='utf-8'))
    if lesson_id not in contracts:
        raise ValueError('No numerical contract for '+lesson_id)
    if answer is None:
        return {'status': 'NOT_RUN', 'reasoning': 'NOT_REVIEWED'}
    if not isinstance(answer, dict):
        return {'status': 'FAIL', 'errors': ['Expected an object'], 'reasoning': 'NOT_REVIEWED'}
    errors = []
    for field, expected in contracts[lesson_id].items():
        value = answer.get(field)
        if isinstance(expected, bool):
            ok = type(value) is bool and value == expected
        elif isinstance(expected, (int, float)):
            ok = type(value) in {int, float} and math.isfinite(value) and math.isclose(
                value, expected, rel_tol=1e-5, abs_tol=1e-7)
        else:
            ok = value == expected
        if not ok:
            errors.append(field)
    return {'status': 'FAIL' if errors else 'PASS', 'errors': errors,
            'scope': 'listed numerical fields only', 'reasoning': 'NOT_REVIEWED'}
