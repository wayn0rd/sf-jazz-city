"use client";

import React, { useEffect, useMemo, useState } from 'react';
import Link from 'next/link';
import { useParams } from 'next/navigation';
import SiteHeader from '../../components/SiteHeader';
import SiteFooter from '../../components/SiteFooter';
import EventCard from '../../components/EventCard';
import { eventsForSlug } from '../../lib/venues';
import type { DisplayEvent } from '../../types/event';

/**
 * /venues/<slug> - one venue's events (spec.md C8).
 *
 * Reads the slug with useParams() rather than the async `params` prop, because
 * this is a client component. Every event the payload holds for the venue is
 * rendered - no second date cutoff on top of the one /api/events already
 * applies, which would silently empty pages after a stale scrape.
 *
 * A slug matching zero events renders a not-found state rather than throwing;
 * that covers both a made-up slug and a real venue that has aged out.
 */
export default function VenuePage() {
  const params = useParams();
  const rawSlug = params?.slug;
  const slug = Array.isArray(rawSlug) ? rawSlug[0] : rawSlug ?? '';

  const [events, setEvents] = useState<DisplayEvent[]>([]);
  const [loading, setLoading] = useState(true);
  const [failed, setFailed] = useState(false);

  useEffect(() => {
    let cancelled = false;

    async function fetchEvents() {
      try {
        const response = await fetch('/api/events');
        if (!response.ok) {
          throw new Error(`Request for /api/events failed with status ${response.status}`);
        }
        const data = await response.json();
        if (cancelled) return;
        setEvents(data.events || []);
      } catch (error) {
        console.error('Failed to fetch events:', error);
        if (!cancelled) setFailed(true);
      } finally {
        if (!cancelled) setLoading(false);
      }
    }

    fetchEvents();
    return () => {
      cancelled = true;
    };
  }, []);

  const venueEvents = useMemo(() => eventsForSlug(events, slug), [events, slug]);

  // The display name is the real name from the data, never the slug. If two
  // distinct names collide on one slug, show the alphabetically first.
  const venueName = useMemo(() => {
    if (venueEvents.length === 0) return '';
    return venueEvents
      .map((event) => event.venue)
      .reduce((first, name) => (name.localeCompare(first, 'en') < 0 ? name : first));
  }, [venueEvents]);

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900">
      <SiteHeader />

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        {loading && (
          <p data-testid="venue-loading" className="text-white/70 text-lg">
            Loading events...
          </p>
        )}

        {!loading && failed && (
          <p data-testid="venues-error" className="text-white/70 text-lg">
            Could not load venues.
          </p>
        )}

        {!loading && !failed && venueEvents.length === 0 && (
          <>
            <h1 data-testid="venue-not-found" className="text-4xl font-bold text-white mb-4">
              Venue not found
            </h1>
            <Link
              href="/venues"
              data-testid="venue-not-found-back"
              className="text-amber-400 hover:text-amber-300 transition"
            >
              Back to all venues
            </Link>
          </>
        )}

        {!loading && !failed && venueEvents.length > 0 && (
          <>
            <h1 data-testid="venue-name" className="text-4xl font-bold text-white mb-2">
              {venueName}
            </h1>
            <Link
              href="/venues"
              data-testid="venue-back-link"
              className="inline-block text-amber-400 hover:text-amber-300 transition mb-8"
            >
              All venues
            </Link>
            <div
              data-testid="venue-event-list"
              className="grid md:grid-cols-2 lg:grid-cols-3 gap-6"
            >
              {venueEvents.map((event) => (
                <EventCard key={event.id} event={event} variant="compact" />
              ))}
            </div>
          </>
        )}
      </main>

      {!loading && <SiteFooter />}
    </div>
  );
}
