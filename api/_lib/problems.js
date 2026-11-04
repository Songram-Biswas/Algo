/**
 * Problem-of-the-Day selection, shared by backend functions.
 *
 * IMPORTANT: This MUST stay in sync with `initializePOD()` and PROBLEM_REGISTRY in
 * dashboard.html, so the reminder email points at the same problem the dashboard shows.
 * Dashboard logic: implemented problems in category "Array", indexed by day-of-month.
 */

const POD_POOL = [
  { slug: 'two-sum', id: 1, title: 'Two Sum', difficulty: 'Easy', category: 'Array' },
  { slug: 'search-in-rotated-sorted-array', id: 33, title: 'Search in Rotated Sorted Array', difficulty: 'Medium', category: 'Array' },
  { slug: 'maximum-subarray', id: 53, title: 'Maximum Subarray', difficulty: 'Medium', category: 'Array' },
  { slug: 'longest-consecutive-sequence', id: 128, title: 'Longest Consecutive Sequence', difficulty: 'Medium', category: 'Array' },
  { slug: 'maximum-product-subarray', id: 152, title: 'Maximum Product Subarray', difficulty: 'Medium', category: 'Array' },
  { slug: 'find-minimum-in-rotated-sorted-array', id: 153, title: 'Find Minimum in Rotated Sorted Array', difficulty: 'Medium', category: 'Array' },
  { slug: 'contains-duplicate', id: 217, title: 'Contains Duplicate', difficulty: 'Easy', category: 'Array' },
  { slug: 'product-of-array-except-self', id: 238, title: 'Product of Array Except Self', difficulty: 'Medium', category: 'Array' },
  { slug: 'container-with-most-water', id: 11, title: 'Container With Most Water', difficulty: 'Medium', category: 'Array' },
];

/**
 * Returns calendar parts for `date` in the given IANA time zone.
 * @returns {{ isoDate: string, day: number }}  e.g. { isoDate: '2026-11-04', day: 4 }
 */
function datePartsInZone(date, timeZone) {
  const parts = Object.fromEntries(
    new Intl.DateTimeFormat('en-CA', { timeZone, year: 'numeric', month: '2-digit', day: '2-digit' })
      .formatToParts(date)
      .map((p) => [p.type, p.value])
  );
  return { isoDate: `${parts.year}-${parts.month}-${parts.day}`, day: Number(parts.day) };
}

function getProblemOfTheDay(date = new Date(), timeZone = 'UTC') {
  const { day } = datePartsInZone(date, timeZone);
  return POD_POOL[day % POD_POOL.length];
}

module.exports = { POD_POOL, getProblemOfTheDay, datePartsInZone };
