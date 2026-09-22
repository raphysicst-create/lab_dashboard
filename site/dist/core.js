export const STORAGE_KEY = 'science-classroom-prep.preferences.v1';

export function normalizeSearch(value) {
  return String(value ?? '').normalize('NFKC').toLocaleLowerCase('ko').replace(/\s+/g, '');
}

export function filterActivities(activities, filters) {
  const terms = String(filters.query ?? '').trim().split(/\s+/).filter(Boolean).map(normalizeSearch);
  return activities.filter(activity => {
    if (filters.grade === 'unknown' && activity.grade != null) return false;
    if (filters.grade !== 'all' && filters.grade !== 'unknown' && String(activity.grade) !== filters.grade) return false;
    if (filters.unit !== 'all' && activity.unit !== filters.unit) return false;
    if (filters.achievement !== 'all' && activity.achievement_id !== filters.achievement) return false;
    if (!filters.publishers.includes(activity.publisher_raw)) return false;
    const fields = [activity.title, activity.materials_raw, activity.achievement_raw, activity.unit, activity.publisher_raw];
    const haystack = fields.map(normalizeSearch).join('\n');
    return terms.every(term => haystack.includes(term));
  });
}

export function sanitizePreferences(input, publishers) {
  const value = input && typeof input === 'object' && !Array.isArray(input) ? input : {};
  return {
    publishers: Array.isArray(value.publishers)
      ? [...new Set(value.publishers.filter(p => publishers.includes(p)))] : [...publishers],
  };
}
