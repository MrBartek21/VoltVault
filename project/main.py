# -*- coding: utf-8 -*-
"""VoltVault: offline electronics inventory with required SD-card storage."""
import asyncio
import os
import shutil
import subprocess
import time
import psutil
from pathlib import Path
from fastapi import FastAPI, Request, UploadFile, File, HTTPException
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from element_manager import ElementManager
from sd_manager import SDManager, APP_NAME, CARD_LABEL, CARD_UUID

BASE_DIR = Path(__file__).resolve().parent
MOUNT_PATH = Path("/mnt") / APP_NAME
SD_POLL_SECONDS = 2
RESTART_DELAY_SECONDS = int(os.environ.get("VOLTVAULT_RESTART_DELAY", os.environ.get("ELEKTROMAGAZYN_RESTART_DELAY", "30")))

EMULATOR = os.environ.get("VOLTVAULT_EMULATOR", os.environ.get("ELEKTROMAGAZYN_EMULATOR", "0")) == "1"
EMULATOR_ROOT = BASE_DIR / "emulator_sd"

sd = SDManager(emulator=EMULATOR, emulator_root=EMULATOR_ROOT if EMULATOR else None)
IMAGE_DIR = sd.mount_point / "images"
sd_ready = False
inserted_at = None
reboot_started = False
restart_error = ""
emulator_restart_count = 0
last_emulator_restart = None

app = FastAPI(title=APP_NAME)
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))
elements = ElementManager(sd)

async def monitor_sd_card():
    """Watch for insertion. A card present at boot is mounted and used directly."""
    global sd_ready, inserted_at, reboot_started, restart_error
    sd_ready = sd.ready()
    while True:
        await asyncio.sleep(SD_POLL_SECONDS)
        was_ready = sd_ready
        now_ready = sd.ready()
        if now_ready and not was_ready:
            elements.load_elements()
            inserted_at = time.monotonic()
            reboot_started = False
            restart_error = ""
        elif not now_ready and was_ready:
            sd_ready = False
            inserted_at = None
            reboot_started = False
            continue
        sd_ready = now_ready
        if now_ready and inserted_at is not None and not reboot_started:
            if time.monotonic() - inserted_at >= RESTART_DELAY_SECONDS:
                reboot_started = True
                success, message = reboot_device()
                if not success:
                    restart_error = message

@app.on_event("startup")
async def startup():
    asyncio.create_task(monitor_sd_card())

def reboot_device():
    """Reboot the Pi, or safely simulate a reboot during Windows development."""
    global emulator_restart_count, last_emulator_restart
    if EMULATOR:
        emulator_restart_count += 1
        last_emulator_restart = time.strftime("%Y-%m-%d %H:%M:%S")
        return True, f"Symulacja restartu nr {emulator_restart_count}; komputer Windows nie został zrestartowany."
    try:
        result = subprocess.run(["sudo", "-n", "/sbin/reboot"], capture_output=True, text=True, timeout=5)
        if result.returncode != 0:
            result = subprocess.run(["sudo", "-n", "/usr/sbin/reboot"], capture_output=True, text=True, timeout=5)
        if result.returncode != 0:
            return False, (result.stderr or result.stdout).strip() or "Polecenie restartu nie powiodło się."
        return True, "Restart urządzenia został uruchomiony."
    except (OSError, subprocess.TimeoutExpired) as exc:
        return False, str(exc)

def require_sd():
    global sd_ready
    sd_ready = sd.is_mounted()
    if not sd_ready:
        raise HTTPException(status_code=503, detail="Brak zamontowanej karty SD")

def observe_sd_status(status):
    global sd_ready, inserted_at, reboot_started, restart_error
    if status["ready"] and not sd_ready:
        elements.load_elements()
        inserted_at = time.monotonic()
        reboot_started = False
        restart_error = ""
    elif not status["ready"] and sd_ready:
        inserted_at = None
        reboot_started = False
        restart_error = ""
    sd_ready = status["ready"]

@app.get("/", response_class=HTMLResponse)
@app.get("/elements", response_class=HTMLResponse)
async def inventory_page(request: Request):
    status = sd.status()
    observe_sd_status(status)
    if status["ready"] and (inserted_at is None or (reboot_started and not restart_error)):
        return templates.TemplateResponse(request=request, name="elements.html", context={"app_name": APP_NAME, "emulator": EMULATOR})
    return templates.TemplateResponse(request=request, name="sd_missing.html", context={"app_name": APP_NAME, "mount_path": str(sd.mount_point), "emulator": EMULATOR, "card_label": CARD_LABEL, "card_uuid": CARD_UUID})


