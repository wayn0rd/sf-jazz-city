import { describe, it, expect, afterEach } from 'vitest';
import { execFileSync } from 'node:child_process';
import path from 'node:path';
import { render, screen, cleanup } from '@testing-library/react';

import SiteHeader from '@/app/components/SiteHeader';
import SiteFooter from '@/app/components/SiteFooter';
import EventCard from '@/app/components/EventCard';
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

afterEach(() => cleanup());

// ---------------------------------------------------------------- T-C4
describe('T-C4 SiteHeader', () => {
  it('T-C4-1: nav-venues links to /venues with text "Venues"', () => {
    render(<SiteHeader />);
    const el = screen.getByTestId('nav-venues');
    expect(el.tagName).toBe('A');
    expect(el.getAttribute('href')).toBe('/venues');
    expect(txt(el)).toBe('Venues');
  });

  it('T-C4-2: nav-tonight and nav-upcoming keep their hrefs and texts', () => {
    render(<SiteHeader />);
    const tonight = screen.getByTestId('nav-tonight');
    expect(tonight.tagName).toBe('A');
    expect(tonight.getAttribute('href')).toBe('/#tonight');
    expect(txt(tonight)).toBe('Tonight');

    const upcoming = screen.getByTestId('nav-upcoming');
    expect(upcoming.tagName).toBe('A');
    expect(upcoming.getAttribute('href')).toBe('/#upcoming');
    expect(txt(upcoming)).toBe('Upcoming');
  });

  it('T-C4-3: no bare-anchor navs remain anywhere in app/', () => {
    const venuesAnchor = grepLines(['-rn', 'href="#venues"', 'app/']);
    expect(venuesAnchor, venuesAnchor.join('\n')).toEqual([]);

    const bareHashes = grepLines(['-rn', '-e', '"#tonight"', '-e', '"#upcoming"', 'app/']);
    expect(bareHashes, bareHashes.join('\n')).toEqual([]);
  });

  it('T-C4-4: brand-home links to /', () => {
    render(<SiteHeader />);
    const brand = screen.getByTestId('brand-home');
    expect(brand.tagName).toBe('A');
    expect(brand.getAttribute('href')).toBe('/');
  });

  it('T-C4-5: renders standalone with no fetch mocked (proves hook-free)', () => {
    expect(() => render(<SiteHeader />)).not.toThrow();
    expect(screen.getByTestId('site-header')).toBeInTheDocument();
  });
});

// ---------------------------------------------------------------- T-C5
describe('T-C5 SiteFooter', () => {
  it('T-C5-1: renders both existing paragraphs verbatim', () => {
    render(<SiteFooter />);
    const footer = screen.getByTestId('site-footer');
    expect(footer).toBeInTheDocument();
    expect(footer.textContent).toContain('SF Jazz City. Your guide to live jazz in San Francisco.');
    expect(footer.textContent).toContain('Always verify details with venues.');
  });
});

// ---------------------------------------------------------------- T-C6
const yoshisEvent = FIXTURE[0];      // Trio One @ Yoshi's
const describedEvent = FIXTURE[1];   // Quartet Two @ SFJAZZ Center, description "A show"

describe('T-C6 EventCard', () => {
  it('T-C6-1: default variant is "compact"', () => {
    const { container: defaulted } = render(<EventCard event={yoshisEvent} />);
    const defaultHtml = defaulted.innerHTML;
    expect(screen.getByTestId('event-card-title')).toBeInTheDocument();
    expect(txt(screen.getByTestId('event-card-title'))).toBe('Trio One');
    cleanup();

    const { container: explicit } = render(<EventCard event={yoshisEvent} variant="compact" />);
    expect(defaultHtml).toBe(explicit.innerHTML);
  });

  it('T-C6-2: compact links the venue name to its venue page', () => {
    render(<EventCard event={yoshisEvent} variant="compact" />);
    const venue = screen.getByTestId('event-card-venue');
    expect(venue.tagName).toBe('A');
    expect(venue.getAttribute('href')).toBe('/venues/yoshi-s');
    expect(txt(venue)).toBe("Yoshi's");
  });

  it('T-C6-3: featured links the venue name to its venue page', () => {
    render(<EventCard event={yoshisEvent} variant="featured" />);
    const venue = screen.getByTestId('event-card-venue');
    expect(venue.tagName).toBe('A');
    expect(venue.getAttribute('href')).toBe('/venues/yoshi-s');
    expect(txt(venue)).toBe("Yoshi's");
  });

  it('T-C6-4: an unsluggable venue renders as a plain span with no href', () => {
    render(<EventCard event={{ ...yoshisEvent, venue: '!!!' }} />);
    const venue = screen.getByTestId('event-card-venue');
    expect(venue.tagName).toBe('SPAN');
    expect(venue.hasAttribute('href')).toBe(false);
    expect(txt(venue)).toBe('!!!');
  });

  it('T-C6-5: featured shows the description, compact does not', () => {
    render(<EventCard event={describedEvent} variant="featured" />);
    expect(screen.getByTestId('event-card').textContent).toContain('A show');
    cleanup();

    render(<EventCard event={describedEvent} variant="compact" />);
    expect(screen.getByTestId('event-card').textContent).not.toContain('A show');
  });
});
