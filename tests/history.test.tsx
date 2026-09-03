/**
 * tests/history.test.tsx — executable form of spec.md §6 (FROZEN test plan), cycle 3.
 *
 * Authored by the Verification phase from `.loopzai/spec.md` + `.loopzai/spec-amendments.md`
 * ALONE, before reading the implementation diff. Once committed this file is frozen for the
 * remainder of the cycle: later attempts run it unchanged; only approved-amendment additions
 * may be appended.
 *
 * Coverage in this file: T1 (10+1), T2 (6), T3 (5), T4 (2), T5 (1), T6 (6), T7-4, T7-5.
 * T7-1/T7-2 are satisfied by the `npx vitest run` invocation that runs this file;
 * T7-3 (pytest) and T7-6 (git status) are shell-level checks recorded in verification.md.
 */
import { describe, it, expect, afterEach, beforeAll } from 'vitest';
import { execFileSync } from 'node:child_process';
import { createHash } from 'node:crypto';
import fs from 'node:fs';
import path from 'node:path';
import { render, screen, cleanup } from '@testing-library/react';

import HistoryPage, { metadata } from '@/app/history/page';
import SiteHeader from '@/app/components/SiteHeader';

const REPO_ROOT = path.resolve(__dirname, '..');

afterEach(() => cleanup());

const H2_TEXTS = [
  'Terrific Street',
  'The Revival at the Dawn Club',
  'The Fillmore',
  'The Blackhawk and the Jazz Workshop',
  'The Beats and the Cool School',
  'Survival and Fusion',
  'SFJAZZ and the Present',
  'Coda',
];

const EM_TEXTS = [
  'In Person: Friday and Saturday Nights at the Blackhawk',
  'Thelonious Alone in San Francisco',
  'Live at the Jazz Workshop',
  'A Charlie Brown Christmas',
  'Concert of Sacred Music',
];

/** Render the history page and return its `history-essay` container. */
function essay(): HTMLElement {
  render(<HistoryPage />);
  return screen.getByTestId('history-essay');
}

const txt = (el: Element) => (el.textContent || '').trim();

// ------------------------------------------------------------------ T1 (C1, C2)
describe('T1 — Essay content (C1, C2)', () => {
  it('T1-1: page renders without throwing and exposes history-essay', () => {
    expect(essay()).toBeTruthy();
  });

  it('T1-2: exactly one <h1> in the essay container', () => {
    expect(essay().querySelectorAll('h1').length).toBe(1);
  });

  it('T1-3: <h1> text is the essay title', () => {
    expect(txt(essay().querySelector('h1')!)).toBe(
      'The Rhythms of the City: A History of San Francisco Jazz',
    );
  });

  it('T1-4: exactly eight <h2> in the essay container', () => {
    expect(essay().querySelectorAll('h2').length).toBe(8);
  });

  it('T1-5: <h2> texts in DOM order', () => {
    expect([...essay().querySelectorAll('h2')].map(txt)).toEqual(H2_TEXTS);
  });

  it('T1-6: exactly 33 <p> in the essay container', () => {
    expect(essay().querySelectorAll('p').length).toBe(33);
  });

  it('T1-7: first <p> opening text', () => {
    const first = txt(essay().querySelectorAll('p')[0]);
    expect(
      first.startsWith(
        "San Francisco's relationship with jazz goes back nearly to the music's beginning.",
      ),
    ).toBe(true);
  });

  it('T1-8: last <p> closing text', () => {
    const ps = essay().querySelectorAll('p');
    expect(txt(ps[ps.length - 1]).endsWith('keep the song moving.')).toBe(true);
  });

  it('T1-9: exactly five <em> in the essay container', () => {
    expect(essay().querySelectorAll('em').length).toBe(5);
  });

  it('T1-10: <em> texts in DOM order', () => {
    expect([...essay().querySelectorAll('em')].map(txt)).toEqual(EM_TEXTS);
  });

  it('T1-11: no raw markdown syntax leaks into rendered text', () => {
    const t = essay().textContent || '';
    expect(t).not.toContain('##');
    expect(t).not.toContain('*');
  });
});

