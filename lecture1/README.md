# lecture1

React + Vite + Material UI(MUI) 개발 환경을 구축하는 1강 실습 프로젝트입니다.

## 기술 스택

| 패키지 | 버전 범위 |
|---|---|
| react / react-dom | ^19.3.1 |
| @mui/material | ^9.5.0 |
| @emotion/react / @emotion/styled | ^11.14.0 / ^11.14.1 |
| vite | ^8.3.4 |
| @vitejs/plugin-react | ^6.1.2 |

Node.js `^20.19.0 || >=22.12.0`이 필요합니다.

## 실행 방법

모든 명령은 `lecture1` 폴더에서 실행합니다.

```powershell
# 의존성 설치 (캐시는 프로젝트 내부, 설치 스크립트 미실행)
npm install --cache ".\.npm-cache" --no-update-notifier --ignore-scripts

# 개발 서버
npm run dev

# 프로덕션 빌드 (dist/ 생성)
npm run build

# 빌드 결과 미리보기
npm run preview
```

## Git 관리 시 제외 대상

`node_modules/`, `dist/`, `.npm-cache/`는 생성물이므로 Git에 포함하지 않는 것을 권장합니다.
