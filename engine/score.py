import json
import re
from dataclasses import dataclass
from fractions import Fraction
from pathlib import Path

import check_shelf

PITCH_RE = re.compile(r'^[A-G][#b]?-?[0-9]{1,2}$')
TONIC_RE = re.compile(r'^[A-G][#b]?$')
FRACTION_RE = re.compile(r'^-?\d+/\d+$')
SEMITONES = {'C': 0, 'D': 2, 'E': 4, 'F': 5, 'G': 7, 'A': 9, 'B': 11}
MODES = {'major', 'minor'}
DENOMINATORS = {1, 2, 4, 8, 16, 32}


class ScoreError(Exception):
    def __init__(self, path, message):
        self.path = path
        self.message = message
        super().__init__(f'{path}: {message}')


@dataclass(frozen=True)
class Range:
    low: str
    high: str


@dataclass(frozen=True)
class Event:
    measure: int
    onset: Fraction
    duration: Fraction
    pitch: str | None


@dataclass(frozen=True)
class Part:
    id: str
    name: str
    range: Range | None
    events: tuple[Event, ...]


@dataclass(frozen=True)
class Score:
    title: str
    meter_numerator: int
    meter_denominator: int
    tonic: str
    mode: str
    parts: tuple[Part, ...]

    @property
    def measure_length(self) -> Fraction:
        return Fraction(self.meter_numerator, self.meter_denominator)


def _object(value, path):
    if not isinstance(value, dict):
        raise ScoreError(path, 'must be an object')
    return value


def _exact_keys(value, keys, path):
    if set(value) != set(keys):
        raise ScoreError(path, f'must have exactly the keys: {", ".join(sorted(keys))}')


def _integer(value, path):
    if isinstance(value, bool) or not isinstance(value, int):
        raise ScoreError(path, 'must be an integer')
    return value


def _non_empty_string(value, path):
    if not isinstance(value, str) or not value.strip():
        raise ScoreError(path, 'must be a non-empty string')
    return value


def _fraction(value, path):
    if isinstance(value, bool):
        raise ScoreError(path, 'bool is not a valid fraction')
    if isinstance(value, int):
        return Fraction(value)
    if isinstance(value, str) and FRACTION_RE.fullmatch(value):
        numerator, denominator = (int(part) for part in value.split('/'))
        if denominator == 0:
            raise ScoreError(path, 'fraction denominator must not be zero')
        return Fraction(numerator, denominator)
    raise ScoreError(path, "must be an integer or an 'n/d' string")


def midi_of(pitch) -> int:
    if not isinstance(pitch, str) or not PITCH_RE.fullmatch(pitch):
        raise ScoreError('pitch', f'invalid pitch: {pitch!r}')
    body = pitch[1:]
    accidental = 0
    if body[:1] in {'#', 'b'}:
        accidental = 1 if body[0] == '#' else -1
        body = body[1:]
    octave = int(body)
    return (octave + 1) * 12 + SEMITONES[pitch[0]] + accidental


def _pitch(value, path, allow_null=True):
    if value is None:
        if allow_null:
            return None
        raise ScoreError(path, 'must be a pitch, not null')
    if not isinstance(value, str) or not PITCH_RE.fullmatch(value):
        raise ScoreError(path, 'must be null or match ^[A-G][#b]?-?[0-9]{1,2}$')
    midi = midi_of(value)
    if not 0 <= midi <= 127:
        raise ScoreError(path, f'midi value out of range 0..127: {value}')
    return value


def _parse_range(value, path):
    value = _object(value, path)
    _exact_keys(value, ('low', 'high'), path)
    low = _pitch(value['low'], f'{path}.low', allow_null=False)
    high = _pitch(value['high'], f'{path}.high', allow_null=False)
    if midi_of(low) > midi_of(high):
        raise ScoreError(path, 'low pitch must not exceed high pitch')
    return Range(low, high)


def _parse_event(value, path, measure_length):
    event = _object(value, path)
    _exact_keys(event, ('measure', 'onset', 'duration', 'pitch'), path)
    measure = _integer(event['measure'], f'{path}.measure')
    if measure < 1:
        raise ScoreError(f'{path}.measure', 'must be >= 1')
    onset = _fraction(event['onset'], f'{path}.onset')
    if onset < 0:
        raise ScoreError(f'{path}.onset', 'must not be negative')
    duration = _fraction(event['duration'], f'{path}.duration')
    if duration <= 0:
        raise ScoreError(f'{path}.duration', 'must be greater than zero')
    if onset + duration > measure_length:
        raise ScoreError(path, f'onset + duration exceeds measure length {fraction_str(measure_length)}')
    pitch = _pitch(event['pitch'], f'{path}.pitch')
    return Event(measure, onset, duration, pitch)


