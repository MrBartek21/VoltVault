(() => {
  const $ = id => document.getElementById(id);
  const formatBytes = bytes => {
    if (!Number.isFinite(bytes)) return "—";
    const units = ["B", "KB", "MB", "GB", "TB"];
    let value = bytes, index = 0;
    while (value >= 1000 && index < units.length - 1) { value /= 1000; index++; }
    return `${value.toFixed(index === 0 ? 0 : 1)} ${units[index]}`;
  };
  const formatMegabytes = value => Number(value || 0).toLocaleString("pl-PL", { maximumFractionDigits: 2 });
  const setMeter = (id, value) => {
    const meter = $(id); const percent = Math.max(0, Math.min(100, Number(value) || 0));
    meter.style.width = `${percent}%`; meter.classList.toggle("meter-warning", percent >= 80); meter.classList.toggle("meter-critical", percent >= 95);
  };
  async function refresh() {
    try {
      const response = await fetch("/system/metrics", { cache: "no-store" });
      if (!response.ok) throw new Error("Brak danych");
      const data = await response.json();
      $("cpu-value").textContent = `${data.cpu_percent.toFixed(0)}%`; setMeter("cpu-meter", data.cpu_percent);
      const ram = data.memory; $("ram-value").textContent = `${formatBytes(ram.used)} / ${formatBytes(ram.total)}`;
      $("ram-hint").textContent = `wykorzystano ${ram.percent.toFixed(1)}% · dostępne ${formatBytes(ram.available)}`; setMeter("ram-meter", ram.percent);
      if (data.sd_card) {
        const card = data.sd_card; $("sd-value").textContent = `${formatBytes(card.used)} / ${formatBytes(card.total)}`;
        $("sd-hint").textContent = `${card.percent.toFixed(1)}% zajęte · wolne ${formatBytes(card.free)}${data.sd_status.emulator ? " · dysk emulatora" : ""}`;
        setMeter("sd-meter", card.percent);
      } else {
        $("sd-value").textContent = "Brak karty"; $("sd-hint").textContent = data.sd_status.mount_path; setMeter("sd-meter", 0);
      }
      const disk = data.system_disk; $("system-disk-value").textContent = `${formatBytes(disk.used)} / ${formatBytes(disk.total)}`;
      $("system-disk-hint").textContent = `${disk.percent.toFixed(1)}% zajęte · wolne ${formatBytes(disk.free)} · ${disk.path}`; setMeter("system-disk-meter", disk.percent);
      $("network-sent").textContent = formatMegabytes(data.network.sent_mb);
      $("network-received").textContent = formatMegabytes(data.network.received_mb);
      $("network-interfaces").textContent = data.network.interfaces.length
        ? data.network.interfaces.map(item => `${item.name}: ↑ ${formatMegabytes(item.sent_mb)} MB · ↓ ${formatMegabytes(item.received_mb)} MB`).join("  |  ")
        : "Brak aktywnych kart sieciowych";
      $("system-state").textContent = data.sd_status.ready ? "System działa · karta dostępna" : "Brak karty SD";
    } catch (_) { $("system-state").textContent = "Nie można odczytać parametrów"; }
  }
  refresh(); setInterval(refresh, 5000);
})();
