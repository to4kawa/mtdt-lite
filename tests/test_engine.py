import ast
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import check_shelf
from engine import ops as ops_module
from engine import registry as registry_module
from engine import score as score_module
from engine import validators as validators_module

MTDT = ROOT / 'mtdt.py'
UPDATE_INDEX = ROOT / 'update_index.py'
SCORE_FIXTURES = ROOT / 'tests' / 'fixtures' / 'scores'
PRODUCTION = [MTDT, UPDATE_INDEX, *sorted((ROOT / 'engine').glob('*.py'))]
ENCODING_PATHS = [
    *PRODUCTION,
    ROOT / 'engine' / 'registry.json',
    ROOT / 'AGENTS.md',
    Path(__file__),
    *sorted(SCORE_FIXTURES.glob('*.json')),
    *sorted((ROOT / 'tests' / 'fixtures' / 'plans').glob('*.json')),
]
ALLOWED_IMPORTS = {'argparse', 'dataclasses', 'fractions', 'json', 'pathlib', 're', 'sys'}
LOCAL_IMPORTS = {'check_shelf', 'engine'}
BANNED_CALLS = {'system', 'popen', 'Popen', 'run', 'check_call', 'check_output'}
TEST_BANNED_IMPORTS = {
    'socket', 'http', 'ftplib', 'ssl', 'smtplib',
    'requests', 'httpx', 'openai', 'anthropic', 'asyncio',
}
RAT = {
    'good-chorale.json': (0, []),
    'good-melody.json': (0, [('voice-range', 'melody', 'info')]),
    'bad-underfull.json': (3, [('measure-fill', 'harmony', 'error')]),
    'bad-range.json': (3, [('voice-range', 'lead', 'error')]),
    'bad-overlap.json': (3, [('note-overlap', 'lead', 'error')]),
}


def run_cli(*args, cwd=ROOT):
    return subprocess.run([sys.executable, str(MTDT), *args], cwd=cwd, capture_output=True, text=True)


def run_update_index(*args, cwd=ROOT):
    return subprocess.run([sys.executable, str(UPDATE_INDEX), *args], cwd=cwd, capture_output=True, text=True)


def load_fixture(name):
    return json.loads((SCORE_FIXTURES / name).read_text(encoding='utf-8'))


def boundary_violations(path=None, source=None, is_engine=False):
    if source is None:
        source = path.read_text(encoding='utf-8')
    tree = ast.parse(source)
    violations = []
    for node in ast.walk(tree):
        names = []
        if isinstance(node, ast.Import):
            names = [alias.name.split('.')[0] for alias in node.names]
        elif isinstance(node, ast.ImportFrom):
            if node.level > 0:
                if not is_engine:
                    violations.append(f'relative import outside engine package: {node.module}')
                continue
            names = [(node.module or '').split('.')[0]]
        for name in names:
            if name not in ALLOWED_IMPORTS | LOCAL_IMPORTS:
                violations.append(f'import outside allowlist: {name}')
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Attribute) and node.func.attr in BANNED_CALLS:
                violations.append(f'banned call: {node.func.attr}')
            if isinstance(node.func, ast.Name) and node.func.id in {'eval', 'exec'}:
                violations.append(f'banned call: {node.func.id}')
    return violations


class RatScoreFixturesTests(unittest.TestCase):
    def test_preregistered_findings(self):
        for name, (_exit_code, expected) in RAT.items():
            with self.subTest(name=name):
                score = score_module.parse_score(load_fixture(name))
                findings = validators_module.run_validators(score)
                observed = [(f.validator, f.part, f.severity) for f in findings]
                self.assertEqual(observed, expected)

    def test_cli_exit_codes(self):
        for name, (exit_code, _expected) in RAT.items():
            with self.subTest(name=name):
                result = run_cli('validate', str(SCORE_FIXTURES / name))
                self.assertEqual(result.returncode, exit_code, result.stderr)
                self.assertEqual(result.stderr, '')
                self.assertIsInstance(json.loads(result.stdout), list)

    def test_good_chorale_has_zero_findings(self):
        result = run_cli('validate', str(SCORE_FIXTURES / 'good-chorale.json'))
        self.assertEqual(result.returncode, 0)
        self.assertEqual(json.loads(result.stdout), [])


