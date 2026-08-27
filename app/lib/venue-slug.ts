/**
 * Derives a URL slug from a venue name (spec.md C1).
 *
 * Pure: no I/O, no clock, no module-level state. No venue list is hardcoded
 * anywhere in the codebase — slugs are always derived from the live payload,
 * which is why this file deliberately contains no example slug literals.
 *
 * Algorithm, exactly and in this order:
 *   1. lowercase
 *   2. collapse every run of one or more characters outside [a-z0-9] to a
 *      single "-". This includes spaces, punctuation, and non-ASCII letters:
 *      an accented letter becomes a separator, not its unaccented form.
 *   3. strip leading and trailing "-"
 *
 * A name with no [a-z0-9] characters at all slugs to the empty string; callers
 * must treat that as "not linkable" rather than emitting a bare /venues/ href.
 */
export function venueSlug(name: string): string {
  return name
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, '-')
    .replace(/^-+|-+$/g, '');
}
