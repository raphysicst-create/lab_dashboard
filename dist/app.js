import { STORAGE_KEY, filterActivities, classroomTotals, positiveInteger,
  sanitizePreferences, calculateQuantity, toCsv } from './core.js';

const $ = id => document.getElementById(id);
const PAGE_SIZE = 30;
const state = {
  activities: [], achievements: [], textbooks: [], quantities: [], sources: {},
  publishers: [], selected: new Set(), preferences: {}, filtered: [], limit: PAGE_SIZE,
  view: 'activities', dialogActivity: null,
};
let toastTimer;

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

function pageLabel(activity) {
  return activity.page == null ? '쪽수 미확인' : `${activity.page}쪽`;
}

function announce(message) {
  clearTimeout(toastTimer);
  $('toast').textContent = message;
  $('toast').hidden = false;
  toastTimer = setTimeout(() => { $('toast').hidden = true; }, 2500);
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
  return sanitizePreferences(value, state.publishers, new Set(state.activities.map(a => a.id)));
}

function savePreferences() {
  const value = { ...state.preferences, selected: [...state.selected] };
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(value));
    $('save-status').textContent = '이 브라우저에 저장됨';
    storageWarning('');
  } catch {
    $('save-status').textContent = '저장되지 않음';
    storageWarning('이 브라우저에서 설정을 저장할 수 없습니다. 사이트 데이터 저장 권한을 확인하세요.');
  }
}

function applyPreferences() {
  $('class-count').value = state.preferences.classes ?? '';
  $('students-per-class').value = state.preferences.students ?? '';
  $('students-per-group').value = state.preferences.groupSize ?? '';
  document.querySelectorAll('[data-publisher]').forEach(input => {
    input.checked = state.preferences.publishers.includes(input.dataset.publisher);
  });
  renderClassSummary();
}

function renderClassSummary() {
  const totals = classroomTotals(state.preferences);
  const students = state.preferences.students;
  $('settings-toggle').textContent = students ? `학급 설정 · ${students}명/반` : '학급 설정';
  $('class-summary').textContent = totals
    ? `학급당 ${totals.groupsPerClass}조 · 전체 ${totals.totalGroups}조 / ${totals.totalStudents}명 (남는 학생은 한 조로 계산)`
    : '학급 수, 학생 수, 조당 학생 수를 입력하면 조 수를 계산합니다.';
}

function populateSelect(select, choices, firstLabel) {
  select.replaceChildren(new Option(firstLabel, 'all'));
  for (const [value, label] of choices) select.add(new Option(label, value));
}

function populateFilters() {
  const units = [...new Set(state.activities.map(a => a.unit))];
  populateSelect($('unit-filter'), units.map(unit => [unit, display(unit)]), '전체 단원');
  const grades = [...new Set(state.activities.map(a => a.grade).filter(g => g != null))].sort();
  populateSelect($('grade-filter'), grades.map(grade => [String(grade), `${grade}학년`]), '전체 학년');
  if (state.activities.some(a => a.grade == null)) $('grade-filter').add(new Option('미확인', 'unknown'));
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
  updateAchievementOptions();
}

function updateAchievementOptions() {
  const current = $('achievement-filter').value;
  const unit = $('unit-filter').value;
  const grade = $('grade-filter').value;
  const standards = state.achievements.filter(a => (unit === 'all' || a.unit === unit)
    && (grade === 'all' || (grade === 'unknown' ? a.grade == null : String(a.grade) === grade)));
  populateSelect($('achievement-filter'), standards.map(a => [a.id, display(a.raw_text)]), '전체 성취기준');
  if (standards.some(a => a.id === current)) $('achievement-filter').value = current;
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
  const select = element('label', null, 'select-activity');
  const input = document.createElement('input');
  input.type = 'checkbox'; input.dataset.selectActivity = activity.id;
  input.checked = state.selected.has(activity.id);
  input.setAttribute('aria-label', `${activity.publisher_raw} ${activity.title} 준비 목록에 담기`);
  input.addEventListener('change', () => setSelected(activity.id, input.checked));
  select.append(input, element('span', '준비 목록에 담기'));
  const actions = element('div', null, 'card-actions');
  actions.append(select, action('상세 보기', () => showActivity(activity.id)));
  card.append(top, title, element('p', activity.unit, 'unit-line'), element('p', '준비물', 'material-label'),
    element('p', display(activity.materials_raw), 'raw-materials'), actions);
  return card;
}

