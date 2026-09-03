import Link from 'next/link';
import { Music } from 'lucide-react';

/**
 * Shared site header (spec.md C4).
 *
 * Markup is carried over from the original app/page.tsx header. Takes no
 * required props and uses no React hooks, so it renders in any context —
 * including before a page's data has loaded, and in a bare test render.
 *
 * The nav uses next/link rather than bare anchors; the "Venues" entry now
 * points at the real /venues route instead of an on-page anchor.
 */
export default function SiteHeader() {
  return (
    <header
      data-testid="site-header"
      className="bg-black/30 backdrop-blur-md border-b border-white/10 sticky top-0 z-50"
    >
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
        <div className="flex items-center justify-between">
          <Link href="/" data-testid="brand-home" className="flex items-center space-x-3">
            <Music className="w-8 h-8 text-amber-400" />
            <div>
              <h1 className="text-2xl font-bold text-white">SF Jazz City</h1>
              <p className="text-sm sm:text-base text-amber-400">Your Guide to San Francisco Jazz</p>
            </div>
          </Link>
          <nav className="hidden md:flex space-x-6 text-sm">
            <Link href="/#tonight" data-testid="nav-tonight" className="text-white hover:text-amber-400 transition">
              Tonight
            </Link>
            <Link href="/#upcoming" data-testid="nav-upcoming" className="text-white hover:text-amber-400 transition">
              Upcoming
            </Link>
            <Link href="/venues" data-testid="nav-venues" className="text-white hover:text-amber-400 transition">
              Venues
            </Link>
            <Link href="/history" data-testid="nav-history" className="text-white hover:text-amber-400 transition">
              SF Jazz History
            </Link>
          </nav>
        </div>
      </div>
    </header>
  );
}
