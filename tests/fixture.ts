// Frozen test fixture — spec.md §6.1.
// The `time` on e4 MUST use the \u202f escape (NARROW NO-BREAK SPACE), never a
// literal pasted character: a literal is invisible in review and degrades to a
// plain space through some editors, which would defeat T-C3-2 entirely.
import type { DisplayEvent } from '@/app/types/event';

export const FIXTURE: DisplayEvent[] = [
  { id: "e1", artist: "Trio One",    venue: "Yoshi's",       date: "2026-09-02", time: "9:30 PM",      price: "$30",       description: "",       ticketUrl: "https://example.com/1", image: "https://example.com/1.jpg" },
  { id: "e2", artist: "Quartet Two", venue: "SFJAZZ Center", date: "2026-09-01", time: "7:30 PM",      price: "$45",       description: "A show", ticketUrl: "https://example.com/2", image: "https://example.com/2.jpg" },
  { id: "e3", artist: "Solo Three",  venue: "Yoshi's",       date: "2026-09-01", time: "TBA",          price: "See venue", description: "",       ticketUrl: "#",                     image: "https://example.com/3.jpg" },
  { id: "e4", artist: "Combo Four",  venue: "Yoshi's",       date: "2026-09-01", time: "8:00\u202fPM", price: "$25",       description: "",       ticketUrl: "https://example.com/4", image: "https://example.com/4.jpg" },
  { id: "e5", artist: "Duo Five",    venue: "Mr. Tipple's",  date: "2026-09-03", time: "11:00 AM",     price: "$20",       description: "",       ticketUrl: "https://example.com/5", image: "https://example.com/5.jpg" },
  { id: "e6", artist: "Big Six",     venue: "Yoshi's",       date: "2026-09-01", time: "12:00 AM",     price: "$15",       description: "",       ticketUrl: "https://example.com/6", image: "https://example.com/6.jpg" },
  { id: "e0", artist: "Zero Seven",  venue: "Yoshi's",       date: "2026-09-01", time: "12:00 AM",     price: "$15",       description: "",       ticketUrl: "https://example.com/0", image: "https://example.com/0.jpg" },
];

/** Exact-match helper — spec §6.0 rule 5: trimmed textContent. */
export const txt = (el: Element | null): string => (el?.textContent ?? '').trim();

/** All 13 frozen slug rows from spec §C1, in spec order. */
export const SLUG_ROWS: Array<[string, string]> = [
  ["SFJAZZ Center", "sfjazz-center"],
  ["Black Cat SF", "black-cat-sf"],
  ["Dawn Club", "dawn-club"],
  ["Keys Jazz Bistro", "keys-jazz-bistro"],
  ["Mr. Tipple's", "mr-tipple-s"],
  ["Yoshi's", "yoshi-s"],
  ["", ""],
  ["!!!", ""],
  ["---", ""],
  ["  SFJAZZ   Center  ", "sfjazz-center"],
  ["Café Du Nord", "caf-du-nord"],
  ["A & B", "a-b"],
  ["123", "123"],
];