@app.get("/system/metrics")
async def system_metrics():
    """Return host, storage, and network counters for the local dashboard."""
    memory = psutil.virtual_memory()
    system_root = (os.environ.get("SystemDrive", "C:") + os.sep) if os.name == "nt" else "/"
    system_disk = psutil.disk_usage(system_root)
    card_status = sd.status()
    card_disk = None
    if card_status["ready"]:
        try:
            usage = psutil.disk_usage(str(sd.mount_point))
            card_disk = {"total": usage.total, "used": usage.used, "free": usage.free, "percent": usage.percent}
        except OSError:
            card_status["ready"] = False
    counters = psutil.net_io_counters(pernic=True) or {}
    interface_states = psutil.net_if_stats()
    interfaces = []
    for name, counter in counters.items():
        normalized = name.casefold()
        state = interface_states.get(name)
        if normalized in {"lo", "loopback pseudo-interface 1"} or (state and not state.isup):
            continue
        interfaces.append({"name": name, "sent_mb": counter.bytes_sent / 1_000_000, "received_mb": counter.bytes_recv / 1_000_000})
    return {
        "cpu_percent": psutil.cpu_percent(interval=None),
        "memory": {"total": memory.total, "used": memory.used, "available": memory.available, "percent": memory.percent},
        "system_disk": {"path": system_root, "total": system_disk.total, "used": system_disk.used, "free": system_disk.free, "percent": system_disk.percent},
        "sd_card": card_disk,
        "sd_status": {"ready": card_status["ready"], "emulator": EMULATOR, "mount_path": str(sd.mount_point)},
        "network": {
            "sent_mb": sum(item["sent_mb"] for item in interfaces),
            "received_mb": sum(item["received_mb"] for item in interfaces),
            "interfaces": interfaces,
        },
        "updated_at": time.time(),
    }

@app.get("/system/status")
async def system_status():
    status = sd.status()
    observe_sd_status(status)
    remaining = None
    if sd_ready and inserted_at is not None and not reboot_started:
        remaining = max(0, RESTART_DELAY_SECONDS - int(time.monotonic() - inserted_at))
    status.update({"restart_countdown": remaining, "restart_started": reboot_started, "restart_error": restart_error,
                   "emulator_restart_count": emulator_restart_count, "last_emulator_restart": last_emulator_restart})
    return status

@app.post("/system/restart")
async def restart_now():
    require_sd()
    global reboot_started, restart_error
    reboot_started = True
    restart_error = ""
    success, message = reboot_device()
    if not success:
        reboot_started = False
        restart_error = message
        raise HTTPException(status_code=503, detail=f"Nie udało się zrestartować urządzenia: {message}")
    return {"status": "restarting", "message": message}

@app.post("/emulator/card/insert")
async def emulator_insert_card():
    if not EMULATOR:
        raise HTTPException(status_code=404, detail="Emulator jest wyłączony")
    sd.set_emulator_inserted(True)
    return {"status": "inserted", "mount_path": str(sd.mount_point)}

@app.post("/emulator/card/remove")
async def emulator_remove_card():
    if not EMULATOR:
        raise HTTPException(status_code=404, detail="Emulator jest wyłączony")
    sd.set_emulator_inserted(False)
    return {"status": "removed"}

@app.post("/emulator/reset-data")
async def emulator_reset_data():
    if not EMULATOR:
        raise HTTPException(status_code=404, detail="Emulator jest wyłączony")
    require_sd()
    elements.elements = {}
    elements.save_elements()
    if IMAGE_DIR.exists():
        for image in IMAGE_DIR.iterdir():
            if image.is_file():
                image.unlink()
    return {"status": "reset"}

@app.get("/elements/list")
async def list_elements():
    require_sd()
    return elements.list_elements()

@app.get("/elements/get/{element_id}")
async def get_element(element_id: str):
    require_sd()
    el = elements.elements.get(str(element_id))
    if el is None: raise HTTPException(status_code=404, detail="Nie znaleziono elementu")
    return el

@app.post("/elements/add")
async def add_element(data: dict):
    require_sd()
    if not data.get("nazwa") or not data.get("oznaczenie"):
        raise HTTPException(status_code=422, detail="Nazwa i oznaczenie są wymagane")
    from uuid import uuid4
    data["id"] = str(data.get("id") or uuid4().hex[:12])
    data["ilosc"] = max(0, int(data.get("ilosc", 1)))
    elements.add_or_update_element(data)
    return {"status": "ok"}

@app.post("/elements/edit/{element_id}")
async def edit_element(element_id: str, data: dict):
    require_sd()
    if element_id not in elements.elements: raise HTTPException(status_code=404, detail="Nie znaleziono elementu")
    elements.edit_element(element_id, data)
    return {"status": "ok"}

@app.post("/elements/delete/{element_id}")
async def delete_element(element_id: str):
    require_sd()
    if element_id not in elements.elements: raise HTTPException(status_code=404, detail="Nie znaleziono elementu")
    elements.delete_element(element_id)
    return {"status": "ok"}

@app.get("/elements/search/{query}")
async def search_elements(query: str):
    require_sd()
    return elements.search(query)

@app.post("/elements/upload-image/{element_id}")
async def upload_image(element_id: str, file: UploadFile = File(...)):
    require_sd()
    if element_id not in elements.elements: raise HTTPException(status_code=404, detail="Nie znaleziono elementu")
    ext = Path(file.filename or "image").suffix.lower()
    if ext not in {".png", ".jpg", ".jpeg", ".webp", ".gif"}:
        raise HTTPException(status_code=400, detail="Nieobsługiwany format obrazu")
    IMAGE_DIR.mkdir(parents=True, exist_ok=True)
    filename = f"{element_id}{ext}"
    with (IMAGE_DIR / filename).open("wb") as out: shutil.copyfileobj(file.file, out)
    elements.edit_element(element_id, {"image": f"/images/{filename}"})
    return {"status": "ok", "image": filename}

@app.get("/images/{filename}")
async def get_image(filename: str):
    require_sd()
    path = (IMAGE_DIR / Path(filename).name).resolve()
    if not path.is_relative_to(IMAGE_DIR.resolve()) or not path.is_file():
        raise HTTPException(status_code=404, detail="Nie znaleziono obrazu")
    return FileResponse(path)
