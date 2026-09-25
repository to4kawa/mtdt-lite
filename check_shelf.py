import argparse
import ast
import hashlib
import json
import re
import sys
from pathlib import Path

REQUIRED_FIELDS = {
    'id', 'title', 'summary_ja', 'category', 'mode', 'level', 'idiom',
    'ensemble', 'status', 'use_when', 'not_when', 'inputs', 'outputs',
    'preconditions', 'effects', 'ops', 'validators', 'theory_refs',
    'examples', 'failure_modes', 'requires', 'composes_with', 'body_path',
    'body_sha256', 'schema_version'
}
OP_FIELDS = {'id', 'implementation'}
VALIDATOR_FIELDS = {'id', 'severity', 'autofix', 'implementation'}
CATEGORIES = {
    'foundations', 'counterpoint', 'harmony', 'melody', 'rhythm', 'form',
    'orchestration', 'playability', 'notation', 'text_setting',
    'production_export'
}
MODES = {'analyze', 'generate', 'check', 'transform'}
LEVELS = {'basic', 'intermediate', 'advanced'}
STATUSES = {'draft', 'validated', 'stable'}
IMPLEMENTATIONS = {'unimplemented', 'advisory', 'implemented'}
SEVERITIES = {'info', 'warning', 'error'}
EXPECTED_COUNTS = {
    'foundations': 4,
    'counterpoint': 4,
    'harmony': 5,
    'melody': 4,
    'rhythm': 3,
    'form': 3,
    'orchestration': 3,
    'playability': 3,
    'notation': 3,
    'text_setting': 2,
    'production_export': 2,
}
EXPECTED_IDS = {
    'foundations': {'pitch-spelling-scales', 'pitch-intervals', 'key-signatures', 'metric-hierarchy'},
    'counterpoint': {'species-counterpoint-1', 'voice-leading-rules', 'parallel-motion-avoidance', 'dissonance-treatment'},
    'harmony': {'functional-harmony-basics', 'cadence-types', 'satb-chorale-harmonization', 'secondary-dominants', 'modulation-common-tone'},
    'melody': {'motive-development', 'melodic-contour', 'phrase-arc', 'sequence-technique'},
    'rhythm': {'note-values', 'syncopation-basics', 'rhythmic-variation'},
    'form': {'period-sentence', 'binary-ternary', 'theme-and-variation'},
    'orchestration': {'string-section-idioms', 'wind-pairing', 'texture-density'},
    'playability': {'piano-idiomatic-limits', 'string-double-stops', 'breath-phrase-limits'},
    'notation': {'satb-closed-score', 'clefs-and-transposing-instruments', 'beaming-dynamics-conventions'},
    'text_setting': {'syllable-underlay-basics', 'melisma-vs-syllabic'},
    'production_export': {'musicxml-roundtrip', 'midi-export-basics'},
}
REQUIRED_SECTIONS = [
    'Purpose', 'Use when', 'Do not use when', 'Inputs', 'Outputs',
    'Procedure', 'Hard constraints', 'Heuristics', 'Validation status',
    'Failure modes', 'Examples', 'References'
]
ID_RE = re.compile(r'^[a-z0-9]+(?:-[a-z0-9]+)*$')
SHA_RE = re.compile(r'^[0-9a-f]{64}$')
CJK_RE = re.compile(r'[\u3040-\u30ff\u4e00-\u9fff]')
ALLOWED_IMPORTS = {'argparse', 'ast', 'hashlib', 'json', 'pathlib', 're', 'sys', 'unicodedata'}
BANNED_IMPORTS = {
    'socket', 'urllib', 'http', 'ftplib', 'ssl', 'smtplib', 'subprocess',
    'multiprocessing', 'pty', 'openai', 'anthropic', 'requests', 'httpx',
    'asyncio'
}


class Issue:
    def __init__(self, code, message):
        self.code = code
        self.message = message

    def __str__(self):
        return f'{self.code}: {self.message}'


