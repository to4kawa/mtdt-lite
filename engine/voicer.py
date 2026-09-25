import json
from dataclasses import dataclass
from pathlib import Path

import check_shelf

from .score import (
    Event,
    Part,
    Score,
    ScoreError,
    TONIC_RE,
    canonical_score_bytes,
    load_score_file,
    midi_of,
    parse_score,
    score_to_dict,
)
from .validators import run_validators

CHORD_DEGREES = {
    'I': 0, 'ii': 1, 'iii': 2, 'IV': 3, 'V': 4, 'vi': 5, 'vii°': 6, 'viio': 6,
}
MAJOR_SEMIS = (0, 2, 4, 5, 7, 9, 11)
PITCH_NAMES = ('C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B')
SEARCH_BUDGET = 200000
OUTER_VOICES = ('soprano', 'bass')
INNER_VOICES = ('alto', 'tenor')


class PlanError(ScoreError):
    def __init__(self, message):
        super().__init__('plan', message)


class VoicerError(Exception):
    pass


@dataclass(frozen=True)
class Plan:
    tonic: str
    slots: tuple


def _plan_object(value, path):
    if not isinstance(value, dict):
        raise PlanError(f'{path}: must be an object')
    return value


def parse_plan(data, path='$') -> Plan:
    root = _plan_object(data, path)
    if set(root) != {'schema_version', 'key', 'slots'}:
        raise PlanError(f'{path}: must have exactly the keys: key, schema_version, slots')
    if root['schema_version'] != '1':
        raise PlanError(f"{path}.schema_version: must be '1'")
    key = _plan_object(root['key'], f'{path}.key')
    if set(key) != {'tonic', 'mode'}:
        raise PlanError(f'{path}.key: must have exactly the keys: mode, tonic')
    tonic = key['tonic']
    if not isinstance(tonic, str) or not TONIC_RE.fullmatch(tonic):
        raise PlanError(f'{path}.key.tonic: must match ^[A-G][#b]?$')
    if key['mode'] != 'major':
        raise PlanError(f"{path}.key.mode: must be 'major' in P3 (minor keys not supported in P3)")
    slots_value = root['slots']
    if not isinstance(slots_value, list) or not slots_value:
        raise PlanError(f'{path}.slots: must be a non-empty array')
    slots = []
    seen = set()
    for position, slot in enumerate(slots_value):
        slot_path = f'{path}.slots[{position}]'
        slot = _plan_object(slot, slot_path)
        if set(slot) != {'measure', 'chord'}:
            raise PlanError(f'{slot_path}: must have exactly the keys: chord, measure')
        measure = slot['measure']
        if isinstance(measure, bool) or not isinstance(measure, int) or measure < 1:
            raise PlanError(f'{slot_path}.measure: must be an integer >= 1')
        chord = slot['chord']
        if chord not in CHORD_DEGREES:
            raise PlanError(
                f'{slot_path}.chord: unknown chord {chord!r} '
                f'(P3 chords: {", ".join(sorted(CHORD_DEGREES))})')
        if measure in seen:
            raise PlanError(f'{slot_path}.measure: duplicate slot measure {measure}')
        seen.add(measure)
        slots.append((measure, chord))
    return Plan(tonic, tuple(sorted(slots)))


def load_plan_file(path) -> Plan:
    issues = []
    data = check_shelf.read_json(Path(path), issues)
    if data is None:
        reason = '; '.join(issue.message for issue in issues) or 'cannot read plan file'
        raise PlanError(f'{path}: {reason}')
    return parse_plan(data, path=str(path))


def tonic_pitch_class(tonic: str) -> int:
    return midi_of(f'{tonic}4') % 12


def chord_pitch_classes(plan: Plan, chord: str) -> set:
    tonic_class = tonic_pitch_class(plan.tonic)
    degree = CHORD_DEGREES[chord]
    classes = set()
    for step in (0, 2, 4):
        index = degree + step
        classes.add((tonic_class + MAJOR_SEMIS[index % 7] + (12 if index >= 7 else 0)) % 12)
    return classes


def midi_to_pitch(midi: int) -> str:
    return f'{PITCH_NAMES[midi % 12]}{midi // 12 - 1}'


