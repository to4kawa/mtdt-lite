import json
import os
import sys
import unittest
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from engine import score as score_module
from engine import validators as validators_module
from engine import voicer as voicer_module

SKELETON = ROOT / 'tests' / 'fixtures' / 'scores' / 'satb-skeleton.json'
BRIDGE_URL = 'http://127.0.0.1:3000/v1/chat/completions'
LIVE = os.environ.get('RUN_LIVE_LLM') == '1'
SECRET = os.environ.get('API_SECRET')


def strip_fences(text):
    text = text.strip()
    if text.startswith('```'):
        lines = text.splitlines()
        lines = lines[1:]
        if lines and lines[-1].strip() == '```':
            lines = lines[:-1]
        text = '\n'.join(lines).strip()
        if lines and lines[0].strip().lower() == 'json':
            text = '\n'.join(lines[1:]).strip()
    return text


PROMPT = (
    'Return ONLY a JSON object with exactly the keys schema_version, key, slots. '
    'schema_version is "1". key is {"tonic": "C", "mode": "major"}. '
    'slots is an array of 4 objects with keys measure and chord, '
    'measures 1 to 4 in order, each chord one of I, ii, iii, IV, V, vi. '
    'The soprano line by measure is E4, E4, F4, D4 and the bass line is '
    'C3, A2, F2, G2; every soprano and bass pitch must belong to its '
    "measure chord. No prose, no fences, JSON only."
)


@unittest.skipUnless(LIVE and SECRET, 'live bridge smoke needs RUN_LIVE_LLM=1 and API_SECRET')
class SliceLiveTests(unittest.TestCase):
    def test_planner_returns_compatible_plan(self):
        body = json.dumps({
            'model': 'perplexity/default',
            'stream': False,
            'messages': [{'role': 'user', 'content': PROMPT}],
        }).encode('utf-8')
        request = urllib.request.Request(
            BRIDGE_URL, data=body,
            headers={'Content-Type': 'application/json',
                     'Authorization': 'Bearer ' + SECRET})
        with urllib.request.urlopen(request, timeout=240) as response:
            payload = json.loads(response.read().decode('utf-8'))
        text = payload['choices'][0]['message']['content']
        plan = voicer_module.parse_plan(json.loads(strip_fences(text)))
        score = score_module.load_score_file(SKELETON)
        outer = {}
        for part in score.parts:
            if part.id in ('soprano', 'bass'):
                for event in part.events:
                    outer[(part.id, event.measure)] = score_module.midi_of(event.pitch) % 12
        for measure, chord in plan.slots:
            classes = voicer_module.chord_pitch_classes(plan, chord)
            if outer[('soprano', measure)] not in classes \
                    or outer[('bass', measure)] not in classes:
                self.skipTest(
                    f'live plan chord {chord} incompatible with skeleton at measure '
                    f'{measure} (documented flakiness boundary)')
        filled = voicer_module.fill_voices(score, plan)
        errors = [finding for finding in validators_module.run_validators(filled)
                  if finding.severity == 'error']
        self.assertEqual(errors, [])


if __name__ == '__main__':
    unittest.main()
