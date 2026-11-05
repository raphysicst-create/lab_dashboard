const fallbackActivities = [
  {
    publisher: "천재(정대홍)", page: 12, grade: "2학년", unit: "8. 물질의 특성", achievement: "물질의 성질",
    title: "양이 달라져도 변하지 않는 값 찾기",
    materials: "스마트 기기, 물, 에탄올, 크기가 다른 철 조각, 크기가 다른 알루미늄 조각, 50 mL 눈금실린더, 200 mL 눈금실린더, 비커, 핀셋, 전자저울, 실, 실험복, 실험용 장갑, 보안경",
    note: "질량과 부피를 측정해 물질의 고유한 성질을 비교하는 탐구입니다."
  },
  {
    publisher: "천재(정대홍)", page: 15, grade: "2학년", unit: "8. 물질의 특성", achievement: "물질의 성질",
    title: "온도에 따른 물의 밀도 비교하기",
    materials: "따뜻한 물, 찬물, 식용 색소, 작은 유리병, 투명 필름, 색연필, 내열 장갑",
    note: "온도가 달라질 때 물의 밀도가 어떻게 달라지는지 관찰합니다."
  },
  {
    publisher: "천재(정대홍)", page: 17, grade: "2학년", unit: "8. 물질의 특성", achievement: "용해도",
    title: "용질의 녹는 양 비교하기",
    materials: "스마트 기기, 황산 구리(Ⅱ), 질산 칼륨, 물, 비커, 시험관, 전자저울, 페트리 접시, 약숟가락, 실험복, 실험용 장갑, 보안경",
    note: "같은 양의 물에 녹는 용질의 양을 비교하고 용해도를 설명합니다."
  },
  {
    publisher: "천재(정대홍)", page: 19, grade: "2학년", unit: "8. 물질의 특성", achievement: "기체의 용해도",
    title: "압력과 온도에 따른 기체의 용해도 비교하기",
    materials: "탄산음료, 감압 용기, 얼음물, 뜨거운 물, 시험관, 비커, 실험복, 내열 장갑, 보안경",
    note: "압력과 온도가 기체의 용해도에 미치는 영향을 확인합니다."
  },
  {
    publisher: "미래엔", page: 42, grade: "2학년", unit: "8. 물질의 특성", achievement: "끓는점",
    title: "액체의 종류와 양에 따른 끓는점 확인하기",
    materials: "스마트 기기, 물, 에탄올, 알코올램프, 끓임쪽, 간이 달리 실험관, 고무관, 온도계, 스탠드, 보안경",
    note: "액체의 종류에 따라 끓는점이 다르며 양에는 영향을 받지 않음을 확인합니다."
  },
  {
    publisher: "동아", page: 26, grade: "1학년", unit: "4. 물질의 상태 변화", achievement: "혼합물 분리",
    title: "순물질과 혼합물의 분류 놀이하기",
    materials: "스마트 기기, 물질 카드, 분류판, 기록지, 사인펜",
    note: "여러 물질을 성분에 따라 순물질과 혼합물로 분류합니다."
  },
  {
    publisher: "비상", page: 61, grade: "3학년", unit: "2. 기권과 날씨", achievement: "기압",
    title: "간이 기압계로 기압 변화 관찰하기",
    materials: "유리병, 풍선, 고무줄, 빨대, 두꺼운 종이, 자, 테이프",
    note: "간이 기압계를 제작하고 날씨에 따른 기압 변화를 기록합니다."
  },
  {
    publisher: "천재(임성숙)", page: 88, grade: "3학년", unit: "5. 생식과 유전", achievement: "유전 원리",
    title: "유전 형질의 전달 과정 모형 만들기",
    materials: "색 구슬, 종이컵, 유전 형질 카드, 기록지, 계산기",
    note: "모형 활동으로 대립유전자의 조합과 형질의 전달 과정을 설명합니다."
  }
].map((item, index) => ({ ...item, id: `sample_${index + 1}` }));

let activities = fallbackActivities;
let publisherCounts = {};
let visibleLimit = 30;
let usingSsot = false;

