// Type matching the scraped JSON structure
export interface DatabaseEvent {
  title: string;
  date: string;
  time: string | null;
  venue: string;
  artists: string[];
  description: string | null;
  ticket_url: string | null;
  price: string | null;
  status: string | null;
  series: string | null;
  image_url: string | null;
  scraped_at: string;
}

// Type for frontend display
export interface DisplayEvent {
  id: string;
  artist: string;
  venue: string;
  date: string;
  time: string;
  price: string;
  description: string;
  ticketUrl: string;
  image: string;
}

// Default fallback image for events without images
const FALLBACK_IMAGE = "https://images.unsplash.com/photo-1415201364774-f6f0bb35f28f?w=400&h=300&fit=crop";

// Check if an image URL is valid (not a placeholder SVG data URI)
function isValidImageUrl(url: string | null): boolean {
  if (!url) return false;
  if (url.startsWith("data:image/svg+xml")) return false;
  return true;
}

// Transform database event to display event
export function transformEvent(event: DatabaseEvent, index: number): DisplayEvent {
  // Generate ID from title + date to ensure uniqueness
  const id = `${event.title}-${event.date}-${index}`.replace(/\s+/g, '-').toLowerCase();

  return {
    id,
    artist: event.title,
    venue: event.venue,
    date: event.date,
    time: event.time || "TBA",
    price: event.price || "See venue",
    description: event.description || "",
    ticketUrl: event.ticket_url || "#",
    image: isValidImageUrl(event.image_url) ? event.image_url! : FALLBACK_IMAGE,
  };
}
