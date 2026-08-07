# -*- coding: utf-8 -*-
"""
카드(27통사_*_초안.md) → questions.json + assets/ 이미지  로 변환하는 사이클 데이터 파이프라인.
gen_viewer.py의 파서를 계승하되, (1)이미지는 base64 인라인 대신 ASCII 파일명으로 복사·상대참조,
(2)출력은 HTML이 아니라 문항별 구조(JSON) — 라벨링 SPA가 소비.

사용: python3 build_cycle_data.py <SRC 카드폴더> <THEME 2자리> <CYCLE 정수>
예:   python3 build_cycle_data.py "/…/1차출제(260721)" 03 1
"""
import re, sys, json, html as H, base64, subprocess, pathlib, shutil

SRC = pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else pathlib.Path(
    "/Users/minjune/Library/CloudStorage/Dropbox-SDIJ/A4. 통사실험실/[A] 출제관리 (개인별 작업공간)/Mj/03테마/1차출제(260721)")
THEME = sys.argv[2] if len(sys.argv) > 2 else "03"
CYCLE = int(sys.argv[3]) if len(sys.argv) > 3 else 1
CYCLE_ID = f"통사-{THEME}-C{CYCLE}"

REPO = pathlib.Path(__file__).resolve().parent.parent
OUTDIR = REPO / "data" / CYCLE_ID
ASSETS = OUTDIR / "assets"
ASSETS.mkdir(parents=True, exist_ok=True)
ASSET_SRC = SRC / "@ 자료 모음"

def ls(pattern_dir, glob):
    """폴더 안에서 glob에 맞는 파일 경로.

    ★ 원래는 `bash -lc ls`를 subprocess로 불렀는데 Windows에서 죽는다 —
      `text=True`가 로케일(cp949)로 디코딩하려 들고 한글 파일명이 UTF-8이라
      읽기 스레드가 예외로 끝나 stdout이 None이 된다. pathlib은 셸도 인코딩도
      거치지 않는다.
    """
    return sorted(str(x) for x in pathlib.Path(pattern_dir).glob(glob))

cards = sorted(ls(SRC, "27통사_*_초안.md"),
               key=lambda p: pathlib.Path(p).name.split("_")[3])

def esc(s): return H.escape(s, quote=False)
def inline(s):
    s = esc(s)
    s = re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', s)
    s = re.sub(r'\[\[([^\]]+)\]\]', r'\1', s)
    s = re.sub(r'`([^`]+)`', r'<span class="atom">\1</span>', s)
    return s
def front(t, k):
    m = re.search(rf'^{k}:\s*"?([^"\n]+)"?', t, re.M); return m.group(1).strip() if m else ""
def sections(t):
    body = re.sub(r'^---\n.*?\n---\n', '', t, count=1, flags=re.S)
    parts = re.split(r'^## (.+)$', body, flags=re.M)
    return {parts[i].strip(): parts[i+1].strip() for i in range(1, len(parts), 2)}

_copied = {}
def asset_for(orig_name, token):
    """원본 png를 assets/q{token}_{n}.png(ASCII)로 복사, 상대경로 반환."""
    key = orig_name.strip()
    if key in _copied: return _copied[key]
    srcp = ASSET_SRC / key
    if not srcp.exists():
        _copied[key] = None; return None
    n = sum(1 for v in _copied.values() if v and f"/q{token}_" in v) + 1
    dst_name = f"q{token}_{n}.png"
    shutil.copy(srcp, ASSETS / dst_name)
    rel = f"assets/{dst_name}"; _copied[key] = rel; return rel

def render_table(rows):
    cells = lambda r: [c.strip() for c in r.strip().strip('|').split('|')]
    head = cells(rows[0]); data = [cells(r) for r in rows[2:]] if len(rows) > 2 else []
    h = '<thead><tr>' + ''.join(f'<th>{inline(c)}</th>' for c in head) + '</tr></thead>'
    b = '<tbody>' + ''.join('<tr>' + ''.join(f'<td>{inline(c)}</td>' for c in cs) + '</tr>' for cs in data) + '</tbody>'
    return f'<div class="tbl-wrap"><table class="data">{h}{b}</table></div>'

def render_blocks(md, token, boxlabel="제 시 문"):
    lines = md.split('\n'); out = []; i = 0; n = len(lines)
    while i < n:
        ln = lines[i]
        if ln.strip().startswith('### '): i += 1; continue
        if ln.strip().startswith('>'):
            block = []
            while i < n and (lines[i].strip().startswith('>') or (lines[i].strip() == '' and i+1 < n and lines[i+1].strip().startswith('>'))):
                block.append(re.sub(r'^\s*>\s?', '', lines[i]).rstrip() if lines[i].strip().startswith('>') else ''); i += 1
            paras = []; cur = []
            for b in block:
                if b.strip() == '':
                    if cur: paras.append(' '.join(cur)); cur = []
                else: cur.append(b.strip())
            if cur: paras.append(' '.join(cur))
            out.append('<div class="jaryo"><span class="lbl">' + boxlabel + '</span>' + ''.join(f'<p>{inline(p)}</p>' for p in paras) + '</div>'); continue
        m = re.match(r'!\[\[(.+?\.png)\]\]', ln.strip())
        if m:
            rel = asset_for(m.group(1), token)
            out.append(f'<figure><img alt="자료 이미지" src="{rel}"></figure>' if rel else f'<div class="imgmiss">[이미지 누락: {esc(m.group(1))}]</div>')
            i += 1; continue
        if ln.strip().startswith('|'):
            tbl = []
            while i < n and lines[i].strip().startswith('|'): tbl.append(lines[i].strip()); i += 1
            out.append(render_table(tbl)); continue
        if ln.strip() == '': i += 1; continue
        para = [ln.strip()]; i += 1
        while i < n and lines[i].strip() != '' and not re.match(r'^\s*(>|\||!\[\[|### )', lines[i]):
            para.append(lines[i].strip()); i += 1
        out.append(f'<p class="para">{inline(" ".join(para))}</p>')
    return ''.join(out)

