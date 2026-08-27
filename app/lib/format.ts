/**
 * Date formatters, moved verbatim from app/page.tsx so the homepage and the
 * venue pages share one implementation (spec.md C9).
 */

export const formatDate = (dateStr: string) => {
  if (dateStr === 'all') return 'All Dates';
  const date = new Date(dateStr + 'T00:00:00');
  return date.toLocaleDateString('en-US', { weekday: 'short', month: 'short', day: 'numeric' });
};

export const formatFullDate = (dateStr: string) => {
  const date = new Date(dateStr + 'T00:00:00');
  return date.toLocaleDateString('en-US', { weekday: 'long', month: 'long', day: 'numeric', year: 'numeric' });
};
