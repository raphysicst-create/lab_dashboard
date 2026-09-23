# 통합과학 1·2, 5개 출판사 활동 추출

사용자 요청(2026-09-23): textbook_wiki에 추가한 미래엔(오현선), 지학사(전상학), 천재교과서(신영준), 비상교육(심규철), 동아출판(김호련)의 통합과학 1·2에서 기존 방식으로 탐구·해보기 활동과 준비물을 JSON으로 추출한다.

## 범위와 원칙

- 원본은 `C:/Users/USER/Desktop/maintain/textbook_wiki/raw/`에서 읽기만 한다. 위키·원본·기존 중학교 데이터·검토표·사이트 파일은 수정하지 않는다.
- 학생 본문의 제목 있는 탐구·해보기·실험·조사·토론·프로젝트 등 독립 수행 활동을 포함한다. 단순 도입 질문, 확인 문제, 평가, 읽을거리, 정답, 교사용 수업 예시, 목차 재등장은 제외한다. 출판사별 실제 활동 유형을 그대로 기록한다.
- 연속 지면의 한 활동은 한 레코드로 합치고 모든 근거 PDF 쪽을 기록한다. 같은 대제목 아래 탐구 1·2는 원칙적으로 한 활동으로 보존한다. 제목 있는 독립 활동은 분리한다.
- `단원명`, `성취기준`, `출판사`, `쪽`, `탐구활동`, `교구`와 `id`, `source_row`를 유지한다. `source_row`는 null. 추가로 `교과서`, `대표저자`, `source`를 둔다.
- `교구`에는 명시된 학생 활동 준비물 목록만 옮긴다. 절차·삽화·교사용 예시에서 추정하지 않는다. 목록이 없거나 판독되지 않으면 null. 판독 불능과 목록 없음은 review_notes에서 구분한다. 농도·규격·수량·중복 표현을 원문대로 보존한다.
- 활동별 직접 연결 근거가 없는 성취기준은 null. 중학교 단원/학년 매핑을 적용하지 않는다. 통합과학 1·2는 책 구분이며 학년으로 환산하지 않는다.
- 모든 PDF 페이지를 텍스트·좌표로 조사하고 활동 후보와 준비물 지면을 이미지로 대조한다. 깨진 글꼴, 다단 배치, 교사 주석 혼입, 제목/목록 경계는 이미지로 확인한다. 확인한 이미지 쪽만 visual_reviewed_pages에 기록한다.

## 권별 산출물 계약

출판사 폴더(`miraen`, `jihaksa`, `chunjae`, `visang`, `donga`) 아래 `IS1`, `IS2`에 각각:

1. `activities.json`: `{metadata, data}`. metadata는 book_id(`<publisher>_IS1` 등), publisher, author, title, volume(1/2), school_level(`고등학교`), grade(null), source_file(절대경로), sha256, pdf_page_count, record_count, extraction_policy, notes.
2. `coverage.json`: `{book_id,pdf_page_count,visual_reviewed_pages, pages:[{pdf_page,printed_page,record_ids,decision,reason}]}`. PDF 전쪽 1회씩. decision은 included/continuation/excluded. 인쇄 쪽 미확인은 null.
3. `extraction_report.md`: 포함/제외 기준, 건수, 준비물 null, 인쇄/PDF 쪽 관계, 확인한 이미지, 한계와 수동 교정 내역.

레코드 source 필수: book_id, pdf_pages(1-based 정수 배열), printed_pages(확인된 정수 배열), activity_type, title_quote, supplies_quote(null 허용), standard_quote(null 허용), review_notes(배열). 가능하면 title_bbox, supplies_bbox 또는 evidence를 기록해 근거 위치를 보존한다. `쪽`은 시작 인쇄 쪽이며 미확인은 null. `탐구활동`은 임의 요약하지 않은 원제목이다.

준비물 목록과 제목의 줄바꿈은 가능한 보존한다. 검색 편의를 위한 공백 정리는 원문 근거 필드와 함께 보관한다. 프로그램의 자동 추출은 후보/초안이며 자동 문자열 규칙만으로 최종 포함 판단을 대신하지 않는다.

작업용 텍스트/이미지/스크립트는 해당 출판사 폴더의 scratch에만 둔다. 최종 통합/검증은 주 에이전트가 담당한다. 기존 파일은 덮어쓰지 않는다.

## 최종 검증

10권 식별, 원본 SHA-256, JSON 타입/필수값/ID 유일성, 쪽 범위, coverage 전쪽 포함 및 양방향 record 연결, 명시 준비물 근거, 누락/중복 후보를 확인한다. 주 에이전트가 출판사별 별도 원문 표본을 이미지로 검토한다. 기계 검증은 원문 모든 픽셀의 전수 판독을 뜻하지 않는다.

## 후속 사용자 지정 (2026-09-23)

최초 추출 이후 두 권 모두 고1로 지정하고 textbook_wiki 원본의 성취기준을 대조하여 연결했다. 최종 범위·연결 방식·미확인 항목은 `achievement_mapping/README.md`를 따른다.
