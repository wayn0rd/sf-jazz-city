import { describe, it, expect } from 'vitest';
import { execFileSync } from 'node:child_process';
import path from 'node:path';

import { venueSlug } from '@/app/lib/venue-slug';
import { timeToMinutes, compareEvents } from '@/app/lib/event-order';
import { venuesFromEvents, eventsForSlug } from '@/app/lib/venues';
import { formatDate } from '@/app/lib/format';
import { FIXTURE, SLUG_ROWS } from './fixture';
import type { DisplayEvent } from '@/app/types/event';

const REPO_ROOT = path.resolve(__dirname, '..');

/** Run grep, returning matching lines. grep exits 1 on "no match" -> []. */
function grepLines(args: string[]): string[] {
  try {
    const out = execFileSync('grep', args, { cwd: REPO_ROOT, encoding: 'utf8' });
    return out.split('\n').filter(Boolean);
  } catch (err: any) {
    if (err && err.status === 1) return [];
    throw err;
  }
}

// ---------------------------------------------------------------- T-C1
describe('T-C1 venueSlug', () => {
  it('T-C1-1: all 13 frozen rows of the spec C1 table map exactly', () => {
    for (const [input, expected] of SLUG_ROWS) {
      expect(venueSlug(input), `venueSlug(${JSON.stringify(input)})`).toBe(expected);
    }
  });

  it('T-C1-2: is idempotent for all 13 inputs, and stable across repeat calls', () => {
    for (const [input] of SLUG_ROWS) {
      const once = venueSlug(input);
      expect(venueSlug(once), `idempotent for ${JSON.stringify(input)}`).toBe(once);
    }
    expect(venueSlug("Yoshi's")).toBe(venueSlug("Yoshi's"));
    expect(venueSlug('SFJAZZ Center')).toBe('sfjazz-center');
  });

  it('T-C1-3: no hardcoded venue slug list anywhere in app/', () => {
    const matches = grepLines([
      '-rn',
      '-e', 'sfjazz-center', '-e', 'black-cat-sf', '-e', 'dawn-club',
      '-e', 'keys-jazz-bistro', '-e', 'mr-tipple-s', '-e', 'yoshi-s',
      'app/',
    ]);
    expect(matches, `unexpected hardcoded slugs:\n${matches.join('\n')}`).toEqual([]);
  });
});

// ---------------------------------------------------------------- T-C3
describe('T-C3 timeToMinutes', () => {
  it('T-C3-1: canonical times convert to minutes since midnight', () => {
    expect(timeToMinutes('12:00 AM')).toBe(0);
    expect(timeToMinutes('11:00 AM')).toBe(660);
    expect(timeToMinutes('12:00 PM')).toBe(720);
    expect(timeToMinutes('7:30 PM')).toBe(1170);
    expect(timeToMinutes('8:00 PM')).toBe(1200);
    expect(timeToMinutes('9:30 PM')).toBe(1290);
    expect(timeToMinutes('4:30 pm')).toBe(990);
  });

  it('T-C3-2: exotic whitespace between minutes and meridiem all yield 1200', () => {
    expect(timeToMinutes('8:00\u202fPM')).toBe(1200); // NARROW NO-BREAK SPACE (real data)
    expect(timeToMinutes('8:00\u00a0PM')).toBe(1200); // NO-BREAK SPACE
    expect(timeToMinutes('8:00PM')).toBe(1200);       // no separator at all
  });

  it('T-C3-3: unparseable / out-of-range times return null', () => {
    for (const bad of ['TBA', '', '25:00 PM', '0:30 AM', '7:70 PM', 'doors 8']) {
      expect(timeToMinutes(bad), `timeToMinutes(${JSON.stringify(bad)})`).toBeNull();
    }
  });
});

/**
 * Independent reference comparator, transcribed from spec C3 prose.
 * T-C3-4 mandates that Verification RECOMPUTE the expected ordering from the
 * rules rather than trusting the spec's example string. This is that recompute.
 */
function referenceTimeToMinutes(time: string): number | null {
  const m = /^\s*(\d{1,2}):(\d{2})\s*(AM|PM)\s*$/i.exec(time);
  if (!m) return null;
  const hour = Number(m[1]);
  const minute = Number(m[2]);
  if (hour < 1 || hour > 12 || minute > 59) return null;
  const meridiem = m[3].toUpperCase();
  const base = (hour % 12) * 60 + minute;
  return meridiem === 'PM' ? base + 720 : base;
}