function renderResults() {
  $('result-count').textContent = `탐구활동 ${state.filtered.length.toLocaleString('ko')}건`;
  $('select-results').disabled = !state.filtered.length;
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
  $('achievement-filter').value = 'all'; $('sort-order').value = 'source';
  state.preferences.publishers = [...state.publishers];
  applyPreferences(); updateAchievementOptions(); savePreferences(); updateResults();
}

function setSelected(id, selected) {
  if (selected) state.selected.add(id); else state.selected.delete(id);
  savePreferences(); updateSelectionUI();
}

function updateSelectionUI() {
  $('selection-count').textContent = state.selected.size;
  document.querySelectorAll('[data-select-activity]').forEach(input => { input.checked = state.selected.has(input.dataset.selectActivity); });
  $('clear-selection').disabled = !state.selected.size;
  $('export-list').disabled = !state.selected.size;
  const dialogButton = $('dialog-select');
  if (dialogButton) dialogButton.textContent = state.selected.has(state.dialogActivity) ? '준비 목록에서 빼기' : '준비 목록에 담기';
  if (state.view === 'materials') renderMaterials();
}

function switchView(view) {
  state.view = view;
  $('activities-view').hidden = view !== 'activities';
  $('materials-view').hidden = view !== 'materials';
  $('activities-tab').setAttribute('aria-pressed', String(view === 'activities'));
  $('materials-tab').setAttribute('aria-pressed', String(view === 'materials'));
  if (view === 'materials') renderMaterials();
}

function selectedActivities() {
  return state.activities.filter(a => state.selected.has(a.id));
}

function quantityRows(activity) {
  return state.quantities.filter(q => q.activity_id === activity.id);
}

const basisLabels = { student: '1인당', group: '1조당', class: '1학급당', activity: '실험 전체' };

function quantityText(activity, calculated = false) {
  const rows = quantityRows(activity);
  if (!rows.length) return '미확인';
  return rows.map(row => {
    const value = calculated ? calculateQuantity(row, state.preferences) : row.quantity;
    if (value == null || !row.unit || !row.source_ref) return `${display(row.material_name)}: 미확인`;
    return `${display(row.material_name)}: ${value} ${row.unit}${calculated ? '' : ` / ${basisLabels[row.basis] ?? '기준 미확인'}`}`;
  }).join('\n');
}

function renderMaterials() {
  const activities = selectedActivities();
  if (!activities.length) {
    const empty = element('div', null, 'empty-state');
    empty.append(element('h3', '담은 활동이 없습니다.'), element('p', '탐구활동에서 준비할 활동을 선택하세요.'), action('탐구활동 보기', () => switchView('activities')));
    $('selected-activities').replaceChildren(empty);
    $('aggregate-materials').replaceChildren(); $('materials-summary').textContent = '';
    return;
  }
  $('selected-activities').replaceChildren(...activities.map(activity => {
    const row = element('div', null, 'selected-row');
    const text = element('div');
    text.append(element('strong', activity.title), element('p', `${activity.publisher_raw} · ${pageLabel(activity)}`));
    row.append(text, action('빼기', () => setSelected(activity.id, false)));
    return row;
  }));
  const missing = activities.filter(a => !a.materials_raw).length;
  $('materials-summary').textContent = `활동 ${activities.length}건${missing ? ` · 준비물 미확인 ${missing}건` : ''}. 준비물은 활동별 원문으로 표시합니다. 수량과 기준이 확인된 항목만 학급 설정에 따라 계산합니다.`;
  const table = element('table');
  const head = element('thead'), heading = element('tr');
  for (const title of ['교과서 활동', '준비물 원문', '교과서 수량', '설정에 따른 수량']) {
    const th = element('th', title); th.scope = 'col'; heading.append(th);
  }
  head.append(heading);
  const body = element('tbody');
  for (const activity of activities) {
    const row = element('tr');
    const name = element('td', activity.title); name.append(element('small', `${activity.publisher_raw} · ${pageLabel(activity)}`));
    row.append(name, element('td', display(activity.materials_raw), 'raw-materials'),
      element('td', quantityText(activity), 'raw-materials quantity'), element('td', quantityText(activity, true), 'raw-materials quantity'));
    body.append(row);
  }
  table.append(head, body);
  const wrap = element('div', null, 'table-wrap'); wrap.append(table);
  $('aggregate-materials').replaceChildren(wrap);
}