class ScoreSchemaTests(unittest.TestCase):
    def make(self):
        return json.loads(json.dumps(load_fixture('good-chorale.json')))

    def expect_reject(self, data, fragment):
        with self.assertRaises(score_module.ScoreError) as context:
            score_module.parse_score(data)
        self.assertIn(fragment, str(context.exception))

    def test_all_fixtures_parse(self):
        for name in RAT:
            with self.subTest(name=name):
                score = score_module.parse_score(load_fixture(name))
                self.assertTrue(score.title)

    def test_schema_negatives(self):
        cases = []
        data = self.make()
        data['extra'] = 1
        cases.append(('extra-top-key', data, 'exactly the keys'))
        data = self.make()
        del data['parts']
        cases.append(('missing-parts', data, 'exactly the keys'))
        data = self.make()
        data['schema_version'] = '2'
        cases.append(('bad-schema-version', data, "must be '1'"))
        data = self.make()
        data['title'] = '   '
        cases.append(('empty-title', data, 'non-empty string'))
        data = self.make()
        del data['meter']['denominator']
        cases.append(('missing-denominator', data, 'exactly the keys'))
        data = self.make()
        data['meter']['denominator'] = 3
        cases.append(('denominator-3', data, 'must be one of 1, 2, 4, 8, 16, 32'))
        data = self.make()
        data['meter']['numerator'] = 0
        cases.append(('numerator-0', data, 'must be >= 1'))
        data = self.make()
        data['meter']['numerator'] = True
        cases.append(('bool-numerator', data, 'must be an integer'))
        data = self.make()
        data['key']['tonic'] = 'H'
        cases.append(('bad-tonic', data, 'must match'))
        data = self.make()
        data['key']['mode'] = 'dorian'
        cases.append(('bad-mode', data, 'must be one of: major, minor'))
        data = self.make()
        data['parts'] = []
        cases.append(('empty-parts', data, 'non-empty array'))
        data = self.make()
        data['parts'].append(json.loads(json.dumps(data['parts'][0])))
        cases.append(('duplicate-part-id', data, 'duplicate part id'))
        data = self.make()
        del data['parts'][0]['name']
        cases.append(('part-missing-name', data, 'optional key range'))
        data = self.make()
        data['parts'][0]['zzz'] = 1
        cases.append(('part-extra-key', data, 'optional key range'))
        data = self.make()
        data['parts'][0]['events'] = []
        cases.append(('empty-events', data, 'non-empty array'))
        data = self.make()
        data['parts'][0]['events'][0]['measure'] = 0
        cases.append(('measure-0', data, 'must be >= 1'))
        data = self.make()
        data['parts'][0]['events'][0]['measure'] = True
        cases.append(('bool-measure', data, 'must be an integer'))
        data = self.make()
        data['parts'][0]['events'][0]['onset'] = 0.5
        cases.append(('float-onset', data, "integer or an 'n/d' string"))
        data = self.make()
        data['parts'][0]['events'][0]['onset'] = '1.5'
        cases.append(('string-decimal', data, "integer or an 'n/d' string"))
        data = self.make()
        data['parts'][0]['events'][0]['onset'] = True
        cases.append(('bool-onset', data, 'bool is not a valid fraction'))
        data = self.make()
        data['parts'][0]['events'][0]['onset'] = -1
        cases.append(('negative-onset', data, 'must not be negative'))
        data = self.make()
        data['parts'][0]['events'][0]['duration'] = 0
        cases.append(('zero-duration', data, 'greater than zero'))
        data = self.make()
        data['parts'][0]['events'][0]['duration'] = '2/0'
        cases.append(('zero-denominator', data, 'denominator must not be zero'))
        data = self.make()
        data['parts'][0]['events'][0]['duration'] = 'a/b'
        cases.append(('malformed-fraction', data, "integer or an 'n/d' string"))
        data = self.make()
        data['parts'][0]['events'][0]['onset'] = '3/4'
        data['parts'][0]['events'][0]['duration'] = '1/2'
        cases.append(('event-overflow', data, 'exceeds measure length'))
        data = self.make()
        data['parts'][0]['events'][0]['pitch'] = 'H4'
        cases.append(('bad-pitch', data, 'must be null or match'))
        data = self.make()
        data['parts'][0]['events'][0]['pitch'] = 'C10'
        cases.append(('midi-out-of-range', data, 'midi value out of range 0..127'))
        data = self.make()
        data['parts'][0]['events'][0]['zzz'] = 1
        cases.append(('event-extra-key', data, 'exactly the keys'))
        data = self.make()
        data['parts'][0]['range']['low'] = None
        cases.append(('null-range-low', data, 'must be a pitch, not null'))
        data = self.make()
        data['parts'][0]['range']['low'] = 'G5'
        data['parts'][0]['range']['high'] = 'C4'
        cases.append(('inverted-range', data, 'low pitch must not exceed high pitch'))
        for label, data, fragment in cases:
            with self.subTest(case=label):
                self.expect_reject(data, fragment)

    def test_duplicate_json_key_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / 'dup.json'
            path.write_text(
                '{"schema_version": "1", "schema_version": "1"}',
                encoding='utf-8', newline='\n')
            with self.assertRaises(score_module.ScoreError) as context:
                score_module.load_score_file(path)
            self.assertIn('duplicate JSON key', str(context.exception))

    def test_missing_file_rejected(self):
        with self.assertRaises(score_module.ScoreError) as context:
            score_module.load_score_file(ROOT / 'does-not-exist.json')
        self.assertIn('missing file', str(context.exception))


