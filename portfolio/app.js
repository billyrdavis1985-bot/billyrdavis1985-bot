/* Progressive enhancement: all repository links exist in the generated HTML. */
(() => {
  "use strict";
  const form = document.querySelector("#project-filters");
  if (!form) return;
  const motion = document.querySelector("#hero-motion");
  if (motion) {
    const artwork = motion.closest(".hero-art");
    artwork.classList.add("is-animated");
    motion.hidden = false;
    motion.addEventListener("click", () => {
      const paused = artwork.classList.toggle("motion-paused");
      motion.textContent = paused ? "Play motion" : "Pause motion";
    });
  }

  const query = document.querySelector("#query");
  const category = document.querySelector("#category");
  const language = document.querySelector("#language");
  const sort = document.querySelector("#sort");
  const list = document.querySelector("#repository-list");
  const count = document.querySelector("#result-count");
  const reset = document.querySelector("#reset-filters");
  const more = document.querySelector("#load-more");
  const empty = document.querySelector("#empty-results");
  const rows = [...list.querySelectorAll(".repo-item")];
  const pageSize = 12;
  let limit = pageSize;
  const normalize = value => value.normalize("NFKD").replace(/[\u0300-\u036f]/g, "").toLocaleLowerCase();
  const records = rows.map(node => ({node, search: normalize(node.dataset.search), name: node.dataset.name,
    category: node.dataset.category, language: node.dataset.language, kind: node.dataset.kind,
    stars: Number(node.dataset.stars), updated: node.dataset.updated}));
  const validSelect = (select, value) => [...select.options].some(option => option.value === value);
  const params = new URLSearchParams(location.search);
  query.value = (params.get("q") || "").slice(0, 200);
  if (validSelect(category, params.get("field"))) category.value = params.get("field");
  if (validSelect(language, params.get("language"))) language.value = params.get("language");
  if (validSelect(sort, params.get("sort"))) sort.value = params.get("sort");
  const initialKind = params.get("kind");
  if (["original", "fork", "all"].includes(initialKind)) form.querySelector(`input[value="${initialKind}"]`).checked = true;
  const state = () => ({q: query.value.trim(), field: category.value, language: language.value,
    sort: sort.value, kind: form.querySelector('input[name="kind"]:checked').value});
  function render(resetLimit = true) {
    if (resetLimit) limit = pageSize;
    const value = state();
    const terms = normalize(value.q).split(/\s+/).filter(Boolean);
    const filtered = records.filter(record => terms.every(term => record.search.includes(term))
      && (value.field === "all" || record.category === value.field)
      && (value.language === "all" || record.language === value.language)
      && (value.kind === "all" || record.kind === value.kind));
    filtered.sort((a, b) => value.sort === "name" ? a.name.localeCompare(b.name)
      : value.sort === "stars" ? b.stars - a.stars || a.name.localeCompare(b.name)
      : b.updated.localeCompare(a.updated) || a.name.localeCompare(b.name));
    records.forEach(record => { record.node.hidden = true; });
    filtered.forEach((record, index) => { record.node.hidden = index >= limit; });
    list.replaceChildren(...filtered.map(record => record.node));
    const shown = Math.min(limit, filtered.length);
    count.textContent = `${filtered.length} ${filtered.length === 1 ? "repository" : "repositories"} found · showing ${shown}`;
    more.hidden = shown >= filtered.length;
    more.textContent = `Show ${Math.min(pageSize, filtered.length - shown)} more projects`;
    empty.hidden = filtered.length !== 0;
    list.hidden = filtered.length === 0;
    reset.hidden = value.q === "" && value.field === "all" && value.language === "all" && value.kind === "original" && value.sort === "updated";
    const nextParams = new URLSearchParams();
    if (value.q) nextParams.set("q", value.q);
    if (value.field !== "all") nextParams.set("field", value.field);
    if (value.language !== "all") nextParams.set("language", value.language);
    if (value.kind !== "original") nextParams.set("kind", value.kind);
    if (value.sort !== "updated") nextParams.set("sort", value.sort);
    const search = nextParams.toString();
    history.replaceState(null, "", `${location.pathname}${search ? `?${search}` : ""}${location.hash}`);
  }
  function clear() { form.reset(); limit = pageSize; render(); }
  form.addEventListener("submit", event => {event.preventDefault();render();});
  query.addEventListener("input", () => render());
  [category, language, sort].forEach(control => control.addEventListener("change", () => render()));
  form.querySelectorAll('input[name="kind"]').forEach(control => control.addEventListener("change", () => render()));
  reset.addEventListener("click", clear);
  document.querySelector("#empty-reset").addEventListener("click", () => {clear();query.focus();});
  more.addEventListener("click", () => {limit += pageSize;render(false);});
  document.querySelector("#filter-controls").disabled = false;
  render();
})();
