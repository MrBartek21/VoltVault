(() => {
  const showToast = message => {
    let toast = document.querySelector("#emulator-toast");
    if (!toast) { toast = document.createElement("div"); toast.id = "emulator-toast"; toast.className = "emulator-toast"; toast.setAttribute("role", "status"); document.body.appendChild(toast); }
    toast.textContent = message; toast.classList.add("show"); setTimeout(() => toast.classList.remove("show"), 4000);
  };
  const post = async (url, body = {}) => {
    const response = await fetch(url, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) });
    const result = await response.json();
    if (!response.ok) throw new Error(result.detail || "Operacja emulatora nie powiodła się.");
    return result;
  };
  const insert = document.querySelector("#emulator-insert");
  if (insert) insert.addEventListener("click", async () => {
    insert.disabled = true;
    try { await post("/emulator/card/insert"); sessionStorage.setItem("emulator-notice", "Wirtualna karta SD włożona. Rozpoczęło się odliczanie do symulowanego restartu."); location.reload(); }
    catch (error) { insert.disabled = false; showToast(error.message); }
  });
  const remove = document.querySelector("#emulator-remove");
  if (remove) remove.addEventListener("click", async () => {
    if (!confirm("Wyjąć wirtualną kartę SD? Dane pozostaną zapisane w folderze emulatora.")) return;
    try { await post("/emulator/card/remove"); location.reload(); }
    catch (error) { showToast(error.message); }
  });
  const restart = document.querySelector("#emulator-restart");
  if (restart) restart.addEventListener("click", async () => {
    restart.disabled = true;
    try {
      const result = await post("/system/restart");
      showToast(result.message);
      setTimeout(() => { restart.disabled = false; }, 900);
    } catch (error) { showToast(error.message); restart.disabled = false; }
  });
  const reset = document.querySelector("#emulator-reset");
  if (reset) reset.addEventListener("click", async () => {
    if (!confirm("Usunąć wszystkie elementy i obrazy z wirtualnej karty? Tej operacji nie można cofnąć.")) return;
    try { await post("/emulator/reset-data"); showToast("Dane testowe wyczyszczone."); setTimeout(() => location.reload(), 500); }
    catch (error) { showToast(error.message); }
  });
  const notice = sessionStorage.getItem("emulator-notice");
  if (notice) { sessionStorage.removeItem("emulator-notice"); showToast(notice); }
})();
