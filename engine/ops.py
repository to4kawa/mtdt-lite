from .score import canonical_score_bytes, load_score_file
from .validators import run_validators


def op_score_load(path):
    score = load_score_file(path)
    return {
        'op': 'score-load',
        'ok': True,
        'title': score.title,
        'parts': len(score.parts),
        'events': sum(len(part.events) for part in score.parts),
        'measures': max(event.measure for part in score.parts for event in part.events),
    }


def op_score_validate(path):
    score = load_score_file(path)
    return [finding.to_dict() for finding in run_validators(score)]


def op_score_normalize(path):
    score = load_score_file(path)
    return canonical_score_bytes(score).decode('utf-8')


OPS_IMPL = {
    'score-load': op_score_load,
    'score-normalize': op_score_normalize,
    'score-validate': op_score_validate,
}