const state = { query: "", grade: "all", unit: "all", achievement: "all", publishers: new Set(), sort: "source" };
const $ = (selector, parent = document) => parent.querySelector(selector);
const $$ = (selector, parent = document) => [...parent.querySelectorAll(selector)];
function updatePublisherCounts() {
  publisherCounts = activities.reduce((acc, item) => {
    acc[item.publisher] = (acc[item.publisher] || 0) + 1;
    return acc;
  }, {});
}

async function loadSsot() {
  try {
    let rows = null;
    for (const source of ["./data/activities.json", "../data/activities.json", "../dist/data/activities.json"]) {
      try {
        const response = await fetch(source);
        if (response.ok) { rows = await response.json(); break; }
      } catch { /* Try the next SSOT-relative path. */ }
    }
    if (!Array.isArray(rows) || !rows.length) throw new Error("Empty activity data");
    activities = rows.map((item) => ({
      id: item.id,
      publisher: item.publisher_raw || "출판사 미확인",
      page: item.page ?? "—",
      grade: item.grade ? `${item.grade}학년` : "학년 미확인",
      unit: item.unit || "단원 미확인",
      achievement: item.achievement_raw || "성취기준 미확인",
      title: item.title || "활동명 미확인",
      materials: item.materials_raw || "준비물 미확인",
      note: item.achievement_raw || "연결된 성취기준을 확인할 수 없습니다."
    }));
    usingSsot = true;
  } catch {
    activities = fallbackActivities;
    usingSsot = false;
  }
}

function unique(key) {
  return [...new Set(activities.map((item) => item[key]))].sort((a, b) => a.localeCompare(b, "ko", { numeric: true }));
}

function fillSelect(id, key, allLabel) {
  const select = $(id);
  select.innerHTML = `<option value="all">${allLabel}</option>` + unique(key)
    .map((value) => `<option value="${value}">${value}</option>`).join("");
}

function makePublisherFilters() {
  const wrap = $("#publisher-options");
  wrap.innerHTML = Object.entries(publisherCounts).map(([name, count]) => `
    <label class="publisher-option">
      <input type="checkbox" value="${name}" checked>
      <span>${name}</span><small>${count}</small>
    </label>`).join("");
  state.publishers = new Set(Object.keys(publisherCounts));
}

function filteredActivities() {
  const query = state.query.trim().toLocaleLowerCase("ko");
  const rows = activities.filter((item) => {
    const haystack = `${item.title} ${item.materials} ${item.publisher}`.toLocaleLowerCase("ko");
    return (!query || haystack.includes(query))
      && (state.grade === "all" || item.grade === state.grade)
      && (state.unit === "all" || item.unit === state.unit)
      && (state.achievement === "all" || item.achievement === state.achievement)
      && state.publishers.has(item.publisher);
  });
  if (state.sort === "title") rows.sort((a, b) => a.title.localeCompare(b.title, "ko"));
  if (state.sort === "page") rows.sort((a, b) => a.page - b.page);
  return rows;
}

function hasActiveFilter() {
  return state.query || state.grade !== "all" || state.unit !== "all" || state.achievement !== "all"
    || state.publishers.size !== Object.keys(publisherCounts).length;
}

function render() {
  const rows = filteredActivities();
  $("#result-count").textContent = hasActiveFilter() ? `검색 결과 ${rows.length}건` : `탐구활동 ${rows.length}건`;
  const shown = Math.min(rows.length, visibleLimit);
  $("#preview-count").textContent = `${usingSsot ? "SSOT" : "예시 데이터"} · ${shown}개 표시`;
  $("#active-count").textContent = String([
    state.query, state.grade !== "all", state.unit !== "all", state.achievement !== "all",
    state.publishers.size !== Object.keys(publisherCounts).length
  ].filter(Boolean).length);
  const results = $("#results");
  if (!rows.length) {
    $("#load-more").hidden = true;
    results.innerHTML = `<div class="empty-state"><strong>조건에 맞는 탐구활동이 없습니다.</strong><p>검색어나 필터를 바꿔 보세요.</p><button type="button" data-reset>필터 초기화</button></div>`;
    $("[data-reset]", results).addEventListener("click", resetFilters);
    return;
  }
  results.innerHTML = rows.slice(0, visibleLimit).map((item, index) => `
    <article class="activity-card" style="--card-index:${index}">
      <div class="card-top"><span class="publisher-tag">${item.publisher}</span><span class="page">${item.page}쪽</span></div>
      <h3>${item.title}</h3>
      <p class="unit-line">${item.unit}</p>
      <p class="material-label">준비물</p>
      <p class="raw-materials">${item.materials}</p>
      <div class="card-actions"><button type="button" class="detail-button" data-id="${item.id}">상세 보기<span aria-hidden="true">→</span></button></div>
    </article>`).join("");
  $$(".detail-button", results).forEach((button) => button.addEventListener("click", () => openDetail(button.dataset.id)));
  const loadMore = $("#load-more");
  loadMore.hidden = rows.length <= visibleLimit;
  loadMore.textContent = `활동 더 보기 (${rows.length - shown}개 남음)`;
}