// ------------------------------------------------------------------ T2 (C3)
describe('T2 — Visual design (C3)', () => {
  it('T2-1: essay container class tokens', () => {
    const el = essay();
    for (const c of [
      'max-w-2xl', 'mx-auto', 'bg-black/30', 'backdrop-blur-md',
      'border', 'border-white/10', 'rounded-xl',
    ]) {
      expect(el.classList.contains(c), `essay container missing "${c}"`).toBe(true);
    }
  });

  it('T2-2: an ancestor is the max-w-7xl page wrapper', () => {
    const required = ['max-w-7xl', 'mx-auto', 'px-4', 'sm:px-6', 'lg:px-8'];
    let node: HTMLElement | null = essay().parentElement;
    let found = false;
    while (node && !found) {
      if (required.every((c) => node!.classList.contains(c))) found = true;
      node = node.parentElement;
    }
    expect(found, `no ancestor carries all of ${required.join(', ')}`).toBe(true);
  });

  it('T2-3: <h1> class tokens', () => {
    const h1 = essay().querySelector('h1')!;
    expect(h1.classList.contains('text-white')).toBe(true);
    expect(h1.classList.contains('font-bold')).toBe(true);
  });

  it('T2-4: every <h2> carries text-amber-400 and font-semibold', () => {
    const h2s = [...essay().querySelectorAll('h2')];
    expect(h2s.length).toBe(8);
    h2s.forEach((h, i) => {
      expect(h.classList.contains('text-amber-400'), `h2[${i}] missing text-amber-400`).toBe(true);
      expect(h.classList.contains('font-semibold'), `h2[${i}] missing font-semibold`).toBe(true);
    });
  });

  it('T2-5: every <p> carries text-gray-200, leading-relaxed, mb-4', () => {
    const ps = [...essay().querySelectorAll('p')];
    expect(ps.length).toBe(33);
    ps.forEach((p, i) => {
      for (const c of ['text-gray-200', 'leading-relaxed', 'mb-4']) {
        expect(p.classList.contains(c), `p[${i}] missing "${c}"`).toBe(true);
      }
    });
  });

  it('T2-6: site-header and site-footer are present on the page', () => {
    render(<HistoryPage />);
    expect(screen.getByTestId('site-header')).toBeTruthy();
    expect(screen.getByTestId('site-footer')).toBeTruthy();
  });
});

// ------------------------------------------------------------------ T3 (C4)
describe('T3 — Navigation (C4)', () => {
  it('T3-1: nav-history link', () => {
    render(<SiteHeader />);
    const el = screen.getByTestId('nav-history');
    expect(el.tagName).toBe('A');
    expect(el.getAttribute('href')).toBe('/history');
    expect(txt(el)).toBe('SF Jazz History');
  });

  it('T3-2: the existing three links are unchanged', () => {
    render(<SiteHeader />);
    const expected: [string, string, string][] = [
      ['nav-tonight', '/#tonight', 'Tonight'],
      ['nav-upcoming', '/#upcoming', 'Upcoming'],
      ['nav-venues', '/venues', 'Venues'],
    ];
    for (const [testid, href, text] of expected) {
      const el = screen.getByTestId(testid);
      expect(el.tagName).toBe('A');
      expect(el.getAttribute('href')).toBe(href);
      expect(txt(el)).toBe(text);
    }
  });

  it('T3-3: nav-history sits in the same <nav> as nav-venues', () => {
    render(<SiteHeader />);
    const navA = screen.getByTestId('nav-history').closest('nav');
    const navB = screen.getByTestId('nav-venues').closest('nav');
    expect(navA).toBeTruthy();
    expect(navA).toBe(navB);
  });

  it('T3-4: that nav stays desktop-only (hidden md:flex)', () => {
    render(<SiteHeader />);
    const nav = screen.getByTestId('nav-history').closest('nav')!;
    expect(nav.classList.contains('hidden')).toBe(true);
    expect(nav.classList.contains('md:flex')).toBe(true);
  });

  it('T3-5: nav-history is reachable from the history page', () => {
    render(<HistoryPage />);
    expect(screen.getByTestId('nav-history')).toBeTruthy();
  });
});

