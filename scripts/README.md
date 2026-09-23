# 다른 컴퓨터에서 실행하기

아래 명령은 저장소 최상위 폴더에서 실행합니다. 원자료와 작업용 파일은 최상위 폴더에 있고, 실제 웹사이트는 `site/dist/`입니다. 사이트 자체는 HTML·CSS·JavaScript·JSON만 사용하며 설치나 빌드가 필요하지 않습니다.

Python 3.10 이상과 Node.js 22 이상을 사용합니다. 이번 작업에서 사용한 버전은 Python 3.12.14, Node.js 24.19.0입니다. Windows에서 `python` 대신 `py -3`를 사용할 수도 있습니다.

## 사이트 열기

```sh
python -m http.server 4173 --directory site/dist
```

브라우저에서 `http://127.0.0.1:4173/`를 엽니다. JSON을 불러오므로 HTML 파일을 직접 더블클릭하는 방식은 사용하지 않습니다. 교과서 출판사 선택은 브라우저의 localStorage에 저장되므로 GitHub 커밋에 포함되지 않습니다. 다른 컴퓨터에서는 해당 설정을 다시 입력합니다.

## 원자료에서 데이터 재생성·검증

추가 Python 패키지 없이 실행할 수 있습니다.

```sh
python scripts/build_data.py
python scripts/verify_chemicals.py
node scripts/verify_core.mjs
```

`build_data.py`는 `outputs/extraction/combined-20260922/science_experiment_supplies_combined.json`과 `output/parsed/`의 약품 MD·JSON을 읽어 `site/dist/data/`의 데이터를 다시 만듭니다. 원자료를 수정하지 않으며, 검토 상태와 변환 보고서는 `output/validation/`에 기록합니다. 수동으로 수정한 생성 데이터는 재생성하면 덮어써지므로 원자료·변환 규칙 변경을 먼저 검토합니다. 원문에 없는 실험·약품 정보는 추가하지 않습니다.

통합 JSON에는 조사한 공식 성취기준 87개와 활동별 연결이 포함됩니다. 최초 적용 도구는 `scripts/extraction/apply_achievement_standards.py`이며, 적용 전 통합본을 보존하고 후속 수정이 있으면 덮어쓰지 않습니다. 현재 상태는 `python scripts/verify_achievement_application.py`로 검증합니다. 조사 생성기와 이전 준비물 분류 생성기는 이미 적용된 성취기준을 덮어쓰지 않도록 중단합니다.

`build_chemicals.py`를 단독 실행하면 약품 변환 보고서를 재작성합니다. 전체 사이트 데이터를 함께 갱신할 때는 `build_data.py`를 사용합니다.

## 브라우저 기능 검증

처음 한 번 테스트 도구와 Chromium을 설치합니다. 런타임 의존성은 웹사이트에 포함되지 않습니다.

```sh
npm install
npx playwright install chromium
```

Linux에서 브라우저 운영체제 라이브러리가 부족하면 Playwright의 운영체제 의존성도 설치해야 합니다. 사이트 서버가 실행된 상태에서 다른 터미널로 다음을 실행합니다.

```sh
npm test
npm run test:browser
npm run test:chemicals
node scripts/verify_cabinets.cjs
```

기본 주소는 `http://127.0.0.1:4173/`입니다. 필요하면 `LAB_DASHBOARD_TEST_BASE_URL` 환경변수로 바꿉니다. 기본 Chromium 대신 설치된 Edge를 사용하려면 `LAB_DASHBOARD_BROWSER_CHANNEL=msedge`로 설정합니다. `LAB_DASHBOARD_TEST_OUTPUT`은 화면 캡처·보고서 출력 폴더를 바꿉니다. PowerShell 예시는 다음과 같습니다.

```powershell
$env:LAB_DASHBOARD_BROWSER_CHANNEL = 'msedge'
npm run test:browser
Remove-Item Env:LAB_DASHBOARD_BROWSER_CHANNEL
```

기본 출력 위치는 일반 검증 `output/validation/`, 약품 검증 `output/validation/chemicals/browser/`입니다. 기존 보고서를 보존하려면 별도 출력 폴더를 지정합니다.

## 배포 파일 묶기

```sh
python scripts/package_github_pages.py
```

