/* 라벨 저장 어댑터.
   현재: localStorage (기기 로컬, 오프라인 동작).
   교체 예정: Cloudflare D1 / Firestore — 아래 인터페이스(getAll/get/set/exportCycle)만 동일하게 구현하면 스왑됨.
   라벨 객체 스키마:
     { curriculum:'Y'|'N'|null, curriculumNote:'',
       difficulty:1..5|null, quality:'S'|'A'|'B'|'C'|'F'|null,
       adopt:'O'|'△'|'X'|null, reviseNote:'', discardNote:'', updated_at:ISO }
*/
window.LabelStore = (function () {
  const PREFIX = 'tongsa-labels:';
  const k = (cycleId) => PREFIX + cycleId;
  const loadAll = (cycleId) => { try { return JSON.parse(localStorage.getItem(k(cycleId)) || '{}'); } catch (e) { return {}; } };
  const saveAll = (cycleId, map) => localStorage.setItem(k(cycleId), JSON.stringify(map));
  return {
    backend: 'local',
    async getAll(cycleId) { return loadAll(cycleId); },
    async get(cycleId, qid) { return loadAll(cycleId)[qid] || null; },
    async set(cycleId, qid, label) {
      const m = loadAll(cycleId);
      m[qid] = Object.assign({}, m[qid], label, { updated_at: new Date().toISOString() });
      saveAll(cycleId, m);
      return m[qid];
    },
    async exportCycle(cycleId) { return loadAll(cycleId); }
  };
})();
