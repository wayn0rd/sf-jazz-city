import type { DisplayEvent } from '../types/event';

/**
 * Matches a 12-hour clock time such as "8:00 PM".
 *
 * The `\s` classes are load-bearing. The real scraped data contains U+202F
 * NARROW NO-BREAK SPACE between the minutes and the meridiem (154 of 726
 * events at time of writing). JS `\s` matches U+202F, U+00A0 and U+0020, so
 * "8:00\u202fPM", "8:00\u00a0PM", "8:00 PM" and "8:00PM" all yield 1200.
 *
 * No `g` flag: the regex is module-level, and a sticky lastIndex would make
 * `exec` stateful.
 */
const TIME_PATTERN = /^\s*(\d{1,2}):(\d{2})\s*(AM|PM)\s*$/i;

/**
 * Parses a DisplayEvent time into minutes since midnight (spec.md C3).
 *
 * Returns null when the string does not match the pattern, or matches but is
 * out of range (hour < 1 or > 12, minute > 59). "12 AM" is 0, "12 PM" is 720.
 * Case-insensitive.
 *
 * "TBA" returns null — note transformEvent already maps a null database time
 * to the string "TBA", so DisplayEvent.time is never null.
 */
export function timeToMinutes(time: string): number | null {
  if (typeof time !== 'string') return null;

  const match = TIME_PATTERN.exec(time);
  if (!match) return null;

  const hour = Number(match[1]);
  const minute = Number(match[2]);
  if (hour < 1 || hour > 12) return null;
  if (minute > 59) return null;

  const isPm = match[3].toUpperCase() === 'PM';
  return (hour % 12) * 60 + minute + (isPm ? 720 : 0);
}

/**
 * Total ordering over events (spec.md C3): date, then time, then id.
 *
 * An unparseable time sorts *last* within its date. The final id tiebreak
 * makes the order total — no ties, so the expected array is unambiguous.
 */
export function compareEvents(a: DisplayEvent, b: DisplayEvent): number {
  // 1. Date. YYYY-MM-DD sorts chronologically under a lexical compare.
  const byDate = a.date.localeCompare(b.date);
  if (byDate !== 0) return byDate;

  // 2. Time, with unparseable times last.
  const ta = timeToMinutes(a.time);
  const tb = timeToMinutes(b.time);
  if (ta !== null && tb !== null) {
    if (ta !== tb) return ta - tb;
  } else if (ta === null && tb !== null) {
    return 1;
  } else if (ta !== null && tb === null) {
    return -1;
  }

  // 3. Id, so the order is total.
  return a.id.localeCompare(b.id);
}