`outputs/github-pages/science-classroom-prep-github-pages.zip`은 웹사이트만 포함하는 배포 묶음입니다. 원자료·검토표를 포함한 전체 작업 백업은 GitHub 저장소 전체를 사용합니다. 이 명령 자체는 GitHub로 전송하거나 배포하지 않습니다.

## 엑셀 검토표

기존 파일은 `outputs/review/science_experiment_review.xlsx`이며 Excel에서 바로 열 수 있습니다. 추가 패키지 없이 원문 보존 상태를 확인할 수 있습니다.

```sh
python scripts/review/verify-review.py
```

기존 XLSX의 이미지 미리보기를 만들 때만 다음 선택 의존성이 필요합니다.

```sh
python -m pip install -r requirements.txt
python scripts/review/render-review.py
```

미리보기에는 한글 글꼴이 필요합니다. Windows 맑은 고딕, macOS Apple SD Gothic Neo, Linux Noto Sans CJK 또는 나눔고딕의 알려진 경로를 탐색합니다. 찾지 못하면 `LAB_DASHBOARD_FONT`에 설치된 한글 글꼴 파일 경로를 지정하고, 필요하면 `LAB_DASHBOARD_FONT_BOLD`도 지정합니다. 미리보기는 기존 XLSX를 수정하지 않습니다.

**검토표 최초 생성기 `build-review.mjs`만 Codex 제공 `@oai/artifact-tool`에 의존합니다.** 이 패키지는 일반 `npm install`에 포함하지 않았습니다. 패키지가 제공된 Codex 환경에서만 재생성할 수 있으며, 일반 컴퓨터에서는 커밋된 XLSX를 그대로 사용합니다. 자세한 내용은 [검토표 안내](review/README.md)를 참고하세요.

## 고1 통합과학 통합 (2026-09-23)

현재 입력은 같은 경로의 1,276행 통합 JSON입니다(후속 부록 제외 적용). `extraction/apply_integrated_science.py`는 중학교 사본을 보존하고 검증된 고1 415개를 추가합니다. 후속 편집이 있으면 재적용을 중단합니다. `build_data.py`는 복수 성취기준과 중1/고1 구분을 공개 데이터에 반영합니다. 고1 준비물도 후속 분류 적용으로 기자재·준비물 두 영역에 표시합니다.

현재 전체 검증: `python scripts/verify_integrated_application.py`, `node scripts/verify_core.mjs`, `node scripts/verify_browser.cjs`, `python scripts/verify_chemicals.py`. 기존 `verify_achievement_application.py`는 중학교 862행 적용 시점 전용 검증이며, 후속 추가 자료가 있는 현재 입력에는 사용하지 않습니다.

## 단원명 정규화

`scripts/extraction/normalize_units.py`는 적용 전 1,277행을 보존하고 교과서의 실제 대단원명·학교급·권수를 기준으로 번호와 단원명을 맞춥니다. 학년이나 성취기준 연결로 소속을 재분배하지 않습니다. 원문 단원명과 소단원 정보는 `단원명 원문`에 그대로 있습니다. 적용 후 `build_data.py`를 실행하며 `verify_integrated_application.py`와 기존 통합/브라우저 검증으로 대조합니다.

## 고1 준비물 분류

`python scripts/extraction/classify_integrated_supplies.py`는 검토한 3개 manifest의 원문 범위와 기존 동일 품목 결정을 검사한 후 고1 분류만 적용합니다. 변경 전 사본을 보존하며 후속 편집이 있으면 덮어쓰기를 중단합니다. 기존 중학교 분류 카탈로그와 원본 추출본은 갱신하지 않습니다. 이어서 `build_data.py`를 실행합니다. 전체 적용 검증은 `verify_integrated_application.py`, 검색 검증은 `verify_core.mjs`, 화면 검증은 `verify_browser.cjs`입니다.

## 출판사 표기 통일

`python scripts/extraction/normalize_publishers.py`는 사용자 지정 3개 별칭만 통일하고 이전 출판사 값을 `출판사 원문` 및 적용 전 사본에 보존합니다. 천재 관련 3개 표기는 변경하지 않습니다. 적용 후 `build_data.py`와 `verify_integrated_application.py`, `verify_core.mjs`, `verify_browser.cjs`로 데이터 보존·별칭 선택 이관·화면을 확인합니다. 후속 변경이 있으면 생성기는 덮어쓰기를 중단합니다.
