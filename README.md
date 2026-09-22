# 중학교 과학 수업 준비

HTML, CSS, JavaScript와 JSON으로 구성한 정적 웹사이트입니다. 실행 시 서버 데이터베이스, 사용자 로그인, 별도 API를 사용하지 않습니다.

새 컴퓨터에서는 아래의 복제·실행 절차를 사용하세요. 현재 결정 사항과 미완료 작업은 [WORKSPACE_STATUS.md](WORKSPACE_STATUS.md), 최초 계획서는 [docs/initial-plan.md](docs/initial-plan.md)에 보존했습니다. 최초 계획서보다 이후 사용자 결정 사항을 우선합니다.

## 구성

- `site/dist/index.html`: 화면 구조
- `site/dist/style.css`: 디자인과 반응형 레이아웃
- `site/dist/app.js`: 검색, 화면 표시, 브라우저 설정 저장
- `site/dist/core.js`: 검색·출판사 선택 처리
- `site/dist/chemical-diagrams.js`: 개별 약품 보관장 강조와 공통 폐수 분류 그림
- `site/dist/data/`: 공개할 데이터만 저장
- `scripts/build_data.py`: 원본 JSON에서 공개 데이터와 비공개 검증 기록 생성
- `outputs/review/science_experiment_review.xlsx`: 원문 대조와 수정을 위한 엑셀 검토표
- `output/validation/`: 내부 검증 기록, 테스트 결과, 화면 캡처

## 현재 구현

454개 활동의 단원·성취기준 원문·출판사 필터, 활동명과 준비물 원문 검색, 활동 상세를 제공합니다. 약품 관리 목록에서는 약품명·화학식으로 약품을 찾을 수 있습니다. 출판사 선택은 같은 사이트 주소의 같은 브라우저에 저장됩니다. 사이트 데이터 삭제, 브라우저 변경, PC 변경 시 공유·복원되지 않습니다. 설정은 서버로 전송하지 않습니다.

학교별 계정·재고관리·서버 저장은 없습니다. 로컬 미리보기와 공개 사이트는 주소가 다르므로 설정을 공유하지 않습니다.

약품 상세 177개에 보관장 그림을 표시합니다. 기존 보관장 자료가 있는 48개는 해당 분류를 강조하고, 나머지 129개는 모든 칸을 회색으로 표시하며 미확인을 유지합니다. 공통 관리 안내에는 전체 보관장 그림과 폐수 분류 순서도가 있습니다.

## 데이터 원칙

1. `science_experiment_supplies.json` 원본은 변경하지 않습니다. 원본 454행의 8개 열(추적용 2열 포함)을 공개 데이터와 전수 대조했습니다.
2. 원자료 변환만 완료된 상태입니다. 교과서 대조 상태는 작업용 엑셀과 `output/validation/verification.json`에만 기록합니다. 전체 작업을 옮기기 위해 해당 파일들도 이 GitHub 저장소에 보존하지만, 사이트 배포 대상인 `site/dist`에는 넣지 않습니다.
3. 미확인 값은 `null`로 보존하고 화면에서는 ‘미확인’으로 표시합니다. 자료 없음과 준비물이 필요 없다는 의미를 혼동하지 않습니다.
4. 학년은 사용자가 지정한 기준(1~8단원=1학년, 9~15단원=2학년)을 적용합니다. 단원 번호와 성취기준의 1-1, 1-2 등의 순서는 원문에서 읽어 연결하며 필터를 숫자순으로 표시합니다. 공식 성취기준 코드·교과서명·판본은 확인되지 않았으므로 연결하지 않았습니다. `ACH-*`, `TXT-*`는 현재 원자료의 표현을 연결하기 위한 내부 ID이며 공식 코드나 확인된 판본 ID가 아닙니다.
5. 준비물 원문을 그대로 보존합니다. 약품 연결은 괄호 밖 쉼표로 나눈 전체 항목이 제공 자료의 명칭 또는 명시된 다른 이름과 일치할 때만 수행합니다. 공백 및 Unicode 표기만 정규화하며 농도·용액·혼합물·기구의 일부 문자열로 동일 물질을 추정하지 않습니다. 미연결 항목은 약품이 없다는 뜻이 아닙니다.
6. `chemicals.json`은 제공된 약품 규정 MD/JSON의 분류·보관장·보관 방법·분리 보관 대상을 문서와 인쇄면 근거와 함께 저장합니다. `materials.json`은 명칭이 확인된 약품의 활동 연결 및 원문을 보존합니다. `chemical_guidelines.json`에는 공통 관리 안내 6개를 별도로 둡니다. 개별 GHS 그림문자와 폐기 방법은 자료에 직접 지정되지 않아 `null`입니다. 분류는 제공 문서의 표현이며 현행 법정 분류로 재해석하지 않습니다. 페놀프탈레인 용액의 상충된 보관장 기재는 미확인으로 두고 내부 검토 기록에 남깁니다. `quantities.json`은 빈 배열이며 규격·농도·온도를 수량으로 해석하지 않습니다.
7. 준비 수량·교과서 수량·설정에 따른 수량 표시와 학급 설정·수량 계산 기능은 사용자 요청으로 제거했습니다. 준비물 원문은 그대로 보존하며 웹사이트에서 수량 데이터를 불러오지 않습니다.

## 실행과 업데이트

프로젝트 루트에서 Python으로 정적 파일 서버를 실행할 수 있습니다.

```powershell
python -m http.server 4173 --bind 127.0.0.1 --directory site/dist
```

