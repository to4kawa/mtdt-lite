import sys
from pathlib import Path

import check_shelf
from engine import registry as registry_module
from engine.registry import RegistryError


class Refused(Exception):
    pass


def semantic_error(message):
    print(f'2: {message}', file=sys.stderr)
    return 2


def require_registered(kind, item_id):
    try:
        data = registry_module.load()
    except RegistryError as exc:
        raise Refused(f'cannot verify {kind} {item_id}: {exc}')
    entries = data['ops'] if kind == 'op' else data['validators']
    if item_id not in {entry['id'] for entry in entries}:
        raise Refused(f'unknown {kind} id: {item_id} (not in the engine registry)')


def apply_action(index, args, root):
    if args.rehash:
        for record in index['skills']:
            body = root / record['body_path']
            if not body.exists():
                raise Refused(f'missing body: {body}')
            record['body_sha256'] = check_shelf.body_hash(body)
        return 'rehash body_sha256 for all cards'
    card = None
    for record in index['skills']:
        if record['id'] == args.card:
            card = record
            break
    if card is None:
        raise Refused(f'unknown card id: {args.card}')
    if args.status is not None:
        card['status'] = args.status
        return f"set status {args.status} for {args.card}"
    if args.add_op is not None:
        if any(op['id'] == args.add_op for op in card['ops']):
            raise Refused(f'card {args.card} already declares op {args.add_op}')
        implementation = args.implementation or 'unimplemented'
        if implementation == 'implemented':
            require_registered('op', args.add_op)
        card['ops'].append({'id': args.add_op, 'implementation': implementation})
        return f'add op {args.add_op} ({implementation}) to {args.card}'
    if args.remove_op is not None:
        kept = [op for op in card['ops'] if op['id'] != args.remove_op]
        if len(kept) == len(card['ops']):
            raise Refused(f'card {args.card} does not declare op {args.remove_op}')
        card['ops'] = kept
        return f'remove op {args.remove_op} from {args.card}'
    if args.add_validator is not None:
        if any(validator['id'] == args.add_validator for validator in card['validators']):
            raise Refused(f'card {args.card} already declares validator {args.add_validator}')
        implementation = args.implementation or 'unimplemented'
        if implementation == 'implemented':
            require_registered('validator', args.add_validator)
        card['validators'].append({
            'id': args.add_validator,
            'severity': args.severity,
            'autofix': args.autofix == 'true',
            'implementation': implementation,
        })
        return f'add validator {args.add_validator} ({implementation}) to {args.card}'
    kept = [validator for validator in card['validators'] if validator['id'] != args.remove_validator]
    if len(kept) == len(card['validators']):
        raise Refused(f'card {args.card} does not declare validator {args.remove_validator}')
    card['validators'] = kept
    return f'remove validator {args.remove_validator} from {args.card}'


def run(args):
    actions = [
        name for name in ('add_op', 'remove_op', 'add_validator', 'remove_validator', 'status')
        if getattr(args, name) is not None
    ]
    if len(actions) > 1:
        return semantic_error(
            'choose at most one of --add-op, --remove-op, --add-validator, --remove-validator, --status')
    if args.rehash and actions:
        return semantic_error('--rehash cannot be combined with card actions')
    if actions and not args.card:
        return semantic_error('--card is required with an op/validator action')
    if args.card is not None and not actions:
        return semantic_error('--card requires an op/validator action')
    if not actions and not args.rehash:
        parser_error = 'one action is required: a card action or --rehash'
        print(f'1: {parser_error}', file=sys.stderr)
        return 1
    root = Path(args.root)
    index_path = root / 'index.json'
    issues = []
    index = check_shelf.read_json(index_path, issues)
    if index is None:
        check_shelf.print_issues(issues)
        return check_shelf.first_code(issues)
    check_shelf.validate_index(index, issues)
    if issues:
        check_shelf.print_issues(issues)
        return check_shelf.first_code(issues)
    try:
        summary = apply_action(index, args, root)
    except Refused as exc:
        return semantic_error(str(exc))
    index['catalog_sha256'] = check_shelf.catalog_hash(index['skills'])
    issues = []
    check_shelf.validate_index(index, issues)
    check_shelf.validate_bodies(root, index, issues)
    if issues:
        check_shelf.print_issues(issues)
        return check_shelf.first_code(issues)
    payload = check_shelf.canonical_index(index)
    if not args.apply:
        print(f'ok (dry-run): {summary}; re-run with --apply to write')
        return 0
    temp_path = index_path.with_name('index.json.tmp')
    temp_path.write_bytes(payload)
    temp_path.replace(index_path)
    post_issues, _post_index = check_shelf.check_shelf(root)
    if post_issues:
        check_shelf.print_issues(post_issues)
        return check_shelf.first_code(post_issues)
    print(f'written: {index_path} ({summary})')
    return 0


def main(argv=None):
    parser = check_shelf.Parser(
        prog='update_index.py',
        description='sanctioned writer for skills/index.json (dry-run unless --apply)')
    parser.add_argument('--root', default='skills')
    parser.add_argument('--card')
    parser.add_argument('--add-op')
    parser.add_argument('--remove-op')
    parser.add_argument('--add-validator')
    parser.add_argument('--remove-validator')
    parser.add_argument('--status', choices=['draft', 'validated'])
    parser.add_argument('--implementation')
    parser.add_argument('--severity', default='error', choices=sorted(check_shelf.SEVERITIES))
    parser.add_argument('--autofix', default='false', choices=['true', 'false'])
    parser.add_argument('--rehash', action='store_true')
    parser.add_argument('--apply', action='store_true')
    try:
        args = parser.parse_args(argv)
    except check_shelf.UsageError as exc:
        print(f'1: {exc}', file=sys.stderr)
        return 1
    try:
        return run(args)
    except check_shelf.UsageError as exc:
        print(f'1: {exc}', file=sys.stderr)
        return 1
    except Exception as exc:
        print(f'1: unexpected error: {exc}', file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