class CliExitCodeTests(unittest.TestCase):
    def test_usage_exit_1(self):
        self.assertEqual(run_cli().returncode, 1)
        self.assertEqual(run_cli('nonsense').returncode, 1)
        self.assertEqual(run_cli('select').returncode, 1)

    def test_missing_file_exit_2(self):
        for command in ('validate', 'normalize'):
            with self.subTest(command=command):
                result = run_cli(command, str(ROOT / 'does-not-exist.json'))
                self.assertEqual(result.returncode, 2)
                self.assertEqual(result.stdout, '')
                self.assertTrue(result.stderr.startswith('2: '), result.stderr)
        result = run_cli('ops', 'score-load', str(ROOT / 'does-not-exist.json'))
        self.assertEqual(result.returncode, 2)
        self.assertEqual(result.stdout, '')

    def test_schema_violation_cli_exit_2(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / 'float-onset.json'
            data = load_fixture('good-chorale.json')
            data['parts'][0]['events'][0]['onset'] = 0.5
            path.write_text(json.dumps(data), encoding='utf-8', newline='\n')
            result = run_cli('validate', str(path))
            self.assertEqual(result.returncode, 2)
            self.assertEqual(result.stdout, '')
            self.assertIn('$', result.stderr)

    def test_unknown_op_exit_2(self):
        result = run_cli('ops', 'ghost-op', str(SCORE_FIXTURES / 'good-chorale.json'))
        self.assertEqual(result.returncode, 2)
        self.assertIn('unknown op: ghost-op', result.stderr)

    def test_findings_exit_3_and_info_only_exit_0(self):
        error_result = run_cli('validate', str(SCORE_FIXTURES / 'bad-range.json'))
        self.assertEqual(error_result.returncode, 3)
        findings = json.loads(error_result.stdout)
        self.assertEqual(len(findings), 1)
        self.assertEqual(findings[0]['severity'], 'error')
        info_result = run_cli('validate', str(SCORE_FIXTURES / 'good-melody.json'))
        self.assertEqual(info_result.returncode, 0)
        findings = json.loads(info_result.stdout)
        self.assertEqual([f['severity'] for f in findings], ['info'])

    def test_ops_exit_codes(self):
        score = str(SCORE_FIXTURES / 'good-chorale.json')
        self.assertEqual(run_cli('ops', 'score-load', score).returncode, 0)
        self.assertEqual(run_cli('ops', 'score-normalize', score).returncode, 0)
        self.assertEqual(run_cli('ops', 'score-validate', score).returncode, 0)
        self.assertEqual(
            run_cli('ops', 'score-validate', str(SCORE_FIXTURES / 'bad-underfull.json')).returncode, 3)

    def test_score_load_summary(self):
        result = run_cli('ops', 'score-load', str(SCORE_FIXTURES / 'good-chorale.json'))
        payload = json.loads(result.stdout)
        self.assertEqual(payload, {
            'op': 'score-load',
            'ok': True,
            'title': 'Good chorale excerpt',
            'parts': 4,
            'events': 16,
            'measures': 2,
        })

    def test_validators_subcommand(self):
        result = run_cli('validators')
        self.assertEqual(result.returncode, 0)
        payload = json.loads(result.stdout)
        self.assertEqual(
            [entry['id'] for entry in payload],
            ['measure-fill', 'note-overlap', 'parallel-perfect', 'voice-crossing', 'voice-range'])
        for entry in payload:
            self.assertEqual(set(entry), {'id', 'severity', 'autofix', 'implementation', 'summary'})
            self.assertEqual(entry['severity'], 'error')
            self.assertIs(entry['autofix'], False)
            self.assertEqual(entry['implementation'], 'implemented')

    def test_cli_writes_no_files(self):
        index_path = ROOT / 'skills' / 'index.json'
        before_index = index_path.read_bytes()
        before_fixtures = {p.name: p.read_bytes() for p in SCORE_FIXTURES.glob('*.json')}
        score = str(SCORE_FIXTURES / 'good-chorale.json')
        run_cli('validate', score)
        run_cli('normalize', score)
        run_cli('ops', 'score-load', score)
        run_cli('validators')
        run_cli('select', 'analyze pitch intervals')
        self.assertEqual(index_path.read_bytes(), before_index)
        after_fixtures = {p.name: p.read_bytes() for p in SCORE_FIXTURES.glob('*.json')}
        self.assertEqual(after_fixtures, before_fixtures)

    def test_select_empty_output_exit_0(self):
        result = run_cli('select', 'zzz nonsense gibberish query')
        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stdout, '')

    def test_select_text_and_json_format(self):
        text_result = run_cli('select', 'analyze pitch intervals')
        self.assertEqual(text_result.returncode, 0)
        first_line = text_result.stdout.splitlines()[0]
        self.assertEqual(first_line, 'pitch-intervals\tfoundations/analyze\tPitch Intervals')
        json_result = run_cli('select', 'analyze pitch intervals', '--format', 'json')
        self.assertEqual(json_result.returncode, 0)
        payload = json.loads(json_result.stdout)
        self.assertEqual(set(payload[0]), {'id', 'title', 'category', 'mode', 'level'})

    def test_select_parity_with_matcher(self):
        index = json.loads((ROOT / 'skills' / 'index.json').read_text(encoding='utf-8'))
        cases = json.loads(
            (ROOT / 'tests' / 'fixtures' / 'selection_cases.json').read_text(encoding='utf-8'))
        for case in cases[:5]:
            with self.subTest(case=case['id']):
                expected = [
                    record['id']
                    for record in check_shelf.select_skills(
                        index, case['task'], case['expected_mode'], case['expected_category'])
                ]
                self.assertEqual(expected, case['expected_ids'])
                arguments = ['select', case['task']]
                if case['expected_mode'] is not None:
                    arguments += ['--mode', case['expected_mode']]
                if case['expected_category'] is not None:
                    arguments += ['--category', case['expected_category']]
                result = run_cli(*arguments)
                self.assertEqual(result.returncode, 0, result.stderr)
                observed = [line.split('\t')[0] for line in result.stdout.splitlines()]
                self.assertEqual(observed, case['expected_ids'])

    def test_select_failing_shelf_returns_shelf_code(self):
        with tempfile.TemporaryDirectory() as temp:
            temp_root = Path(temp)
            for name in ('mtdt.py', 'check_shelf.py'):
                shutil.copy2(ROOT / name, temp_root / name)
            shutil.copytree(ROOT / 'engine', temp_root / 'engine')
            shutil.copytree(ROOT / 'skills', temp_root / 'skills')
            body = temp_root / 'skills' / 'pitch-intervals.md'
            body.write_bytes(body.read_bytes() + b'\n')
            result = subprocess.run(
                [sys.executable, str(temp_root / 'mtdt.py'), 'select', 'analyze pitch intervals'],
                capture_output=True, text=True)
            self.assertEqual(result.returncode, 3, result.stderr)
            self.assertEqual(result.stdout, '')


