import fs from 'fs';
import path from 'path';
import ReactMarkdown from 'react-markdown';
import SiteHeader from '../components/SiteHeader';
import SiteFooter from '../components/SiteFooter';

/**
 * /history - the SF Jazz History editorial page (spec.md C1-C3, C5, C7).
 *
 * Deliberately a *synchronous* server component (spec.md D-s2): an async
 * component cannot be rendered by React Testing Library, which would make the
 * whole frozen test plan unimplementable. fs.readFileSync renders fine both in
 * jsdom under vitest and at build time under `next build`, so the essay is
 * baked into static HTML and no markdown is ever shipped to the browser.
 *
 * The prose lives in app/history/essay.md and is read from disk rather than
 * inlined as JSX so it can be edited as a plain file. That file is read-only
 * this cycle (spec.md C6).
 */

export const metadata = {
  title: 'SF Jazz History — SF Jazz City',
  description: 'A history of jazz in San Francisco, from the Barbary Coast to SFJAZZ.',
};

// Per-element styling replaces @tailwindcss/typography (spec.md A2): the colors
// are explicit commitments in C3, not a plugin's defaults.
const components = {
  h1: ({ children }: { children?: React.ReactNode }) => (
    <h1 className="text-4xl text-white font-bold mb-8 leading-tight">{children}</h1>
  ),
  h2: ({ children }: { children?: React.ReactNode }) => (
    <h2 className="text-2xl text-amber-400 font-semibold mt-10 mb-4">{children}</h2>
  ),
  p: ({ children }: { children?: React.ReactNode }) => (
    <p className="text-gray-200 leading-relaxed mb-4">{children}</p>
  ),
};

export default function HistoryPage() {
  const essay = fs.readFileSync(path.join(process.cwd(), 'app/history/essay.md'), 'utf8');

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900">
      <SiteHeader />

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        <article
          data-testid="history-essay"
          className="max-w-2xl mx-auto bg-black/30 backdrop-blur-md border border-white/10 rounded-xl p-6 sm:p-10"
        >
          <ReactMarkdown components={components}>{essay}</ReactMarkdown>
        </article>
      </main>

      <SiteFooter />
    </div>
  );
}
