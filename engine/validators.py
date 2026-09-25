from dataclasses import dataclass
from fractions import Fraction

from .score import Score, fraction_str, midi_of


@dataclass(frozen=True)
class Finding:
    validator: str
    severity: str
    part: str | None
    measure: int | None
    message: str

    def to_dict(self) -> dict:
        return {
            'validator': self.validator,
            'severity': self.severity,
            'part': self.part,
            'measure': self.measure,
            'message': self.message,
        }


def sort_key(finding: Finding):
    return (
        finding.validator,
        finding.part or '',
        -1 if finding.measure is None else finding.measure,
        finding.message,
    )


def measure_fill(score: Score) -> list[Finding]:
    findings = []
    measure_length = score.measure_length
    max_measure = max(event.measure for part in score.parts for event in part.events)
    for part in score.parts:
        for measure in range(1, max_measure + 1):
            intervals = sorted(
                (event.onset, event.onset + event.duration)
                for event in part.events
                if event.measure == measure
            )
            if not intervals:
                findings.append(Finding(
                    'measure-fill', 'error', part.id, measure,
                    f"part '{part.id}' measure {measure} has no events "
                    f"(coverage 0 of {fraction_str(measure_length)})"))
                continue
            covered = Fraction(0)
            for start, end in intervals:
                if start > covered:
                    break
                if end > covered:
                    covered = end
            if covered < measure_length:
                findings.append(Finding(
                    'measure-fill', 'error', part.id, measure,
                    f"part '{part.id}' measure {measure} is underfull: "
                    f"covered {fraction_str(covered)} of {fraction_str(measure_length)}"))
    return findings


def voice_range(score: Score) -> list[Finding]:
    findings = []
    for part in score.parts:
        if part.range is None:
            findings.append(Finding(
                'voice-range', 'info', part.id, None,
                f"part '{part.id}' has no declared range; voice-range skipped"))
            continue
        low = midi_of(part.range.low)
        high = midi_of(part.range.high)
        for event in part.events:
            if event.pitch is None:
                continue
            pitch_midi = midi_of(event.pitch)
            if pitch_midi < low:
                findings.append(Finding(
                    'voice-range', 'error', part.id, event.measure,
                    f"measure {event.measure}: pitch {event.pitch} is below "
                    f"the declared low {part.range.low}"))
            elif pitch_midi > high:
                findings.append(Finding(
                    'voice-range', 'error', part.id, event.measure,
                    f"measure {event.measure}: pitch {event.pitch} is above "
                    f"the declared high {part.range.high}"))
    return findings


def note_overlap(score: Score) -> list[Finding]:
    findings = []
    measure_length = score.measure_length
    for part in score.parts:
        running_end = None
        seen = set()
        for event in sorted(part.events, key=lambda item: (item.measure, item.onset)):
            start = (event.measure - 1) * measure_length + event.onset
            end = start + event.duration
            key = (event.measure, event.onset, event.duration)
            if running_end is not None and start < running_end:
                if key in seen:
                    message = (
                        f"measure {event.measure}: duplicate event "
                        f"(same onset and duration) overlaps an earlier event")
                else:
                    earlier_end = running_end - (event.measure - 1) * measure_length
                    message = (
                        f"measure {event.measure}: event at {fraction_str(event.onset)} "
                        f"overlaps an earlier event ending at {fraction_str(earlier_end)}")
                findings.append(Finding('note-overlap', 'error', part.id, event.measure, message))
            if running_end is None or end > running_end:
                running_end = end
            seen.add(key)
    return findings


def run_validators(score: Score) -> list[Finding]:
    findings = []
    for validator_id in sorted(VALIDATORS):
        function, _severity, _autofix = VALIDATORS[validator_id]
        findings.extend(function(score))
    findings.sort(key=sort_key)
    return findings


def _timeline(score: Score):
    measure_length = score.measure_length
    attacks = set()
    segments = []
    for part in score.parts:
        events = sorted(
            part.events, key=lambda item: ((item.measure - 1) * measure_length + item.onset))
        ranges = []
        for event in events:
            start = (event.measure - 1) * measure_length + event.onset
            end = start + event.duration
            midi = None if event.pitch is None else midi_of(event.pitch)
            ranges.append((start, end, midi))
            attacks.add((event.measure, start))
        segments.append(ranges)
    ordered = sorted(attacks, key=lambda item: item[1])
    table = []
    for ranges in segments:
        row = []
        for _, moment in ordered:
            sounding = None
            for start, end, midi in ranges:
                if start <= moment < end:
                    sounding = midi
            row.append(sounding)
        table.append(row)
    return [measure for measure, _moment in ordered], table


def parallel_perfect(score: Score) -> list[Finding]:
    findings = []
    measures, table = _timeline(score)
    parts = score.parts
    for upper_index in range(len(parts)):
        for lower_index in range(upper_index + 1, len(parts)):
            upper_id = parts[upper_index].id
            lower_id = parts[lower_index].id
            for position in range(len(measures) - 1):
                first_upper = table[upper_index][position]
                first_lower = table[lower_index][position]
                second_upper = table[upper_index][position + 1]
                second_lower = table[lower_index][position + 1]
                if None in (first_upper, first_lower, second_upper, second_lower):
                    continue
                first_class = (first_upper - first_lower) % 12
                second_class = (second_upper - second_lower) % 12
                if first_class != second_class or first_class not in (0, 7):
                    continue
                upper_motion = second_upper - first_upper
                lower_motion = second_lower - first_lower
                if upper_motion == 0 or lower_motion == 0:
                    continue
                if (upper_motion > 0) != (lower_motion > 0):
                    continue
                arrival = abs(second_upper - second_lower)
                if first_class == 7:
                    kind = 'fifths'
                elif arrival == 0:
                    kind = 'unisons'
                else:
                    kind = 'octaves'
                findings.append(Finding(
                    'parallel-perfect', 'error', None, measures[position + 1],
                    f'parallel {kind}: {upper_id} and {lower_id}, '
                    f'measures {measures[position]}->{measures[position + 1]}'))
    return findings


def voice_crossing(score: Score) -> list[Finding]:
    findings = []
    measures, table = _timeline(score)
    parts = score.parts
    for upper_index in range(len(parts) - 1):
        upper_id = parts[upper_index].id
        lower_id = parts[upper_index + 1].id
        for position, measure in enumerate(measures):
            upper = table[upper_index][position]
            lower = table[upper_index + 1][position]
            if upper is None or lower is None:
                continue
            if upper < lower:
                findings.append(Finding(
                    'voice-crossing', 'error', None, measure,
                    f'voice crossing: {upper_id} ({upper}) sounds below '
                    f'{lower_id} ({lower}) at measure {measure}'))
    return findings


VALIDATORS = {
    'measure-fill': (measure_fill, 'error', False),
    'note-overlap': (note_overlap, 'error', False),
    'parallel-perfect': (parallel_perfect, 'error', False),
    'voice-crossing': (voice_crossing, 'error', False),
    'voice-range': (voice_range, 'error', False),
}


def run_validators(score: Score) -> list[Finding]:
    findings = []
    for validator_id in sorted(VALIDATORS):
        function, _severity, _autofix = VALIDATORS[validator_id]
        findings.extend(function(score))
    findings.sort(key=sort_key)
    return findings