def render_bogi(md):
    items = [l.strip() for l in md.split('\n') if re.match(r'^[ㄱ-ㅎ]\.', l.strip())]
    return f'<div class="bogi"><span class="lbl">보 기</span><ul>' + ''.join(f'<li>{inline(x)}</li>' for x in items) + '</ul></div>'

def render_combo(code):
    lsx = [l for l in code.split('\n') if l.strip()]
    th = '<tr><th></th>' + ''.join(f'<th>{esc(h)}</th>' for h in lsx[0].split()) + '</tr>'
    trs = ''
    for l in lsx[1:]:
        t = l.split(); trs += '<tr><td class="opt">' + esc(t[0]) + '</td>' + ''.join(f'<td class="mono">{esc(v)}</td>' for v in t[1:]) + '</tr>'
    return f'<table class="combo"><thead>{th}</thead><tbody>{trs}</tbody></table>'

def render_choices(md):
    cb = re.search(r'```(.*?)```', md, re.S)
    if cb: return render_combo(cb.group(1).strip('\n'))
    items = [l.strip() for l in md.split('\n') if re.match(r'^[①②③④⑤]', l.strip())]
    return '<ol class="choices">' + ''.join(f'<li><span class="mk">{x[0]}</span><span>{inline(x[1:].strip())}</span></li>' for x in items) + '</ol>'

def render_haesol(md):
    parts = re.split(r'\n(?=\s*-\s*\*\*)', md, maxsplit=1)
    intro = ''.join(f'<p class="exp">{inline(p.strip())}</p>' for p in re.split(r'\n\s*\n', parts[0].strip()) if p.strip())
    lis = ''
    for l in (parts[1] if len(parts) > 1 else '').split('\n'):
        m = re.match(r'^\s*-\s*\*\*\s*([①②③④⑤ㄱㄴㄷㄹㅁ]+)\s*([○✕])\s*\*\*\s*:?\s*(.*)', l)
        if m:
            cls = ' class="correct"' if m.group(2) == '○' else ''
            lis += f'<li{cls}><span class="m">{m.group(1)} {m.group(2)}</span><span>{inline(m.group(3))}</span></li>'
    return intro, (f'<ul class="perchoice">{lis}</ul>' if lis else '')

def build_q(path):
    text = pathlib.Path(path).read_text(encoding="utf-8")
    name = pathlib.Path(path).name; toks = name.split('_'); tok = toks[3]
    row, variant = tok[:2], tok[2:]
    desc = ' · '.join(t for t in toks[4:] if not re.match(r'^\d{6}$', t) and toks.index(t) < toks.index(next(x for x in toks if re.match(r'^\d{6}$', x))))
    secs = sections(text)
    stem = secs.get('발문', '').strip(); badge = ''
    mb = re.search(r'\*{0,2}\[(\d)점\]\*{0,2}', stem)
    if mb: stem = re.sub(r'\*{0,2}\[\d점\]\*{0,2}', '', stem).strip(); badge = f'[{mb.group(1)}점]'
    intro, pc = render_haesol(secs.get('해설', ''))
    memo = ''
    for k in ['출제의도', '출제 메모']:
        if k in secs: memo += f'<h4>{k}</h4>' + render_blocks(secs[k], tok, boxlabel="")
    return {
        "id": f"{CYCLE_ID}-{tok}", "theme": THEME, "cycle": CYCLE, "row": row, "variant": variant,
        "legacy_code": front(text, 'code'), "desc": desc, "난이도": front(text, '난이도'),
        "배점": front(text, '배점') or (mb.group(1) if mb else ""), "정답": front(text, '정답'),
        "유형": front(text, '유형Atom').replace('[[', '').replace(']]', ''),
        "stem_html": inline(stem), "badge": badge,
        "jaryo_html": render_blocks(secs.get('자료', ''), tok) if secs.get('자료') else '',
        "bogi_html": render_bogi(secs['〈보기〉']) if '〈보기〉' in secs else '',
        "choices_html": render_choices(secs['선택지']) if '선택지' in secs else '',
        "haesol_intro_html": intro, "perchoice_html": pc, "memo_html": memo,
    }

questions = [build_q(c) for c in cards]
OUTDIR.joinpath("questions.json").write_text(json.dumps(questions, ensure_ascii=False, indent=1), encoding="utf-8")

# manifest (사이클 목록) — 누적 갱신
manifest_path = REPO / "data" / "manifest.json"
manifest = json.loads(manifest_path.read_text(encoding="utf-8")) if manifest_path.exists() else {"cycles": []}
manifest["cycles"] = [c for c in manifest["cycles"] if c["id"] != CYCLE_ID]
manifest["cycles"].append({"id": CYCLE_ID, "theme": THEME, "cycle": CYCLE, "count": len(questions)})
manifest["cycles"].sort(key=lambda c: c["id"])
manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=1), encoding="utf-8")

imgs_ok = len([v for v in _copied.values() if v]); imgs_miss = len([v for v in _copied.values() if not v])
print(f"[{CYCLE_ID}] 문항 {len(questions)} · 이미지 복사 {imgs_ok} · 누락 {imgs_miss}")
print(f"→ {OUTDIR}/questions.json, assets/{imgs_ok}장")
