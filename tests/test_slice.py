import json
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
from engine import voicer as voicer_module

SCORES = ROOT / 'tests' / 'fixtures' / 'scores'
PLANS = ROOT / 'tests' / 'fixtures' / 'plans'
SKELETON = SCORES / 'satb-skeleton.json'
PLAN = PLANS / 'satb-chord-plan.json'


def run_cli(*args, cwd=ROOT):
    return subprocess.run(
        [sys.executable, str(ROOT / 'mtdt.py'), *args],
        cwd=cwd, capture_output=True, text=True, encoding='utf-8')


def load_score(name):
    return score_module.load_score_file(SCORES / name)


def load_plan():
    return voicer_module.load_plan_file(PLAN)


def pitches(score, part_id):
    for part in score.parts:
        if part.id == part_id:
            return [event.pitch for event in part.events]
    raise AssertionError(f'unknown part: {part_id}')


class PlanSchemaTests(unittest.TestCase):
    def make(self):
        return json.loads(PLAN.read_text(encoding='utf-8'))

    def expect_reject(self, data, fragment):
        with self.assertRaises(voicer_module.PlanError) as context:
            voicer_module.parse_plan(data)
        self.assertIn(fragment, str(context.exception))

    def test_good_plan(self):
        plan = load_plan()
        self.assertEqual(plan.tonic, 'C')
        self.assertEqual(plan.slots, ((1, 'I'), (2, 'vi'), (3, 'IV'), (4, 'V')))

    def test_extra_key_rejected(self):
        data = self.make()
        data['extra'] = 1
        self.expect_reject(data, 'exactly the keys')

    def test_unknown_chord_rejected(self):
        data = self.make()
        data['slots'][0]['chord'] = 'Imaj7'
        self.expect_reject(data, 'unknown chord')

    def test_minor_mode_rejected(self):
        data = self.make()
        data['key']['mode'] = 'minor'
        self.expect_reject(data, 'minor keys not supported in P3')

    def test_duplicate_measure_rejected(self):
        data = self.make()
        data['slots'].append({'measure': 2, 'chord': 'V'})
        self.expect_reject(data, 'duplicate')

    def test_plan_error_is_score_error(self):
        self.assertTrue(issubclass(voicer_module.PlanError, score_module.ScoreError))