function detailPair(list, label, value) {
  list.append(element('dt', label), element('dd', display(value)));
}

function showActivity(id) {
  const activity = state.activities.find(a => a.id === id);
  if (!activity) return;
  state.dialogActivity = id;
  $('dialog-title').textContent = activity.title;
  const achievement = state.achievements.find(a => a.id === activity.achievement_id);
  const textbook = state.textbooks.find(t => t.id === activity.textbook_id);
  const list = element('dl');
  detailPair(list, '출판사·저자', activity.publisher_raw);
  detailPair(list, '교과서 쪽수', activity.page == null ? null : `${activity.page}쪽`);
  detailPair(list, '학년', activity.grade == null ? null : `${activity.grade}학년`);
  detailPair(list, '단원', activity.unit);
  detailPair(list, '성취기준', activity.achievement_raw);
  detailPair(list, '공식 코드', achievement?.code);
  detailPair(list, '교과서명', textbook?.title);
  detailPair(list, '판본', textbook?.edition);
  const materials = element('section', null, 'dialog-section');
  materials.append(element('h3', '준비물 원문'), element('p', display(activity.materials_raw), 'raw-materials'));
  const quantity = element('section', null, 'dialog-section');
  quantity.append(element('h3', '준비 수량'));
  const quantityList = element('dl');
  detailPair(quantityList, '교과서 수량', quantityText(activity));
  detailPair(quantityList, '설정에 따른 수량', quantityText(activity, true));
  quantity.append(quantityList);
  const source = element('section', null, 'dialog-section');
  source.append(element('h3', '출처'), element('p', state.sources.source_name, 'raw-materials'), element('p', `기본자료 시트 ${activity.source_row}행`, 'help'));
  const button = action(state.selected.has(id) ? '준비 목록에서 빼기' : '준비 목록에 담기', () => setSelected(id, !state.selected.has(id)));
  button.id = 'dialog-select';
  $('dialog-content').replaceChildren(button, list, materials, quantity, source);
  if (!$('activity-dialog').open) $('activity-dialog').showModal();
}

function exportList() {
  const rows = [['활동 ID', '출판사·저자', '단원', '성취기준 원문', '쪽수', '활동명', '준비물 원문', '교과서 수량', '설정에 따른 수량', '학급 수', '학급당 학생 수', '조당 학생 수']];
  for (const activity of selectedActivities()) {
    rows.push([activity.id, activity.publisher_raw, activity.unit, activity.achievement_raw, activity.page,
      activity.title, activity.materials_raw, quantityText(activity), quantityText(activity, true),
      state.preferences.classes, state.preferences.students, state.preferences.groupSize]);
  }
  const url = URL.createObjectURL(new Blob([toCsv(rows)], { type: 'text/csv;charset=utf-8' }));
  const anchor = document.createElement('a'); anchor.href = url; anchor.download = '과학_수업_준비목록.csv';
  document.body.append(anchor); anchor.click(); anchor.remove();
  setTimeout(() => URL.revokeObjectURL(url), 30000);
  announce('준비 목록을 다운로드했습니다.');
}