class NormalizeTests(unittest.TestCase):
    def test_idempotent_round_trip(self):
        result = run_cli('normalize', str(SCORE_FIXTURES / 'good-chorale.json'))
        self.assertEqual(result.returncode, 0, result.stderr)
        first = result.stdout.encode('utf-8')
        score = score_module.parse_score(json.loads(first))
        self.assertEqual(score_module.canonical_score_bytes(score), first)
        second = run_cli('normalize', str(SCORE_FIXTURES / 'good-chorale.json'))
        self.assertEqual(second.stdout.encode('utf-8'), first)

    def test_part_order_preserved(self):
        result = run_cli('normalize', str(SCORE_FIXTURES / 'good-chorale.json'))
        payload = json.loads(result.stdout)
        self.assertEqual(
            [part['id'] for part in payload['parts']],
            ['soprano', 'alto', 'tenor', 'bass'])

    def test_fraction_canonicalization(self):
        data = {
            'schema_version': '1',
            'title': 'fractions',
            'meter': {'numerator': 4, 'denominator': 4},
            'key': {'tonic': 'C', 'mode': 'major'},
            'parts': [{
                'id': 'p',
                'name': 'P',
                'events': [
                    {'measure': 1, 'onset': '0/4', 'duration': '4/4', 'pitch': 'C4'},
                    {'measure': 1, 'onset': '2/4', 'duration': '1/4', 'pitch': 'E4'},
                ],
            }],
        }
        score = score_module.parse_score(data)
        payload = score_module.score_to_dict(score)
        events = payload['parts'][0]['events']
        self.assertEqual(events[0]['onset'], 0)
        self.assertEqual(events[0]['duration'], 1)
        self.assertEqual(events[1]['onset'], '1/2')
        self.assertEqual(events[1]['duration'], '1/4')


