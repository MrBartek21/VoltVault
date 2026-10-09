(() => {
  const title = document.querySelector("#waiting-title");
  const message = document.querySelector("#waiting-message");
  const countdownBox = document.querySelector("#countdown-box");
  const restartButton = document.querySelector("#restart-now");
  const errorBox = document.querySelector("#card-error");
  let reloading = false;
  async function refresh() {
    try {
      const response = await fetch("/system/status", { cache: "no-store" });
      const status = await response.json();
      if (status.ready) {
        title.textContent = status.restart_error ? "Nie udało się zrestartować" : "Karta SD gotowa";
        message.textContent = status.restart_error ? "Karta jest zamontowana. Możesz ponowić restart przyciskiem poniżej." : "Karta została zamontowana i dane magazynu są dostępne.";
        document.querySelector("#waiting-foot").innerHTML = '<span class="pulse-dot"></span> Karta zamontowana';
        countdownBox.classList.toggle("hidden", status.restart_countdown === null);
        restartButton.classList.remove("hidden");
        if (status.restart_countdown !== null) document.querySelector("#countdown").textContent = status.restart_countdown;
        if (status.restart_error) { errorBox.textContent = status.restart_error; errorBox.classList.remove("hidden"); }
        else errorBox.classList.add("hidden");
        if (status.restart_started && !status.restart_error && status.restart_countdown === null && !reloading) {
          if (status.emulator) sessionStorage.setItem("emulator-notice", `Symulowany restart urządzenia nr ${status.emulator_restart_count}. Komputer Windows nie został zrestartowany.`);
          reloading = true; location.reload();
        }
      } else {
        document.querySelector("#waiting-foot").innerHTML = '<span class="pulse-dot"></span> Oczekiwanie na kartę SD';
        title.textContent = status.device_present ? "Karta wykryta — nie można zamontować" : "Brak karty SD";
        message.textContent = status.device_present ? "Sprawdź etykietę karty, wpis w /etc/fstab i uprawnienia montowania." : "Włóż kartę pamięci, aby uruchomić magazyn i odczytać zapisane elementy.";
        countdownBox.classList.add("hidden"); restartButton.classList.add("hidden");
        if (status.error) { errorBox.textContent = status.error; errorBox.classList.remove("hidden"); }
      }
    } catch (_) { message.textContent = "Nie można połączyć się z usługą. Ponawiam sprawdzanie…"; }
  }
  restartButton.addEventListener("click", async () => {
    restartButton.disabled = true; restartButton.textContent = "Restartowanie…";
    try {
      const response = await fetch("/system/restart", { method: "POST" });
      const result = await response.json();
      if (!response.ok) throw new Error(result.detail || "Nie udało się uruchomić restartu.");
      message.textContent = "Urządzenie uruchamia się ponownie. Odśwież stronę za chwilę.";
    } catch (error) {
      errorBox.textContent = error.message; errorBox.classList.remove("hidden");
      restartButton.disabled = false; restartButton.textContent = "Zrestartuj teraz";
    }
    setTimeout(refresh, 2500);
  });
  refresh(); setInterval(refresh, 1000);
})();