function bindEvents() {
  $('settings-toggle').addEventListener('click', () => {
    const expanded = $('settings-toggle').getAttribute('aria-expanded') === 'true';
    $('settings-toggle').setAttribute('aria-expanded', String(!expanded));
    $('settings-panel').hidden = expanded;
  });
  for (const [id, property] of [['class-count', 'classes'], ['students-per-class', 'students'], ['students-per-group', 'groupSize']]) {
    $(id).addEventListener('input', () => {
      const value = positiveInteger($(id).value);
      $(id).setCustomValidity($(id).value !== '' && value == null ? '1부터 100까지의 정수를 입력하세요.' : '');
      $(id).setAttribute('aria-invalid', String(!$(id).validity.valid));
      state.preferences[property] = value;
      renderClassSummary(); savePreferences();
      if (value == null && $(id).value !== '') $('class-summary').textContent = '학급 설정에는 1부터 100까지의 정수를 입력하세요.';
      if (state.view === 'materials') renderMaterials();
    });
  }
  $('search').addEventListener('input', updateResults);
  ['achievement-filter', 'sort-order'].forEach(id => $(id).addEventListener('change', updateResults));
  ['grade-filter', 'unit-filter'].forEach(id => $(id).addEventListener('change', () => { updateAchievementOptions(); updateResults(); }));
  $('reset-filters').addEventListener('click', resetFilters);
  $('activities-tab').addEventListener('click', () => switchView('activities'));
  $('materials-tab').addEventListener('click', () => switchView('materials'));
  $('load-more').addEventListener('click', () => { state.limit += PAGE_SIZE; renderResults(); });
  $('select-results').addEventListener('click', () => {
    for (const activity of state.filtered) state.selected.add(activity.id);
    savePreferences(); updateSelectionUI(); announce(`검색 결과 ${state.filtered.length}건을 준비 목록에 담았습니다.`);
  });
  $('clear-selection').addEventListener('click', () => { state.selected.clear(); savePreferences(); updateSelectionUI(); });
  $('export-list').addEventListener('click', exportList);
  $('close-dialog').addEventListener('click', () => $('activity-dialog').close());
  $('activity-dialog').addEventListener('click', event => {
    if (event.target === $('activity-dialog')) {
      const r = $('activity-dialog').getBoundingClientRect();
      if (event.clientX < r.left || event.clientX > r.right || event.clientY < r.top || event.clientY > r.bottom) $('activity-dialog').close();
    }
  });
  window.addEventListener('storage', event => {
    if (event.key === STORAGE_KEY || event.key === null) {
      state.preferences = readPreferences(); state.selected = new Set(state.preferences.selected);
      applyPreferences(); updateResults(); updateSelectionUI();
    }
  });
}

async function start() {
  try {
    const names = ['activities', 'achievements', 'textbooks', 'quantities', 'sources'];
    const results = await Promise.all(names.map(async name => {
      const response = await fetch(new URL(`./data/${name}.json`, import.meta.url));
      if (!response.ok) throw new Error(`Failed to load ${name}: ${response.status}`);
      return response.json();
    }));
    names.forEach((name, i) => { state[name] = results[i]; });
    if (!Array.isArray(state.activities) || !state.activities.every(a => typeof a.id === 'string')
      || new Set(state.activities.map(a => a.id)).size !== state.activities.length) throw new Error('Invalid activity data');
    state.publishers = [...new Set(state.activities.map(a => a.publisher_raw))].sort((a, b) => a.localeCompare(b, 'ko'));
    state.preferences = readPreferences(); state.selected = new Set(state.preferences.selected);
    populateFilters(); applyPreferences(); bindEvents(); updateResults(); updateSelectionUI();
    $('load-status').hidden = true;
  } catch (error) {
    console.error(error);
    $('load-status').replaceChildren(element('p', '활동을 불러오지 못했습니다. 연결 상태를 확인한 후 다시 시도하세요.'), action('다시 불러오기', () => location.reload()));
    $('activities-view').hidden = true;
  }
}

start();
