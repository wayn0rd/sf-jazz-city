import { describe, it, expect, afterEach, vi } from 'vitest';
import { render, screen, cleanup } from '@testing-library/react';

import { FIXTURE, txt } from './fixture';

// C8 mandates useParams(); jsdom has no App Router context, so the hook is stubbed.
const params: { slug: string } = { slug: '' };
vi.mock('next/navigation', () => ({
  useParams: () => params,
  useRouter: () => ({ push: vi.fn(), replace: vi.fn(), back: vi.fn(), prefetch: vi.fn() }),
  usePathname: () => '/venues/' + params.slug,
  useSearchParams: () => new URLSearchParams(),
}));

import VenueDetailPage from '@/app/venues/[slug]/page';

function setSlug(slug: string) { params.slug = slug; }

function mockFetchResolving(events: unknown[]) {
  vi.stubGlobal('fetch', vi.fn().mockResolvedValue({ ok: true, json: async () => ({ events }) }));
}

afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
});

describe("T-C8 /venues/[slug]", () => {
  it('T-C8-1: h1 shows the real venue name, not the slug', async () => {
    setSlug('yoshi-s');
    mockFetchResolving(FIXTURE);
    render(<VenueDetailPage />);
    const h1 = await screen.findByTestId('venue-name');
    expect(h1.tagName).toBe('H1');
    expect(txt(h1)).toBe("Yoshi's");
  });

  it('T-C8-2: lists all 5 Yoshi\'s events in comparator order', async () => {
    setSlug('yoshi-s');
    mockFetchResolving(FIXTURE);
    render(<VenueDetailPage />);
    const list = await screen.findByTestId('venue-event-list');
    expect(list.querySelectorAll('[data-testid="event-card"]')).toHaveLength(5);
    const titles = Array.from(list.querySelectorAll('[data-testid="event-card-title"]')).map(txt);
    expect(titles).toEqual(['Zero Seven', 'Big Six', 'Combo Four', 'Solo Three', 'Trio One']);
  });

  it('T-C8-3: every rendered card self-links to this venue', async () => {
    setSlug('yoshi-s');
    mockFetchResolving(FIXTURE);
    render(<VenueDetailPage />);
    await screen.findByTestId('venue-event-list');
    const venues = screen.getAllByTestId('event-card-venue');
    expect(venues).toHaveLength(5);
    for (const v of venues) {
      expect(v.tagName).toBe('A');
      expect(v.getAttribute('href')).toBe('/venues/yoshi-s');
    }
  });

  it('T-C8-4: another slug renders only its own events', async () => {
    setSlug('sfjazz-center');
    mockFetchResolving(FIXTURE);
    render(<VenueDetailPage />);
    const h1 = await screen.findByTestId('venue-name');
    expect(txt(h1)).toBe('SFJAZZ Center');
    expect(screen.getAllByTestId('event-card')).toHaveLength(1);
    const titles = screen.getAllByTestId('event-card-title').map(txt);
    expect(titles).not.toContain('Trio One');
    expect(titles).not.toContain('Duo Five');
  });

  it('T-C8-5: a valid slug with zero events renders the not-found state', async () => {
    setSlug('black-cat-sf');
    mockFetchResolving(FIXTURE);
    render(<VenueDetailPage />);
    const nf = await screen.findByTestId('venue-not-found');
    expect(nf.textContent).toContain('Venue not found');
    expect(screen.queryByTestId('venue-name')).toBeNull();
    expect(screen.queryByTestId('venue-event-list')).toBeNull();
  });

  it('T-C8-6: an unknown slug renders not-found plus a back link', async () => {
    setSlug('totally-made-up');
    mockFetchResolving(FIXTURE);
    render(<VenueDetailPage />);
    const nf = await screen.findByTestId('venue-not-found');
    expect(nf.textContent).toContain('Venue not found');
    expect(screen.queryByTestId('venue-name')).toBeNull();
    expect(screen.queryByTestId('venue-event-list')).toBeNull();

    const back = screen.getByTestId('venue-not-found-back');
    expect(back.tagName).toBe('A');
    expect(back.getAttribute('href')).toBe('/venues');
    expect(txt(back)).toBe('Back to all venues');
  });

  it('T-C8-7: the populated page has an "All venues" back link', async () => {
    setSlug('yoshi-s');
    mockFetchResolving(FIXTURE);
    render(<VenueDetailPage />);
    await screen.findByTestId('venue-event-list');
    const back = screen.getByTestId('venue-back-link');
    expect(back.tagName).toBe('A');
    expect(back.getAttribute('href')).toBe('/venues');
    expect(txt(back)).toBe('All venues');
  });

  it('T-C8-8: loading state and header coexist while the fetch is pending', () => {
    setSlug('yoshi-s');
    vi.stubGlobal('fetch', vi.fn().mockReturnValue(new Promise(() => {})));
    render(<VenueDetailPage />);
    expect(txt(screen.getByTestId('venue-loading'))).toBe('Loading events...');
    expect(screen.getByTestId('site-header')).toBeInTheDocument();
  });

  it('T-C8-9: no second date cutoff is applied — the 2026-09-02 event renders', async () => {
    setSlug('yoshi-s');
    mockFetchResolving(FIXTURE);
    render(<VenueDetailPage />);
    const list = await screen.findByTestId('venue-event-list');
    expect(list.querySelectorAll('[data-testid="event-card"]')).toHaveLength(5);
    expect(screen.getAllByTestId('event-card-title').map(txt)).toContain('Trio One');
  });

  it("T-C8-10: an apostrophe round-trips through the slug lookup", async () => {
    setSlug('mr-tipple-s');
    mockFetchResolving(FIXTURE);
    render(<VenueDetailPage />);
    const h1 = await screen.findByTestId('venue-name');
    expect(txt(h1)).toBe("Mr. Tipple's");
    expect(screen.getAllByTestId('event-card')).toHaveLength(1);
  });

  it('T-C8 error state (C8): a rejected fetch shows the venues-error copy', async () => {
    setSlug('yoshi-s');
    vi.stubGlobal('fetch', vi.fn().mockRejectedValue(new Error('network down')));
    render(<VenueDetailPage />);
    const err = await screen.findByTestId('venues-error');
    expect(txt(err)).toBe('Could not load venues.');
  });
});
