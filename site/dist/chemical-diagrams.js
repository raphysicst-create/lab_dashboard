// Visual layout from test-chemical-cabinets.html; classifications come only from
// the existing source-backed cabinet records, never from chemical names/formulas.
const categoryKeys = new Map([
  ['산', 'acid'], ['염기', 'base'], ['위험이 높은 무기 화합물', 'inorganic'],
  ['금속', 'metal'], ['위험성이 낮은 고체 약품', 'solid'],
  ['위험성이 낮은 무기·유기 고체 약품', 'solid'],
  ['인화성·휘발성 물질', 'flammable'],
  ['인화성·휘발성 물질 및 혼합 금지 물질', 'flammable'],
]);

export function cabinetCategories(records = []) {
  return [...new Set((records ?? []).map(record => categoryKeys.get(record.category)).filter(Boolean))];
}

export function cabinetMap(records, { all = false } = {}) {
  const map = document.createElement('div');
  map.className = 'cabinet-map';
  map.setAttribute('role', 'group');
  const categories = cabinetCategories(records);
  map.setAttribute('aria-label', all ? '전체 약품 보관장 분류 6칸' :
    categories.length ? '약품 보관장 분류: 해당 분류 칸 강조' : '약품 보관장 분류 미확인: 모든 칸 회색');
  map.innerHTML = `<div class="cabinet-group">
      <div class="cabinet-title"><span>밀폐형 약품장<br><small>환기식(필터식)</small></span></div>
      <div class="sealed">
        <div class="compartment acid" data-category="acid"><strong>산</strong></div>
        <div class="compartment base" data-category="base"><strong>염기</strong></div>
        <div class="compartment inorganic" data-category="inorganic"><strong>위험이 높은<br>무기 화합물</strong></div>
        <div class="compartment metal" data-category="metal"><strong>금속</strong></div>
      </div>
    </div>
    <div class="other-cabinets">
      <div class="cabinet-group">
        <div class="cabinet-title">일반 약품 보관장</div>
        <div class="general-shell"><div class="compartment solid" data-category="solid"><strong>위험성이 낮은<br>고체 약품</strong></div></div>
      </div>
      <div class="cabinet-group">
        <div class="cabinet-title">가연성 물질 전용 보관장</div>
        <div class="flammable-shell"><div class="compartment flammable" data-category="flammable"><strong>가연성 물질</strong><span class="subtitle">인화성·휘발성 물질<br>및 혼합 금지 물질</span></div></div>
      </div>
    </div>`;
  for (const compartment of map.querySelectorAll('[data-category]')) {
    const active = categories.includes(compartment.dataset.category);
    compartment.classList.toggle('inactive', !all && !active);
    if (!all && active) {
      const badge = document.createElement('span');
      badge.className = 'current';
      badge.textContent = '해당 분류';
      compartment.prepend(badge);
    }
  }
  return map;
}

export function wasteFlow() {
  const template = document.createElement('template');
  template.innerHTML = `<div class="waste-flow" role="group" aria-label="폐수 분류 순서도">
          <div class="waste-step waste-start">
            <div class="waste-box waste-question waste-source">폐수</div>
          </div>
          <div class="waste-step">
            <div class="waste-box waste-question">유기계 폐수인가?<span class="waste-no">NO</span></div>
            <div class="waste-branch"><span class="waste-yes">YES</span></div>
            <div class="waste-result"><div class="waste-box">유기계 폐수</div><p>폐수처리 의뢰 전표의 <strong>유기계 폐수란</strong>에 표시</p></div>
          </div>
          <div class="waste-step">
            <div class="waste-box waste-question">산성 폐수인가?<span class="waste-no">NO</span></div>
            <div class="waste-branch"><span class="waste-yes">YES</span><p class="waste-branch-note">크로뮴산 포함</p></div>
            <div class="waste-result"><div class="waste-box">산성 폐수</div><p>폐수처리 의뢰 전표의 <strong>산성 폐수란</strong>에 표시</p></div>
          </div>
          <div class="waste-step">
            <div class="waste-box waste-question waste-last-question">알칼리계 폐수인가?<span class="waste-no">NO</span></div>
            <div class="waste-branch"><span class="waste-yes">YES</span><p class="waste-branch-note">예외) 암모니아 함유폐수는 유기계 폐수에</p></div>
            <div class="waste-result"><div class="waste-box">알칼리계 폐수</div><p>폐수처리 의뢰 전표의 <strong>알칼리계 폐수란</strong>에 표시</p></div>
          </div>
          <div class="waste-step waste-final">
            <div class="waste-turn" aria-hidden="true"></div>
            <div class="waste-result"><div class="waste-box">무기계 폐수</div><p>폐수처리 의뢰 전표의 <strong>무기계 폐수란</strong>에 표시</p></div>
          </div>
        </div>`;
  return template.content.cloneNode(true);
}