def _parse_part(value, path, measure_length):
    part = _object(value, path)
    if not {'id', 'name', 'events'} <= set(part) or not set(part) <= {'id', 'name', 'range', 'events'}:
        raise ScoreError(path, 'must have keys id, name, events and optional key range')
    part_id = part['id']
    if not isinstance(part_id, str) or not check_shelf.ID_RE.fullmatch(part_id):
        raise ScoreError(f'{path}.id', 'must be kebab-case')
    name = _non_empty_string(part['name'], f'{path}.name')
    range_value = _parse_range(part['range'], f'{path}.range') if 'range' in part else None
    events_value = part['events']
    if not isinstance(events_value, list) or not events_value:
        raise ScoreError(f'{path}.events', 'must be a non-empty array')
    events = tuple(
        _parse_event(event, f'{path}.events[{position}]', measure_length)
        for position, event in enumerate(events_value)
    )
    return Part(part_id, name, range_value, events)


def parse_score(data, path='$') -> Score:
    root = _object(data, path)
    _exact_keys(root, ('schema_version', 'title', 'meter', 'key', 'parts'), path)
    if root['schema_version'] != '1':
        raise ScoreError(f'{path}.schema_version', "must be '1'")
    title = _non_empty_string(root['title'], f'{path}.title')
    meter_path = f'{path}.meter'
    meter = _object(root['meter'], meter_path)
    _exact_keys(meter, ('numerator', 'denominator'), meter_path)
    numerator = _integer(meter['numerator'], f'{meter_path}.numerator')
    denominator = _integer(meter['denominator'], f'{meter_path}.denominator')
    if numerator < 1:
        raise ScoreError(f'{meter_path}.numerator', 'must be >= 1')
    if denominator not in DENOMINATORS:
        raise ScoreError(f'{meter_path}.denominator', 'must be one of 1, 2, 4, 8, 16, 32')
    measure_length = Fraction(numerator, denominator)
    key_path = f'{path}.key'
    key = _object(root['key'], key_path)
    _exact_keys(key, ('tonic', 'mode'), key_path)
    tonic = key['tonic']
    if not isinstance(tonic, str) or not TONIC_RE.fullmatch(tonic):
        raise ScoreError(f'{key_path}.tonic', 'must match ^[A-G][#b]?$')
    mode = key['mode']
    if mode not in MODES:
        raise ScoreError(f'{key_path}.mode', 'must be one of: major, minor')
    parts_value = root['parts']
    if not isinstance(parts_value, list) or not parts_value:
        raise ScoreError(f'{path}.parts', 'must be a non-empty array')
    parts = []
    seen = set()
    for position, part_value in enumerate(parts_value):
        part_path = f'{path}.parts[{position}]'
        part = _parse_part(part_value, part_path, measure_length)
        if part.id in seen:
            raise ScoreError(f'{part_path}.id', f'duplicate part id: {part.id}')
        seen.add(part.id)
        parts.append(part)
    return Score(title, numerator, denominator, tonic, mode, tuple(parts))


def fraction_str(value: Fraction):
    if value.denominator == 1:
        return value.numerator
    return f'{value.numerator}/{value.denominator}'


def score_to_dict(score: Score) -> dict:
    parts = []
    for part in score.parts:
        entry = {
            'id': part.id,
            'name': part.name,
            'events': [
                {
                    'measure': event.measure,
                    'onset': fraction_str(event.onset),
                    'duration': fraction_str(event.duration),
                    'pitch': event.pitch,
                }
                for event in part.events
            ],
        }
        if part.range is not None:
            entry['range'] = {'low': part.range.low, 'high': part.range.high}
        parts.append(entry)
    return {
        'schema_version': '1',
        'title': score.title,
        'meter': {'numerator': score.meter_numerator, 'denominator': score.meter_denominator},
        'key': {'tonic': score.tonic, 'mode': score.mode},
        'parts': parts,
    }


def canonical_score_bytes(score: Score) -> bytes:
    text = json.dumps(score_to_dict(score), ensure_ascii=False, sort_keys=True, indent=2)
    return (text + '\n').encode('utf-8')


def load_score_file(path) -> Score:
    issues = []
    data = check_shelf.read_json(Path(path), issues)
    if data is None:
        reason = '; '.join(issue.message for issue in issues) or 'cannot read score file'
        raise ScoreError(str(path), reason)
    return parse_score(data)
