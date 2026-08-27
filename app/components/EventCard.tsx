import Link from 'next/link';
import { MapPin, Clock, ExternalLink } from 'lucide-react';
import type { DisplayEvent } from '../types/event';
import { venueSlug } from '../lib/venue-slug';
import { formatDate } from '../lib/format';

/**
 * Shared event card (spec.md C6), in the two markups the homepage already had.
 *
 * - 'featured' is the "Playing Tonight" card: taller image, larger body, shows
 *   the description, and shows time + price (the date is implied by "tonight").
 * - 'compact' is the "Browse All Shows" card: shows the date, which venue pages
 *   need because they span many dates.
 *
 * In both variants the venue name links to that venue's page. A venue whose
 * name contains no [a-z0-9] characters slugs to the empty string; it renders as
 * a plain <span> so we never emit a link to a bare /venues/ URL.
 */
export default function EventCard({
  event,
  variant = 'compact',
}: {
  event: DisplayEvent;
  variant?: 'featured' | 'compact';
}) {
  const slug = venueSlug(event.venue);

  const venueNode =
    slug !== '' ? (
      <Link href={`/venues/${slug}`} data-testid="event-card-venue" className="hover:text-amber-400 transition">
        {event.venue}
      </Link>
    ) : (
      <span data-testid="event-card-venue">{event.venue}</span>
    );

  if (variant === 'featured') {
    return (
      <div
        data-testid="event-card"
        className="bg-white/10 backdrop-blur-sm rounded-xl overflow-hidden border border-white/20 hover:border-amber-400/50 transition-all hover:scale-105 hover:shadow-2xl hover:shadow-amber-500/20"
      >
        {/* eslint-disable-next-line @next/next/no-img-element */}
        <img src={event.image} alt={event.artist} className="w-full h-48 object-cover" />
        <div className="p-6">
          <div className="mb-3">
            <h4 data-testid="event-card-title" className="text-xl font-bold text-white">
              {event.artist}
            </h4>
          </div>
          <div className="space-y-2 text-sm text-white/80 mb-4">
            <div className="flex items-center">
              <MapPin className="w-4 h-4 mr-2 text-amber-400" />
              {venueNode}
            </div>
            <div className="flex items-center">
              <Clock className="w-4 h-4 mr-2 text-amber-400" />
              {event.time} &middot; {event.price}
            </div>
          </div>
          {event.description && (
            <p className="text-white/70 text-sm mb-4 line-clamp-3">{event.description}</p>
          )}
          <a
            href={event.ticketUrl}
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center justify-center w-full bg-amber-500 hover:bg-amber-400 text-black font-semibold py-2 px-4 rounded-lg transition"
          >
            Get Tickets
            <ExternalLink className="w-4 h-4 ml-2" />
          </a>
        </div>
      </div>
    );
  }

  return (
    <div
      data-testid="event-card"
      className="bg-white/10 backdrop-blur-sm rounded-xl overflow-hidden border border-white/20 hover:border-amber-400/50 transition-all hover:scale-105"
    >
      {/* eslint-disable-next-line @next/next/no-img-element */}
      <img src={event.image} alt={event.artist} className="w-full h-40 object-cover" />
      <div className="p-5">
        <div className="mb-2">
          <h4 data-testid="event-card-title" className="text-lg font-bold text-white">
            {event.artist}
          </h4>
        </div>
        <div className="space-y-1 text-sm text-white/80 mb-3">
          <div className="flex items-center">
            <MapPin className="w-4 h-4 mr-2 text-amber-400" />
            {venueNode}
          </div>
          <div className="flex items-center">
            <Clock className="w-4 h-4 mr-2 text-amber-400" />
            {formatDate(event.date)} &middot; {event.time}
          </div>
          <div className="text-amber-400 font-medium">{event.price}</div>
        </div>
        <a
          href={event.ticketUrl}
          target="_blank"
          rel="noopener noreferrer"
          className="inline-flex items-center justify-center w-full bg-amber-500 hover:bg-amber-400 text-black font-semibold py-2 px-4 rounded-lg transition text-sm"
        >
          Get Tickets
          <ExternalLink className="w-4 h-4 ml-2" />
        </a>
      </div>
    </div>
  );
}