class RegistryTests(unittest.TestCase):
    def load_raw(self):
        return json.loads((ROOT / 'engine' / 'registry.json').read_text(encoding='utf-8'))

    def test_schema_and_sync(self):
        data = registry_module.load()
        self.assertEqual(set(data), {'schema_version', 'ops', 'validators'})
        self.assertEqual(data['schema_version'], '1')
        op_ids = [entry['id'] for entry in data['ops']]
        validator_ids = [entry['id'] for entry in data['validators']]
        self.assertEqual(op_ids, sorted(op_ids))
        self.assertEqual(validator_ids, sorted(validator_ids))
        self.assertEqual(set(op_ids), set(ops_module.OPS_IMPL))
        self.assertEqual(set(validator_ids), set(validators_module.VALIDATORS))
        self.assertEqual(
            set(op_ids), {'score-load', 'score-normalize', 'score-validate', 'voice-fill'})
        self.assertEqual(
            set(validator_ids),
            {'measure-fill', 'note-overlap', 'parallel-perfect', 'voice-crossing', 'voice-range'})
        for entry in data['ops']:
            self.assertEqual(set(entry), {'id', 'implementation', 'summary'})
            self.assertEqual(entry['implementation'], 'implemented')

    def test_rejects_code_drift(self):
        data = self.load_raw()
        data['ops'].append({
            'id': 'z-ghost-op', 'implementation': 'implemented', 'summary': 'ghost'})
        with self.assertRaises(registry_module.RegistryError) as context:
            registry_module.validate_registry(data)
        self.assertIn('do not match code', str(context.exception))
        data = self.load_raw()
        data['ops'] = [entry for entry in data['ops'] if entry['id'] != 'score-load']
        with self.assertRaises(registry_module.RegistryError):
            registry_module.validate_registry(data)
        data = self.load_raw()
        data['validators'] = [
            entry for entry in data['validators'] if entry['id'] != 'measure-fill']
        with self.assertRaises(registry_module.RegistryError):
            registry_module.validate_registry(data)

    def test_rejects_schema_violations(self):
        data = self.load_raw()
        data['extra'] = 1
        with self.assertRaises(registry_module.RegistryError):
            registry_module.validate_registry(data)
        data = self.load_raw()
        data['validators'][0]['severity'] = 'bogus'
        with self.assertRaises(registry_module.RegistryError):
            registry_module.validate_registry(data)
        data = self.load_raw()
        data['validators'][0]['autofix'] = 'yes'
        with self.assertRaises(registry_module.RegistryError):
            registry_module.validate_registry(data)
        data = self.load_raw()
        data['ops'] = list(reversed(data['ops']))
        with self.assertRaises(registry_module.RegistryError):
            registry_module.validate_registry(data)
        data = self.load_raw()
        data['ops'][0]['implementation'] = 'unimplemented'
        with self.assertRaises(registry_module.RegistryError):
            registry_module.validate_registry(data)

    def test_op_lookup(self):
        self.assertIs(registry_module.op('score-load'), ops_module.op_score_load)
        with self.assertRaises(registry_module.RegistryError):
            registry_module.op('ghost-op')

    def test_corrupt_registry_file_is_exit_2(self):
        with tempfile.TemporaryDirectory() as temp:
            bad = Path(temp) / 'registry.json'
            bad.write_text('{', encoding='utf-8', newline='\n')
            with self.assertRaises(registry_module.RegistryError):
                registry_module.load(bad)


