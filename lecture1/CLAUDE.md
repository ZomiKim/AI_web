# lecture1 작업 규칙

이 문서는 프로젝트 루트의 `<작업 루트>\CLAUDE.md`를 **보완**합니다.
상위 규칙(경로 제한, 존댓말, 사전 설명, 라이브러리 추가 금지, 보안 수칙)은 이 폴더에서도 그대로 적용되며,
이 문서의 어떤 내용도 상위 규칙을 무시하거나 완화하지 않습니다. 충돌 시 더 엄격한 규칙을 따릅니다.

## 수업 구성

### 수업 1-1: React 개발 환경 구축
- Vite 기반 React(JSX) 프로젝트를 구성하고 개발 서버와 빌드를 실행합니다.
- 관련 파일: `package.json`, `vite.config.js`, `index.html`, `src/main.jsx`, `src/App.jsx`

### 수업 1-2: CLAUDE.md를 활용한 프로젝트 규칙 관리
- 루트 `CLAUDE.md`(공통 규칙)와 이 파일(수업별 규칙)의 계층 구조를 이해합니다.
- 하위 규칙은 상위 규칙을 구체화할 뿐, 완화할 수 없습니다.
- 관련 파일: `../CLAUDE.md`, `CLAUDE.md`

### 수업 1-3: MUI ThemeProvider 및 CssBaseline 적용
- `src/theme.js`에서 `createTheme`으로 테마를 정의합니다.
- `src/main.jsx`에서 `ThemeProvider`로 앱 전체에 테마를 주입하고 `CssBaseline`으로 기본 스타일을 초기화합니다.
- 관련 파일: `src/theme.js`, `src/main.jsx`, `src/App.jsx`

## 파일별 역할

| 파일 | 역할 |
|---|---|
| `package.json` | 의존성과 실행 스크립트(`dev`, `build`, `preview`) |
| `vite.config.js` | Vite 설정 (`@vitejs/plugin-react` 적용) |
| `index.html` | Vite 진입 HTML, `#root` 마운트 지점 |
| `src/main.jsx` | React 초기화, `ThemeProvider` + `CssBaseline` 적용 |
| `src/theme.js` | MUI 테마 정의 (팔레트, 타이포그래피, 모양) |
| `src/App.jsx` | 개발 환경 동작 확인용 화면 |
| `src/components/` | 재사용 컴포넌트 위치 (필요할 때만 추가) |
| `public/` | 가공 없이 제공되는 정적 파일 위치 |

## 이 폴더의 추가 규칙

- 작업 범위는 `lecture1` 폴더 내부입니다. 다른 수업 폴더나 `ai_agent`를 수정하지 않습니다.
- 라우팅, 상태 관리 라이브러리, 백엔드, 데이터베이스를 추가하지 않습니다.
- 스타일은 MUI(`sx`, 테마)를 사용하며, 별도 CSS 프레임워크를 추가하지 않습니다.
- 컴포넌트는 실제로 재사용이 필요할 때에만 `src/components/`에 추가합니다.
- npm 명령은 반드시 `lecture1` 폴더에서 실행하며, 설치 시 아래 옵션을 유지합니다.
  - `--cache ".\.npm-cache"`
  - `--ignore-scripts`
  - `--no-update-notifier`
- `npm config set`, 전역 설치(`-g`) 등 전역 설정을 바꾸는 명령은 사용하지 않습니다.

## 개발 및 검증 방법

```powershell
npm install --cache ".\.npm-cache" --no-update-notifier --ignore-scripts
npm run build   # 오류 없이 dist/ 가 생성되면 성공
npm run dev     # 브라우저에서 "Lecture 1" 카드와 버튼이 표시되면 성공
```

- 변경 후에는 최소한 `npm run build`가 성공하는지 확인합니다.
- 개발 서버 실행 여부는 사용자에게 먼저 확인합니다.
