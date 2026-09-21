import { normalizeSearch } from './core.js?v=chemicals-1';

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

export function createChemicalUI({ chemicals, activities, guidelines, onFilter, onSearch }) {
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
    if (!dialog.open) dialog.showModal();
  }

  function closeDetails() {
    dialog.close();
    const activityDialog = document.getElementById('activity-dialog');
    if (activityDialog.open) activityDialog.close();
  }

  function showGuidelines() {
    title.textContent = '약품 공통 관리 안내';
    back.hidden = false;
    content.replaceChildren(node('p', '폐수는 성분과 혼합 상태를 기준으로 확인하며, 약품명만으로 개별 폐기 방법을 지정하지 않습니다.', 'help'));
    for (const guide of guidelines) {
      const section = node('section', null, 'dialog-section');
      section.append(node('h3', guide.title));
      for (const block of guide.content_markdown.split(/\n\n+/)) {
        if (/^#{2,4} /.test(block)) section.append(node('h4', block.replace(/^#{2,4} /, '')));
        else section.append(node('p', block.replace(/^> /gm, '').replace(/^- /gm, '• '), 'raw-materials guide-paragraph'));
      }
      content.append(section);
    }
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
    const related = activities.filter(activity => (activity.chemical_ids ?? []).includes(id));
    const intro = node('div', null, 'chemical-intro');
    const names = node('dl');
    names.append(node('dt', '화학식'), node('dd', chemical.formula || '미확인'));
    if (chemical.aliases?.length) names.append(node('dt', '다른 이름'), node('dd', chemical.aliases.join(', ')));
    intro.append(names);
    const filter = button(`사용 활동 보기 (연결 ${related.length}건)`, () => {
      closeDetails();
      onFilter(id);
    });
    const findActivities = node('div', null, 'chemical-links');
    findActivities.append(button('약품명으로 활동 검색', () => { closeDetails(); onSearch(chemical.name); }));
    if (related.length) findActivities.append(filter);
    intro.append(findActivities);
    const unknown = node('section', null, 'dialog-section');
    unknown.append(node('h3', '안전표지·폐기 방법'));
    const unknownList = node('dl');
    unknownList.append(node('dt', 'GHS 그림문자'), node('dd', '미확인'), node('dt', '개별 약품 폐기 방법'), node('dd', '미확인'));
    unknown.append(unknownList, button('공통 관리 안내', showGuidelines));
    content.replaceChildren(intro,
      factSection('분류', chemical.classifications, item => [item.group, item.label].filter(Boolean).join(' · ')),
      factSection('보관장 분류', chemical.cabinets, item => [item.name, item.category, item.qualifier].filter(Boolean).join(' · ')),
      factSection('보관·관리 방법', chemical.storage, item => `${item.property}\n${item.instruction}`),
      factSection('분리 보관 대상', chemical.incompatibilities, item => item.materials_raw), unknown);
    content.scrollTop = 0; dialog.scrollTop = 0; open();
  }

  back.addEventListener('click', () => showCatalog(catalogQuery));
  document.getElementById('chemical-close').addEventListener('click', () => dialog.close());
  document.getElementById('open-chemicals').addEventListener('click', () => showCatalog());
  document.getElementById('open-chemicals').disabled = false;
  dialog.addEventListener('click', event => {
    if (event.target !== dialog) return;
    const bounds = dialog.getBoundingClientRect();
    if (event.clientX < bounds.left || event.clientX > bounds.right || event.clientY < bounds.top || event.clientY > bounds.bottom) dialog.close();
  });

  return {
    byId,
    showCatalog,
    showChemical,
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
    renderSearch(query, container) {
      const found = query.trim() ? matches(query) : [];
      container.hidden = !found.length;
      if (!found.length) { container.replaceChildren(); return; }
      const links = node('div', null, 'chemical-links');
      links.append(...found.slice(0, 6).map(chemical => button(chemical.name, () => showChemical(chemical.id))));
      if (found.length > 6) links.append(button(`약품 ${found.length}건 모두 보기`, () => showCatalog(query)));
      container.replaceChildren(node('h3', '약품 관리 정보'), links);
    },
  };
}
