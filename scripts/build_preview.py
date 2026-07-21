# -*- coding: utf-8 -*-
"""대표 문항 몇 개를 data URI로 인라인한 자체완결 프리뷰 HTML(Artifact용) 생성.
사이트 본체(fetch 기반)와 동일한 styles.css/store.js/app.js를 인라인하고,
window.__EMBEDDED__로 데이터를 주입 → Artifact 샌드박스(외부 fetch 불가)에서도 동작."""
import json, base64, re, pathlib, sys

REPO = pathlib.Path(__file__).resolve().parent.parent
CYCLE_ID = sys.argv[1] if len(sys.argv) > 1 else "통사-03-C1"
SUBSET = sys.argv[2].split(",") if len(sys.argv) > 2 else ["01A", "09C", "03A", "19A", "20A"]
DATA = REPO / "data" / CYCLE_ID
OUT = pathlib.Path("/private/tmp/claude-501/-Users-minjune-bots-tongsa/455fbe77-ef35-4445-8a96-bd4ffcb8784d/scratchpad/labeling_preview.html")

qs = json.loads((DATA / "questions.json").read_text(encoding="utf-8"))
pick = [q for q in qs if (q["row"] + q["variant"]) in SUBSET]

# 이미지 data URI 인라인
def inline_imgs(html):
    def repl(m):
        rel = m.group(1)  # assets/qXXX.png
        p = DATA / rel
        if not p.exists(): return m.group(0)
        b = base64.b64encode(p.read_bytes()).decode()
        return f'src="data:image/png;base64,{b}"'
    return re.sub(r'src="(assets/[^"]+)"', repl, html)

for q in pick:
    q["jaryo_html"] = inline_imgs(q["jaryo_html"])
    q["memo_html"] = inline_imgs(q["memo_html"])

embedded = {"manifest": {"cycles": [{"id": CYCLE_ID, "count": len(pick)}]}, "questions": pick}

css = (REPO / "styles.css").read_text(encoding="utf-8")
store = (REPO / "lib" / "store.js").read_text(encoding="utf-8")
appjs = (REPO / "app.js").read_text(encoding="utf-8")

# index.html의 body 내용(appbar+main)만 추출
html = f"""<style>{css}</style>
<div class="appbar">
  <span class="brand">통사 라벨링 · 프리뷰</span>
  <select id="cycleSel" aria-label="사이클 선택"></select>
  <span class="grow"></span>
  <span class="prog" id="prog"></span>
  <button class="btn accent" id="exportBtn">내보내기</button>
  <button class="btn" id="themeBtn" aria-label="테마 전환">◐</button>
</div>
<main id="app"></main>
<script>window.__EMBEDDED__ = {json.dumps(embedded, ensure_ascii=False)};</script>
<script>{store}</script>
<script>{appjs}</script>
"""
OUT.write_text(html, encoding="utf-8")
print(f"프리뷰 생성: {OUT} · 문항 {len(pick)} · {len(html)//1024}KB")
print("포함 문항:", [q["row"]+q["variant"] for q in pick])