class ValidatorsContractTests(unittest.TestCase):
    def test_finding_shape_exact_keys(self):
        score = score_module.parse_score(load_fixture('bad-underfull.json'))
        for finding in validators_module.run_validators(score):
            self.assertEqual(
                set(finding.to_dict()),
                {'validator', 'severity', 'part', 'measure', 'message'})
            self.assertIn(finding.validator, validators_module.VALIDATORS)

    def test_deterministic_order_independent_of_input_part_order(self):
        data = {
            'schema_version': '1',
            'title': 'ordering',
            'meter': {'numerator': 4, 'denominator': 4},
            'key': {'tonic': 'C', 'mode': 'major'},
            'parts': [
                {'id': 'zebra', 'name': 'Zebra', 'events': [
                    {'measure': 1, 'onset': 0, 'duration': '1/2', 'pitch': 'C4'}]},
                {'id': 'alpha', 'name': 'Alpha', 'events': [
                    {'measure': 1, 'onset': 0, 'duration': '1/2', 'pitch': 'C4'}]},
            ],
        }
        score = score_module.parse_score(data)
        findings = validators_module.run_validators(score)
        observed = [(f.validator, f.part, f.severity) for f in findings]
        self.assertEqual(observed, [
            ('measure-fill', 'alpha', 'error'),
            ('measure-fill', 'zebra', 'error'),
            ('voice-range', 'alpha', 'info'),
            ('voice-range', 'zebra', 'info'),
        ])

    def test_rangeless_part_info_skip(self):
        score = score_module.parse_score(load_fixture('good-melody.json'))
        findings = validators_module.run_validators(score)
        self.assertEqual(len(findings), 1)
        finding = findings[0]
        self.assertEqual(finding.severity, 'info')
        self.assertEqual(finding.part, 'melody')
        self.assertIsNone(finding.measure)
        self.assertIn('no declared range', finding.message)

    def test_boundary_contact_is_not_overlap(self):
        data = {
            'schema_version': '1',
            'title': 'boundary',
            'meter': {'numerator': 4, 'denominator': 4},
            'key': {'tonic': 'C', 'mode': 'major'},
            'parts': [{
                'id': 'p',
                'name': 'P',
                'range': {'low': 'C4', 'high': 'C5'},
                'events': [
                    {'measure': 1, 'onset': 0, 'duration': '1/2', 'pitch': 'C4'},
                    {'measure': 1, 'onset': '1/2', 'duration': '1/2', 'pitch': 'E4'},
                ],
            }],
        }
        score = score_module.parse_score(data)
        self.assertEqual(validators_module.run_validators(score), [])

    def test_duplicate_event_message(self):
        data = {
            'schema_version': '1',
            'title': 'duplicates',
            'meter': {'numerator': 4, 'denominator': 4},
            'key': {'tonic': 'C', 'mode': 'major'},
            'parts': [{
                'id': 'p',
                'name': 'P',
                'range': {'low': 'C4', 'high': 'C5'},
                'events': [
                    {'measure': 1, 'onset': 0, 'duration': '1/4', 'pitch': 'C4'},
                    {'measure': 1, 'onset': 0, 'duration': '1/4', 'pitch': 'C4'},
                    {'measure': 1, 'onset': '1/4', 'duration': '1/4', 'pitch': 'D4'},
                    {'measure': 1, 'onset': '1/2', 'duration': '1/2', 'pitch': 'E4'},
                ],
            }],
        }
        score = score_module.parse_score(data)
        findings = validators_module.run_validators(score)
        self.assertEqual([(f.validator, f.severity) for f in findings], [('note-overlap', 'error')])
        self.assertIn('duplicate event', findings[0].message)

    def test_registry_severity_matches_findings(self):
        data = registry_module.load()
        severities = {entry['id']: entry['severity'] for entry in data['validators']}
        for name in RAT:
            score = score_module.parse_score(load_fixture(name))
            for finding in validators_module.run_validators(score):
                if finding.severity == 'info':
                    self.assertEqual(finding.validator, 'voice-range')
                    self.assertIn('no declared range', finding.message)
                    continue
                self.assertEqual(finding.severity, severities[finding.validator])


