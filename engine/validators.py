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


VALIDATORS = {
    'measure-fill': (measure_fill, 'error', False),
    'note-overlap': (note_overlap, 'error', False),
    'voice-range': (voice_range, 'error', False),
}


def run_validators(score: Score) -> list[Finding]:
    findings = []
    for validator_id in sorted(VALIDATORS):
        function, _severity, _autofix = VALIDATORS[validator_id]
        findings.extend(function(score))
    findings.sort(key=sort_key)
    return findings
