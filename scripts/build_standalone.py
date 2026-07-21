# -*- coding: utf-8 -*-
"""전체 문항 + 이미지 data URI를 한 파일에 담은 오프라인 단독 실행 HTML.
서버·인터넷 없이 더블클릭으로 열려 라벨링(localStorage)·내보내기까지 동작.
호스팅(Cloudflare) 준비 전 임시 배포용."""
import json, base64, re, pathlib, sys

REPO = pathlib.Path(__file__).resolve().parent.parent
CYCLE_ID = sys.argv[1] if len(sys.argv) > 1 else "통사-03-C1"
OUT = pathlib.Path(sys.argv[2]) if len(sys.argv) > 2 else REPO / f"{CYCLE_ID}_standalone.html"
DATA = REPO / "data" / CYCLE_ID

qs = json.loads((DATA / "questions.json").read_text(encoding="utf-8"))

_cache = {}
def inline_imgs(html):
    def repl(m):
        rel = m.group(1)
        if rel in _cache: return f'src="{_cache[rel]}"'
        p = DATA / rel
        if not p.exists(): return m.group(0)
        uri = "data:image/png;base64," + base64.b64encode(p.read_bytes()).decode()
        _cache[rel] = uri
        return f'src="{uri}"'
    return re.sub(r'src="(assets/[^"]+)"', repl, html)

for q in qs:
    q["jaryo_html"] = inline_imgs(q["jaryo_html"])
    q["memo_html"] = inline_imgs(q["memo_html"])

embedded = {"manifest": {"cycles": [{"id": CYCLE_ID, "count": len(qs)}]}, "questions": qs}
css = (REPO / "styles.css").read_text(encoding="utf-8")
store = (REPO / "lib" / "store.js").read_text(encoding="utf-8")
appjs = (REPO / "app.js").read_text(encoding="utf-8")
emb = json.dumps(embedded, ensure_ascii=False).replace("</", "<\\/")  # 스크립트 조기종료 방지

html = f"""<!doctype html><html lang="ko"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>통사 라벨링 · {CYCLE_ID}</title>
<style>{css}</style></head><body>
<div class="appbar">
  <span class="brand">통사 라벨링</span>
  <select id="cycleSel" aria-label="사이클 선택"></select>
  <span class="grow"></span><span class="prog" id="prog"></span>
  <button class="btn accent" id="exportBtn">내보내기</button>
  <button class="btn" id="themeBtn" aria-label="테마 전환">◐</button>
</div>
<main id="app"></main>
<script>window.__EMBEDDED__ = {emb};</script>
<script>{store}</script>
<script>{appjs}</script>
</body></html>"""
OUT.write_text(html, encoding="utf-8")
print(f"단독본 생성: {OUT}")
print(f"문항 {len(qs)} · 이미지 {len(_cache)} · {len(html)//1024//1024}MB")