class ImportBoundaryTests(unittest.TestCase):
    def test_production_allowlist(self):
        for path in PRODUCTION:
            with self.subTest(path=path.name):
                is_engine = path.parent.name == 'engine'
                self.assertEqual(boundary_violations(path=path, is_engine=is_engine), [])

    def test_seeded_violations_are_detected(self):
        source = 'import socket\nimport subprocess\nimport os\nos.system("x")\neval("1")\n'
        violations = boundary_violations(source=source)
        self.assertTrue(any('socket' in item for item in violations))
        self.assertTrue(any('subprocess' in item for item in violations))
        self.assertTrue(any('os' in item for item in violations))
        self.assertTrue(any('banned call: system' in item for item in violations))
        self.assertTrue(any('banned call: eval' in item for item in violations))

    def test_clean_source_passes_and_relative_imports_need_engine(self):
        self.assertEqual(boundary_violations(source='import json\nimport check_shelf\n'), [])
        violations = boundary_violations(source='from .score import Score\n', is_engine=False)
        self.assertTrue(any('relative import outside engine' in item for item in violations))
        self.assertEqual(
            boundary_violations(source='from .score import Score\n', is_engine=True), [])

    def test_test_files_have_no_network_or_llm_imports(self):
        for path in sorted((ROOT / 'tests').glob('test_*.py')):
            with self.subTest(path=path.name):
                tree = ast.parse(path.read_text(encoding='utf-8'))
                imports = set()
                for node in ast.walk(tree):
                    if isinstance(node, ast.Import):
                        imports.update(alias.name.split('.')[0] for alias in node.names)
                    elif isinstance(node, ast.ImportFrom):
                        imports.add((node.module or '').split('.')[0])
                self.assertFalse(imports & TEST_BANNED_IMPORTS, imports & TEST_BANNED_IMPORTS)


class UpdateIndexTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.skills = Path(self.temp.name) / 'skills'
        shutil.copytree(ROOT / 'skills', self.skills)
        self.original = (self.skills / 'index.json').read_bytes()

    def tearDown(self):
        self.temp.cleanup()

    def run_update(self, *args):
        return run_update_index('--root', str(self.skills), *args)

    def index_bytes(self):
        return (self.skills / 'index.json').read_bytes()

    def shelf_check(self):
        return subprocess.run(
            [sys.executable, str(ROOT / 'check_shelf.py'), '--root', str(self.skills), '--check'],
            capture_output=True, text=True)

    def test_dry_run_writes_nothing(self):
        result = self.run_update('--card', 'pitch-intervals', '--add-op', 'score-load')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('dry-run', result.stdout)
        self.assertEqual(self.index_bytes(), self.original)

    def test_accepts_implemented_for_registered_op(self):
        result = self.run_update(
            '--card', 'pitch-intervals', '--add-op', 'score-load',
            '--implementation', 'implemented')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('dry-run', result.stdout)
        self.assertEqual(self.index_bytes(), self.original)

    def test_accepts_implemented_for_registered_validator(self):
        result = self.run_update(
            '--card', 'pitch-intervals', '--add-validator', 'measure-fill',
            '--implementation', 'implemented')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('dry-run', result.stdout)
        self.assertEqual(self.index_bytes(), self.original)

    def test_refuses_implemented_for_unknown_id(self):
        result = self.run_update(
            '--card', 'pitch-intervals', '--add-validator', 'bogus-id',
            '--implementation', 'implemented')
        self.assertEqual(result.returncode, 2, result.stderr)
        self.assertEqual(self.index_bytes(), self.original)

    def test_apply_add_and_remove_restores_bytes(self):
        added = self.run_update(
            '--card', 'pitch-intervals', '--add-op', 'score-load', '--apply')
        self.assertEqual(added.returncode, 0, added.stderr)
        self.assertIn('written', added.stdout)
        self.assertNotEqual(self.index_bytes(), self.original)
        self.assertFalse((self.skills / 'index.json.tmp').exists())
        payload = json.loads(self.index_bytes().decode('utf-8'))
        card = [entry for entry in payload['skills'] if entry['id'] == 'pitch-intervals'][0]
        self.assertEqual(
            card['ops'], [{'id': 'score-load', 'implementation': 'unimplemented'}])
        self.assertEqual(self.shelf_check().returncode, 0)
        duplicate = self.run_update(
            '--card', 'pitch-intervals', '--add-op', 'score-load', '--apply')
        self.assertEqual(duplicate.returncode, 2, duplicate.stderr)
        removed = self.run_update(
            '--card', 'pitch-intervals', '--remove-op', 'score-load', '--apply')
        self.assertEqual(removed.returncode, 0, removed.stderr)
        self.assertEqual(self.index_bytes(), self.original)

    def test_apply_validator_metadata(self):
        result = self.run_update(
            '--card', 'pitch-intervals', '--add-validator', 'measure-fill', '--apply')
        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(self.index_bytes().decode('utf-8'))
        card = [entry for entry in payload['skills'] if entry['id'] == 'pitch-intervals'][0]
        self.assertEqual(card['validators'], [{
            'id': 'measure-fill',
            'severity': 'error',
            'autofix': False,
            'implementation': 'unimplemented',
        }])
        self.assertEqual(self.shelf_check().returncode, 0)

    def test_rehash_is_idempotent(self):
        result = self.run_update('--rehash', '--apply')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.index_bytes(), self.original)

    def test_error_paths(self):
        cases = [
            (('--card', 'no-such-card', '--add-op', 'x', '--apply'), 2),
            (('--card', 'pitch-intervals', '--remove-op', 'never-added'), 2),
            (('--add-op', 'a', '--remove-op', 'b'), 2),
            (('--card', 'pitch-intervals', '--add-op', 'a', '--rehash'), 2),
            (('--card', 'pitch-intervals',), 2),
            (('--card', 'pitch-intervals', '--add-op', 'a', '--add-validator', 'b'), 2),
            ((), 1),
            (('--card', 'pitch-intervals', '--add-op', 'a', '--severity', 'bogus'), 1),
            (('--card', 'pitch-intervals', '--add-op', 'a', '--autofix', 'maybe'), 1),
        ]
        for arguments, expected in cases:
            with self.subTest(arguments=arguments):
                result = self.run_update(*arguments)
                self.assertEqual(result.returncode, expected, result.stderr)
                self.assertEqual(self.index_bytes(), self.original)


class P2SourceEncodingTests(unittest.TestCase):
    def test_utf8_no_bom_lf(self):
        for path in ENCODING_PATHS:
            with self.subTest(path=str(path.relative_to(ROOT))):
                raw = path.read_bytes()
                self.assertFalse(raw.startswith(b'\xef\xbb\xbf'), path)
                self.assertNotIn(b'\r', raw, path)
                raw.decode('utf-8')


if __name__ == '__main__':
    unittest.main()