function openDetail(id) {
  const item = activities.find((entry) => entry.id === id);
  $("#dialog-title").textContent = item.title;
  $("#dialog-content").innerHTML = `
    <div class="detail-meta"><span>${item.publisher}</span><span>${item.grade}</span><span>${item.page}쪽</span></div>
    <dl><dt>단원</dt><dd>${item.unit}</dd><dt>성취기준</dt><dd>${item.achievement}</dd><dt>준비물</dt><dd>${item.materials}</dd></dl>
    <div class="dialog-note"><strong>수업 메모</strong><p>${item.note}</p></div>`;
  $("#activity-dialog").showModal();
}

function resetFilters() {
  state.query = ""; state.grade = "all"; state.unit = "all"; state.achievement = "all"; state.sort = "source";
  state.publishers = new Set(Object.keys(publisherCounts));
  visibleLimit = 30;
  $("#search").value = "";
  $("#grade-filter").value = "all";
  $("#unit-filter").value = "all";
  $("#achievement-filter").value = "all";
  $("#sort-order").value = "source";
  $$("#publisher-options input").forEach((input) => { input.checked = true; });
  render();
}

function bind() {
  $("#search").addEventListener("input", (event) => { state.query = event.target.value; visibleLimit = 30; render(); });
  [["#grade-filter", "grade"], ["#unit-filter", "unit"], ["#achievement-filter", "achievement"], ["#sort-order", "sort"]]
    .forEach(([selector, key]) => $(selector).addEventListener("change", (event) => { state[key] = event.target.value; visibleLimit = 30; render(); }));
  $("#publisher-options").addEventListener("change", () => {
    state.publishers = new Set($$("#publisher-options input:checked").map((input) => input.value));
    visibleLimit = 30;
    render();
  });
  $("#reset-filters").addEventListener("click", resetFilters);
  $("#settings-toggle").addEventListener("click", () => {
    const panel = $("#settings-panel");
    panel.hidden = !panel.hidden;
    $("#settings-toggle").setAttribute("aria-expanded", String(!panel.hidden));
  });
  $("#filter-toggle").addEventListener("click", () => {
    const filters = $("#filters");
    const open = filters.classList.toggle("is-open");
    $("#filter-toggle").setAttribute("aria-expanded", String(open));
  });
  $("#close-dialog").addEventListener("click", () => $("#activity-dialog").close());
  $("#load-more").addEventListener("click", () => { visibleLimit += 30; render(); });
  $("#activity-dialog").addEventListener("click", (event) => {
    if (event.target === $("#activity-dialog")) $("#activity-dialog").close();
  });
  $("#quick-search")?.addEventListener("click", () => {
    $("#search").focus();
    window.scrollTo({ top: $("#filters").offsetTop - 16, behavior: "smooth" });
  });
  $$("#settings-panel input").forEach((input) => input.addEventListener("input", () => {
    const values = $$("#settings-panel input").map((field) => field.value || "—");
    $("#class-summary").textContent = `학급 ${values[0]}개 · 학급당 ${values[1]}명 · 조당 ${values[2]}명`;
  }));
}

async function initialize() {
  await loadSsot();
  updatePublisherCounts();
  fillSelect("#grade-filter", "grade", "전체 학년");
  fillSelect("#unit-filter", "unit", "전체 단원");
  fillSelect("#achievement-filter", "achievement", "전체 성취기준");
  makePublisherFilters();
  bind();
  render();
}

initialize();
