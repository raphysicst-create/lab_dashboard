import { STORAGE_KEY, achievementIds, compareAchievements, filterActivities, gradeKey, sanitizePreferences } from './core.js?v=integrated-20260923';
import { createChemicalUI } from './chemical-ui.js?v=guides-2';

const $ = id => document.getElementById(id);
const PAGE_SIZE = 30;
const state = {
  activities: [], achievements: [], chemicals: [], materials: [],
  publishers: [], preferences: {}, filtered: [], limit: PAGE_SIZE,
};
let chemicalUI;

function element(tag, text, className) {
  const node = document.createElement(tag);
  if (text != null) node.textContent = text;
  if (className) node.className = className;
  return node;
}

function action(label, callback, className) {
  const button = element('button', label, className);
  button.type = 'button';
  button.addEventListener('click', callback);
  return button;
}

function display(value) {
  return value == null || value === '' ? '미확인' : String(value);
}

function displayItems(items) {
  return items == null ? '미확인' : items.length ? items.join(', ') : '해당 항목 없음';
}

function pageLabel(activity) {
  return activity.page == null ? '쪽수 미확인' : `${activity.page}쪽`;
}

function gradeLabel(item) {
  if (item.grade_label) return item.grade_label;
  if (item.grade == null) return '학년 미확인';
  return `${item.school_level === '고등학교' ? '고' : '중'}${item.grade}`;
}

function gradeOrder(item) {
  return item.grade == null ? Infinity : (gradeKey(item)?.startsWith('high-') ? 100 : 0) + item.grade;
}

function materialGroups(activity) {
  if (activity.material_classification_pending === true
    || (activity.school_level === '고등학교' && activity.equipment == null && activity.supplies == null)) {
    return [['실험 준비물 원문', display(activity.materials_raw)]];
  }
  return [['실험 기자재', displayItems(activity.equipment)], ['실험 준비물', displayItems(activity.supplies)]];
}

function standardUnitKey(standard) {
  return JSON.stringify([standard.school_level ?? '중학교', standard.volume ?? null, standard.unit]);
}

function standardUnitLabel(standard) {
  const unit = display(standard.unit);
  return standard.school_level === '고등학교' && standard.volume != null && !unit.startsWith('통합과학')
    ? `통합과학 ${standard.volume} · ${unit}` : unit;
}

function storageWarning(message) {
  $('storage-warning').textContent = message;
  $('storage-warning').hidden = !message;
}

function readPreferences() {
  let value = null;
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (raw != null) value = JSON.parse(raw);
  } catch {
    storageWarning('저장된 설정을 읽을 수 없습니다. 현재 화면의 설정으로 사용할 수 있습니다.');
  }
  return sanitizePreferences(value, state.publishers);
}

function savePreferences() {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(state.preferences));
    storageWarning('');
  } catch {
    storageWarning('이 브라우저에서 설정을 저장할 수 없습니다. 사이트 데이터 저장 권한을 확인하세요.');
  }
}

function applyPreferences() {
  document.querySelectorAll('[data-publisher]').forEach(input => {
    input.checked = state.preferences.publishers.includes(input.dataset.publisher);
  });
}

function populateSelect(select, choices, firstLabel) {
  select.replaceChildren(new Option(firstLabel, 'all'));
  for (const [value, label] of choices) select.add(new Option(label, value));
}

function populateFilters() {
  const grades = new Map([...state.activities].sort((a, b) => gradeOrder(a) - gradeOrder(b))
    .filter(activity => gradeKey(activity) != null).map(activity => [gradeKey(activity), gradeLabel(activity)]));
  populateSelect($('grade-filter'), [...grades], '전체 학년');
  if (state.activities.some(a => gradeKey(a) == null)) $('grade-filter').add(new Option('미확인', 'unknown'));
  const options = state.publishers.map(publisher => {
    const label = element('label', null, 'publisher-option');
    const input = document.createElement('input');
    input.type = 'checkbox'; input.dataset.publisher = publisher;
    input.checked = state.preferences.publishers.includes(publisher);
    input.addEventListener('change', () => {
      state.preferences.publishers = [...document.querySelectorAll('[data-publisher]:checked')].map(n => n.dataset.publisher);
      savePreferences(); updateResults();
    });
    label.append(input, element('span', publisher), element('small', state.activities.filter(a => a.publisher_raw === publisher).length));
    return label;
  });
  $('publisher-options').replaceChildren(...options);
  updateUnitOptions();
  updateAchievementOptions();
}

function matchesGrade(item) {
  const grade = $('grade-filter').value;
  return grade === 'all' || (grade === 'unknown' ? gradeKey(item) == null : gradeKey(item) === grade);
}

