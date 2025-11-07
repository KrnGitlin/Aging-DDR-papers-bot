const state = {
  papers: [],
  selectedKeywords: new Set(),
  search: "",
  sort: "newest",
};

async function loadData() {
  const res = await fetch("./data/papers.json", { cache: "no-store" });
  const data = await res.json();
  state.papers = Array.isArray(data) ? data : data.papers;
  renderKeywords();
  renderList();
}

function uniqueKeywords() {
  const set = new Set();
  for (const p of state.papers) {
    (p.matched_keywords || []).forEach(k => set.add(k));
  }
  return Array.from(set).sort((a, b) => a.localeCompare(b));
}

function renderKeywords() {
  const container = document.getElementById("keywords");
  container.innerHTML = "";
  const keys = uniqueKeywords();
  if (!keys.length) return;
  for (const k of keys) {
    const btn = document.createElement("button");
    btn.className = "keyword";
    btn.textContent = k;
    if (state.selectedKeywords.has(k)) btn.classList.add("active");
    btn.onclick = () => {
      if (state.selectedKeywords.has(k)) state.selectedKeywords.delete(k);
      else state.selectedKeywords.add(k);
      renderKeywords();
      renderList();
    };
    container.appendChild(btn);
  }
}

function fmtDate(iso) {
  const d = new Date(iso);
  return d.toISOString().slice(0, 10);
}

function renderList() {
  const list = document.getElementById("list");
  list.innerHTML = "";

  const q = state.search.trim().toLowerCase();
  const hasKW = state.selectedKeywords.size > 0;

  let items = state.papers.slice();

  items = items.filter(p => {
    if (q) {
      const text = `${p.title}\n${p.summary}`.toLowerCase();
      if (!text.includes(q)) return false;
    }
    if (hasKW) {
      const kws = new Set(p.matched_keywords || []);
      for (const k of state.selectedKeywords) {
        if (!kws.has(k)) return false;
      }
    }
    return true;
  });

  items.sort((a, b) => {
    const da = new Date(a.published).getTime();
    const db = new Date(b.published).getTime();
    return state.sort === "newest" ? db - da : da - db;
  });

  for (const p of items) {
    const card = document.createElement("div");
    card.className = "card";
    const cats = (p.categories || []).map(c => `<span class="tag">${c}</span>`).join(" ");
    const src = p.source ? `<span class="tag">${p.source}</span>` : "";
    const kws = (p.matched_keywords || []).map(k => `<span class="tag">${k}</span>`).join(" ");

    card.innerHTML = `
      <h3><a href="${p.link}" target="_blank" rel="noopener noreferrer">${p.title}</a></h3>
      <div class="meta">${fmtDate(p.published)} · ${p.authors?.slice(0, 5).join(", ") || ""}</div>
      <div>${(p.summary || "").slice(0, 240)}${(p.summary || "").length > 240 ? "…" : ""}</div>
      <div class="tags" style="margin-top:8px;">${src} ${cats} ${kws}</div>
    `;
    list.appendChild(card);
  }
}

function wireControls() {
  const search = document.getElementById("search");
  const sort = document.getElementById("sort");
  search.oninput = (e) => {
    state.search = e.target.value;
    renderList();
  };
  sort.onchange = (e) => {
    state.sort = e.target.value;
    renderList();
  };
}

wireControls();
loadData();
