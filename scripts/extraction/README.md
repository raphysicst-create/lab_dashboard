# 교과서 활동 추출 검증

## 고등학교 통합과학 1·2 (5개 출판사)

`verify_integrated_science.py`는 미래엔·지학사·천재교과서·비상교육·동아출판 10권의 추출 결과를 검사하고 별도 통합 JSON을 생성합니다. Python과 PyMuPDF(`fitz`)가 필요합니다.

2026-09-23 후속 요청에 따라 두 권 모두 고1로 지정하고 교과서 성취기준 표의 31개 기준을 활동에 연결했습니다. `achievement_mapping/`의 검토된 연결안과 코드 목록을 사용하며, 키워드 자동 분류가 아닙니다. 복수 기준, 직접 지정/내용 대조/미확인, 부분·권간 연결의 한계를 기록합니다. 최초 추출본은 같은 폴더의 `before_mapping/`에 보존합니다.

```powershell
python -X utf8 scripts/extraction/map_integrated_achievements.py --check
```

위 검사는 코드, 근거 쪽, PDF 인용문(명시한 생략 부호로 나눈 각 발췌 포함), 이미지 전사 예외, 원활동·준비물 보존을 확인합니다. `--check` 없이 실행하면 검토된 연결안을 권별 JSON에 적용합니다. 이후 아래 검증·통합 명령을 실행합니다. 출판사별 초기 추출 스크립트를 다시 실행하면 후속 연결이 사라질 수 있으므로 이 두 단계를 다시 수행해야 합니다.

```powershell
python -X utf8 scripts/extraction/verify_integrated_science.py
```

입력과 결과는 `outputs/extraction/integrated-science-20260923/` 아래에 있습니다. `--source-dir`으로 원본 PDF 폴더를, `--output`으로 결과 폴더를 지정할 수 있습니다. 원본 PDF SHA-256와 실제 쪽수, 필수 열·null·중복 ID·쪽 범위, 전쪽 coverage와 양방향 활동 참조, 기록된 이미지 확인 범위, 독립 이미지 표본, 성취기준 근거 쪽을 검사합니다. 기존 원자료 JSON·검토 엑셀·중학교 통합본도 기준 해시와 비교합니다.

통과 시 `science_experiment_supplies_integrated_science.json`을 생성하며 결과는 `validation.json`에 기록합니다. 실패하면 기존 통합본은 그대로 남을 수 있으므로 최신 검증 상태를 확인해야 합니다. 준비물은 학생 본문에 명시된 목록만 보존하고 미기재는 `null`로 둡니다. 통합과학 1·2는 권수이며 학년을 뜻하지 않습니다. 이 도구는 원문 의미·모든 픽셀을 자동 검증하거나 활동을 자동 판별하는 추출기가 아닙니다. 실제 이미지 대조와 제외 범위는 권별 보고서 및 `parent_review/`에 기록합니다. 기존 사이트 데이터 생성 입력은 변경하지 않습니다.

## 지학사 K7·K8

`verify_jihaksa.py`는 두 에이전트가 작성한 지학사 K7·K8 JSON을 검사하고 통합합니다. PDF에서 활동을 자동 판별하는 추출기는 아닙니다. 제목·준비물·본문 범위 판정에는 원본 이미지 검토가 필요합니다.

프로젝트 루트에서 실행합니다. Python 표준 라이브러리만 사용합니다.

```powershell
python -X utf8 scripts/extraction/verify_jihaksa.py
```

다른 컴퓨터에서는 원본 PDF 폴더를 지정합니다.

```powershell
python -X utf8 scripts/extraction/verify_jihaksa.py --source-dir 'C:/path/to/textbook_wiki/raw'
```

입력은 `outputs/extraction/jihaksa-20260922/K7/` 및 `K8/`의 추출 JSON과 `coverage.json`, 그리고 각 원본 PDF입니다. 검사 대상은 필수 열, 값의 타입, 미확인 값의 null 처리, ID 중복, 페이지 범위, 출처 해시, 뷰 참조, 근거 문자열 존재, 의심스러운 글꼴 해독 문자입니다.

