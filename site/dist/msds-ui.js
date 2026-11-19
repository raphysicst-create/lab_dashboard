// 약품 상세의 "MSDS 받는 곳" 칸을 그린다.
// - data/msds.json(scripts/build_msds_site_data.py가 만듦)은 약품 상세를 처음 열 때 한 번만 불러온다.
// - (가) 이 약품 바로 받기 링크 (나) 병 라벨 업체로 찾는 받는 순서. 모든 링크는 새 탭·noopener.
// - MSDS 파일은 사이트에 두지 않고 업체·공단 주소로만 안내한다(사용자 결정 2026-11-19).
// 검증: node scripts/verify_msds.cjs (정적 서버 127.0.0.1:4173 필요)

const DATA_URL = './data/msds.json?v=msds-20261119';
const LEAD = '병 라벨에 적힌 업체의 MSDS를 받습니다.'; // 11-19 사용자: "비치하세요" 문장 빼기(11-05 MSDS 비치 줄글 삭제와 같은 취지)
let dataLoad;

function node(tag, text, className) {
  const result = document.createElement(tag);
  if (text != null) result.textContent = text;
  if (className) result.className = className;
  return result;
}

function externalLink(text, url) {
  const link = node('a', text);
  link.href = url;
  link.target = '_blank';
  link.rel = 'noopener noreferrer';
  return link;
}

function host(url) {
  return new URL(url).hostname.replace(/^www\./, '');
}

function loadData() {
  dataLoad ??= fetch(new URL(DATA_URL, import.meta.url)).then(response => {
    if (!response.ok) throw new Error(`Failed to load msds: ${response.status}`);
    return response.json();
  }).catch(error => {
    dataLoad = null;
    throw error;
  });
  return dataLoad;
}

function directLinks(entry, data, openChemical, names) {
  const wrap = node('div', null, 'msds-direct');
  wrap.append(node('h4', '이 약품 바로 받기'));
  const links = entry?.links ?? [];
  if (links.length) {
    const list = node('ul', null, 'msds-links');
    for (const link of links) {
      const item = node('li');
      item.append(externalLink(`${link.supplier} · ${link.language}`, link.url));
      if (link.reference) item.append(' ', node('span', '참고용', 'msds-tag'));
      if (link.product) item.append(node('span', link.product, 'msds-product'));
      list.append(item);
    }
    wrap.append(list);
    if (links.every(link => link.reference)) {
      wrap.append(node('p', '업체 MSDS 바로 받기 링크는 찾지 못했습니다. 아래에서 병 라벨의 업체로 찾으세요.', 'help'));
    } else if (links.some(link => link.reference)) {
      wrap.append(node('p', '안전보건공단 자료는 참고용입니다.', 'help'));
    }
    return wrap;
  }
  wrap.append(node('p', '혼합물·용액·일반명이라 약품별 링크가 없습니다. 아래에서 병 라벨의 업체로 찾으세요.', 'help'));
  const see = (entry?.see ?? []).filter(id => names.has(id));
  if (see.length) {
    const buttons = node('div', null, 'chemical-links');
    for (const id of see) {
      const open = node('button', `${names.get(id)} MSDS 보기`);
      open.type = 'button';
      open.addEventListener('click', () => openChemical(id));
      buttons.append(open);
    }
    wrap.append(buttons);
  }
  const reference = node('p', null, 'msds-reference');
  reference.append(externalLink(data.reference.name, data.reference.url), ' ', node('span', '참고용', 'msds-tag'));
  wrap.append(reference);
  return wrap;
}

function supplierRow(supplier) {
  const item = node('li', null, 'msds-supplier');
  item.dataset.supplierId = supplier.id;
  const name = node('p', null, 'msds-supplier-name');
  name.append(node('strong', supplier.name), ' ', node('span', supplier.role, 'msds-role'));
  const main = supplier.places[0];
  const open = node('p', null, 'msds-open');
  open.append(externalLink(`${host(main.url)} ${main.label} 열기`, main.url));
  const details = node('details');
  details.append(node('summary', '받는 순서 보기'));
  for (const place of supplier.places) {
    const block = node('div', null, 'msds-place');
    const head = node('p', null, 'msds-place-head');
    head.append(externalLink(`${host(place.url)} ${place.label}`, place.url),
      node('span', [place.language, place.latest_date && `최근 자료 ${place.latest_date}`].filter(Boolean).join(' · '), 'msds-meta'));
    const steps = node('ol', null, 'msds-steps');
    steps.append(...place.steps.map(step => node('li', step)));
    block.append(head, steps);
    details.append(block);
  }
  if (supplier.cautions.length) {
    const cautions = node('ul', null, 'msds-cautions');
    cautions.append(...supplier.cautions.map(text => node('li', text)));
    details.append(cautions);
  }
  item.append(name, node('p', supplier.line, 'msds-line'), open, details);
  return item;
}

function render(section, data, chemicalId, openChemical, names) {
  const suppliers = node('div', null, 'msds-by-label');
  suppliers.append(node('h4', '병 라벨 업체로 찾기'));
  const list = node('ul', null, 'msds-suppliers');
  list.append(...data.suppliers.map(supplierRow));
  suppliers.append(list);
  section.replaceChildren(node('h3', 'MSDS 받는 곳'), node('p', LEAD, 'msds-lead'),
    directLinks(data.chemicals[chemicalId], data, openChemical, names), suppliers,
    node('p', `주소와 순서는 ${data.checked_at}에 확인했습니다. 업체 화면이 바뀌면 다를 수 있습니다.`, 'help'));
}

export function msdsSection(chemicalId, { openChemical, names }) {
  const section = node('section', null, 'dialog-section msds-section');
  section.id = 'msds-section';
  function populate() {
    section.setAttribute('aria-busy', 'true');
    section.replaceChildren(node('h3', 'MSDS 받는 곳'), node('p', 'MSDS 받는 곳을 불러오는 중입니다.', 'help'));
    // 불러오기 실패만 다시 시도로 안내한다. 그리기 오류는 숨기지 않는다(페이지 오류로 드러남).
    loadData().then(data => render(section, data, chemicalId, openChemical, names), () => {
      const retry = node('button', '다시 시도');
      retry.type = 'button';
      retry.addEventListener('click', populate);
      section.replaceChildren(node('h3', 'MSDS 받는 곳'), node('p', 'MSDS 받는 곳을 불러오지 못했습니다.', 'help'), retry);
    }).finally(() => section.setAttribute('aria-busy', 'false'));
  }
  populate();
  return section;
}