class UsageError(Exception):
    pass


class Parser(argparse.ArgumentParser):
    def error(self, message):
        raise UsageError(message)


def add(issues, code, message):
    issues.append(Issue(code, message))


def first_code(issues):
    for code in (1, 2, 3, 4, 5):
        if any(issue.code == code for issue in issues):
            return code
    return 0


def read_json(path, issues):
    try:
        raw = path.read_bytes()
        text = raw.decode('utf-8')
    except FileNotFoundError:
        add(issues, 2, f'missing file: {path}')
        return None
    except (OSError, UnicodeDecodeError) as exc:
        add(issues, 2, f'cannot read UTF-8 file {path}: {exc}')
        return None
    try:
        return json.loads(text, object_pairs_hook=unique_object)
    except (json.JSONDecodeError, ValueError) as exc:
        add(issues, 2, f'invalid JSON {path}: {exc}')
        return None


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f'duplicate JSON key: {key}')
        result[key] = value
    return result


def canonical_index(index):
    normalized = dict(index)
    normalized['skills'] = sorted(index.get('skills', []), key=lambda record: record.get('id', '') if isinstance(record, dict) else '')
    return (json.dumps(normalized, ensure_ascii=False, sort_keys=True, indent=2) + '\n').encode('utf-8')


def catalog_hash(records):
    ordered = sorted(records, key=lambda record: record.get('id', '') if isinstance(record, dict) else '')
    payload = json.dumps(ordered, ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode('utf-8')
    return hashlib.sha256(payload).hexdigest()


def body_hash(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def normalize(text):
    return re.sub(r'[^a-z0-9]+', ' ', text.lower()).strip()


def select_skills(index, task, mode=None, category=None):
    task_text = normalize(task)
    candidates = []
    for record in index.get('skills', []):
        if mode is not None and record.get('mode') != mode:
            continue
        if category is not None and record.get('category') != category:
            continue
        if any(normalize(phrase) in task_text for phrase in record.get('not_when', [])):
            continue
        score = sum(1 for phrase in record.get('use_when', []) if normalize(phrase) in task_text)
        if score:
            candidates.append((score, record.get('id', ''), record))
    candidates.sort(key=lambda item: (-item[0], item[1]))
    return [item[2] for item in candidates[:3]]


def validate_list(record, field, issues, index, required=False):
    value = record.get(field)
    if not isinstance(value, list) or any(not isinstance(item, str) for item in value):
        add(issues, 2, f'{index}.{field} must be a list of strings')
        return False
    if required and not value:
        add(issues, 2, f'{index}.{field} must not be empty')
        return False
    return True


def validate_record(record, position, issues):
    prefix = f'skills[{position}]'
    if not isinstance(record, dict):
        add(issues, 2, f'{prefix} must be an object')
        return
    fields = set(record)
    if fields != REQUIRED_FIELDS:
        add(issues, 2, f'{prefix} fields mismatch')
    card_id = record.get('id')
    if not isinstance(card_id, str) or not ID_RE.fullmatch(card_id):
        add(issues, 2, f'{prefix}.id is not kebab-case')
    if record.get('category') not in CATEGORIES:
        add(issues, 2, f'{prefix}.category is invalid')
    if record.get('mode') not in MODES:
        add(issues, 2, f'{prefix}.mode is invalid')
    if record.get('level') not in LEVELS:
        add(issues, 2, f'{prefix}.level is invalid')
    if record.get('status') != 'draft':
        add(issues, 2, f'{prefix}.status must be draft in P1')
    if record.get('schema_version') != '1':
        add(issues, 2, f'{prefix}.schema_version must be 1')
    if record.get('body_path') != f'{card_id}.md':
        add(issues, 2, f'{prefix}.body_path does not match id')
    if not isinstance(record.get('title'), str) or not record['title'].strip():
        add(issues, 2, f'{prefix}.title is empty')
    summary = record.get('summary_ja')
    if not isinstance(summary, str) or not summary.strip():
        add(issues, 2, f'{prefix}.summary_ja is empty')
    elif not re.search(r'[\u3040-\u30ff\u4e00-\u9fff]', summary):
        add(issues, 2, f'{prefix}.summary_ja must contain Japanese text')
    elif re.search(r'[\u0400-\u04ff]', summary):
        add(issues, 2, f'{prefix}.summary_ja contains Cyrillic text')
    elif summary != summary.strip():
        add(issues, 2, f'{prefix}.summary_ja has outer whitespace')
    if not isinstance(record.get('body_sha256'), str) or not SHA_RE.fullmatch(record['body_sha256']):
        add(issues, 2, f'{prefix}.body_sha256 is invalid')
    for field in ('idiom', 'ensemble', 'not_when', 'inputs', 'outputs', 'preconditions', 'effects', 'theory_refs', 'examples', 'failure_modes', 'requires', 'composes_with'):
        validate_list(record, field, issues, prefix)
    validate_list(record, 'use_when', issues, prefix, required=True)
    ops = record.get('ops')
    if not isinstance(ops, list):
        add(issues, 2, f'{prefix}.ops must be a list')
    else:
        for op_index, op in enumerate(ops):
            if not isinstance(op, dict) or set(op) != OP_FIELDS or op.get('implementation') != 'unimplemented' or not isinstance(op.get('id'), str) or not op['id']:
                add(issues, 2, f'{prefix}.ops[{op_index}] is invalid or not unimplemented')
    validators = record.get('validators')
    if not isinstance(validators, list):
        add(issues, 2, f'{prefix}.validators must be a list')
    else:
        for validator_index, validator in enumerate(validators):
            if not isinstance(validator, dict) or set(validator) != VALIDATOR_FIELDS or not isinstance(validator.get('id'), str) or not validator['id'] or validator.get('severity') not in SEVERITIES or not isinstance(validator.get('autofix'), bool) or validator.get('implementation') not in {'unimplemented', 'advisory'}:
                add(issues, 2, f'{prefix}.validators[{validator_index}] is invalid for P1')


def validate_index(index, issues):
    if not isinstance(index, dict):
        add(issues, 2, 'index root must be an object')
        return
    if set(index) != {'schema_version', 'catalog_sha256', 'skills'}:
        add(issues, 2, 'index top-level keys must be schema_version, catalog_sha256, skills')
    if index.get('schema_version') != '1':
        add(issues, 2, 'index schema_version must be 1')
    if not isinstance(index.get('catalog_sha256'), str) or not SHA_RE.fullmatch(index['catalog_sha256']):
        add(issues, 2, 'index catalog_sha256 is invalid')
    records = index.get('skills')
    if not isinstance(records, list):
        add(issues, 2, 'index skills must be an array')
        return
    ids = []
    for position, record in enumerate(records):
        validate_record(record, position, issues)
        if isinstance(record, dict) and isinstance(record.get('id'), str):
            ids.append(record['id'])
    if len(ids) != len(set(ids)):
        add(issues, 2, 'duplicate skill ids')
    if ids != sorted(ids):
        add(issues, 2, 'skills must be sorted by id')
    if len(records) != 36:
        add(issues, 4, f'expected 36 cards, found {len(records)}')
    counts = {}
    for record in records:
        if isinstance(record, dict) and record.get('category') in CATEGORIES:
            counts[record['category']] = counts.get(record['category'], 0) + 1
    if counts != EXPECTED_COUNTS:
        add(issues, 4, f'category counts mismatch: {counts}')
    expected = set().union(*EXPECTED_IDS.values())
    if set(ids) != expected:
        add(issues, 4, 'seed id set mismatch')
    record_map = {record.get('id'): record for record in records if isinstance(record, dict)}
    for record in records:
        if not isinstance(record, dict):
            continue
        for field in ('requires', 'composes_with'):
            values = record.get(field, [])
            if not isinstance(values, list):
                continue
            for target in values:
                if target == record.get('id') or target not in record_map:
                    add(issues, 4, f'{record.get("id")}.{field} references unknown/self id {target}')
    return index


def validate_bodies(root, index, issues):
    records = index.get('skills', []) if isinstance(index, dict) else []
    expected = {record.get('id') for record in records if isinstance(record, dict) and isinstance(record.get('id'), str)}
    actual = {path.stem for path in root.glob('*.md')}
    if actual != expected:
        add(issues, 2, f'body file set mismatch: expected {sorted(expected)}, found {sorted(actual)}')
    expected_files = {f'{card_id}.md' for card_id in expected} | {'index.json'}
    actual_files = {path.name for path in root.iterdir() if path.is_file()}
    if actual_files != expected_files:
        add(issues, 2, f'index directory layout mismatch: expected {sorted(expected_files)}, found {sorted(actual_files)}')
    for record in records:
        if not isinstance(record, dict):
            continue
        path = root / f'{record.get("id")}.md'
        if not path.exists():
            add(issues, 2, f'missing body: {path}')
            continue
        raw = path.read_bytes()
        try:
            text = raw.decode('utf-8')
        except UnicodeDecodeError as exc:
            add(issues, 2, f'{path} is not UTF-8: {exc}')
            continue
        if raw.startswith(b'\xef\xbb\xbf') or b'\r' in raw:
            add(issues, 2, f'{path} is not UTF-8 no-BOM LF')
        for section in REQUIRED_SECTIONS:
            count = len(re.findall(rf'^## {re.escape(section)}$', text, re.MULTILINE))
            if count != 1:
                add(issues, 2, f'{path} section {section} count={count}')
        if CJK_RE.search(text):
            add(issues, 2, f'{path} contains Japanese/CJK text')
        if body_hash(path) != record.get('body_sha256'):
            add(issues, 3, f'{path} body_sha256 mismatch')
    if isinstance(index, dict) and isinstance(index.get('skills'), list):
        if catalog_hash(index['skills']) != index.get('catalog_sha256'):
            add(issues, 3, 'catalog_sha256 mismatch')


def self_scan(issues):
    path = Path(__file__).resolve()
    try:
        tree = ast.parse(path.read_text(encoding='utf-8'))
    except (OSError, SyntaxError, UnicodeDecodeError) as exc:
        add(issues, 1, f'cannot self-scan checker: {exc}')
        return
    for node in ast.walk(tree):
        names = []
        if isinstance(node, ast.Import):
            names = [alias.name.split('.')[0] for alias in node.names]
        elif isinstance(node, ast.ImportFrom):
            names = [(node.module or '').split('.')[0]]
        for name in names:
            if name not in ALLOWED_IMPORTS or name in BANNED_IMPORTS:
                add(issues, 5, f'banned or non-allowlisted production import: {name}')
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Attribute) and node.func.attr in {'system', 'popen', 'Popen', 'run', 'check_call', 'check_output'}:
                add(issues, 5, f'banned production call: {node.func.attr}')
            if isinstance(node.func, ast.Name) and node.func.id in {'eval', 'exec'}:
                add(issues, 5, f'banned production call: {node.func.id}')


def check_shelf(root):
    issues = []
    index_path = root / 'index.json'
    index = read_json(index_path, issues)
    if index is not None:
        validate_index(index, issues)
        validate_bodies(root, index, issues)
        raw = index_path.read_bytes()
        if raw != canonical_index(index):
            add(issues, 2, 'index is not canonical JSON')
    self_scan(issues)
    return issues, index


def validate_fixture(path, index, issues):
    fixture = read_json(path, issues)
    if fixture is None:
        return
    if not isinstance(fixture, list):
        add(issues, 2, 'selection fixture root must be an array')
        return
    if len(fixture) < 12:
        add(issues, 4, 'selection fixture must contain at least 12 cases')
    seen = set()
    categories = set()
    has_filter = False
    has_exclusion = False
    cards = {record.get('id'): record for record in index.get('skills', []) if isinstance(record, dict)}
    for position, case in enumerate(fixture):
        prefix = f'fixture[{position}]'
        if not isinstance(case, dict) or set(case) != {'id', 'task', 'expected_ids', 'expected_mode', 'expected_category', 'rationale'}:
            add(issues, 2, f'{prefix} fields are invalid')
            continue
        case_id = case.get('id')
        if not isinstance(case_id, str) or not ID_RE.fullmatch(case_id) or case_id in seen:
            add(issues, 2, f'{prefix}.id is invalid or duplicate')
        seen.add(case_id)
        if not isinstance(case.get('task'), str) or not case['task'].strip():
            add(issues, 2, f'{prefix}.task is invalid')
        expected_ids = case.get('expected_ids')
        if not isinstance(expected_ids, list) or len(expected_ids) > 3 or any(not isinstance(item, str) for item in expected_ids):
            add(issues, 2, f'{prefix}.expected_ids is invalid')
            expected_ids = []
        if len(expected_ids) != len(set(expected_ids)) or any(item not in cards for item in expected_ids):
            add(issues, 2, f'{prefix}.expected_ids contains unknown/duplicate id')
        mode = case.get('expected_mode')
        category = case.get('expected_category')
        if mode is not None and mode not in MODES:
            add(issues, 2, f'{prefix}.expected_mode is invalid')
        if category is not None and category not in CATEGORIES:
            add(issues, 2, f'{prefix}.expected_category is invalid')
        if mode is not None or category is not None:
            has_filter = True
        if category is not None:
            categories.add(category)
        categories.update(cards[item].get('category') for item in expected_ids if item in cards)
        if not isinstance(case.get('rationale'), str) or not case['rationale'].strip():
            add(issues, 2, f'{prefix}.rationale is empty')
        actual = select_skills(index, case.get('task', ''), mode, category)
        actual_ids = [record.get('id') for record in actual]
        if actual_ids != expected_ids:
            add(issues, 4, f'{prefix} expected {expected_ids}, got {actual_ids}')
        normalized_task = normalize(case.get('task', ''))
        excluded = []
        for card_id, card in cards.items():
            if mode is not None and card.get('mode') != mode:
                continue
            if category is not None and card.get('category') != category:
                continue
            if any(normalize(phrase) in normalized_task for phrase in card.get('not_when', [])) and any(normalize(phrase) in normalized_task for phrase in card.get('use_when', [])):
                excluded.append(card_id)
        if excluded and any(card_id not in expected_ids for card_id in excluded):
            has_exclusion = True
    if CATEGORIES - categories:
        add(issues, 4, f'fixture misses categories: {sorted(CATEGORIES - categories)}')
    if not has_filter:
        add(issues, 4, 'fixture needs a mode/category-filtered case')
    if not has_exclusion:
        add(issues, 4, 'fixture needs a real not_when exclusion case')


def print_issues(issues):
    for issue in issues:
        print(str(issue), file=sys.stderr)


def main(argv=None):
    parser = Parser()
    parser.add_argument('--root', required=True)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument('--check', action='store_true')
    mode.add_argument('--selection-fixture')
    try:
        args = parser.parse_args(argv)
    except UsageError as exc:
        print(f'1: {exc}', file=sys.stderr)
        return 1
    try:
        root = Path(args.root)
        issues, index = check_shelf(root)
        if issues:
            print_issues(issues)
            return first_code(issues)
        if args.selection_fixture is not None:
            fixture_issues = []
            validate_fixture(Path(args.selection_fixture), index, fixture_issues)
            if fixture_issues:
                print_issues(fixture_issues)
                return first_code(fixture_issues)
    except Exception as exc:
        print(f'1: unexpected error: {exc}', file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())