function referenceCompare(a: DisplayEvent, b: DisplayEvent): number {
  const byDate = a.date.localeCompare(b.date);
  if (byDate !== 0) return byDate;
  const ta = referenceTimeToMinutes(a.time);
  const tb = referenceTimeToMinutes(b.time);
  if (ta !== null && tb !== null && ta - tb !== 0) return ta - tb;
  if (ta === null && tb !== null) return 1;
  if (ta !== null && tb === null) return -1;
  return a.id.localeCompare(b.id);
}

describe('T-C3 compareEvents', () => {
  it('T-C3-4: sorts the fixture into the order recomputed from the C3 rules', () => {
    const expectedIds = [...FIXTURE].sort(referenceCompare).map((e) => e.id);
    const actualIds = [...FIXTURE].sort(compareEvents).map((e) => e.id);
    expect(actualIds).toEqual(expectedIds);
    // Guard: the recomputed order must be total (no ties) and cover every event.
    expect(new Set(actualIds).size).toBe(FIXTURE.length);
  });

  it('T-C3-5: an unparseable time sorts last, in both argument orders', () => {
    const tba = FIXTURE.find((e) => e.id === 'e3')!;            // 2026-09-01, "TBA"
    const timed = { ...tba, id: 'e9', time: '9:30 PM' };        // same date, parseable
    expect(compareEvents(tba, timed)).toBeGreaterThan(0);
    expect(compareEvents(timed, tba)).toBeLessThan(0);
    expect([tba, timed].sort(compareEvents).map((e) => e.id)).toEqual(['e9', 'e3']);
    expect([timed, tba].sort(compareEvents).map((e) => e.id)).toEqual(['e9', 'e3']);
  });
});

// ---------------------------------------------------------------- T-C2
describe('T-C2 venue derivation', () => {
  it('T-C2-1: venuesFromEvents(FIXTURE) deep-equals the frozen summary array', () => {
    expect(venuesFromEvents(FIXTURE)).toEqual([
      { name: "Mr. Tipple's", slug: 'mr-tipple-s', eventCount: 1 },
      { name: 'SFJAZZ Center', slug: 'sfjazz-center', eventCount: 1 },
      { name: "Yoshi's", slug: 'yoshi-s', eventCount: 5 },
    ]);
  });

  it('T-C2-2: venuesFromEvents([]) is []', () => {
    expect(venuesFromEvents([])).toEqual([]);
  });

  it('T-C2-3: eventsForSlug(FIXTURE, "yoshi-s") is ordered by the C3 comparator', () => {
    const expectedIds = FIXTURE
      .filter((e) => venueSlug(e.venue) === 'yoshi-s')
      .sort(referenceCompare)
      .map((e) => e.id);
    expect(eventsForSlug(FIXTURE, 'yoshi-s').map((e) => e.id)).toEqual(expectedIds);
  });

  it('T-C2-4: non-matching slugs return []', () => {
    expect(eventsForSlug(FIXTURE, 'black-cat-sf')).toEqual([]);
    expect(eventsForSlug(FIXTURE, '')).toEqual([]);
    expect(eventsForSlug(FIXTURE, 'nope')).toEqual([]);
  });

  it('T-C2-5: colliding slugs stay separate entries but union their events', () => {
    const collide: DisplayEvent[] = [
      { ...FIXTURE[0], id: 'c1', venue: 'The Spot' },
      { ...FIXTURE[0], id: 'c2', venue: 'The  Spot!' },
    ];
    expect(venueSlug('The Spot')).toBe('the-spot');
    expect(venueSlug('The  Spot!')).toBe('the-spot');

    const summaries = venuesFromEvents(collide);
    expect(summaries).toHaveLength(2);
    expect(summaries.map((v) => v.name).sort()).toEqual(['The  Spot!', 'The Spot'].sort());
    expect(summaries.every((v) => v.slug === 'the-spot')).toBe(true);

    expect(eventsForSlug(collide, 'the-spot').map((e) => e.id).sort()).toEqual(['c1', 'c2']);
  });

  it('purity: derivation does not mutate its input array', () => {
    const before = JSON.stringify(FIXTURE);
    venuesFromEvents(FIXTURE);
    eventsForSlug(FIXTURE, 'yoshi-s');
    expect(JSON.stringify(FIXTURE)).toBe(before);
  });
});

// ---------------------------------------------------------------- T-C9-1
describe('T-C9 formatters', () => {
  it("T-C9-1: formatDate('all') === 'All Dates'", () => {
    expect(formatDate('all')).toBe('All Dates');
  });
});