function updateUnitOptions() {
  const current = $('unit-filter').value;
  const activities = state.activities.filter(matchesGrade)
    .sort((a, b) => {
      const order = item => item.school_level === '고등학교'
        ? 100 + (item.volume ?? 0) * 10 + (item.unit_number ?? 0) : item.unit_number ?? Infinity;
      return order(a) - order(b) || String(a.unit).localeCompare(String(b.unit), 'ko', { numeric: true });
    });
  const units = [...new Set(activities.map(a => a.unit))];
  populateSelect($('unit-filter'), units.map(unit => [unit, display(unit)]), '전체 단원');
  if (units.includes(current)) $('unit-filter').value = current;
}

function updateAchievementOptions() {
  const current = $('achievement-filter').value;
  const selectedUnit = $('unit-filter').value;
  const activities = state.activities.filter(activity => matchesGrade(activity)
    && (selectedUnit === 'all' || activity.unit === selectedUnit));
  const linkedIds = new Set(activities.flatMap(achievementIds));
  const standards = state.achievements.filter(standard => linkedIds.has(standard.id))
    .sort(compareAchievements);
  const select = $('achievement-filter');
  select.replaceChildren(new Option('전체 성취기준', 'all'));
  const groups = new Map();
  for (const standard of standards) {
    const groupKey = standardUnitKey(standard);
    if (!groups.has(groupKey)) {
      const group = document.createElement('optgroup');
      const groupIds = new Set(standards.filter(item => standardUnitKey(item) === groupKey).map(item => item.id));
      const grades = [...new Set(activities.filter(activity => achievementIds(activity).some(id => groupIds.has(id)))
        .sort((a, b) => gradeOrder(a) - gradeOrder(b)).map(gradeLabel))];
      group.label = `${standardUnitLabel(standard)} · ${grades.join('·')}`;
      groups.set(groupKey, group);
      select.append(group);
    }
    groups.get(groupKey).append(new Option(display(standard.raw_text), standard.id));
  }
  if ([...select.options].some(option => option.value === current)) select.value = current;
}

function getFilters() {
  return { query: $('search').value,
    grade: $('grade-filter').value, unit: $('unit-filter').value,
    achievement: $('achievement-filter').value, publishers: state.preferences.publishers };
}

function updateResults() {
  state.limit = PAGE_SIZE;
  state.filtered = filterActivities(state.activities, getFilters());
  const sort = $('sort-order').value;
  if (sort === 'achievement') {
    const achievements = new Map(state.achievements.map(item => [item.id, item]));
    state.filtered.sort((a, b) => {
      const left = achievements.get(a.achievement_id);
      const right = achievements.get(b.achievement_id);
      return compareAchievements(left, right)
        || a.publisher_raw.localeCompare(b.publisher_raw, 'ko')
        || a.source_row - b.source_row;
    });
  }
  if (sort === 'publisher') state.filtered.sort((a, b) => a.publisher_raw.localeCompare(b.publisher_raw, 'ko') || a.source_row - b.source_row);
  if (sort === 'title') state.filtered.sort((a, b) => a.title.localeCompare(b.title, 'ko') || a.source_row - b.source_row);
  const achievement = state.achievements.find(a => a.id === $('achievement-filter').value);
  $('active-achievement').hidden = !achievement;
  if (achievement) {
    $('active-achievement').replaceChildren(element('h3', '성취기준별 교과서 활동'), element('p', achievement.raw_text));
  }
  renderResults();
}

function createActivityCard(activity) {
  const card = element('article', null, 'activity-card');
  card.dataset.activityId = activity.id;
  const top = element('div', null, 'card-top');
  top.append(element('span', activity.publisher_raw, 'publisher-tag'), element('span', pageLabel(activity), 'page'));
  const title = element('h3');
  title.append(action(activity.title, () => showActivity(activity.id)));
  const actions = element('div', null, 'card-actions');
  actions.append(action('상세 보기', () => showActivity(activity.id)));
  card.append(top, title, element('p', `${gradeLabel(activity)} · ${display(activity.unit)}`, 'unit-line'));
  for (const [label, value] of materialGroups(activity)) {
    card.append(element('p', label, 'material-label'), element('p', value, 'raw-materials'));
  }
  card.append(actions);
  return card;
}

