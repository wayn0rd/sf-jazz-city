import { describe, it, expect, afterEach, beforeEach, vi } from 'vitest';
import { execFileSync } from 'node:child_process';
import path from 'node:path';
import { render, screen, cleanup, waitFor, fireEvent } from '@testing-library/react';

import Home from '@/app/page';
import { FIXTURE, txt } from './fixture';

const REPO_ROOT = path.resolve(__dirname, '..');

function grepLines(args: string[]): string[] {
  try {
    return execFileSync('grep', args, { cwd: REPO_ROOT, encoding: 'utf8' })
      .split('\n').filter(Boolean);
  } catch (err: any) {
    if (err && err.status === 1) return [];
    throw err;
  }
}

function mockFetchResolving(events: unknown[]) {
  vi.stubGlobal('fetch', vi.fn().mockResolvedValue({ ok: true, json: async () => ({ events }) }));
}

/** Cards inside a given section id — keeps Tonight and Browse counts separate. */
function cardsIn(sectionId: string): Element[] {
  const section = document.getElementById(sectionId);
  expect(section, `section #${sectionId} must exist`).not.toBeNull();
  return Array.from(section!.querySelectorAll('[data-testid="event-card"]'));
}

function titlesIn(sectionId: string): string[] {
  const section = document.getElementById(sectionId);
  return Array.from(section!.querySelectorAll('[data-testid="event-card-title"]')).map(txt);
}

const searchInput = () =>
  screen.getByPlaceholderText('Search artists or venues...') as HTMLInputElement;

afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
  vi.useRealTimers();
});

describe('T-C9 homepage regressions', () => {
  describe('loaded with the fixture payload', () => {
    beforeEach(async () => {
      mockFetchResolving(FIXTURE);
      render(<Home />);
      await screen.findByTestId('site-header');
    });

    it('T-C9-2: shared header and footer both render after load', async () => {
      expect(screen.getByTestId('site-header')).toBeInTheDocument();
      await waitFor(() => expect(screen.getByTestId('site-footer')).toBeInTheDocument());
    });

    it('T-C9-3: the #tonight and #upcoming section ids survive the refactor', () => {
      expect(document.getElementById('tonight')).not.toBeNull();
      expect(document.getElementById('upcoming')).not.toBeNull();
    });

    it('T-C9-4: both section headings are present', () => {
      expect(screen.getByText('Playing Tonight')).toBeInTheDocument();
      expect(screen.getByText('Browse All Shows')).toBeInTheDocument();
    });

    it('T-C9-5: Browse renders the whole fixture — 7 cards', () => {
      expect(cardsIn('upcoming')).toHaveLength(7);
    });

    it('T-C9-6: searching "yoshi" narrows Browse to 5 (venue-name search works)', async () => {
      fireEvent.change(searchInput(), { target: { value: 'yoshi' } });
      await waitFor(() => expect(cardsIn('upcoming')).toHaveLength(5));
    });

    it('T-C9-7: searching "trio" narrows Browse to 1 (artist search works)', async () => {
      fireEvent.change(searchInput(), { target: { value: 'trio' } });
      await waitFor(() => expect(cardsIn('upcoming')).toHaveLength(1));
      expect(titlesIn('upcoming')).toEqual(['Trio One']);
    });

    it('T-C9-8: a no-match search shows the empty-results copy', async () => {
      fireEvent.change(searchInput(), { target: { value: 'zzzznomatch' } });
      await screen.findByText('No shows found. Try adjusting your filters.');
      expect(cardsIn('upcoming')).toHaveLength(0);
    });

    it('T-C9-9: the date select offers All Dates plus one option per distinct date', () => {
      const select = document.querySelector('select') as HTMLSelectElement;
      expect(select).not.toBeNull();
      const options = Array.from(select.options);
      expect(options).toHaveLength(4);
      expect(options[0].value).toBe('all');
      expect(txt(options[0])).toBe('All Dates');
      expect(options.slice(1).map((o) => o.value))
        .toEqual(['2026-09-01', '2026-09-02', '2026-09-03']);
    });

    it('T-C9-10: selecting a date narrows Browse to that date', async () => {
      const select = document.querySelector('select') as HTMLSelectElement;
      fireEvent.change(select, { target: { value: '2026-09-03' } });
      await waitFor(() => expect(cardsIn('upcoming')).toHaveLength(1));
      expect(titlesIn('upcoming')).toEqual(['Duo Five']);
    });

    it("T-C9-11: Browse venue names for Yoshi's events link to /venues/yoshi-s", () => {
      const section = document.getElementById('upcoming')!;
      const venues = Array.from(section.querySelectorAll('[data-testid="event-card-venue"]'));
      const yoshis = venues.filter((v) => txt(v) === "Yoshi's");
      expect(yoshis).toHaveLength(5);
      for (const v of yoshis) {
        expect(v.tagName).toBe('A');
        expect(v.getAttribute('href')).toBe('/venues/yoshi-s');
      }
    });
  });

  it('T-C9-12: the loading screen is unchanged — no header, original copy', () => {
    vi.stubGlobal('fetch', vi.fn().mockReturnValue(new Promise(() => {})));
    render(<Home />);
    expect(screen.getByText('Loading jazz events...')).toBeInTheDocument();
    expect(screen.queryByTestId('site-header')).toBeNull();
  });

  it('T-C9-13: Tonight renders featured cards for today\'s events', async () => {
    vi.useFakeTimers({ shouldAdvanceTime: true });
    vi.setSystemTime(new Date('2026-09-01T12:00:00'));
    try {
      mockFetchResolving(FIXTURE);
      render(<Home />);
      await screen.findByTestId('site-header');
      await waitFor(() => expect(cardsIn('tonight')).toHaveLength(5));

      // Every Tonight card links its venue name.
      const section = document.getElementById('tonight')!;
      const venues = Array.from(section.querySelectorAll('[data-testid="event-card-venue"]'));
      expect(venues).toHaveLength(5);
      for (const v of venues) {
        expect(v.tagName).toBe('A');
        expect(v.getAttribute('href')).toBe('/venues/' + (txt(v) === "Yoshi's" ? 'yoshi-s' : 'sfjazz-center'));
      }
      // Class-free proof these are the *featured* variant: featured renders the
      // description ("A show" on e2); the compact variant does not.
      expect(section.textContent).toContain('A show');
    } finally {
      vi.useRealTimers();
    }
  });

  it('T-C9-14: the homepage does not import from app/venues/', () => {
    const importsFromVenues = grepLines(['-n', '-e', "from ['\"].*app/venues", '-e', "from ['\"]@/app/venues", 'app/page.tsx']);
    expect(importsFromVenues, importsFromVenues.join('\n')).toEqual([]);
  });
});