def fill_voices(score: Score, plan: Plan) -> Score:
    by_id = {part.id: part for part in score.parts}
    if [part.id for part in score.parts] != ['soprano', 'alto', 'tenor', 'bass']:
        raise VoicerError(
            'voice-fill needs parts [soprano, alto, tenor, bass], found '
            f'{[part.id for part in score.parts]}')
    for part in score.parts:
        if part.range is None:
            raise VoicerError(f"part '{part.id}' needs a declared range for voice-fill")
    measure_length = score.measure_length
    outer = {}
    for voice in OUTER_VOICES:
        events = [event for event in by_id[voice].events
                  if event.measure in {measure for measure, _chord in plan.slots}]
        if len(events) != len(plan.slots):
            raise VoicerError(
                f"part '{voice}' must hold exactly one event per plan measure")
        for event in events:
            if event.onset != 0 or event.duration != measure_length or event.pitch is None:
                raise VoicerError(
                    f"part '{voice}' measure {event.measure} must be a full-measure note")
            outer[(voice, event.measure)] = midi_of(event.pitch)
    for voice in INNER_VOICES:
        events = [event for event in by_id[voice].events
                  if event.measure in {measure for measure, _chord in plan.slots}]
        if len(events) != len(plan.slots):
            raise VoicerError(
                f"part '{voice}' must hold exactly one rest per plan measure")
        for event in events:
            if event.onset != 0 or event.duration != measure_length or event.pitch is not None:
                raise VoicerError(
                    f"part '{voice}' measure {event.measure} must be an unfilled "
                    'full-measure rest (pitch null)')
    leading_class = (tonic_pitch_class(plan.tonic) + 11) % 12
    ranges = {part.id: (midi_of(part.range.low), midi_of(part.range.high))
              for part in score.parts}
    slot_pcs = {measure: chord_pitch_classes(plan, chord) for measure, chord in plan.slots}
    for voice in OUTER_VOICES:
        for measure, _chord in plan.slots:
            pitch_class = outer[(voice, measure)] % 12
            if pitch_class not in slot_pcs[measure]:
                raise VoicerError(
                    f'measure {measure}: {voice} pitch class {pitch_class} is not a '
                    f'{dict(plan.slots)[measure]} chord tone (revise the plan)')
    ordered_slots = sorted(plan.slots)

    def candidates(voice, classes, previous):
        low, high = ranges[voice]
        options = [midi for midi in range(low, high + 1) if midi % 12 in classes]
        if previous is None:
            return sorted(options)
        return sorted(options, key=lambda midi: (abs(midi - previous), midi))

    state = {'placements': 0}
    solution = {}

    def parallels_ok(placed, previous):
        if previous is None:
            return True
        ids = ('soprano', 'alto', 'tenor', 'bass')
        for first in range(len(ids)):
            for second in range(first + 1, len(ids)):
                first_class = (placed[ids[first]] - placed[ids[second]]) % 12
                second_class = (previous[ids[first]] - previous[ids[second]]) % 12
                if first_class != second_class or first_class not in (0, 7):
                    continue
                first_motion = placed[ids[first]] - previous[ids[first]]
                second_motion = placed[ids[second]] - previous[ids[second]]
                if first_motion == 0 or second_motion == 0:
                    continue
                if (first_motion > 0) == (second_motion > 0):
                    return False
        return True

    def search(slot_index, previous):
        if slot_index >= len(ordered_slots):
            return True
        measure, _chord = ordered_slots[slot_index]
        classes = slot_pcs[measure]
        soprano = outer[('soprano', measure)]
        bass = outer[('bass', measure)]
        previous_alto = solution.get(slot_index - 1, {}).get('alto')
        previous_tenor = solution.get(slot_index - 1, {}).get('tenor')
        for alto in candidates('alto', classes, previous_alto):
            if alto > soprano:
                continue
            for tenor in candidates('tenor', classes, previous_tenor):
                if tenor > alto or tenor < bass:
                    continue
                state['placements'] += 1
                if state['placements'] > SEARCH_BUDGET:
                    raise VoicerError('search budget exhausted (revise the plan)')
                placed = {'soprano': soprano, 'alto': alto, 'tenor': tenor, 'bass': bass}
                if not parallels_ok(placed, previous):
                    continue
                if {pitch % 12 for pitch in placed.values()} != classes:
                    continue
                if sum(1 for pitch in placed.values() if pitch % 12 == leading_class) > 1:
                    continue
                solution[slot_index] = {'alto': alto, 'tenor': tenor}
                if search(slot_index + 1, placed):
                    return True
                del solution[slot_index]
        return False

    if not search(0, None):
        raise VoicerError('no voicing satisfies all rules for the given plan (revise the plan)')
    filled = []
    for part in score.parts:
        if part.id not in INNER_VOICES:
            filled.append(part)
            continue
        events = tuple(
            Event(measure, 0, measure_length, midi_to_pitch(solution[position][part.id]))
            for position, (measure, _chord) in enumerate(ordered_slots))
        filled.append(Part(part.id, part.name, part.range, events))
    rebuilt = Score(score.title, score.meter_numerator, score.meter_denominator,
                    score.tonic, score.mode, tuple(filled))
    return parse_score(score_to_dict(rebuilt))


def op_voice_fill(score_path, plan_path=None):
    if plan_path is None:
        raise ScoreError(str(score_path), 'voice-fill requires a plan file (--plan)')
    score = load_score_file(score_path)
    plan = load_plan_file(plan_path)
    filled = fill_voices(score, plan)
    return {
        'op': 'voice-fill',
        'score': score_to_dict(filled),
        'findings': [finding.to_dict() for finding in run_validators(filled)],
    }
