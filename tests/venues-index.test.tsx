import { describe, it, expect, afterEach, beforeEach, vi } from 'vitest';
import { render, screen, cleanup, waitFor } from '@testing-library/react';

import VenuesPage from '@/app/venues/page';
import { FIXTURE, txt } from './fixture';

function mockFetchResolving(events: unknown[]) {
  const f = vi.fn().mockResolvedValue({ ok: true, json: async () => ({ events }) });
  vi.stubGlobal('fetch', f);
  return f;
}

afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
  vi.restoreAllMocks();
});

describe('T-C7 /venues index', () => {
  describe('loaded with the fixture payload', () => {
    beforeEach(() => mockFetchResolving(FIXTURE));

    it('T-C7-1: renders exactly 3 venue cards', async () => {
      render(<VenuesPage />);
      await screen.findByTestId('venue-index');
      expect(screen.getAllByTestId('venue-card')).toHaveLength(3);
    });

    it('T-C7-2: venue names appear in alphabetical DOM order', async () => {
      render(<VenuesPage />);
      await screen.findByTestId('venue-index');
      expect(screen.getAllByTestId('venue-card-name').map(txt))
        .toEqual(["Mr. Tipple's", 'SFJAZZ Center', "Yoshi's"]);
    });

    it('T-C7-3: counts pluralise exactly, in DOM order', async () => {
      render(<VenuesPage />);
      await screen.findByTestId('venue-index');
      expect(screen.getAllByTestId('venue-card-count').map(txt))
        .toEqual(['1 upcoming event', '1 upcoming event', '5 upcoming events']);
    });

    it('T-C7-4: each card links to its venue page', async () => {
      render(<VenuesPage />);
      await screen.findByTestId('venue-index');
      const hrefs = screen.getAllByTestId('venue-card').map((card) => {
        const anchor = card.tagName === 'A' ? card : card.querySelector('a');
        return anchor?.getAttribute('href');
      });
      expect(hrefs).toEqual(['/venues/mr-tipple-s', '/venues/sfjazz-center', '/venues/yoshi-s']);
    });

    it('T-C7-8: page has an <h1> reading "Venues"', async () => {
      render(<VenuesPage />);
      await screen.findByTestId('venue-index');
      const h1s = Array.from(document.querySelectorAll('h1')).map(txt);
      expect(h1s).toContain('Venues');
    });
  });

  it('T-C7-5: while the fetch is in flight, loading state and header coexist', () => {
    vi.stubGlobal('fetch', vi.fn().mockReturnValue(new Promise(() => {})));
    render(<VenuesPage />);
    const loading = screen.getByTestId('venues-loading');
    expect(txt(loading)).toBe('Loading venues...');
    // C7: the header must be present *at the same time* as the loading state.
    expect(screen.getByTestId('site-header')).toBeInTheDocument();
  });

  it('T-C7-6: a rejected fetch shows the error state and raises no unhandled rejection', async () => {
    const unhandled: unknown[] = [];
    const onUnhandled = (e: any) => { unhandled.push(e); };
    process.on('unhandledRejection', onUnhandled);
    try {
      vi.stubGlobal('fetch', vi.fn().mockRejectedValue(new Error('network down')));
      render(<VenuesPage />);
      const err = await screen.findByTestId('venues-error');
      expect(txt(err)).toBe('Could not load venues.');
      await new Promise((r) => setTimeout(r, 20));
      expect(unhandled).toEqual([]);
    } finally {
      process.off('unhandledRejection', onUnhandled);
    }
  });

  it('T-C7-6b (C7): a non-OK response also shows the error state', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue({
      ok: false, status: 500, json: async () => ({}),
    }));
    render(<VenuesPage />);
    const err = await screen.findByTestId('venues-error');
    expect(txt(err)).toBe('Could not load venues.');
  });

  it('T-C7-7: an empty payload shows the empty state and zero cards', async () => {
    mockFetchResolving([]);
    render(<VenuesPage />);
    const empty = await screen.findByTestId('venues-empty');
    expect(txt(empty)).toBe('No venues found.');
    expect(screen.queryAllByTestId('venue-card')).toHaveLength(0);
    await waitFor(() => expect(screen.getByTestId('site-footer')).toBeInTheDocument());
  });
});
