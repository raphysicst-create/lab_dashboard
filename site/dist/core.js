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

export function positiveInteger(value, max = 100) {
  if (value === '' || value == null) return null;
  const number = Number(value);
  return Number.isSafeInteger(number) && number >= 1 && number <= max ? number : null;
}

export function classroomTotals(settings) {
  const classes = positiveInteger(settings.classes);
  const students = positiveInteger(settings.students);
  const groupSize = positiveInteger(settings.groupSize);
  if (classes == null || students == null || groupSize == null) return null;
  const groupsPerClass = Math.ceil(students / groupSize);
  return {classes, students, groupSize, groupsPerClass,
    totalGroups: groupsPerClass * classes, totalStudents: students * classes};
}

// No amount, unit, or basis is inferred from a material's name or vessel size.
// Evidence is an explicit reference to the quantity's source, not an AI score.
export function calculateQuantity(record, settings) {
  if (!record || typeof record.quantity !== 'number' || !Number.isFinite(record.quantity)
      || record.quantity <= 0 || !record.unit || !record.source_ref || !record.basis) return null;
  const classes = positiveInteger(settings.classes);
  const students = positiveInteger(settings.students);
  const groupSize = positiveInteger(settings.groupSize);
  let multiplier;
  if (record.basis === 'student' && classes && students) multiplier = classes * students;
  else if (record.basis === 'group' && classes && students && groupSize) multiplier = classes * Math.ceil(students / groupSize);
  else if (record.basis === 'class' && classes) multiplier = classes;
  // "activity" is a single stated experiment total; don't assume repetition count.
  else return null;
  const total = record.quantity * multiplier;
  return Number.isFinite(total) ? Number(total.toPrecision(12)) : null;
}

export function sanitizePreferences(input, publishers) {
  const value = input && typeof input === 'object' && !Array.isArray(input) ? input : {};
  return {
    publishers: Array.isArray(value.publishers)
      ? [...new Set(value.publishers.filter(p => publishers.includes(p)))] : [...publishers],
    classes: positiveInteger(value.classes), students: positiveInteger(value.students),
    groupSize: positiveInteger(value.groupSize),
  };
}
