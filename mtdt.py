import json
import sys
from pathlib import Path

import check_shelf
from engine import ops as ops_module
from engine import registry as registry_module
from engine.registry import RegistryError
from engine.score import ScoreError

SKILLS_ROOT = Path(__file__).resolve().parent / 'skills'


def emit(value):
    if isinstance(value, str):
        sys.stdout.write(value)
    else:
        print(json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2))


def command_select(args):
    issues, index = check_shelf.check_shelf(SKILLS_ROOT)
    if issues:
        check_shelf.print_issues(issues)
        return check_shelf.first_code(issues)
    records = check_shelf.select_skills(index, args.task, args.mode, args.category)
    if not records:
        return 0
    if args.format == 'json':
        emit([
            {key: record[key] for key in ('id', 'title', 'category', 'mode', 'level')}
            for record in records
        ])
        return 0
    for record in records:
        print(f"{record['id']}\t{record['category']}/{record['mode']}\t{record['title']}")
    return 0


def command_validate(args):
    try:
        findings = ops_module.op_score_validate(args.score)
    except ScoreError as exc:
        print(f'2: {exc}', file=sys.stderr)
        return 2
    emit(findings)
    if any(finding['severity'] == 'error' for finding in findings):
        return 3
    return 0


def command_normalize(args):
    try:
        text = ops_module.op_score_normalize(args.score)
    except ScoreError as exc:
        print(f'2: {exc}', file=sys.stderr)
        return 2
    sys.stdout.write(text)
    return 0


def command_ops(args):
    try:
        operation = registry_module.op(args.op_id)
    except RegistryError as exc:
        print(f'2: {exc}', file=sys.stderr)
        return 2
    try:
        result = operation(args.score)
    except ScoreError as exc:
        print(f'2: {exc}', file=sys.stderr)
        return 2
    emit(result)
    if isinstance(result, list) and any(finding['severity'] == 'error' for finding in result):
        return 3
    return 0


def command_validators(args):
    try:
        data = registry_module.load()
    except RegistryError as exc:
        print(f'2: {exc}', file=sys.stderr)
        return 2
    emit(data['validators'])
    return 0


HANDLERS = {
    'select': command_select,
    'validate': command_validate,
    'normalize': command_normalize,
    'ops': command_ops,
    'validators': command_validators,
}


def main(argv=None):
    parser = check_shelf.Parser(prog='mtdt.py', description='mtdt-lite deterministic CLI')
    subparsers = parser.add_subparsers(dest='command', required=True)
    select_parser = subparsers.add_parser('select', help='select skill cards for a task')
    select_parser.add_argument('task')
    select_parser.add_argument('--mode', choices=sorted(check_shelf.MODES))
    select_parser.add_argument('--category', choices=sorted(check_shelf.CATEGORIES))
    select_parser.add_argument('--format', choices=['text', 'json'], default='text')
    validate_parser = subparsers.add_parser('validate', help='run the mechanical validators')
    validate_parser.add_argument('score')
    normalize_parser = subparsers.add_parser('normalize', help='print the canonical score serialization')
    normalize_parser.add_argument('score')
    ops_parser = subparsers.add_parser('ops', help='run a named registry operation')
    ops_parser.add_argument('op_id')
    ops_parser.add_argument('score')
    subparsers.add_parser('validators', help='list registered validators')
    try:
        args = parser.parse_args(argv)
    except check_shelf.UsageError as exc:
        print(f'1: {exc}', file=sys.stderr)
        return 1
    try:
        return HANDLERS[args.command](args)
    except check_shelf.UsageError as exc:
        print(f'1: {exc}', file=sys.stderr)
        return 1
    except Exception as exc:
        print(f'1: unexpected error: {exc}', file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
