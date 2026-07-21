# 통사 라벨링 사이트 (tongsa-labeling)

통합사회 AI 출제 사이클별 문항을 **실제 시험지 형태**로 모바일·PC에서 보고, 하단에서 **태깅·서술 응답**을 남기는 정적 웹앱. 라벨 데이터가 출제 파이프라인(배치표 보강기·오류 검수기·출제원리)을 진화시키는 연료가 된다.

## 구조
```
index.html          앱 셸(appbar + #app)
styles.css          평가원 시험지 톤 · 라이트/다크 · 명조
app.js              데이터 구동 SPA(그리드 → 문항 상세 → 라벨 패널)
lib/store.js        라벨 저장 어댑터 (현재 localStorage, D1/Firestore로 스왑 예정)
data/
  manifest.json     사이클 목록
  통사-03-C1/
    questions.json  문항별 구조(HTML 조각 + 메타)
    assets/*.png    자료 이미지(ASCII 파일명)
scripts/
  build_cycle_data.py   카드(md) → questions.json + assets   [파이프라인]
  build_preview.py      대표 문항 인라인 자체완결 프리뷰(Artifact용)
```

## 코드 체계
- 문항 ID: `통사-{테마}-C{사이클}-{행}{변형}` 예 `통사-03-C1-09A`.
- 사이클 = 한 번의 출제·라벨 라운드. 테마 = 03(기후)/04(지형)/08(문화권)/38(인구)/39(에너지).

## 사이클 데이터 만들기
```
python3 scripts/build_cycle_data.py "<카드 폴더>" <테마2자리> <사이클>
# 예: python3 scripts/build_cycle_data.py "/…/1차출제(260721)" 03 1
```
카드(`27통사_*_초안.md`)를 파싱해 `data/통사-03-C1/`에 questions.json + 이미지 생성, manifest 갱신.

## 로컬 실행 / 배포
- 로컬: `python3 -m http.server` 후 브라우저(파일 직접 열기는 fetch 막혀 불가 — 정적 서버 필요).
- 배포: private GitHub repo → **Cloudflare Pages**(무료). 접속 게이트는 Cloudflare Access 또는 앱 passphrase.

## 라벨 저장 (DB 스왑)
현재 `lib/store.js`는 localStorage(기기 로컬). 인터페이스 `getAll/get/set/exportCycle`만 동일하게 **Cloudflare D1**(Pages Functions `/api/labels`) 또는 Firestore 어댑터로 교체하면 모바일↔PC 동기화가 된다. 그전까지는 상단 **내보내기**로 `labels_*.json`을 저장해 전달.

## 라벨 스키마
`{ curriculum:'Y'|'N', curriculumNote, difficulty:1..5, quality:'S'|'A'|'B'|'C'|'F', adopt:'O'|'△'|'X', reviseNote, discardNote, updated_at }`
- O = 문항 창고 채택 · △ = 수정 후 다음 사이클 재평가 · X = 폐기.
