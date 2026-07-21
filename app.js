/* 통사 라벨링 SPA — 데이터 구동(questions.json) + 시험지 렌더 + 라벨 패널.
   데이터 소스: 기본 fetch(data/…), 프리뷰 모드는 window.__EMBEDDED__ 사용. */
(function () {
  const EM = window.__EMBEDDED__ || null;
  const app = document.getElementById('app');
  const el = (id) => document.getElementById(id);
  const state = { cycleId: null, questions: [], labels: {}, view: 'grid', idx: 0 };

  const QUALITY = ['S', 'A', 'B', 'C', 'F'];
  const DIFF = [1, 2, 3, 4, 5];
  const ADOPT = ['O', '△', 'X'];

  async function fetchJSON(path) {
    const r = await fetch(path, { cache: 'no-store' });
    if (!r.ok) throw new Error('load fail: ' + path);
    return r.json();
  }
  async function loadManifest() {
    if (EM) return EM.manifest;
    return fetchJSON('data/manifest.json');
  }
  async function loadCycle(cycleId) {
    if (EM) return EM.questions;
    return fetchJSON('data/' + encodeURIComponent(cycleId) + '/questions.json');
  }
  function imgBase(cycleId) { return EM ? '' : 'data/' + cycleId + '/'; }
  function resolveImgs(htmlStr, cycleId) {
    if (EM) return htmlStr; // 프리뷰는 data URI 인라인됨
    return htmlStr.replace(/src="assets\//g, 'src="' + imgBase(cycleId) + 'assets/');
  }
  const labeled = (l) => !!(l && l.adopt);
  function markOn(b) { b.classList.add('on'); if (b.dataset.v === 'Y') b.classList.add('yes'); if (b.dataset.v === 'N') b.classList.add('no'); }

  // ---------- 초기화 ----------
  async function init() {
    const manifest = await loadManifest();
    const sel = el('cycleSel');
    sel.innerHTML = manifest.cycles.map(c =>
      `<option value="${c.id}">${c.id} (${c.count}문항)</option>`).join('');
    sel.onchange = () => selectCycle(sel.value);
    const hash = decodeURIComponent(location.hash.replace(/^#/, ''));
    const [hcycle] = hash.split('/');
    const start = manifest.cycles.find(c => c.id === hcycle) ? hcycle : manifest.cycles[0].id;
    sel.value = start;
    await selectCycle(start, hash);
  }

  async function selectCycle(cycleId, hash) {
    state.cycleId = cycleId;
    state.questions = await loadCycle(cycleId);
    state.labels = await LabelStore.getAll(cycleId);
    const parts = (hash || '').split('/');
    if (parts[1]) {
      const i = state.questions.findIndex(q => q.id === parts[1]);
      if (i >= 0) { state.idx = i; return renderDetail(); }
    }
    renderGrid();
  }

  function updateProgress() {
    const done = state.questions.filter(q => labeled(state.labels[q.id])).length;
    el('prog').textContent = `${done} / ${state.questions.length} 라벨`;
  }

  // ---------- 그리드 ----------
  function renderGrid() {
    state.view = 'grid';
    location.hash = encodeURIComponent(state.cycleId);
    updateProgress();
    const cards = state.questions.map((q, i) => {
      const l = state.labels[q.id] || {};
      const dots = ['curriculum', 'difficulty', 'quality'].map(f =>
        `<span class="dot ${l[f] != null && l[f] !== '' ? 'set' : ''}"></span>`).join('');
      const adopt = l.adopt ? `<span class="adopt ${l.adopt}">${l.adopt}</span>` : '';
      return `<a class="gcard" data-i="${i}" href="#${encodeURIComponent(state.cycleId)}/${encodeURIComponent(q.id)}">
        <div class="gid">${q.row}${q.variant}${adopt}</div>
        <div class="gdesc">${q.desc}</div>
        <div class="gtags">${dots}</div></a>`;
    }).join('');
    app.innerHTML = `<div class="grid-head"><h1>${state.cycleId}</h1>
      <div class="sub">문항을 눌러 보고, 하단에서 라벨링하세요. ● = 입력된 항목 · 우상단 = 채택</div></div>
      <div class="grid">${cards}</div>
      <p class="footnote">라벨은 이 기기에 자동 저장됩니다(현재 localStorage). 상단 '내보내기'로 JSON을 저장해 전달하세요.</p>`;
    app.querySelectorAll('.gcard').forEach(a => a.onclick = (e) => {
      e.preventDefault(); state.idx = +a.dataset.i; renderDetail();
    });
    window.scrollTo(0, 0);
  }

  // ---------- 상세(시험지 + 라벨) ----------
  function renderDetail() {
    state.view = 'detail';
    const q = state.questions[state.idx];
    location.hash = encodeURIComponent(state.cycleId) + '/' + encodeURIComponent(q.id);
    const cid = state.cycleId;
    const ptChip = q['배점'] ? `<span class="chip pt">${q['배점']}점</span>` : '';
    const nanChip = q['난이도'] ? `<span class="chip">난이도 ${q['난이도']}</span>` : '';
    const memo = q.memo_html ? `<details class="memo"><summary>검토용 메모 (출제의도·출제메모)</summary><div class="memo-body">${resolveImgs(q.memo_html, cid)}</div></details>` : '';
    app.innerHTML = `<div class="detail">
      <article class="sheet">
        <div class="sheet-head"><span class="chip type">${q.row}${q.variant} · ${q.desc}</span>${nanChip}${ptChip}<span class="grow"></span><span class="qcode">${q.id}</span></div>
        <div class="body">
          <p class="stem">${q.stem_html} ${q.badge ? `<span class="pt-inl">${q.badge}</span>` : ''}</p>
          ${resolveImgs(q.jaryo_html, cid)}${q.bogi_html}${q.choices_html}
        </div>
      </article>
      <details class="sol"><summary><span class="tw">▸</span> 정답 · 해설 보기</summary>
        <div class="sol-body">
          <div class="ans-line"><span class="ans-badge">${q['정답']}</span><span class="t">정답</span></div>
          ${q.haesol_intro_html}${q.perchoice_html}${memo}
        </div></details>
      ${labelPanelHTML(q)}
    </div>
    <div class="detailnav">
      <button class="btn" id="toGrid">☰ 목차</button><span class="grow"></span>
      <button class="btn" id="prevQ">← 이전</button>
      <span class="pos">${state.idx + 1} / ${state.questions.length}</span>
      <button class="btn" id="nextQ">다음 →</button>
    </div>`;
    wireLabelPanel(q);
    el('toGrid').onclick = renderGrid;
    el('prevQ').disabled = state.idx === 0;
    el('nextQ').disabled = state.idx === state.questions.length - 1;
    el('prevQ').onclick = () => { if (state.idx > 0) { state.idx--; renderDetail(); } };
    el('nextQ').onclick = () => { if (state.idx < state.questions.length - 1) { state.idx++; renderDetail(); } };
    window.scrollTo(0, 0);
  }

  function labelPanelHTML(q) {
    return `<div class="label-panel">
      <h3>라벨링 <span class="save" id="saveInd">미저장</span></h3>
      <div class="lfield">
        <label>1. 교육과정 적합 여부 <span class="req">*</span></label>
        <div class="seg yn" data-field="curriculum">
          <button data-v="Y" class="yes">예 (적합)</button>
          <button data-v="N" class="no">아니오 (위반)</button></div>
        <div class="note-wrap" data-for="curriculum"><textarea class="note" data-field="curriculumNote" placeholder="교육과정 위반 사유를 서술하세요"></textarea></div>
      </div>
      <div class="lfield">
        <label>2. 난이도 (1 쉬움 ~ 5 어려움)</label>
        <div class="seg" data-field="difficulty">${DIFF.map(d => `<button data-v="${d}">${d}</button>`).join('')}</div>
      </div>
      <div class="lfield">
        <label>3. 퀄리티</label>
        <div class="seg quality" data-field="quality">${QUALITY.map(v => `<button data-v="${v}">${v}</button>`).join('')}</div>
      </div>
      <div class="lfield">
        <label>4. 채택 여부 <span class="req">*</span> <span style="font-weight:400;color:var(--muted)">O 창고 · △ 수정 후 재평가 · X 폐기</span></label>
        <div class="seg adopt" data-field="adopt">${ADOPT.map(v => `<button data-v="${v}">${v}</button>`).join('')}</div>
        <div class="note-wrap" data-for="adopt-revise"><textarea class="note" data-field="reviseNote" placeholder="△ 어떻게 수정할지 서술하세요"></textarea></div>
        <div class="note-wrap" data-for="adopt-discard"><textarea class="note" data-field="discardNote" placeholder="X 폐기 사유를 서술하세요"></textarea></div>
      </div>
    </div>`;
  }

  function wireLabelPanel(q) {
    const cur = state.labels[q.id] || {};
    const panel = app.querySelector('.label-panel');
    // 초기 반영
    panel.querySelectorAll('.seg').forEach(seg => {
      const f = seg.dataset.field;
      seg.querySelectorAll('button').forEach(b => {
        const v = f === 'difficulty' ? +b.dataset.v : b.dataset.v;
        if (cur[f] === v || String(cur[f]) === b.dataset.v) markOn(b);
        b.onclick = () => setField(q, f, v, b);
      });
    });
    panel.querySelectorAll('textarea.note').forEach(ta => {
      ta.value = cur[ta.dataset.field] || '';
      ta.oninput = () => setField(q, ta.dataset.field, ta.value, null, true);
    });
    reflectNotes(panel, cur);
    setSaveInd(labeled(cur) ? 'saved' : 'idle');
  }

  function reflectNotes(panel, l) {
    panel.querySelector('[data-for="curriculum"]').classList.toggle('show', l.curriculum === 'N');
    panel.querySelector('[data-for="adopt-revise"]').classList.toggle('show', l.adopt === '△');
    panel.querySelector('[data-for="adopt-discard"]').classList.toggle('show', l.adopt === 'X');
  }

  async function setField(q, field, value, btn, isText) {
    const l = Object.assign({}, state.labels[q.id]);
    // 세그먼트 토글: 같은 값 다시 누르면 해제
    if (!isText && l[field] === value) value = null;
    l[field] = value;
    state.labels[q.id] = l;
    if (!isText && btn) {
      const seg = btn.closest('.seg');
      seg.querySelectorAll('button').forEach(b => b.classList.remove('on', 'yes', 'no'));
      if (value != null) markOn(btn);
      reflectNotes(app.querySelector('.label-panel'), l);
    }
    setSaveInd('saving');
    try { await LabelStore.set(state.cycleId, q.id, l); setSaveInd('saved'); }
    catch (e) { setSaveInd('error'); }
    updateProgress();
  }

  let saveT;
  function setSaveInd(mode) {
    const s = el('saveInd'); if (!s) return;
    clearTimeout(saveT);
    if (mode === 'saving') { s.textContent = '저장 중…'; s.className = 'save'; }
    else if (mode === 'saved') { s.textContent = '✓ 저장됨'; s.className = 'save on'; }
    else if (mode === 'error') { s.textContent = '⚠ 저장 실패'; s.className = 'save'; }
    else { s.textContent = '미저장'; s.className = 'save'; }
  }

  // ---------- 내보내기 ----------
  async function exportLabels() {
    const map = await LabelStore.exportCycle(state.cycleId);
    const payload = { cycle: state.cycleId, exported_at: new Date().toISOString(), count: Object.keys(map).length, labels: map };
    const blob = new Blob([JSON.stringify(payload, null, 1)], { type: 'application/json' });
    const a = document.createElement('a');
    a.href = URL.createObjectURL(blob);
    a.download = `labels_${state.cycleId}_${new Date().toISOString().slice(0, 10)}.json`;
    a.click(); URL.revokeObjectURL(a.href);
  }

  // ---------- 테마 토글 ----------
  function toggleTheme() {
    const root = document.documentElement;
    const cur = root.getAttribute('data-theme') ||
      (matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light');
    root.setAttribute('data-theme', cur === 'dark' ? 'light' : 'dark');
  }

  el('exportBtn').onclick = exportLabels;
  el('themeBtn').onclick = toggleTheme;
  init().catch(e => { app.innerHTML = `<p class="footnote">데이터 로드 실패: ${e.message}<br>정적 서버로 열어야 합니다(파일 직접 열기 불가).</p>`; });
})();
