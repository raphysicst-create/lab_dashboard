# 중학교 과학 수업 준비

HTML, CSS, JavaScript와 JSON으로 동작하는 정적 사이트입니다. 별도 서버, 데이터베이스, 빌드 도구를 설치하지 않고 GitHub Pages로 배포할 수 있습니다.

## GitHub Pages에 배포하기

1. GitHub에서 저장소를 만들고 기본 브랜치를 `main`으로 사용합니다.
2. 배포용 ZIP의 압축을 풀어 **내부 파일과 폴더를 저장소 최상위**에 올립니다. ZIP 파일 자체나 `site` 폴더 한 겹을 추가해서 올리지 않습니다.
3. `.github/workflows/deploy-pages.yml`이 포함되었는지 확인합니다. 점으로 시작하는 폴더가 파일 선택 화면에서 숨겨질 수 있습니다.
4. 저장소의 **Settings → Pages → Build and deployment → Source**에서 **GitHub Actions**를 선택합니다.
5. **Actions → Deploy to GitHub Pages → Run workflow → main → Run workflow**로 최초 배포를 실행합니다. Pages 설정 전에 시작된 실행이 실패했다면 설정 후 다시 실행하면 됩니다.
6. 실행이 성공하면 배포 결과 또는 **Settings → Pages**에 표시된 주소로 접속합니다. 일반적인 프로젝트 주소 형식은 `https://계정명.github.io/저장소이름/`입니다.

이후 `dist`의 HTML·CSS·JavaScript·JSON 파일을 수정하여 `main`에 올리면 자동으로 다시 배포합니다. `main` 이외의 기본 브랜치를 사용하는 경우 배포 설정의 `branches`도 해당 브랜치로 변경합니다.

GitHub Free에서는 공개 저장소에 Pages를 사용할 수 있습니다. 비공개 저장소 사용 가능 여부는 GitHub 요금제에 따라 다릅니다. 별도의 개인 액세스 토큰을 저장할 필요는 없습니다.

### 저장소 구조

```text
.github/
  workflows/
    deploy-pages.yml
.gitignore
README.md
dist/
  index.html
  style.css
  app.js
  core.js
  data/
    achievements.json
    activities.json
    textbooks.json
    materials.json
    quantities.json
    chemicals.json
    sources.json
```

웹사이트로 배포되는 것은 `dist` 폴더의 내용입니다. 워크플로와 README는 웹 화면에 포함되지 않습니다.

## 설정 저장

출판사, 학급 수, 학급당 학생 수, 조당 학생 수는 브라우저에 자동 저장됩니다. 같은 브라우저에서 같은 사이트 주소로 다시 접속하면 유지됩니다.

기존 사이트와 GitHub Pages는 도메인이 다르므로 기존 브라우저 설정이 자동으로 옮겨지지 않습니다. GitHub Pages에서 처음 한 번 설정하면 이후 유지됩니다. 브라우저의 사이트 데이터를 지우면 설정이 초기화됩니다.

## 로컬 실행

Python이 설치되어 있다면 저장소 최상위에서 다음 명령으로 확인할 수 있습니다.

```sh
python -m http.server 4173 --bind 127.0.0.1 --directory dist
```

브라우저에서 `http://127.0.0.1:4173/`을 엽니다. `index.html`을 파일로 직접 열면 JSON을 읽지 못할 수 있으므로 HTTP 서버를 사용합니다.

## 수정할 파일

- 화면 구성: `dist/index.html`
- 디자인: `dist/style.css`
- 화면 동작: `dist/app.js`
- 검색·계산·설정 처리: `dist/core.js`
- 공개 데이터: `dist/data/*.json`

이미 배포된 기존 사이트의 주소나 접근 설정은 이 GitHub 설정만으로 바뀌지 않습니다.

## 공식 참고 문서

- [GitHub Pages 배포 소스 설정](https://docs.github.com/en/pages/getting-started-with-github-pages/configuring-a-publishing-source-for-your-github-pages-site)
- [GitHub Actions로 Pages 배포](https://docs.github.com/en/pages/getting-started-with-github-pages/using-custom-workflows-with-github-pages)
- [GitHub Pages 주소와 사용 조건](https://docs.github.com/en/pages/getting-started-with-github-pages/what-is-github-pages)