function renderResults() {
  $('result-count').textContent = `탐구활동 ${state.filtered.length.toLocaleString('ko')}건`;
  if (!state.filtered.length) {
    const empty = element('div', null, 'empty-state');
    empty.append(element('h3', '검색 결과가 없습니다.'),
      element('p', state.preferences.publishers.length ? '검색어 또는 선택한 필터를 바꿔보세요.' : '출판사를 한 곳 이상 선택하세요.'),
      action('필터 초기화', resetFilters));
    $('results').replaceChildren(empty);
  } else {
    $('results').replaceChildren(...state.filtered.slice(0, state.limit).map(createActivityCard));
  }
  $('load-more').hidden = state.limit >= state.filtered.length;
  $('load-more').textContent = `활동 더 보기 (${Math.min(state.limit, state.filtered.length)} / ${state.filtered.length})`;
}

function resetFilters() {
  $('search').value = '';
  $('grade-filter').value = 'all'; $('unit-filter').value = 'all';
  $('achievement-filter').value = 'all'; $('sort-order').value = 'achievement';
  state.preferences.publishers = [...state.publishers];
  applyPreferences(); updateUnitOptions(); updateAchievementOptions(); savePreferences(); updateResults();
}

function detailPair(list, label, value) {
  list.append(element('dt', label), element('dd', display(value)));
}

function showActivity(id) {
  const activity = state.activities.find(a => a.id === id);
  if (!activity) return;
  $('dialog-title').textContent = activity.title;
  const list = element('dl');
  detailPair(list, '출판사·저자', activity.publisher_raw);
  detailPair(list, '교과서 쪽수', activity.page == null ? null : `${activity.page}쪽`);
  detailPair(list, '학년', activity.grade == null ? null : gradeLabel(activity));
  detailPair(list, '단원', activity.unit);
  detailPair(list, '성취기준', activity.achievement_raw);
  const materials = materialGroups(activity).map(([label, value]) => {
    const section = element('section', null, 'dialog-section');
    section.append(element('h3', label), element('p', value, 'raw-materials'));
    return section;
  });
  $('dialog-content').replaceChildren(list, ...materials, chemicalUI.activitySection(activity));
  if (!$('activity-dialog').open) $('activity-dialog').showModal();
}

function bindEvents() {
  $('search').addEventListener('input', updateResults);
  ['achievement-filter', 'sort-order'].forEach(id => $(id).addEventListener('change', updateResults));
  $('grade-filter').addEventListener('change', () => { updateUnitOptions(); updateAchievementOptions(); updateResults(); });
  $('unit-filter').addEventListener('change', () => { updateAchievementOptions(); updateResults(); });
  $('reset-filters').addEventListener('click', resetFilters);
  $('load-more').addEventListener('click', () => { state.limit += PAGE_SIZE; renderResults(); });
  $('close-dialog').addEventListener('click', () => $('activity-dialog').close());
  $('activity-dialog').addEventListener('click', event => {
    if (event.target === $('activity-dialog')) {
      const r = $('activity-dialog').getBoundingClientRect();
      if (event.clientX < r.left || event.clientX > r.right || event.clientY < r.top || event.clientY > r.bottom) $('activity-dialog').close();
    }
  });
  window.addEventListener('storage', event => {
    if (event.key === STORAGE_KEY || event.key === null) {
      state.preferences = readPreferences();
      applyPreferences(); updateResults();
    }
  });
}

async function start() {
  try {
    const names = ['activities', 'achievements', 'chemicals', 'materials'];
    const results = await Promise.all(names.map(async name => {
      const url = new URL(`./data/${name}.json`, import.meta.url);
      url.search = '?v=integrated-20260923';
      const response = await fetch(url);
      if (!response.ok) throw new Error(`Failed to load ${name}: ${response.status}`);
      return response.json();
    }));
    names.forEach((name, i) => { state[name] = results[i]; });
    if (!Array.isArray(state.activities) || !state.activities.every(a => typeof a.id === 'string')
      || new Set(state.activities.map(a => a.id)).size !== state.activities.length) throw new Error('Invalid activity data');
    if (!Array.isArray(state.chemicals) || !Array.isArray(state.materials)) throw new Error('Invalid chemical data');
    chemicalUI = createChemicalUI({ chemicals: state.chemicals });
    state.publishers = [...new Set(state.activities.map(a => a.publisher_raw))].sort((a, b) => a.localeCompare(b, 'ko'));
    state.preferences = readPreferences();
    populateFilters(); applyPreferences(); bindEvents(); updateResults();
    $('load-status').hidden = true;
  } catch (error) {
    console.error(error);
    $('load-status').replaceChildren(element('p', '활동을 불러오지 못했습니다. 연결 상태를 확인한 후 다시 시도하세요.'), action('다시 불러오기', () => location.reload()));
    $('activities-view').hidden = true;
  }
}

start();
