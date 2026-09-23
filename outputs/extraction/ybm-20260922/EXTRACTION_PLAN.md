# YBM K7·K8·K9 탐구활동 추출 계획

작성일 2026-09-22. 이전 지학사 추출과 같은 원문 보존 정책을 적용한다. `gpt-5.6-sol`, reasoning effort `high`의 독립 서브 에이전트 3개가 K7·K8·K9를 한 권씩 동시에 추출하며 주 에이전트가 통합 및 독립 대조를 수행한다.

## 입력과 저장 위치

입력은 `C:/Users/USER/Desktop/maintain/textbook_wiki/raw/`의 `textbook_YBM_K7.pdf`(252쪽), `textbook_YBM_K8.pdf`(328쪽), `textbook_YBM_K9.pdf`(328쪽)다. 원본 및 다른 프로젝트는 읽기 전용이다. K8은 교사용 해설이 포함된 파일임을 사전 확인했다. 각 권은 학생용/교사용 여부와 가시 영역, 인쇄쪽과 PDF쪽 관계를 독립 확인한다.

최종 결과는 이 폴더의 K7, K8, K9 하위에, 중간 텍스트·이미지는 현 프로젝트 `scratchpad/ybm-20260922/<권>/`에 둔다. 기존 454개 JSON, 지학사 추출본, 검토 엑셀, 웹 공개 데이터는 수정하지 않는다.

## 추출 범위와 원칙

1. 전권 텍스트와 좌표를 조사해 제목 있는 독립 학생 수행 활동을 목록화한다. 탐구 실험뿐 아니라 해보기·간이 활동·조사·토의·놀이·제작·프로젝트 및 탐구 방법 익히기도 포함한다.
2. 단순 도입 질문·확인/평가 문항·읽을거리만 있는 지면·목차·정답·책 사용 안내 속 본문 복제와 교사용 대체 활동은 제외하고 판단을 coverage에 기록한다. 진로·읽을거리라도 실제 독립 수행 과제가 있으면 범위를 검토하고 근거를 남긴다.
3. 같은 상위 제목 아래 여러 쪽에 걸친 활동은 한 건으로 묶고 모든 연속 페이지를 출처에 기록한다. 별도 제목과 수행 과제를 가진 단계는 따로 기록하되 series_id로 연결할 수 있다. 여러 부분의 준비물 목록이 있으면 빠짐없이 함께 보존한다.
4. 준비물은 학생 본문에서 명시한 박스·체크리스트·'다음 준비물' 목록만 기록한다. 절차·그림·교사 팁·예시 답안에서 보충하지 않는다. 목록이 없거나 판독 불가하면 null과 사유를 남긴다. 부분 판독만 가능한 항목은 원문 및 불확실성을 별도 source 메모로 보존하고 확정 목록인 것처럼 내놓지 않는다.
5. 단어·괄호·용액/제형·규격·농도·온도·원래 수량을 보존하며 수량 계산이나 약품 추정은 하지 않는다. PDF 추출 줄바꿈 정리는 허용하지만 원문 내용은 바꾸지 않는다.
6. 제목과 모든 명시 준비물 목록은 읽을 수 있는 크기의 렌더 이미지로 대조한다. 특히 다단 편집·연속 지면·기호·폰트 해독 오류는 확대 확인한다. 실제 확인한 페이지와 자동 스캔만 한 페이지를 구분한다. 원문 전체 시각 확인을 하지 않았다면 전수 확인 완료라고 기록하지 않는다.
7. 성취기준은 원문에 직접 명시되고 활동과의 연결이 확인되는 경우만 기입한다. 학습목표나 단원 전체 성취기준을 개별 활동의 기준으로 임의 변환하지 않는다.
8. 교과서 원래 단원명·번호를 보존한다. K7/8/9 grade는 각각 1/2/3이다. 기존 웹사이트 단원-학년 매핑을 적용하지 않는다.

## 공통 스키마 및 권별 산출물

파일명: `science_experiment_supplies_YBM_K7.json`(K8/K9 동일 규칙).

최상위 `metadata`, `data`, `views`.

- metadata: schema_version, source_file, sha256(또는 source_sha256), book_id(`YBM_K7`), grade(1), pdf_page_count, record_count, source_document_type, extraction_policy, notes.
- 각 data: `id`(`ybm_k7_0001` 형식), `source_row:null`, `단원명`, `성취기준`(문자열 또는 null), `출판사:"YBM"`, `쪽`(인쇄쪽 int 또는 null), `탐구활동`(원문 제목), `교구`(원문 목록 string 또는 null), `source`.
- source: book_id(`YBM_K7`), pdf_pages(1부터 시작하는 파일쪽 정수 배열), printed_pages(인쇄쪽 정수 배열), activity_type(원문 라벨), chapter_label(원문 단원 번호), title_quote, supplies_quote(또는 null), standard_quote(또는 null), review_notes(배열). 추가 근거·series_id·부분별 준비물 등 허용.
- views.기본자료: record_count, record_ids(전체 data 순서와 동일).

`coverage.json`: pdf_page_count, source_file, sha256, criteria, methods, visual_reviewed_pages(실제로 본 파일쪽 정수 배열), remaining_ambiguities, pages(전체 PDF 페이지 순서).

각 pages 항목: pdf_page, printed_page(또는 null), category, record_ids(해당 지면이 출처인 레코드 전부), activity_candidates([{title, decision, reason, record_id 또는 null}]), visual_review({reviewed, scope}). 본문 아닌 쪽도 전부 분류한다.

`extraction_report.md`: 방법, 활동/단원별 건수, null 사유, 쪽 매핑, 실제 시각 검토 범위, 남은 한계를 적는다. 모든 원본 파일 SHA-256을 기록하고 끝에 확인한다.

## 검증과 인계

각 에이전트는 JSON 구조·ID 중복·쪽 범위·근거·views·coverage 연결을 자체 검사한다. 특히 전권 제목 목록을 다시 읽어 오독을 확인하고 모든 준비물 페이지의 처음과 끝 항목/다음 쪽 계속 여부를 대조한다.

주 에이전트가 세 권의 구조와 원본 해시, 908쪽 coverage 연결을 검증하고 고위험 원문 표본의 제목·준비물을 별도로 대조한다. 오류를 고친 뒤 최종 통합 JSON·종합 보고서·검증 결과를 만든다. 원본 454개·지학사 자료에 자동 합치거나 사이트 배포하지 않는다.

## 실행 환경

현 Windows `python -X utf8`에 PyMuPDF(`fitz`)와 pypdf가 설치되어 있다. UTF-8 출력 사용. `fitz.Page.get_text(clip=page.rect)`로 가시 영역을 확인하고 get_pixmap으로 렌더 가능하다. PDF 스킬: `C:/Users/USER/.codex/plugins/cache/openai-primary-runtime/pdf/26.905.11957/skills/pdf/SKILL.md`. 이번 작업은 PDF를 생성·수정하지 않는 JSON 추출이다. 원본은 수백 MB이므로 불필요한 복사/전체 read_bytes 반복 대신 스트리밍 해시를 권장한다.

이전 실패 사례: 준비물 '드라이어'를 '드라이아이스'로 오독, 제목의 고유명사/동사 오독, 긴 목록 끝 기구 누락, 탐구 익히기 누락, 교사용 대체 실험과 혼입, 연속 페이지 누락. 이 항목들을 집중 확인한다.
