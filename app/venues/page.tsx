"use client";

import React, { useEffect, useMemo, useState } from 'react';
import Link from 'next/link';
import SiteHeader from '../components/SiteHeader';
import SiteFooter from '../components/SiteFooter';
import { venuesFromEvents } from '../lib/venues';
import type { DisplayEvent } from '../types/event';

/**
 * /venues - the venue index (spec.md C7).
 *
 * The venue set is derived from the live /api/events payload, not a hardcoded
 * list. That route filters to upcoming events, so a venue with nothing
 * scheduled simply is not here; after a stale scrape this page can be empty.
 * That is the intended behaviour (spec 0), not a bug to paper over.
 *
 * SiteHeader renders immediately, before and during loading, so the page is
 * navigable while the fetch is in flight.
 */
export default function VenuesPage() {
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

  const venues = useMemo(() => venuesFromEvents(events), [events]);

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900">
      <SiteHeader />

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        <h1 className="text-4xl font-bold text-white mb-8">Venues</h1>

        {loading && (
          <p data-testid="venues-loading" className="text-white/70 text-lg">
            Loading venues...
          </p>
        )}

        {!loading && failed && (
          <p data-testid="venues-error" className="text-white/70 text-lg">
            Could not load venues.
          </p>
        )}

        {!loading && !failed && venues.length === 0 && (
          <p data-testid="venues-empty" className="text-white/70 text-lg">
            No venues found.
          </p>
        )}

        {!loading && !failed && venues.length > 0 && (
          <div data-testid="venue-index" className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
            {venues.map((venue) => (
              <div
                key={venue.name}
                data-testid="venue-card"
                className="bg-white/10 backdrop-blur-sm rounded-xl overflow-hidden border border-white/20 hover:border-amber-400/50 transition-all hover:scale-105"
              >
                <Link href={`/venues/${venue.slug}`} className="block p-6">
                  <h2 data-testid="venue-card-name" className="text-xl font-bold text-white mb-2">
                    {venue.name}
                  </h2>
                  <p data-testid="venue-card-count" className="text-amber-400 font-medium text-sm">
                    {venue.eventCount === 1
                      ? '1 upcoming event'
                      : `${venue.eventCount} upcoming events`}
                  </p>
                </Link>
              </div>
            ))}
          </div>
        )}
      </main>

      {!loading && <SiteFooter />}
    </div>
  );
}