class VoicerRatTests(unittest.TestCase):
    def test_rat_exact_voicing(self):
        filled = voicer_module.fill_voices(load_score('satb-skeleton.json'), load_plan())
        self.assertEqual(pitches(filled, 'alto'), ['G3', 'A3', 'A3', 'B3'])
        self.assertEqual(pitches(filled, 'tenor'), ['C3', 'C3', 'C3', 'G3'])
        self.assertEqual(
            pitches(filled, 'soprano'), ['E4', 'E4', 'F4', 'D4'])
        self.assertEqual(
            pitches(filled, 'bass'), ['C3', 'A2', 'F2', 'G2'])

    def test_rat_validate_clean(self):
        filled = voicer_module.fill_voices(load_score('satb-skeleton.json'), load_plan())
        self.assertEqual(validators_module.run_validators(filled), [])
        result = run_cli('voice-fill', str(SKELETON), str(PLAN))
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_voice_fill_cli_payload(self):
        result = run_cli('voice-fill', str(SKELETON), str(PLAN))
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stderr, '')
        payload = json.loads(result.stdout)
        self.assertEqual(set(payload), {'findings', 'score'})
        self.assertEqual(payload['findings'], [])
        parts = {part['id']: part for part in payload['score']['parts']}
        self.assertEqual(
            [event['pitch'] for event in parts['alto']['events']],
            ['G3', 'A3', 'A3', 'B3'])
        self.assertEqual(
            [event['pitch'] for event in parts['tenor']['events']],
            ['C3', 'C3', 'C3', 'G3'])

    def test_voice_fill_out_file(self):
        with tempfile.TemporaryDirectory() as temp:
            out = Path(temp) / 'filled.json'
            result = run_cli('voice-fill', str(SKELETON), str(PLAN), '--out', str(out))
            self.assertEqual(result.returncode, 0, result.stderr)
            from_file = json.loads(out.read_bytes().decode('utf-8'))
            direct = json.loads(run_cli('voice-fill', str(SKELETON), str(PLAN)).stdout)
            self.assertEqual(from_file, direct)

    def test_voice_fill_bad_plan_exit_2(self):
        with tempfile.TemporaryDirectory() as temp:
            bad = Path(temp) / 'bad-plan.json'
            data = json.loads(PLAN.read_text(encoding='utf-8'))
            data['slots'][0]['chord'] = 'Imaj7'
            bad.write_text(json.dumps(data), encoding='utf-8')
            result = run_cli('voice-fill', str(SKELETON), str(bad))
            self.assertEqual(result.returncode, 2, result.stderr)

    def test_voice_fill_prefilled_exit_1(self):
        with tempfile.TemporaryDirectory() as temp:
            pitched = Path(temp) / 'pitched.json'
            data = json.loads(SKELETON.read_text(encoding='utf-8'))
            for part in data['parts']:
                if part['id'] == 'alto':
                    part['events'][0]['pitch'] = 'C4'
            pitched.write_text(json.dumps(data), encoding='utf-8')
            result = run_cli('voice-fill', str(pitched), str(PLAN))
            self.assertEqual(result.returncode, 1, result.stderr)

    def test_ops_voice_fill_needs_plan(self):
        result = run_cli('ops', 'voice-fill', str(SKELETON))
        self.assertEqual(result.returncode, 2, result.stderr)

    def test_ops_voice_fill_with_plan(self):
        result = run_cli('ops', 'voice-fill', str(SKELETON), '--plan', str(PLAN))
        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(payload['op'], 'voice-fill')
        self.assertEqual(payload['findings'], [])

    def test_op_signatures_accept_extra(self):
        score = load_score('satb-skeleton.json')
        self.assertTrue(ops_module.op_score_load(str(SKELETON), None)['ok'])
        self.assertIsInstance(ops_module.op_score_validate(str(SKELETON), None), list)
        self.assertTrue(score.title)


class AdversarialTests(unittest.TestCase):
    def observed(self, name):
        score = load_score(name)
        return [(finding.validator, finding.part, finding.severity, finding.measure,
                 finding.message)
                for finding in validators_module.run_validators(score)]

    def test_parallel_fifths_detected(self):
        observed = self.observed('satb-parallel.json')
        self.assertEqual(len(observed), 1)
        validator, part, severity, measure, message = observed[0]
        self.assertEqual((validator, part, severity, measure),
                         ('parallel-perfect', None, 'error', 2))
        self.assertIn('parallel fifths', message)
        self.assertIn('soprano', message)
        self.assertIn('alto', message)
        result = run_cli('validate', str(SCORES / 'satb-parallel.json'))
        self.assertEqual(result.returncode, 3, result.stderr)

    def test_crossing_detected(self):
        observed = self.observed('satb-crossing.json')
        self.assertEqual(len(observed), 1)
        validator, part, severity, measure, message = observed[0]
        self.assertEqual((validator, part, severity, measure),
                         ('voice-crossing', None, 'error', 1))
        self.assertIn('soprano', message)
        self.assertIn('alto', message)
        result = run_cli('validate', str(SCORES / 'satb-crossing.json'))
        self.assertEqual(result.returncode, 3, result.stderr)

    def test_contrary_motion_legal(self):
        self.assertEqual(self.observed('satb-contrary.json'), [])
        result = run_cli('validate', str(SCORES / 'satb-contrary.json'))
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout), [])


