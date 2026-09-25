import ast
import hashlib
import json
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TOOL_ROOT = ROOT
# Repo scaffolding that is not part of the tool's tracked source set (see test_source_layout).
NON_TOOL_TOP = {'.git', '.github', 'docs', 'README.md', 'LICENSE', '.gitignore', '.gitattributes', 'AGENTS.md'}
CHECKER = TOOL_ROOT / 'check_shelf.py'
SKILLS = TOOL_ROOT / 'skills'
FIXTURE = TOOL_ROOT / 'tests/fixtures/selection_cases.json'
EXPECTED = {
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
ALLOWED = {'argparse', 'ast', 'hashlib', 'json', 'pathlib', 're', 'sys', 'unicodedata'}
BANNED = {'socket', 'urllib', 'http', 'ftplib', 'ssl', 'smtplib', 'requests', 'httpx', 'openai', 'anthropic', 'asyncio'}
SECTIONS = ['Purpose', 'Use when', 'Do not use when', 'Inputs', 'Outputs', 'Procedure', 'Hard constraints', 'Heuristics', 'Validation status', 'Failure modes', 'Examples', 'References']
CJK = re.compile(r'[\u3040-\u30ff\u4e00-\u9fff]')


def run_checker(root, *extra, checker=CHECKER):
    command = [sys.executable, str(checker), '--root', str(root), *extra]
    return subprocess.run(command, cwd=ROOT, capture_output=True, text=True)


def read_index(root=SKILLS):
    return json.loads((root / 'index.json').read_text(encoding='utf-8'))


def write_index(root, index):
    ordered = dict(index)
    ordered['skills'] = sorted(index['skills'], key=lambda record: record['id'])
    payload = json.dumps(ordered['skills'], ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode('utf-8')
    ordered['catalog_sha256'] = hashlib.sha256(payload).hexdigest()
    ordered['schema_version'] = '1'
    ordered['skills'] = sorted(ordered['skills'], key=lambda record: record['id'])
    (root / 'index.json').write_text(json.dumps(ordered, ensure_ascii=False, sort_keys=True, indent=2) + '\n', encoding='utf-8', newline='\n')


def copied_skills(temp):
    root = Path(temp) / 'skills'
    shutil.copytree(SKILLS, root)
    return root


class ShelfTests(unittest.TestCase):
    def test_index_schema_valid(self):
        index = read_index()
        self.assertEqual(set(index), {'schema_version', 'catalog_sha256', 'skills'})
        self.assertEqual(index['schema_version'], '1')
        self.assertEqual(index['skills'], sorted(index['skills'], key=lambda record: record['id']))
        self.assertEqual(len(index['skills']), 36)
        self.assertRegex(index['catalog_sha256'], r'^[0-9a-f]{64}$')
        for record in index['skills']:
            self.assertEqual(set(record), {'id', 'title', 'summary_ja', 'category', 'mode', 'level', 'idiom', 'ensemble', 'status', 'use_when', 'not_when', 'inputs', 'outputs', 'preconditions', 'effects', 'ops', 'validators', 'theory_refs', 'examples', 'failure_modes', 'requires', 'composes_with', 'body_path', 'body_sha256', 'schema_version'})

    def test_index_idempotent_rewrite(self):
        raw = (SKILLS / 'index.json').read_bytes()
        index = read_index()
        index['skills'] = sorted(index['skills'], key=lambda record: record['id'])
        canonical = (json.dumps(index, ensure_ascii=False, sort_keys=True, indent=2) + '\n').encode('utf-8')
        self.assertEqual(raw, canonical)

    def test_catalog_exact_36(self):
        index = read_index()
        counts = {}
        for record in index['skills']:
            counts[record['category']] = counts.get(record['category'], 0) + 1
        self.assertEqual(counts, EXPECTED)
        self.assertEqual(len({record['id'] for record in index['skills']}), 36)

    def test_bodies_language_and_sections(self):
        index = read_index()
        bodies = sorted((SKILLS / 'index.json').parent.glob('*.md'))
        self.assertEqual(len(bodies), 36)
        for path in bodies:
            raw = path.read_bytes()
            text = raw.decode('utf-8')
            self.assertFalse(raw.startswith(b'\xef\xbb\xbf'))
            self.assertNotIn(b'\r', raw)
            self.assertFalse(CJK.search(text), path)
            for section in SECTIONS:
                self.assertEqual(len(re.findall(rf'^## {re.escape(section)}$', text, re.MULTILINE)), 1, (path, section))
        self.assertEqual({path.stem for path in bodies}, {record['id'] for record in index['skills']})
        for record in index['skills']:
            summary = record['summary_ja']
            self.assertRegex(summary, r'[\u3040-\u30ff\u4e00-\u9fff]')
            self.assertNotRegex(summary, r'[\u0400-\u04ff]')
            self.assertEqual(summary, summary.strip())

    def test_all_source_encoding(self):
        paths = [CHECKER, FIXTURE, Path(__file__), SKILLS / 'index.json', *sorted(SKILLS.glob('*.md'))]
        for path in paths:
            raw = path.read_bytes()
            self.assertFalse(raw.startswith(b'\xef\xbb\xbf'), path)
            self.assertNotIn(b'\r', raw, path)
            raw.decode('utf-8')

    def test_hash_integrity(self):
        index = read_index()
        ordered = sorted(index['skills'], key=lambda record: record['id'])
        payload = json.dumps(ordered, ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode('utf-8')
        self.assertEqual(index['catalog_sha256'], hashlib.sha256(payload).hexdigest())
        for record in index['skills']:
            body = SKILLS / record['body_path']
            self.assertEqual(record['body_sha256'], hashlib.sha256(body.read_bytes()).hexdigest())

    def test_no_implemented_checks(self):
        for record in read_index()['skills']:
            self.assertEqual(record['status'], 'draft')
            self.assertTrue(all(op['implementation'] == 'unimplemented' for op in record['ops']))
            self.assertTrue(all(validator['implementation'] in {'unimplemented', 'advisory'} for validator in record['validators']))
            self.assertNotIn('implemented', [op['implementation'] for op in record['ops']])
            self.assertNotIn('implemented', [validator['implementation'] for validator in record['validators']])

    def test_op_validator_availability(self):
        for record in read_index()['skills']:
            for op in record['ops']:
                self.assertEqual(set(op), {'id', 'implementation'})
                self.assertEqual(op['implementation'], 'unimplemented')
            for validator in record['validators']:
                self.assertEqual(set(validator), {'id', 'severity', 'autofix', 'implementation'})
                self.assertIn(validator['implementation'], {'unimplemented', 'advisory'})
                self.assertIsInstance(validator['autofix'], bool)

    def test_dependency_references_resolve(self):
        ids = {record['id'] for record in read_index()['skills']}
        for record in read_index()['skills']:
            for field in ('requires', 'composes_with'):
                for target in record[field]:
                    self.assertIn(target, ids)
                    self.assertNotEqual(target, record['id'])

    def test_selection_fixture_passes(self):
        result = run_checker(SKILLS, '--selection-fixture', str(FIXTURE))
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_selection_fixture_coverage(self):
        cases = json.loads(FIXTURE.read_text(encoding='utf-8'))
        self.assertGreaterEqual(len(cases), 12)
        self.assertEqual(len({case['id'] for case in cases}), len(cases))
        categories = {case['expected_category'] for case in cases if case['expected_category'] is not None}
        self.assertEqual(categories, set(EXPECTED))
        self.assertTrue(any('exclusion' in case['rationale'].lower() for case in cases))
        self.assertTrue(any(case['expected_mode'] is not None or case['expected_category'] is not None for case in cases))

    def test_ast_import_boundaries(self):
        for path in (CHECKER, Path(__file__)):
            tree = ast.parse(path.read_text(encoding='utf-8'))
            imports = set()
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    imports.update(alias.name.split('.')[0] for alias in node.names)
                elif isinstance(node, ast.ImportFrom):
                    imports.add((node.module or '').split('.')[0])
            self.assertFalse(imports & BANNED, (path, imports & BANNED))
            if path == CHECKER:
                self.assertTrue(imports <= ALLOWED, imports - ALLOWED)
            else:
                self.assertIn('subprocess', imports)

    def test_checker_exit_code_mapping(self):
        result = subprocess.run([sys.executable, str(CHECKER)], cwd=ROOT, capture_output=True, text=True)
        self.assertEqual(result.returncode, 1)
        with tempfile.TemporaryDirectory() as temp:
            root = copied_skills(temp)
            index = read_index(root)
            index['extra'] = True
            write_index(root, index)
            body = root / 'pitch-intervals.md'
            body.write_text(body.read_text(encoding='utf-8') + '\n', encoding='utf-8', newline='\n')
            self.assertEqual(run_checker(root, '--check').returncode, 2)
        with tempfile.TemporaryDirectory() as temp:
            root = copied_skills(temp)
            body = root / 'pitch-intervals.md'
            body.write_text(body.read_text(encoding='utf-8') + '\n', encoding='utf-8', newline='\n')
            self.assertEqual(run_checker(root, '--check').returncode, 3)
        with tempfile.TemporaryDirectory() as temp:
            root = copied_skills(temp)
            index = read_index(root)
            index['skills'][0]['requires'] = ['missing-skill']
            write_index(root, index)
            self.assertEqual(run_checker(root, '--check').returncode, 4)
        with tempfile.TemporaryDirectory() as temp:
            root = copied_skills(temp)
            checker = Path(temp) / 'check_shelf.py'
            shutil.copy2(CHECKER, checker)
            checker.write_text(checker.read_text(encoding='utf-8') + '\nimport socket\n', encoding='utf-8', newline='\n')
            self.assertEqual(run_checker(root, '--check', checker=checker).returncode, 5)
        with tempfile.TemporaryDirectory() as temp:
            self.assertEqual(run_checker(SKILLS, '--selection-fixture', str(Path(temp) / 'missing.json')).returncode, 2)
            malformed = Path(temp) / 'malformed.json'
            malformed.write_text('{', encoding='utf-8', newline='\n')
            self.assertEqual(run_checker(SKILLS, '--selection-fixture', str(malformed)).returncode, 2)
        self.assertEqual(run_checker(SKILLS, '--check').returncode, 0)

    def test_source_layout(self):
        expected = {CHECKER.relative_to(TOOL_ROOT), (SKILLS / 'index.json').relative_to(TOOL_ROOT), FIXTURE.relative_to(TOOL_ROOT), Path(__file__).relative_to(TOOL_ROOT)}
        expected.update((SKILLS / f'{record["id"]}.md').relative_to(TOOL_ROOT) for record in read_index()['skills'])
        actual = {path.relative_to(TOOL_ROOT) for path in TOOL_ROOT.rglob('*') if path.is_file() and '__pycache__' not in path.parts and path.suffix != '.pyc' and path.relative_to(TOOL_ROOT).parts[0] not in NON_TOOL_TOP}
        self.assertEqual(actual, expected)


if __name__ == '__main__':
    unittest.main()
