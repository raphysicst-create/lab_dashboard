import { normalizeSearch } from './core.js?v=publishers-20260923';

function node(tag, text, className) {
  const result = document.createElement(tag);
  if (text != null) result.textContent = text;
  if (className) result.className = className;
  return result;
}

function button(text, callback, className) {
  const result = node('button', text, className);
  result.type = 'button';
  result.addEventListener('click', callback);
  return result;
}

function factSection(title, records, describe) {
  const section = node('section', null, 'dialog-section');
  section.append(node('h3', title));
  if (!records?.length) {
    section.append(node('p', '미확인'));
    return section;
  }
  const list = node('ul', null, 'chemical-facts');
  for (const record of records) {
    const item = node('li');
    item.append(node('p', describe(record), 'raw-materials'));
    list.append(item);
  }
  section.append(list);
  return section;
}

export function createChemicalUI({ chemicals, diagrams }) {
  const { cabinetMap, cabinetCategories, wasteFlow } = diagrams;
  const dialog = document.getElementById('chemical-dialog');
  const title = document.getElementById('chemical-title');
  const content = document.getElementById('chemical-content');
  const back = document.getElementById('chemical-back');
  const catalog = [...chemicals].sort((a, b) => a.name.localeCompare(b.name, 'ko'));
  const byId = new Map(chemicals.map(chemical => [chemical.id, chemical]));
  let catalogQuery = '';

  function matches(query) {
    const terms = String(query ?? '').trim().split(/\s+/).filter(Boolean).map(normalizeSearch);
    return catalog.filter(chemical => {
      const names = [chemical.name, ...(chemical.aliases ?? []), chemical.formula].map(normalizeSearch).join('\n');
      return terms.every(term => names.includes(term));
    });
  }

  function open() {
    content.setAttribute('aria-busy', 'false');
    if (!dialog.open) dialog.showModal();
  }

  function showGuidelines() {
    title.textContent = '약품 공통 관리 안내';
    back.hidden = false;
    const overview = node('section', null, 'dialog-section');
    overview.append(node('h3', '학교 화학 약품의 보관장 관리'),
      cabinetMap([], { all: true }),
      node('p', '가연성 물질 전용 보관장이 없는 경우 밀폐형 약품장에 보관할 수 있으나, 장기적으로 가연성 물질 전용 보관장을 구비하기 위한 노력이 필요합니다.', 'map-caption'));
    const wastewater = node('section', null, 'dialog-section');
    wastewater.append(node('h3', '폐수 분류'), wasteFlow());
    content.replaceChildren(overview, wastewater);
    dialog.scrollTop = 0; open();
  }

  function showCatalog(query = '') {
    catalogQuery = query;
    title.textContent = '약품 관리';
    back.hidden = true;
    const label = node('label', '약품명 또는 화학식');
    label.htmlFor = 'chemical-search';
    const search = node('input');
    search.id = 'chemical-search'; search.type = 'search'; search.value = query;
    search.placeholder = '예: 염산, 에탄올, HCl';
    const count = node('p', null, 'help');
    count.id = 'chemical-count'; count.setAttribute('aria-live', 'polite');
    const results = node('div', null, 'chemical-catalog');
    results.id = 'chemical-results';
    const more = button('약품 더 보기', () => { limit += 40; render(); }, 'load-more');
    let limit = 40;
    function render() {
      const found = matches(search.value);
      count.textContent = `약품 ${found.length}건`;
      results.replaceChildren(...found.slice(0, limit).map(chemical => {
        const card = node('article', null, 'chemical-card');
        card.append(button(chemical.name, () => showChemical(chemical.id), 'chemical-name'));
        if (chemical.formula) card.append(node('p', chemical.formula, 'help'));
        const cabinets = [...new Set((chemical.cabinets ?? []).map(item => item.name))];
        card.append(node('p', `보관장: ${cabinets.join(' / ') || '미확인'}`));
        return card;
      }));
      if (!found.length) results.append(node('p', '연결된 약품 자료가 없습니다. 관리 방법은 미확인입니다.', 'empty-state'));
      more.hidden = limit >= found.length;
      more.textContent = `약품 더 보기 (${Math.min(limit, found.length)} / ${found.length})`;
    }
    search.addEventListener('input', () => { catalogQuery = search.value; limit = 40; render(); });
    content.replaceChildren(button('공통 관리 안내', showGuidelines, 'guide-button'), label, search, count, results, more);
    render(); open();
  }

  function showChemical(id) {
    const chemical = byId.get(id);
    if (!chemical) return;
    title.textContent = chemical.name;
    back.hidden = false;
    const intro = node('div', null, 'chemical-intro');
    const names = node('dl');
    names.append(node('dt', '화학식'), node('dd', chemical.formula || '미확인'));
    if (chemical.aliases?.length) names.append(node('dt', '다른 이름'), node('dd', chemical.aliases.join(', ')));
    intro.append(names);
    const storage = node('section', null, 'dialog-section');
    storage.append(node('h3', '보관장 분류'));
    if (!chemical.cabinets?.length) storage.append(node('p', '미확인'));
    storage.append(cabinetMap(chemical.cabinets), node('p', cabinetCategories(chemical.cabinets).length
      ? '해당 약품의 보관 분류만 색으로 표시합니다.'
      : '보관장 분류가 미확인되어 모든 칸을 회색으로 표시합니다.', 'map-caption'));
    content.replaceChildren(intro,
      storage,
      factSection('분류', chemical.classifications, item => [item.group, item.label].filter(Boolean).join(' · ')),
      factSection('보관·관리 방법', chemical.storage, item => `${item.property}\n${item.instruction}`),
      factSection('분리 보관 대상', chemical.incompatibilities, item => item.materials_raw));
    content.scrollTop = 0; dialog.scrollTop = 0; open();
  }

  back.addEventListener('click', () => showCatalog(catalogQuery));

  return {
    showCatalog,
    activitySection(activity) {
      const section = node('section', null, 'dialog-section');
      section.append(node('h3', '약품 관리'));
      const linked = (activity.chemical_ids ?? []).map(id => byId.get(id)).filter(Boolean);
      if (!linked.length) section.append(node('p', '연결된 약품 정보: 미확인'));
      else {
        section.append(node('p', '준비물 원문에서 연결된 약품을 선택하면 관리 방법이 열립니다.', 'help'));
        const links = node('div', null, 'chemical-links');
        links.append(...linked.map(chemical => button(chemical.name, () => showChemical(chemical.id))));
        section.append(links);
      }
      return section;
    },
  };
}
