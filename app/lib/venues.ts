import type { DisplayEvent } from '../types/event';
import { venueSlug } from './venue-slug';
import { compareEvents } from './event-order';

export interface VenueSummary {
  name: string;
  slug: string;
  eventCount: number;
}

/**
 * Derives the venue list from a list of events (spec.md C2).
 *
 * The venue set is whatever is in the passed `events` array — no hardcoded
 * list, no minimum count. Groups by the *exact* `event.venue` string, so two
 * distinct names that happen to slug alike stay separate entries.
 *
 * Sorted ascending by name. Pure: no I/O, no clock, no module-level state.
 */
export function venuesFromEvents(events: DisplayEvent[]): VenueSummary[] {
  const countsByName = new Map<string, number>();
  for (const event of events) {
    countsByName.set(event.venue, (countsByName.get(event.venue) ?? 0) + 1);
  }

  return Array.from(countsByName, ([name, eventCount]) => ({
    name,
    slug: venueSlug(name),
    eventCount,
  })).sort((a, b) => a.name.localeCompare(b.name, 'en'));
}

/**
 * All events whose venue slugs to `slug`, in spec.md C3 order (spec.md C2).
 *
 * On a slug collision this returns the union of the colliding venues' events,
 * so behaviour is total rather than undefined. `filter` copies first, so the
 * caller's array is never mutated by the sort.
 */
export function eventsForSlug(events: DisplayEvent[], slug: string): DisplayEvent[] {
  return events
    .filter((event) => venueSlug(event.venue) === slug)
    .sort(compareEvents);
}