// ------------------------------------------------------------------ T4 (C5)
describe('T4 — Metadata (C5)', () => {
  it('T4-1: title string is exact', () => {
    expect(metadata.title).toBe('SF Jazz History — SF Jazz City');
  });

  it('T4-2: em dash, not hyphen', () => {
    expect(String(metadata.title).includes('—')).toBe(true);
    expect(String(metadata.title).includes(' - ')).toBe(false);
  });
});

// ------------------------------------------------------------------ T5 (C6)
describe('T5 — Essay integrity (C6)', () => {
  it('T5-1: essay.md sha256 is unchanged since ideation freeze', () => {
    const buf = fs.readFileSync(path.join(REPO_ROOT, 'app/history/essay.md'));
    expect(createHash('sha256').update(buf).digest('hex')).toBe(
      '8787ac29ab84986b4927a66ce649b512feb2396e4cfe7559d911f83a72a993e5',
    );
  });
});

// ------------------------------------------------------------------ T6 (C7)
describe('T6 — Build & static rendering (C7)', () => {
  let buildStatus = -1;
  let buildOut = '';
  const HTML = path.join(REPO_ROOT, '.next/server/app/history.html');

  beforeAll(() => {
    try {
      buildOut = execFileSync('npx', ['next', 'build'], {
        cwd: REPO_ROOT, encoding: 'utf8', stdio: 'pipe',
        env: { ...process.env, NEXT_TELEMETRY_DISABLED: '1' },
      });
      buildStatus = 0;
    } catch (err: any) {
      buildStatus = typeof err?.status === 'number' ? err.status : 1;
      buildOut = `${err?.stdout || ''}\n${err?.stderr || ''}`;
    }
  }, 600_000);

  it('T6-1: `npx next build` exits 0', () => {
    expect(buildStatus, buildOut.slice(-4000)).toBe(0);
  });

  it('T6-2: /history is prerendered to .next/server/app/history.html', () => {
    expect(fs.existsSync(HTML)).toBe(true);
  });

  it('T6-3: the static HTML contains the essay', () => {
    expect(fs.readFileSync(HTML, 'utf8')).toContain('The Rhythms of the City');
  });

  it('T6-4: the static HTML contains exactly eight <h2 occurrences', () => {
    const html = fs.readFileSync(HTML, 'utf8');
    expect((html.match(/<h2/g) || []).length).toBe(8);
  });

  it('T6-5: no "use client" anywhere under app/history/', () => {
    let out = '';
    try {
      out = execFileSync('grep', ['-r', 'use client', 'app/history/'], {
        cwd: REPO_ROOT, encoding: 'utf8',
      });
    } catch (err: any) {
      if (err && err.status === 1) out = '';
      else throw err;
    }
    expect(out.trim()).toBe('');
  });

  it('T6-6: the /history route-table line is marked static (circle)', () => {
    const line = buildOut
      .split('\n')
      .find((l) => /\s\/history(\s|$)/.test(l) && /\d/.test(l));
    expect(line, 'no /history line in the build route table').toBeTruthy();
    // Strip box-drawing/tree glyphs and whitespace that Next prints before the marker.
    const marker = line!.replace(/^[\s─-╿]*/, '');
    expect(marker.startsWith('○'), `route line was: ${JSON.stringify(line)}`).toBe(true);
  });
});

// ------------------------------------------------------------------ T7-4 / T7-5 (C8)
describe('T7 — Regression, dependency placement (C8)', () => {
  const pkg = JSON.parse(fs.readFileSync(path.join(REPO_ROOT, 'package.json'), 'utf8'));

  it('T7-4: react-markdown is a dependency, not a devDependency', () => {
    expect(typeof pkg.dependencies?.['react-markdown']).toBe('string');
    expect((pkg.dependencies?.['react-markdown'] || '').length).toBeGreaterThan(0);
    expect(pkg.devDependencies?.['react-markdown']).toBeUndefined();
  });

  it('T7-5: package-lock.json records node_modules/react-markdown', () => {
    const lock = fs.readFileSync(path.join(REPO_ROOT, 'package-lock.json'), 'utf8');
    expect(lock).toContain('node_modules/react-markdown');
  });
});
