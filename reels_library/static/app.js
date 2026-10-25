"use strict";

const $ = (selector, root = document) => root.querySelector(selector);
const $$ = (selector, root = document) => [...root.querySelectorAll(selector)];
const esc = (value) => String(value ?? "").replace(/[&<>"']/g, (character) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[character]);
const STAGES = { to_use: "À utiliser", in_progress: "En cours", used: "Utilisé", archived: "Archivé" };
const INTENTIONS = { learn: "À apprendre", cook: "À cuisiner", make: "À fabriquer", reference: "Référence" };
const STATUS = { imported: "Ajoutée", duplicate: "Doublon", ignored: "Ignorée", error: "Erreur" };
const state = { view: "library", category: "", data: null, current: null, importPayload: null, loadId: 0, syncRunning: false, syncLoading: false, lastSyncId: null };
let searchTimer;
let toastTimer;

const glyphs = {
  cook: '<path d="M8 3v7m4-7v7M4 3v7c0 3 8 3 8 0M8 12v17M24 29V3c-5 4-6 12 0 13"/>',
  learn: '<rect x="3" y="4" width="26" height="18" rx="3"/><path d="M11 29h10M16 22v7M10 10l-3 3 3 3m12-6 3 3-3 3m-4-7-3 9"/>',
  make: '<path d="m16 3 13 7v14l-13 7-13-7V10L16 3Zm0 14 13-7M16 17 3 10m13 7v14M9 6l13 8"/>',
  reference: '<rect x="5" y="3" width="23" height="28" rx="3"/><path d="M11 10h11M11 16h11M11 22h7"/>',
};
const icon = (kind) => `<svg viewBox="0 0 34 34" fill="none" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">${glyphs[kind] || glyphs.reference}</svg>`;

async function api(path, options = {}) {
  const response = await fetch(path, { ...options, headers: { ...(options.body ? { "Content-Type": "application/json" } : {}), ...options.headers } });
  const data = await response.json();
  if (!response.ok) throw new Error(data.error || "La requête a échoué.");
  return data;
}

function errorAt(selector, error) {
  const element = $(selector);
  element.textContent = error ? error.message || String(error) : "";
  element.hidden = !error;
}

function toast(message) {
  clearTimeout(toastTimer);
  $("#toast").textContent = message;
  $("#toast").hidden = false;
  toastTimer = setTimeout(() => { $("#toast").hidden = true; }, 4500);
}

async function busy(button, action) {
  button.disabled = true;
  try { return await action(); } finally { button.disabled = false; }
}

function openDialog(id) {
  $(id).showModal();
}

function formatDate(value, withTime = false) {
  if (!value) return "Date inconnue";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "Date inconnue";
  return new Intl.DateTimeFormat("fr-FR", { dateStyle: "medium", ...(withTime ? { timeStyle: "short" } : {}) }).format(date);
}

function filterParams() {
  const params = new URLSearchParams();
  for (const [key, selector] of [["q", "#search"], ["stage", "#stage-filter"], ["intention", "#intention-filter"], ["collection", "#collection-filter"], ["technical_status", "#coverage-filter"], ["sort", "#sort"]]) {
    if ($(selector).value) params.set(key, $(selector).value);
  }
  if (state.category) params.set("category", state.category);
  if (state.view === "starred") params.set("starred", "1");
  return params;
}

async function loadLibrary() {
  const loadId = ++state.loadId;
  $("#reel-grid").setAttribute("aria-busy", "true");
  try {
    const data = await api(`/api/library?${filterParams()}`);
    if (loadId !== state.loadId) return;
    state.data = data;
    errorAt("#global-error", null);
    renderLibrary();
  } catch (error) {
    if (loadId === state.loadId) errorAt("#global-error", new Error(`Impossible de charger la bibliothèque. ${error.message}`));
  } finally {
    if (loadId === state.loadId) $("#reel-grid").setAttribute("aria-busy", "false");
  }
}

function updateOptions(selector, options, firstLabel, current) {
  const select = $(selector);
  select.innerHTML = `<option value="">${esc(firstLabel)}</option>${options.map(({ value, label }) => `<option value="${esc(value)}">${esc(label)}</option>`).join("")}`;
  select.value = current || "";
}

function renderLibrary() {
  const { stats, reels, categories, collections } = state.data;
  $("#nav-total").textContent = stats.total;
  $("#nav-starred").textContent = stats.starred;
  $("#stats").innerHTML = [["▦", stats.total, "Idées sauvegardées"], ["↗", stats.to_use, "À utiliser"], ["✓", stats.used, "Idées utilisées"], ["☆", stats.starred, "Dans ma sélection"]].map(([symbol, count, label]) => `<div class="stat"><span class="stat-icon" aria-hidden="true">${symbol}</span><div><div class="stat-value">${count}</div><div class="stat-label">${label}</div></div></div>`).join("");
  $("#category-nav").innerHTML = categories.filter((category) => !category.archived).map((category) => `<button class="category-item ${state.category === category.name ? "active" : ""}" data-category="${esc(category.name)}"><span class="category-dot"></span><span>${esc(category.name)}</span><span class="nav-count">${category.count}</span></button>`).join("") + `<button class="category-item ${state.category === "__unclassified__" ? "active" : ""}" data-category="__unclassified__"><span class="category-dot"></span><span>À classer</span><span class="nav-count">${stats.unclassified}</span></button>`;
  updateOptions("#category-filter", [...categories.map((category) => ({ value: category.name, label: category.name + (category.archived ? " (archivé)" : "") })), { value: "__unclassified__", label: "À classer" }], "Tous les thèmes", state.category);
  updateOptions("#collection-filter", collections.map((collection) => ({ value: collection.name, label: collection.name })), "Toutes les collections", $("#collection-filter").value);
  const hasFilters = Boolean(state.category || $("#search").value || $("#stage-filter").value || $("#intention-filter").value || $("#collection-filter").value || $("#coverage-filter").value);
  $("#reset-filters").hidden = !hasFilters;
  $("#results-title").textContent = state.category === "__unclassified__" ? "Les idées à classer" : state.category || (state.view === "starred" ? "À garder sous la main" : "Toutes vos idées");
  $("#results-count").textContent = `${reels.length} référence${reels.length > 1 ? "s" : ""}`;
  $("#reel-grid").innerHTML = reels.map(card).join("");
  $("#empty-state").hidden = reels.length > 0;
  if (!reels.length) renderEmpty(stats.total, hasFilters);
}

function card(reel) {
  const kind = reel.intention !== "reference" ? reel.intention : reel.categories.some((name) => /cuisine/i.test(name)) ? "cook" : reel.categories.some((name) => /informatique|ia|data|robot/i.test(name)) ? "learn" : reel.categories.some((name) => /making|diy|3d/i.test(name)) ? "make" : "reference";
  const theme = { cook: "food", learn: "tech", make: "maker", reference: "other" }[kind];
  const title = reel.title || `Reel ${reel.url.split("/").filter(Boolean).pop()}`;
  const description = reel.summary || reel.notes || reel.source_text;
  const tags = [...reel.categories, ...reel.tags].slice(0, 4);
  return `<article class="reel-card theme-${theme}"><div class="card-top"><span class="card-glyph">${icon(kind)}</span><span class="card-type">${esc(INTENTIONS[kind])}</span><button class="star-button" data-star="${reel.id}" aria-pressed="${reel.starred}" aria-label="${reel.starred ? "Retirer de" : "Ajouter à"} ma sélection : ${esc(title)}">${reel.starred ? "★" : "☆"}</button></div><div class="card-body"><div class="card-author">${esc(reel.author || "Auteur non renseigné")}</div><button class="card-title" data-open="${reel.id}">${esc(title)}</button><p class="card-description ${description ? "" : "is-missing"}">${esc(description ? description.slice(0, 260) : "Le lien est conservé. Ajoutez du texte ou vos notes pour enrichir cette idée.")}</p><div class="card-tags">${tags.length ? tags.map((tag) => `<span class="tag">${esc(tag)}</span>`).join("") : '<span class="tag">À classer</span>'}</div></div><div class="card-footer"><span class="coverage ${reel.source_text ? "has-text" : ""}"><span class="coverage-dot"></span>${reel.source_text ? "Texte disponible" : "Lien seul"}</span><span class="stage-badge stage-${reel.stage}">${esc(STAGES[reel.stage])}</span></div></article>`;
}

function renderEmpty(total, hasFilters) {
  const selection = state.view === "starred" && total > 0 && !hasFilters;
  $("#empty-state").innerHTML = total > 0
    ? `<div class="empty-main"><div class="empty-symbol" aria-hidden="true">${selection ? "☆" : "⌕"}</div><h2>${selection ? "Vos prochaines bonnes idées, ici." : "Aucune idée avec ces filtres."}</h2><p>${selection ? "Cliquez sur l’étoile d’une référence pour la garder dans votre sélection personnelle." : "Essayez un autre mot, un thème différent ou effacez les filtres pour retrouver toutes vos références."}</p><button class="button button-secondary" data-empty-action="${selection ? "library" : "reset"}">${selection ? "Explorer ma bibliothèque" : "Effacer les filtres"}</button></div>`
    : '<div class="empty-main"><div class="empty-symbol" aria-hidden="true">↗</div><h2>Tout commence par une bonne idée.</h2><p>Une recette à cuisiner, un concept à comprendre, un projet à fabriquer. Rassemblez vos Reels ici pour les retrouver au bon moment.</p><div class="empty-actions"><button class="button button-primary" data-empty-action="add">+ Ajouter mon premier Reel</button><button class="button button-secondary" data-empty-action="import">Importer mes sauvegardes</button></div></div><div class="onboarding-grid"><div class="onboarding-step"><span class="step-number">01</span><div><h3>Rassemblez</h3><p>Un lien ou un fichier de sauvegardes.<br>Vos références ont enfin une place.</p></div></div><div class="onboarding-step"><span class="step-number">02</span><div><h3>Faites les liens</h3><p>Classez par thème, ajoutez vos notes<br>et retrouvez une idée avec vos mots.</p></div></div><div class="onboarding-step"><span class="step-number">03</span><div><h3>Passez à l’action</h3><p>Choisissez quoi apprendre, cuisiner<br>ou fabriquer. Marquez ce qui est utilisé.</p></div></div></div>';
}

function resetFilters() {
  state.category = "";
  for (const selector of ["#search", "#stage-filter", "#intention-filter", "#collection-filter", "#coverage-filter"]) $(selector).value = "";
  loadLibrary();
}

async function setView(view) {
  state.view = view;
  state.category = "";
  $$("[data-view]").forEach((button) => button.classList.toggle("active", button.dataset.view === view));
  const copy = {
    library: ["Votre bibliothèque", "Bibliothèque", "Retrouvez ce qui vous inspire. Faites-en quelque chose."],
    starred: ["Votre sélection", "Ma sélection", "Quelques idées à portée de main, quand le moment est venu."],
    imports: ["Vos imports", "Mes imports", "De nouvelles références, et une trace de chaque import."],
    sync: ["Vos sauvegardes, reliées", "Synchronisation", "D’Instagram à votre bibliothèque, avec un suivi de chaque passage."],
  }[view];
  $("#page-title").innerHTML = `${esc(copy[0])}<span>.</span>`;
  $("#breadcrumb").textContent = copy[1];
  $("#page-description").textContent = copy[2];
  $("#library-view").hidden = ["imports", "sync"].includes(view);
  $("#imports-view").hidden = view !== "imports";
  $("#sync-view").hidden = view !== "sync";
  await loadLibrary();
  if (view === "imports") await loadHistory();
  if (view === "sync") await loadSync(true);
}

async function loadSync(populate = false) {
  if (state.syncLoading) return;
  state.syncLoading = true;
  try {
    const data = await api("/api/sync");
    const form = $("#sync-form");
    if (populate) {
      for (const key of ["interval_minutes", "limit"]) form.elements[key].value = data.settings[key];
      form.elements.enabled.checked = data.settings.enabled;
    }
    const finished = state.syncRunning && !data.running;
    state.syncRunning = data.running;
    $$("button[type=submit]", form).forEach((button) => { button.disabled = data.running; });
    const last = data.runs[0];
    const heading = data.running ? "Synchronisation en cours…" : last?.status === "success" ? "Dernier passage réussi" : last ? "Une connexion à vérifier" : "Prêt pour le premier test";
    const description = data.running ? "Lecture des sauvegardes dans Instagram. Vos fiches actuelles restent disponibles." : last?.message || "Fournissez une session Instagram, puis lancez un premier passage.";
    $("#session-state").textContent = data.session.configured ? `Session présente dans cette installation · importée le ${formatDate(data.session.updated_at, true)}. Son accès effectif reste à vérifier par un passage.` : "Aucune session valide dans cette installation. Fichier Netscape, 128 Ko maximum.";
    $("#remove-session").hidden = !data.session.configured;
    $("button[type=submit]", $("#session-form")).disabled = data.running;
    $("#remove-session").disabled = data.running;
    $("#sync-status").classList.toggle("is-error", Boolean(!data.running && last && last.status !== "success"));
    $("#sync-status").innerHTML = `<h3>${esc(heading)}</h3><p>${esc(description)}</p>${data.next_run ? `<p>Prochain passage : ${esc(formatDate(data.next_run, true))}.</p>` : ""}`;
    const labels = { success: "Terminé", error: "Échec", running: "En cours", interrupted: "Interrompu" };
    $("#sync-history").innerHTML = data.runs.map((run) => `<article class="history-item"><span class="sync-run-status ${run.status === "error" ? "error" : ""}">${esc(labels[run.status] || run.status)}</span><h3>${esc(formatDate(run.started_at, true))}</h3><p class="sync-run-message">${esc(run.message || "Passage en cours…")}</p>${run.total !== null ? `<div class="history-counts"><span>${run.total} référence(s) reçue(s)</span><span>${run.imported} ajoutée(s)</span><span>${run.duplicate} déjà présente(s)</span><span>${run.ignored + run.error} ignorée(s) ou en erreur</span></div>` : ""}</article>`).join("") || '<p class="field-help">Aucun passage pour le moment.</p>';
    if (finished) await loadLibrary();
  } catch (error) { errorAt("#sync-error", error); }
  finally { state.syncLoading = false; }
}

async function loadHistory() {
  try {
    const { imports } = await api("/api/imports");
    $("#import-history").innerHTML = imports.length ? imports.map((job) => `<article class="history-item"><h3>${esc(job.filename)}</h3><span class="history-date">${esc(formatDate(job.created_at, true))} · ${job.total} entrée${job.total > 1 ? "s" : ""}</span><div class="history-counts"><span>${job.imported} ajoutée(s)</span><span>${job.duplicate} doublon(s)</span><span>${job.ignored} ignorée(s)</span><span>${job.error} erreur(s)</span></div></article>`).join("") : '<div class="empty-main"><div class="empty-symbol" aria-hidden="true">↓</div><h2>Votre historique commence ici.</h2><p>Importez un fichier de sauvegardes. Un bilan restera disponible après chaque import.</p></div>';
  } catch (error) { errorAt("#global-error", error); }
}

function openAdd() {
  $("#add-form").reset();
  errorAt("#add-error", null);
  openDialog("#add-dialog");
}

async function openDetail(identifier) {
  try {
    const reel = await api(`/api/reels/${identifier}`);
    state.current = reel;
    const form = $("#detail-form");
    for (const key of ["title", "author", "summary", "notes", "source_text", "stage", "intention", "kind"]) form.elements[key].value = reel[key];
    form.elements.tags.value = reel.tags.join(", ");
    form.elements.collections.value = reel.collections.join(", ");
    form.elements.starred.checked = reel.starred;
    $("#detail-source").innerHTML = `<a href="${esc(reel.url)}" target="_blank" rel="noopener noreferrer">Voir la publication Instagram ↗</a><span>${reel.saved_at ? `Sauvegardé le ${esc(formatDate(reel.saved_at))}` : `Ajouté le ${esc(formatDate(reel.imported_at))}`}</span>`;
    const categories = state.data.categories.filter((category) => !category.archived || reel.categories.includes(category.name));
    $("#detail-categories").innerHTML = categories.map((category) => `<label class="chip-label"><input type="checkbox" name="categories" value="${esc(category.name)}" ${reel.categories.includes(category.name) ? "checked" : ""}>${esc(category.name)}${category.archived ? " (archivé)" : ""}</label>`).join("") || '<p class="field-help">Créez un thème depuis la navigation pour classer cette référence.</p>';
    $("#detail-coverage").textContent = reel.source_text ? `Texte ${reel.source_kind === "manual" ? "fourni manuellement" : "présent dans l’import"}. Aucune analyse automatique n’a été effectuée.` : "Seul le lien est disponible. La vidéo, l’audio et les informations qu’ils contiennent n’ont pas été récupérés.";
    $("#detail-provenance").innerHTML = reel.sources.map((source) => `<details class="source-record"><summary>${source.kind === "manual" ? "Texte manuel" : "Entrée importée"} · ${esc(formatDate(source.created_at, true))}${source.text ? ` · ${source.text.length} caractères` : " · référence seule"}</summary><pre>${esc(JSON.stringify({ text: source.text, raw: source.raw }, null, 2))}</pre></details>`).join("");
    $(".source-details", form).open = false;
    errorAt("#detail-error", null);
    openDialog("#detail-dialog");
  } catch (error) { errorAt("#global-error", error); }
}

function invalidateImport() {
  state.importPayload = null;
  $("#commit-import").hidden = true;
  $("#import-report").hidden = true;
  errorAt("#import-error", null);
}

function openImport() {
  $("#import-form").reset();
  $("#import-filename").textContent = "";
  invalidateImport();
  openDialog("#import-dialog");
}

function renderReport(report, committed = false) {
  const counts = [["imported", committed ? "Ajoutée(s)" : "À ajouter"], ["duplicate", "Doublon(s)"], ["ignored", "Ignorée(s)"], ["error", "Erreur(s)"]];
  $("#import-report").innerHTML = `<div class="report-counts">${counts.map(([key, label]) => `<div class="report-count"><strong>${report[key]}</strong>${label}</div>`).join("")}</div><p class="report-note">${report.total} entrée(s) comptabilisée(s). ${committed ? "Import terminé. Vos corrections personnelles ont été conservées." : "Aucune donnée n’a encore été enregistrée. Les doublons conserveront leurs fiches actuelles."}</p>${report.entries.length ? `<div class="report-list">${report.entries.slice(0, 200).map((entry) => `<div class="report-line"><span>${entry.position}</span><span>${esc(STATUS[entry.status])}</span><span>${esc(entry.title || entry.url || entry.reason)}${entry.title || entry.url ? `<br>${esc(entry.reason)}` : ""}</span></div>`).join("")}</div>` : ""}${report.entries.length > 200 ? '<p class="field-help">Les 200 premières entrées sont affichées. Les totaux couvrent le fichier entier.</p>' : ""}`;
  $("#import-report").hidden = false;
}

function renderCategories() {
  $("#category-list").innerHTML = state.data.categories.map((category) => `<form class="category-editor" data-category-id="${category.id}" data-archived="${Boolean(category.archived)}"><label><span class="sr-only">Nom du thème</span><input name="name" value="${esc(category.name)}" maxlength="80" required></label><button type="submit" class="text-button" data-action="rename">Renommer</button><button type="submit" class="text-button" data-action="archive">${category.archived ? "Réactiver" : "Archiver"}</button></form>`).join("");
}

$$(".close-dialog").forEach((button) => button.addEventListener("click", () => button.closest("dialog").close()));
$$("[data-view]").forEach((button) => button.addEventListener("click", () => setView(button.dataset.view)));
$("#open-add").addEventListener("click", openAdd);
$("#open-import").addEventListener("click", openImport);
$("#reset-filters").addEventListener("click", resetFilters);
$("#search").addEventListener("input", () => { clearTimeout(searchTimer); searchTimer = setTimeout(loadLibrary, 180); });
for (const selector of ["#stage-filter", "#intention-filter", "#collection-filter", "#coverage-filter", "#sort"]) $(selector).addEventListener("change", loadLibrary);
$("#category-filter").addEventListener("change", (event) => { state.category = event.target.value; loadLibrary(); });
$("#category-nav").addEventListener("click", (event) => {
  const button = event.target.closest("[data-category]");
  if (!button) return;
  state.category = state.category === button.dataset.category ? "" : button.dataset.category;
  if (["imports", "sync"].includes(state.view)) {
    state.view = "library";
    const category = state.category;
    setView("library").then(() => { state.category = category; loadLibrary(); });
  } else loadLibrary();
});
$("#empty-state").addEventListener("click", (event) => {
  const action = event.target.closest("[data-empty-action]")?.dataset.emptyAction;
  if (action === "add") openAdd();
  if (action === "import") openImport();
  if (action === "reset") resetFilters();
  if (action === "library") setView("library");
});
$("#reel-grid").addEventListener("click", async (event) => {
  const open = event.target.closest("[data-open]");
  if (open) return openDetail(open.dataset.open);
  const star = event.target.closest("[data-star]");
  if (!star) return;
  try {
    await busy(star, () => api(`/api/reels/${star.dataset.star}`, { method: "PATCH", body: JSON.stringify({ starred: star.getAttribute("aria-pressed") !== "true" }) }));
    await loadLibrary();
  } catch (error) { errorAt("#global-error", error); }
});
$("#add-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  errorAt("#add-error", null);
  try {
    const data = Object.fromEntries(new FormData(event.currentTarget));
    const result = await busy($("button[type=submit]", event.currentTarget), () => api("/api/reels", { method: "POST", body: JSON.stringify(data) }));
    $("#add-dialog").close();
    await loadLibrary();
    toast(result.duplicate ? "Cette référence est déjà dans la bibliothèque. Sa fiche a été conservée." : "Une nouvelle idée dans votre bibliothèque.");
    await openDetail(result.id);
  } catch (error) { errorAt("#add-error", error); }
});
$("#detail-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  const form = event.currentTarget;
  const data = Object.fromEntries(new FormData(form));
  data.categories = $$("input[name=categories]:checked", form).map((input) => input.value);
  data.tags = data.tags.split(",").map((tag) => tag.trim()).filter(Boolean);
  data.collections = data.collections.split(",").map((name) => name.trim()).filter(Boolean);
  data.starred = form.elements.starred.checked;
  if (data.source_text === state.current.source_text) delete data.source_text;
  errorAt("#detail-error", null);
  try {
    await busy($("button[type=submit]", form), () => api(`/api/reels/${state.current.id}`, { method: "PATCH", body: JSON.stringify(data) }));
    $("#detail-dialog").close();
    await loadLibrary();
    toast("Votre fiche est enregistrée.");
  } catch (error) { errorAt("#detail-error", error); }
});
$("#delete-reel").addEventListener("click", async (event) => {
  if (!confirm("Supprimer cette référence, ses sources et vos notes ? Cette suppression est définitive. Vous pouvez aussi l’archiver depuis le champ Suivi.")) return;
  try {
    await busy(event.currentTarget, () => api(`/api/reels/${state.current.id}`, { method: "DELETE" }));
    $("#detail-dialog").close();
    await loadLibrary();
    toast("La référence et ses données ont été supprimées.");
  } catch (error) { errorAt("#detail-error", error); }
});
$("#import-file").addEventListener("change", () => {
  $("#import-text").value = "";
  $("#import-filename").textContent = $("#import-file").files[0]?.name || "";
  invalidateImport();
});
$("#import-text").addEventListener("input", () => {
  $("#import-file").value = "";
  $("#import-filename").textContent = "";
  invalidateImport();
});
$("#import-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  errorAt("#import-error", null);
  const file = $("#import-file").files[0];
  try {
    await busy($("#preview-import"), async () => {
      if (file && file.size > 10 * 1024 * 1024) throw new Error("Le fichier dépasse 10 Mo. Divisez-le en plusieurs fichiers de sauvegardes.");
      const content = file ? new TextDecoder("utf-8", { fatal: true }).decode(await file.arrayBuffer()) : $("#import-text").value;
      const payload = { content, filename: file?.name || "liens.txt" };
      const report = await api("/api/import/preview", { method: "POST", body: JSON.stringify(payload) });
      state.importPayload = payload;
      renderReport(report);
      $("#commit-import").hidden = report.imported === 0;
    });
  } catch (error) { errorAt("#import-error", error); }
});
$("#commit-import").addEventListener("click", async (event) => {
  if (!state.importPayload) return;
  const payload = state.importPayload;
  try {
    const report = await busy(event.currentTarget, () => api("/api/import", { method: "POST", body: JSON.stringify(payload) }));
    state.importPayload = null;
    $("#commit-import").hidden = true;
    renderReport(report, true);
    await loadLibrary();
    if (state.view === "imports") await loadHistory();
    toast(`${report.imported} référence(s) ajoutée(s).`);
  } catch (error) { errorAt("#import-error", error); }
});
$("#manage-categories").addEventListener("click", () => {
  if (!state.data) return;
  renderCategories();
  errorAt("#category-error", null);
  openDialog("#category-dialog");
});
$("#category-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  const form = event.currentTarget;
  try {
    await busy($("button[type=submit]", form), () => api("/api/categories", { method: "POST", body: JSON.stringify({ name: form.elements.name.value }) }));
    form.reset();
    await loadLibrary();
    renderCategories();
    errorAt("#category-error", null);
  } catch (error) { errorAt("#category-error", error); }
});
$("#category-list").addEventListener("submit", async (event) => {
  event.preventDefault();
  const form = event.target;
  const original = state.data.categories.find((category) => category.id === form.dataset.categoryId);
  const data = { name: form.elements.name.value, archived: event.submitter.dataset.action === "archive" ? !original.archived : Boolean(original.archived) };
  try {
    const result = await busy(event.submitter, () => api(`/api/categories/${form.dataset.categoryId}`, { method: "PATCH", body: JSON.stringify(data) }));
    if (state.category === original.name) state.category = result.name;
    await loadLibrary();
    renderCategories();
    errorAt("#category-error", null);
  } catch (error) { errorAt("#category-error", error); }
});
document.addEventListener("keydown", (event) => {
  if (event.key === "/" && !event.ctrlKey && !event.metaKey && !event.altKey && !$("dialog[open]") && !["INPUT", "TEXTAREA", "SELECT"].includes(document.activeElement.tagName)) {
    event.preventDefault();
    $("#search").focus();
  }
});
$("#sync-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  const form = event.currentTarget;
  const action = event.submitter.value;
  const settings = { enabled: form.elements.enabled.checked, interval_minutes: Number(form.elements.interval_minutes.value), limit: Number(form.elements.limit.value) };
  errorAt("#sync-error", null);
  try {
    await busy(event.submitter, async () => {
      await api("/api/sync/settings", { method: "POST", body: JSON.stringify(settings) });
      if (action === "run") {
        await api("/api/sync/start", { method: "POST", body: "{}" });
        state.syncRunning = true;
      } else toast("Les réglages de synchronisation sont enregistrés.");
    });
    await loadSync();
  } catch (error) { errorAt("#sync-error", error); }
});
$("#session-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  const form = event.currentTarget;
  const file = form.elements.session.files[0];
  errorAt("#session-error", null);
  try {
    await busy(event.submitter, async () => {
      if (!file || file.size > 128 * 1024) throw new Error("Choisissez un fichier de session de 128 Ko maximum.");
      const content = new TextDecoder("utf-8", { fatal: true }).decode(await file.arrayBuffer());
      await api("/api/sync/session", { method: "POST", body: JSON.stringify({ content }) });
    });
    form.reset();
    await loadSync();
    toast("La session est enregistrée dans cette installation. Vous pouvez tester la synchronisation.");
  } catch (error) { errorAt("#session-error", error); }
});
$("#remove-session").addEventListener("click", async (event) => {
  if (!confirm("Retirer la session Instagram de cette installation et désactiver les passages automatiques ? Vos références resteront dans la bibliothèque.")) return;
  try {
    await busy(event.currentTarget, () => api("/api/sync/session", { method: "DELETE" }));
    await loadSync(true);
    toast("Session retirée. La synchronisation automatique est désactivée.");
  } catch (error) { errorAt("#session-error", error); }
});
setInterval(() => { if (state.view === "sync" || state.syncRunning) loadSync(); }, 4000);
loadLibrary();
