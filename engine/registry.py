from pathlib import Path

import check_shelf

from .ops import OPS_IMPL
from .validators import VALIDATORS

DEFAULT_REGISTRY = Path(__file__).resolve().parent / 'registry.json'


class RegistryError(Exception):
    pass


def _entries(values, keys, kind):
    if not isinstance(values, list):
        raise RegistryError(f'registry {kind} entries must be an array')
    ids = []
    previous = None
    for position, entry in enumerate(values):
        if not isinstance(entry, dict) or set(entry) != set(keys):
            raise RegistryError(
                f'{kind}[{position}] must have exactly the keys: {", ".join(sorted(keys))}')
        entry_id = entry['id']
        if not isinstance(entry_id, str) or not check_shelf.ID_RE.fullmatch(entry_id):
            raise RegistryError(f'{kind}[{position}].id must be kebab-case')
        if previous is not None and entry_id <= previous:
            raise RegistryError(f'{kind} entries must be sorted by id and unique')
        previous = entry_id
        if entry['implementation'] != 'implemented':
            raise RegistryError(f'{kind} {entry_id} must be implemented')
        summary = entry['summary']
        if not isinstance(summary, str) or not summary.strip():
            raise RegistryError(f'{kind} {entry_id}: summary must be a non-empty string')
        ids.append(entry_id)
    return ids


def validate_registry(data) -> dict:
    if not isinstance(data, dict):
        raise RegistryError('registry root must be an object')
    if set(data) != {'schema_version', 'ops', 'validators'}:
        raise RegistryError(
            'registry keys must be exactly schema_version, ops, validators')
    if data['schema_version'] != '1':
        raise RegistryError("registry schema_version must be '1'")
    op_ids = _entries(
        data['ops'], ('id', 'implementation', 'summary'), 'op')
    validator_ids = _entries(
        data['validators'],
        ('id', 'severity', 'autofix', 'implementation', 'summary'),
        'validator')
    for entry in data['validators']:
        if entry['severity'] not in check_shelf.SEVERITIES:
            raise RegistryError(
                f"validator {entry['id']}: invalid severity {entry['severity']!r}")
        if not isinstance(entry['autofix'], bool):
            raise RegistryError(f"validator {entry['id']}: autofix must be a boolean")
    if set(op_ids) != set(OPS_IMPL):
        raise RegistryError(
            'registry ops do not match code: '
            f'missing in code {sorted(set(op_ids) - set(OPS_IMPL))}, '
            f'missing in registry {sorted(set(OPS_IMPL) - set(op_ids))}')
    if set(validator_ids) != set(VALIDATORS):
        raise RegistryError(
            'registry validators do not match code: '
            f'missing in code {sorted(set(validator_ids) - set(VALIDATORS))}, '
            f'missing in registry {sorted(set(VALIDATORS) - set(validator_ids))}')
    return data


def load(path=None) -> dict:
    registry_path = Path(path) if path is not None else DEFAULT_REGISTRY
    issues = []
    data = check_shelf.read_json(registry_path, issues)
    if data is None:
        raise RegistryError('; '.join(issue.message for issue in issues))
    return validate_registry(data)


def op(op_id):
    data = load()
    if op_id not in {entry['id'] for entry in data['ops']}:
        raise RegistryError(f'unknown op: {op_id}')
    return OPS_IMPL[op_id]
