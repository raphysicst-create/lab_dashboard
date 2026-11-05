# 엑셀 검토표 사용·재생성

기존 검토표는 `outputs/review/science_experiment_review.xlsx`입니다. 다른 컴퓨터에서는 이 파일을 Excel에서 열어 작업을 이어갑니다. 원본 `science_experiment_supplies.json`은 읽기 전용으로 사용하며, 검토표 수정 내용은 사이트에 자동 반영되지 않습니다.

저장소 최상위 폴더에서 표준 Python으로 검증할 수 있습니다. 별도 패키지는 필요하지 않습니다.

```sh
python scripts/review/verify-review.py
```

`verify-review.py`는 XLSX 내부 XML에서 원문 3,632셀, 빈 교구 25셀, 초기 검토 상태, 필터, 고정행·고정열, 드롭다운, 실행 가능한 수식이 없음을 확인합니다. 검토 상태 등을 수정한 후에는 최초 생성 상태에 대한 검사 항목이 실패할 수 있습니다. 검토 내용을 초기화하여 검사에 맞추지 않습니다. 결과는 `outputs/review/xlsx-validation.json`에 저장됩니다.

기존 XLSX를 이미지로 확인하려면 다음 선택 의존성을 설치합니다.

```sh
python -m pip install -r requirements.txt
python scripts/review/render-review.py
```

`render-review.py`는 XLSX를 openpyxl로 읽기만 하고 Pillow로 두 시트의 미리보기와 셀 크기 검사를 수행합니다. XLSX를 덮어쓰지 않으며 Microsoft Excel 자체 렌더링을 검증하는 것은 아닙니다. 미리보기와 `render-validation.json`은 `outputs/review/`에 기록됩니다. 한글 글꼴 자동 탐색에 실패하면 `LAB_DASHBOARD_FONT`와 선택적으로 `LAB_DASHBOARD_FONT_BOLD` 환경변수에 글꼴 파일 경로를 지정합니다.

## 최초 상태로 재생성하는 경우만

`build-review.mjs`는 Codex 번들에 제공되는 **`@oai/artifact-tool`** 패키지가 필요합니다. 일반 브라우저·데이터 검증용 `npm install`에는 이 패키지가 포함되지 않습니다. 재생성하려면 해당 패키지가 제공된 Codex 환경에서 Node.js가 패키지를 찾을 수 있도록 구성해야 합니다. 기존 컴퓨터의 `node_modules` junction은 로컬 설치 경로를 가리키므로 GitHub에 포함하거나 다른 컴퓨터에 복사하지 않습니다.

```sh
node scripts/review/build-review.mjs --skip-render
python scripts/review/verify-review.py
python scripts/review/render-review.py
```

기존 검토표가 있으면 생성기가 덮어쓰기를 거부합니다. 검토 내용을 별도로 백업한 뒤 최초 상태로 재생성하려는 경우에만 첫 번째 명령 끝에 `--replace`를 추가합니다. 검토 기록을 새 검토표로 가져오는 기능은 없습니다.

`--skip-render`는 이 작업 환경에서 Artifact Tool의 Windows 렌더러가 Vulkan 초기화 오류를 일으켜 사용했습니다. XLSX 작성·검사·내보내기는 Artifact Tool을 사용하고, 이미지 미리보기는 별도 Python 스크립트로 처리합니다.
