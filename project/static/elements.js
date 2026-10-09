(() => {
  const $ = (selector) => document.querySelector(selector);
  const tbody = $("#elements-table tbody");
  const modal = $("#element-modal");
  const form = $("#element-form");
  const search = $("#search");
  const categoryFilter = $("#category-filter");
  let allElements = [];
  let editingId = null;
  let toastTimer;

  function notify(message) {
    const toast = $("#toast"); toast.textContent = message; toast.classList.add("show");
    clearTimeout(toastTimer); toastTimer = setTimeout(() => toast.classList.remove("show"), 2600);
  }
  function openModal(element = null) {
    editingId = element?.id ?? null; form.reset();
    $("#modal-title").textContent = element ? "Edytuj element" : "Dodaj element";
    if (element) for (const key of ["nazwa", "oznaczenie", "kategorie", "ilosc", "cena", "opis", "datasheet"]) {
      const input = document.getElementById(key); if (input) input.value = element[key] ?? "";
    }
    modal.classList.remove("hidden"); $("#nazwa").focus();
  }
  function closeModal() { modal.classList.add("hidden"); editingId = null; }
  $("#add-element").addEventListener("click", () => openModal());
  $("#empty-add").addEventListener("click", () => openModal());
  $(".close-btn").addEventListener("click", closeModal);
  $("#cancel-modal").addEventListener("click", closeModal);
  modal.addEventListener("click", event => { if (event.target === modal) closeModal(); });
  document.addEventListener("keydown", event => { if (event.key === "Escape") closeModal(); });

  async function request(url, options) {
    const response = await fetch(url, options);
    if (!response.ok) { let message = "Wystąpił błąd."; try { message = (await response.json()).detail || message; } catch {} throw new Error(message); }
    return response.status === 204 ? null : response.json();
  }
  function updateStats(items) {
    $("#total-quantity").textContent = items.reduce((sum, item) => sum + (Number(item.ilosc) || 0), 0);
    $("#unique-count").textContent = items.length;
    $("#low-count").textContent = items.filter(item => Number(item.ilosc) <= 5).length;
  }
  function cell(row, text, className = "") {
    const td = document.createElement("td"); td.textContent = text || "—"; if (className) td.className = className; row.appendChild(td); return td;
  }
  function render() {
    const term = search.value.trim().toLocaleLowerCase("pl");
    const category = categoryFilter.value;
    const filtered = allElements.filter(item => {
      const searchable = [item.nazwa, item.oznaczenie, item.kategorie, item.opis].join(" ").toLocaleLowerCase("pl");
      return (!term || searchable.includes(term)) && (!category || item.kategorie === category);
    });
    tbody.replaceChildren(); $("#empty-state").classList.toggle("hidden", filtered.length > 0);
    $("#result-count").textContent = `Wyświetlono ${filtered.length} z ${allElements.length} pozycji`;
    for (const item of filtered) {
      const row = document.createElement("tr");
      const name = cell(row, "", "item-name");
      const nameWrap = document.createElement("div"); nameWrap.textContent = item.nazwa || "Bez nazwy"; name.appendChild(nameWrap);
      const sub = document.createElement("div"); sub.className = "item-sub"; sub.textContent = `ID: ${item.id}`; name.appendChild(sub);
      cell(row, item.oznaczenie);
      const categoryCell = cell(row, ""); const tag = document.createElement("span"); tag.className = "tag"; tag.textContent = item.kategorie || "Inne"; categoryCell.appendChild(tag);
      const quantity = Number(item.ilosc) || 0; cell(row, String(quantity), `qty${quantity <= 2 ? " critical" : quantity <= 5 ? " low" : ""}`);
      const price = Number(item.cena); cell(row, Number.isFinite(price) && price > 0 ? `${price.toFixed(2)} zł` : "—");
      const descriptionCell = cell(row, item.opis || "—");
      if (item.datasheet) { descriptionCell.replaceChildren(); const link = document.createElement("a"); link.href = item.datasheet; link.target = "_blank"; link.rel = "noopener noreferrer"; link.textContent = item.opis || "Datasheet ↗"; descriptionCell.appendChild(link); }
      const actions = cell(row, "", "actions");
      const edit = document.createElement("button"); edit.type = "button"; edit.className = "icon-btn"; edit.textContent = "Edytuj"; edit.addEventListener("click", () => openModal(item)); actions.appendChild(edit);
      const remove = document.createElement("button"); remove.type = "button"; remove.className = "icon-btn delete"; remove.textContent = "Usuń";
      remove.addEventListener("click", async () => { if (!confirm(`Usunąć element „${item.nazwa}”?`)) return; try { await request(`/elements/delete/${encodeURIComponent(item.id)}`, { method: "POST" }); await loadElements(); notify("Element usunięty."); } catch (error) { notify(error.message); } }); actions.appendChild(remove);
      tbody.appendChild(row);
    }
  }
  function updateCategories() {
    const selected = categoryFilter.value;
    const categories = [...new Set(allElements.map(item => item.kategorie).filter(Boolean))].sort((a,b) => a.localeCompare(b, "pl"));
    categoryFilter.replaceChildren(new Option("Wszystkie kategorie", ""));
    for (const category of categories) categoryFilter.add(new Option(category, category));
    categoryFilter.value = categories.includes(selected) ? selected : "";
  }
  async function loadElements() {
    try { allElements = await request("/elements/list"); updateStats(allElements); updateCategories(); render(); }
    catch (error) { notify(`Nie udało się wczytać magazynu: ${error.message}`); }
  }
  search.addEventListener("input", render); categoryFilter.addEventListener("change", render);
  form.addEventListener("submit", async event => {
    event.preventDefault();
    const data = Object.fromEntries(["nazwa", "oznaczenie", "kategorie", "ilosc", "cena", "opis", "datasheet"].map(key => [key, document.getElementById(key).value.trim()]));
    data.ilosc = Number(data.ilosc); data.cena = Number(data.cena) || 0;
    try {
      const wasEditing = editingId !== null;
      const url = wasEditing ? `/elements/edit/${encodeURIComponent(editingId)}` : "/elements/add";
      await request(url, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(data) });
      closeModal(); await loadElements(); notify(wasEditing ? "Zmiany zapisane." : "Element dodany.");
    } catch (error) { notify(error.message); }
  });
  async function monitorCard() {
    try {
      const response = await fetch("/system/status", { cache: "no-store" });
      const status = await response.json();
      if (!status.ready) location.reload();
    } catch (_) { /* preserve the current view while the server restarts */ }
  }
  loadElements();
  setInterval(monitorCard, 3000);
})();