성공하면 상위 결과 폴더의 `science_experiment_supplies_jihaksa.json` 및 `validation.json`을 갱신합니다. 실패하면 `validation.json`을 기록하고 비정상 종료하며 통합본을 생성하지 않습니다. 과거 통합본이 있으면 그대로 남으므로 항상 `validation.json`의 최신 상태를 확인해야 합니다.

원래의 454개 활동 JSON, 검토용 엑셀, 웹 공개 데이터는 수정하지 않습니다. 구조 검증 통과는 원문 전체의 전수 시각 검증이나 활동별 성취기준 매핑 완료를 의미하지 않습니다. 추출 방법과 실제 확인 범위는 결과 폴더의 계획서와 권별 보고서를 참고하세요.

## YBM K7·K8·K9

`verify_ybm.py`는 같은 방식으로 세 권의 추출 결과를 검사하고 통합합니다.

```powershell
python -X utf8 scripts/extraction/verify_ybm.py
```

입력과 결과는 `outputs/extraction/ybm-20260922/` 아래에 있습니다. `--source-dir`과 `--output`으로 경로를 바꿀 수 있습니다. 각 원본 PDF의 SHA-256, 페이지별 포함 기록, 학년·ID·근거 필드와 독립 이미지 대조 표본을 검사합니다. `baseline.json`의 기존 원자료 및 지학사 통합본 해시도 비교합니다. 성공하면 `science_experiment_supplies_YBM.json`을 만들고, 통과 여부와 검사 결과는 `validation.json`에 기록합니다. 실패 시 기존 통합본이 남을 수 있으므로 최신 검증 상태를 확인하세요.

## 전체 통합 및 준비물 분류

`combine_all.py`는 원자료·지학사·YBM을 합칩니다. 이미 준비물 분류가 추가된 통합본은 덮어쓰지 않도록 중단합니다.

`classify_supplies.py`는 `outputs/extraction/combined-20260922/`의 통합 JSON에 `실험 기자재`, `실험 준비물`, `분류 보류`, `준비물 분류` 필드를 추가합니다. `교구`와 기존 모든 행 필드는 보존합니다. 최초 분류 전 파일은 `science_experiment_supplies_combined.unclassified.json`에 바이트 단위로 백업하며, 재실행 때 기존 원문이 변경되었으면 중단합니다.

```powershell
python -X utf8 scripts/extraction/classify_supplies.py
```

애매한 항목은 `classification_review_groups.md`의 유형별 요약과 `classification_review.md`의 전수 목록에서 검토합니다. 사용자 결정을 `classification_decisions.json`의 해당 항목 ID에 `category: "실험 기자재"` 또는 `category: "실험 준비물"`로 입력하고 재실행하면 반영됩니다. 결정하지 않은 값은 null을 유지합니다. 활동마다 다른 분류가 필요한 경우에는 일괄 결정하지 않고 별도로 처리해야 합니다.

분류는 약품규정 목록 일치 여부와 무관합니다. `classification_decisions.json`의 사용자 결정을 기본 규칙보다 우선합니다. 2026-09-23 결정에 따라 부록 표기·프로그램 등은 기자재, 지정한 종이·제작 재료 등은 준비물로 확정했습니다. 적용 내역과 변경 직전 자료는 결과 폴더의 `decision_history/20260923/`에 보존했습니다. 아직 결정하지 않은 항목만 보류 목록에 남습니다. 원문 항목 경계, 누락·중복, 분류별 원문 보존, 103개 null, 세 입력 파일의 해시를 검사한 결과는 `classification_validation.json`에 저장합니다. `validation.json`은 현재 통합본을, `merge_validation_unclassified.json`은 분류 전 통합본을 대상으로 한 기록입니다.