class CardWiringTests(unittest.TestCase):
    def index(self):
        return json.loads((ROOT / 'skills' / 'index.json').read_text(encoding='utf-8'))

    def test_exactly_three_validated(self):
        records = {record['id']: record for record in self.index()['skills']}
        validated = sorted(
            card_id for card_id, record in records.items() if record['status'] == 'validated')
        self.assertEqual(validated, [
            'parallel-motion-avoidance',
            'satb-chorale-harmonization',
            'voice-leading-rules',
        ])
        for card_id, record in records.items():
            if card_id not in validated:
                self.assertEqual(record['status'], 'draft', card_id)
                self.assertEqual(record['ops'], [], card_id)
                self.assertEqual(record['validators'], [], card_id)

    def test_wiring_declarations_exact(self):
        records = {record['id']: record for record in self.index()['skills']}
        self.assertEqual(
            records['parallel-motion-avoidance']['validators'],
            [{'id': 'parallel-perfect', 'severity': 'error', 'autofix': False,
              'implementation': 'implemented'}])
        self.assertEqual(records['parallel-motion-avoidance']['ops'], [])
        self.assertEqual(
            records['voice-leading-rules']['validators'],
            [{'id': 'voice-crossing', 'severity': 'error', 'autofix': False,
              'implementation': 'implemented'}])
        self.assertEqual(records['voice-leading-rules']['ops'], [])
        self.assertEqual(
            records['satb-chorale-harmonization']['ops'],
            [{'id': 'voice-fill', 'implementation': 'implemented'}])
        self.assertEqual(records['satb-chorale-harmonization']['validators'], [])

    def test_validated_items_link_to_code(self):
        data = registry_module.load()
        registry_ops = {entry['id'] for entry in data['ops']}
        registry_validators = {entry['id'] for entry in data['validators']}
        for record in self.index()['skills']:
            if record['status'] != 'validated':
                continue
            for op in record['ops']:
                self.assertIn(op['id'], ops_module.OPS_IMPL, record['id'])
                self.assertIn(op['id'], registry_ops, record['id'])
            for validator in record['validators']:
                self.assertIn(validator['id'], validators_module.VALIDATORS, record['id'])
                self.assertIn(validator['id'], registry_validators, record['id'])

    def test_validated_cards_reject_invalid_scores(self):
        parallel = load_score('satb-parallel.json')
        kinds = {finding.validator for finding in validators_module.run_validators(parallel)}
        self.assertIn('parallel-perfect', kinds)
        crossing = load_score('satb-crossing.json')
        kinds = {finding.validator for finding in validators_module.run_validators(crossing)}
        self.assertIn('voice-crossing', kinds)


class UpdaterGuardTests(unittest.TestCase):
    def run_update(self, *args):
        return subprocess.run(
            [sys.executable, str(ROOT / 'update_index.py'), *args],
            cwd=ROOT, capture_output=True, text=True, encoding='utf-8')

    def test_typo_guard_refuses_unknown_implemented_id(self):
        before = (ROOT / 'skills' / 'index.json').read_bytes()
        result = self.run_update(
            '--card', 'pitch-intervals', '--add-validator', 'bogus-id',
            '--implementation', 'implemented')
        self.assertEqual(result.returncode, 2, result.stderr)
        self.assertEqual((ROOT / 'skills' / 'index.json').read_bytes(), before)

    def test_implemented_accepted_for_registered_id(self):
        result = self.run_update(
            '--card', 'pitch-intervals', '--add-validator', 'voice-range',
            '--implementation', 'implemented')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('dry-run', result.stdout)

    def test_status_validated_accepted_for_wired_card(self):
        before = (ROOT / 'skills' / 'index.json').read_bytes()
        result = self.run_update(
            '--card', 'satb-chorale-harmonization', '--status', 'validated')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('dry-run', result.stdout)
        self.assertEqual((ROOT / 'skills' / 'index.json').read_bytes(), before)

    def test_status_validated_refused_for_unwired_card(self):
        before = (ROOT / 'skills' / 'index.json').read_bytes()
        result = self.run_update(
            '--card', 'pitch-intervals', '--status', 'validated')
        self.assertEqual(result.returncode, 2, result.stderr)
        self.assertEqual((ROOT / 'skills' / 'index.json').read_bytes(), before)

    def test_status_stable_not_offered(self):
        result = self.run_update(
            '--card', 'pitch-intervals', '--status', 'stable')
        self.assertEqual(result.returncode, 1, result.stderr)


if __name__ == '__main__':
    unittest.main()