브라우저에서 `http://127.0.0.1:4173/`에 접속합니다. `index.html`을 파일로 직접 여는 방식은 JSON 요청 때문에 지원하지 않습니다.

```powershell
python scripts/build_data.py
node scripts/verify_core.mjs
node scripts/verify_browser.cjs
python scripts/verify_chemicals.py
node scripts/verify_chemicals.cjs
```

검증 도구 설치와 실행 방법은 [scripts/README.md](scripts/README.md)에 있습니다. 브라우저 검증 전에 정적 서버가 켜져 있어야 합니다. 사이트 자체에는 Node나 Python 설치가 필요하지 않습니다.

엑셀 수정은 사이트에 자동 반영되지 않습니다. 검토표의 원문 열을 보존한 상태에서 수정 제안·근거·검토 결과를 기록하고, 반영할 항목을 결정한 다음 데이터 갱신 및 배포를 수행합니다. 자세한 엑셀 재생성 방법은 `scripts/review/README.md`를 참고하세요. 기존 검토표는 기본적으로 덮어쓰지 않습니다.

`build_data.py`는 최초 원자료 기준으로 공개 JSON을 재생성하므로, 이후 검토로 추가한 데이터가 있으면 기존 파일을 백업하고 변환기를 먼저 갱신해야 합니다.

`scripts/build_chemicals.py`가 약품 자료를 변환합니다. 전체 준비물 항목과 명칭이 일치하지 않은 항목, 원문 내부 충돌 등은 `output/validation/chemicals/chemical-conversion-report.json`에서 검토합니다. 실험 준비물 원문, 수량, 교과서 대조 상태를 약품 자료로 추정·변경하지 않습니다.

## 공개 범위

배포되는 웹 파일은 `site/dist`뿐입니다. 원자료 JSON, 약품 규정 PDF, 파싱 자료, 검토용 엑셀, 검증 기록, 테스트와 화면 캡처는 저장소에 보존하고 Pages 웹사이트에는 배포하지 않습니다. 현재 저장소는 공개 상태이므로 이 자료들은 GitHub에서 열람할 수 있습니다. 화면과 CSS는 분리되어 있어 데이터·기능을 유지하면서 디자인을 바꿀 수 있습니다.

## 새 컴퓨터에서 이어서 작업하기

```sh
git clone https://github.com/raphysicst-create/lab_dashboard.git
cd lab_dashboard
python -m http.server 4173 --bind 127.0.0.1 --directory site/dist
```

브라우저에서 `http://127.0.0.1:4173/`을 엽니다. Python 명령이 `python3`인 환경에서는 위 명령의 `python`을 `python3`으로 바꿉니다. 미리보기에는 Python만 필요하고 사이트는 브라우저에서 실행됩니다. 검증·재생성용 의존성은 [scripts/README.md](scripts/README.md)를 따릅니다.

GitHub의 **Code → Download ZIP**으로 받아도 같은 파일을 복원할 수 있습니다. 변경을 계속 커밋하려면 `git clone` 방식이 편리합니다. Codex 등 편집기에서 복제한 저장소 루트를 열고 `WORKSPACE_STATUS.md`를 먼저 읽으면 됩니다. 브라우저에만 저장된 출판사 선택과 Codex 대화 이력 자체는 Git 저장소에 포함되지 않습니다.

## GitHub Pages 배포

전체 작업 저장소의 배포 설정은 루트 `.github/workflows/deploy-pages.yml`입니다. `main`의 `site/dist/**` 또는 해당 워크플로를 변경하면 **`site/dist`만** 게시합니다. 저장소 Settings → Pages의 Source는 GitHub Actions입니다.

- 저장소: https://github.com/raphysicst-create/lab_dashboard
- 공개 사이트: https://raphysicst-create.github.io/lab_dashboard/
- 현재 배포 장애 및 마지막 확인 상태: [WORKSPACE_STATUS.md](WORKSPACE_STATUS.md)

`site/.github/workflows/deploy-pages.yml`과 `site/README.md`는 공개 파일만 담는 별도 배포용 ZIP의 템플릿입니다. 전체 저장소의 실제 워크플로는 루트 `.github`에 있는 파일입니다.

```sh
python scripts/package_github_pages.py
```

이 명령은 `outputs/github-pages/science-classroom-prep-github-pages.zip`을 만듭니다. 이 ZIP은 원자료가 없는 **사이트 전용 배포본**이므로 작업 전체 백업용으로 쓰지 마세요. 전체 작업은 이 저장소를 clone하거나 GitHub의 Download ZIP으로 받습니다.

프로젝트 하위 주소에서 브라우저 검증을 실행하려면 `LAB_DASHBOARD_TEST_BASE_URL` 환경변수를 지정합니다. 일반 브라우저 검증 결과 폴더는 `LAB_DASHBOARD_TEST_OUTPUT`으로 바꿀 수 있습니다.

## 백업 범위

원자료 JSON과 약품 PDF 2개, 약품 파싱 MD·JSON, 최초 계획서, 공개 사이트 코드·데이터, 변환·검증·패키징 스크립트, 스키마, 검토 엑셀과 미리보기, 검증 기록, 디자인 문서와 비교 시안을 보존합니다.

`tmp/`, `scratchpad/`, 런타임·패키지 캐시, 기존 중첩 `.git` 이력, 과거 Sites의 `.openai` 연결 설정은 제외합니다. 이전 로컬 `site/.git`은 별도 Sites 이력이므로 새 PC에서는 GitHub clone으로 시작합니다. 파일 목록과 무결성 검증은 `docs/workspace-backup-manifest.json`을 참고하세요.
