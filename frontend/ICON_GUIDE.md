# PWA 아이콘 생성 가이드

Refresh Plus PWA 아이콘을 생성하고 커스터마이징하는 방법을 안내합니다.

---

## 📋 목차

1. [빠른 시작](#빠른-시작)
2. [아이콘 커스터마이징](#아이콘-커스터마이징)
3. [생성되는 파일](#생성되는-파일)
4. [문제 해결](#문제-해결)
5. [수동 생성 방법](#수동-생성-방법)

---

## 🚀 빠른 시작

### 1단계: 의존성 설치

```bash
cd frontend
npm install
```

이 명령어는 `sharp` 라이브러리를 포함한 모든 의존성을 설치합니다.

### 2단계: 아이콘 생성

```bash
npm run generate-icons
```

이 명령어는 `public/icon-template.svg`를 기반으로 모든 필요한 아이콘 크기를 자동 생성합니다.

### 3단계: 결과 확인

생성된 아이콘은 `frontend/public/` 디렉토리에 저장됩니다:

```
frontend/public/
├── icon-72x72.png
├── icon-96x96.png
├── icon-128x128.png
├── icon-144x144.png
├── icon-152x152.png
├── icon-192x192.png
├── icon-384x384.png
├── icon-512x512.png
└── badge-72x72.png
```

### 4단계: 개발 서버에서 테스트

```bash
npm run dev
```

브라우저에서 `http://localhost:3000`으로 접속하여 아이콘이 올바르게 표시되는지 확인하세요.

---

## 🎨 아이콘 커스터마이징

### SVG 템플릿 수정

`frontend/public/icon-template.svg` 파일을 직접 수정하여 아이콘을 커스터마이징할 수 있습니다.

#### 색상 변경

```svg
<!-- 배경색 변경 -->
<rect width="512" height="512" rx="64" fill="#0066cc"/>
<!-- 원하는 색상 코드로 변경 (예: #ff6600) -->

<!-- 아이콘 색상 변경 -->
<path ... fill="white" opacity="0.9"/>
<!-- 색상 및 투명도 조정 -->
```

#### 디자인 요소 추가/제거

SVG 템플릿은 3개의 주요 그룹으로 구성되어 있습니다:

1. **배경** (`<rect>`): 앱 아이콘의 배경색과 모서리 둥글기
2. **Refresh 심볼** (`<g transform="translate(256, 256)">`): 순환 화살표
3. **Plus 심볼** (`<g transform="translate(256, 380)">`): 플러스 기호
4. **텍스트** (`<text>`): "R+" 텍스트

원하는 요소를 제거하거나 새로운 SVG 요소를 추가할 수 있습니다.

#### 텍스트 변경

```svg
<text x="256" y="150" ... >R+</text>
<!-- "R+"를 원하는 텍스트로 변경 -->
```

#### 예시: 간단한 로고로 변경

```svg
<svg width="512" height="512" viewBox="0 0 512 512" fill="none" xmlns="http://www.w3.org/2000/svg">
  <!-- 파란색 배경 -->
  <rect width="512" height="512" rx="64" fill="#0066cc"/>

  <!-- 흰색 원 -->
  <circle cx="256" cy="256" r="150" fill="white"/>

  <!-- 중앙 텍스트 -->
  <text x="256" y="280" font-family="Arial, sans-serif" font-size="100" font-weight="bold" fill="#0066cc" text-anchor="middle">R+</text>
</svg>
```

### 디자인 툴 사용

SVG를 직접 편집하는 대신 디자인 툴을 사용할 수도 있습니다:

1. **Figma**: 무료, 브라우저 기반
   - 512x512 아트보드 생성
   - 디자인 완성 후 SVG로 export
   - `icon-template.svg` 파일 교체

2. **Inkscape**: 무료, 오픈소스 SVG 에디터
   - 캔버스 크기: 512x512
   - SVG로 저장

3. **Adobe Illustrator**: 유료, 전문가용
   - 아트보드: 512x512
   - SVG로 export

### 아이콘 생성 스크립트 커스터마이징

`frontend/scripts/generate-icons.js` 파일을 수정하여 생성 옵션을 변경할 수 있습니다:

```javascript
// 다른 크기 추가
const ICON_SIZES = [
  { size: 72, filename: 'icon-72x72.png' },
  { size: 180, filename: 'icon-180x180.png' }, // Apple Touch Icon
  // ... 더 추가
];

// PNG 품질 조정
await sharp(svgBuffer)
  .resize(size, size)
  .png({ quality: 100, compressionLevel: 9 })
  .toFile(outputPath);
```

---

## 📦 생성되는 파일

| 파일명 | 크기 | 용도 |
|--------|------|------|
| `icon-72x72.png` | 72x72 | Android Chrome (hdpi) |
| `icon-96x96.png` | 96x96 | Android Chrome (xhdpi) |
| `icon-128x128.png` | 128x128 | Android Chrome (xxhdpi) |
| `icon-144x144.png` | 144x144 | Windows Metro Tile |
| `icon-152x152.png` | 152x152 | iOS Safari (iPad) |
| `icon-192x192.png` | 192x192 | Android Chrome (xxxhdpi) |
| `icon-384x384.png` | 384x384 | Android Chrome (xxxhdpi x2) |
| `icon-512x512.png` | 512x512 | Android Chrome Splash Screen |
| `badge-72x72.png` | 72x72 | 알림 배지 아이콘 |

### manifest.json 참조

이 아이콘들은 `frontend/public/manifest.json`에서 참조됩니다:

```json
{
  "icons": [
    {
      "src": "/icon-192x192.png",
      "sizes": "192x192",
      "type": "image/png",
      "purpose": "any maskable"
    },
    {
      "src": "/icon-512x512.png",
      "sizes": "512x512",
      "type": "image/png",
      "purpose": "any maskable"
    }
  ]
}
```

### Service Worker 참조

Service Worker (`public/sw.js`)에서도 이 아이콘을 사용합니다:

```javascript
self.registration.showNotification(data.title, {
  body: data.body,
  icon: '/icon-192x192.png',
  badge: '/badge-72x72.png'
});
```

---

## 🔧 문제 해결

### 문제: `sharp` 설치 실패

**증상**:
```
npm ERR! Failed to install sharp
```

**해결 방법**:
1. Node.js 버전 확인 (v18 이상 권장):
   ```bash
   node --version
   ```

2. 캐시 정리 후 재설치:
   ```bash
   npm cache clean --force
   rm -rf node_modules package-lock.json
   npm install
   ```

3. 플랫폼별 빌드 도구 설치:
   - **macOS**: `xcode-select --install`
   - **Windows**: Visual Studio Build Tools
   - **Linux**: `apt-get install build-essential`

### 문제: SVG가 올바르게 변환되지 않음

**증상**: 생성된 PNG가 깨지거나 비어있음

**해결 방법**:
1. SVG 문법 검증: [SVG Validator](https://validator.w3.org/)
2. SVG에 `width`, `height`, `viewBox` 속성이 있는지 확인
3. SVG 내부 요소가 viewBox 범위 안에 있는지 확인

### 문제: 아이콘이 웹에서 표시되지 않음

**증상**: 개발 서버에서 아이콘이 안 보임

**해결 방법**:
1. 개발 서버 재시작:
   ```bash
   npm run dev
   ```

2. 브라우저 캐시 클리어 (Cmd+Shift+R 또는 Ctrl+Shift+R)

3. 파일 경로 확인:
   ```bash
   ls -la frontend/public/icon-*.png
   ```

4. manifest.json 문법 검증: [Web App Manifest Validator](https://manifest-validator.appspot.com/)

### 문제: PWA 설치 프롬프트가 안 뜸

**증상**: 아이콘은 생성되었지만 PWA 설치 불가

**해결 방법**:
1. HTTPS 사용 확인 (localhost는 예외)
2. manifest.json이 올바르게 로드되는지 확인:
   - Chrome DevTools → Application → Manifest
3. Service Worker 등록 확인:
   - Chrome DevTools → Application → Service Workers
4. 아이콘 크기 요구사항 확인:
   - 최소 192x192, 512x512 필수

---

## 🛠️ 수동 생성 방법

자동 스크립트를 사용하지 않고 수동으로 아이콘을 생성하려면:

### 방법 1: 온라인 툴 사용

1. **PWA Asset Generator**: https://www.pwabuilder.com/imageGenerator
   - SVG 또는 PNG 업로드
   - 모든 크기 자동 생성 및 다운로드

2. **RealFaviconGenerator**: https://realfavicongenerator.net/
   - 이미지 업로드
   - PWA 옵션 선택
   - 생성된 파일 다운로드

### 방법 2: Photoshop/GIMP 사용

1. 512x512 크기로 아이콘 디자인
2. 각 필요한 크기로 resize하여 export:
   - File → Export → Export As
   - 크기 변경 후 PNG로 저장

### 방법 3: ImageMagick 사용 (CLI)

```bash
# 설치
brew install imagemagick  # macOS
sudo apt-get install imagemagick  # Linux

# SVG를 다양한 크기로 변환
for size in 72 96 128 144 152 192 384 512; do
  convert -background none -resize ${size}x${size} icon-template.svg icon-${size}x${size}.png
done
```

---

## ✅ 체크리스트

아이콘 생성 후 다음 사항을 확인하세요:

- [ ] 모든 9개 PNG 파일이 `frontend/public/`에 생성됨
- [ ] `manifest.json`이 올바른 경로를 참조함
- [ ] Service Worker가 올바른 아이콘 경로를 사용함
- [ ] 개발 서버에서 아이콘이 올바르게 표시됨
- [ ] PWA 설치 프롬프트가 표시됨 (iOS Safari 또는 Android Chrome)
- [ ] 설치 후 홈 화면 아이콘이 올바르게 표시됨
- [ ] 푸시 알림에서 아이콘과 배지가 올바르게 표시됨

---

## 📚 추가 자료

- [PWA Icons Best Practices](https://web.dev/maskable-icon/)
- [Web App Manifest](https://developer.mozilla.org/en-US/docs/Web/Manifest)
- [Service Worker API](https://developer.mozilla.org/en-US/docs/Web/API/Service_Worker_API)
- [Sharp Documentation](https://sharp.pixelplumbing.com/)

---

**작성일**: 2024-12-08
**버전**: 1.0.0
