/**
 * Shared site footer (spec.md C5).
 *
 * Markup and both paragraphs are carried over verbatim from the original
 * app/page.tsx footer. Hook-free, no required props.
 */
export default function SiteFooter() {
  return (
    <footer
      data-testid="site-footer"
      className="bg-black/30 backdrop-blur-md border-t border-white/10 mt-20"
    >
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="text-center text-white/60 text-sm">
          <p className="mb-2">&copy; 2025 SF Jazz City. Your guide to live jazz in San Francisco.</p>
          <p className="text-xs">Event data updated daily. Always verify details with venues.</p>
        </div>
      </div>
    </footer>
  );
}
