# -*- coding: utf-8 -*-
"""Required removable SD storage for VoltVault."""
import json
import os
import subprocess
from pathlib import Path

APP_NAME = "VoltVault"
CARD_LABEL = "BACKUP_SD"
CARD_UUID = "79A2-FD57"
MOUNT_PATH = Path("/mnt") / APP_NAME
DEVICE_PATHS = (
    Path("/dev/disk/by-label") / CARD_LABEL,
    Path("/dev/disk/by-uuid") / CARD_UUID,
)

class SDManager:
    def __init__(self, mount_point=str(MOUNT_PATH), device_paths=DEVICE_PATHS, emulator=False, emulator_root=None):
        self.emulator = emulator
        self.mount_point = Path(emulator_root) if emulator_root else Path(mount_point)
        self.device_paths = tuple(Path(item) for item in device_paths)
        self.inserted_marker = self.mount_point / ".emulator-card-inserted"
        self.last_error = ""
        if self.emulator:
            self.mount_point.mkdir(parents=True, exist_ok=True)

    def is_device_present(self):
        return self.inserted_marker.exists() if self.emulator else any(path.exists() for path in self.device_paths)

    def detected_device(self):
        if self.emulator:
            return str(self.inserted_marker) if self.inserted_marker.exists() else None
        for path in self.device_paths:
            if path.exists():
                return str(path)
        return None

    def is_mounted(self):
        return self.is_device_present() if self.emulator else self.mount_point.is_mount()

    def set_emulator_inserted(self, inserted):
        if not self.emulator:
            raise RuntimeError("Emulator karty jest wyłączony")
        self.mount_point.mkdir(parents=True, exist_ok=True)
        if inserted:
            self.inserted_marker.touch(exist_ok=True)
        else:
            self.inserted_marker.unlink(missing_ok=True)

    def ensure_mounted(self):
        self.last_error = ""
        self.mount_point.mkdir(parents=True, exist_ok=True)
        if self.emulator:
            if not self.is_device_present():
                self.last_error = "W emulatorze nie włożono wirtualnej karty SD."
                return False
            return True
        if self.is_mounted():
            return True
        if not self.is_device_present():
            self.last_error = f"Nie wykryto karty {CARD_LABEL} ani UUID {CARD_UUID}."
            return False
        try:
            result = subprocess.run(
                ["sudo", "-n", "mount", str(self.mount_point)],
                capture_output=True, text=True, timeout=8, check=False,
            )
            if result.returncode == 0 and self.is_mounted():
                return True
            detail = (result.stderr or result.stdout).strip()
            self.last_error = detail or "System nie zamontował karty SD. Sprawdź /etc/fstab i uprawnienia sudo."
        except (OSError, subprocess.TimeoutExpired) as exc:
            self.last_error = str(exc)
        return False

    def ready(self):
        return self.ensure_mounted()

    def status(self):
        present = self.is_device_present()
        mounted = self.is_mounted()
        if not mounted and present:
            mounted = self.ensure_mounted()
        if not present and not mounted:
            self.last_error = f"Nie wykryto karty {CARD_LABEL} ani UUID {CARD_UUID}."
        return {
            "app_name": APP_NAME,
            "emulator": self.emulator,
            "mount_path": str(self.mount_point),
            "detected_device": self.detected_device(),
            "accepted_label": CARD_LABEL,
            "accepted_uuid": CARD_UUID,
            "device_present": present,
            "mounted": mounted,
            "ready": mounted,
            "error": self.last_error,
        }

    def _path(self, filename):
        path = (self.mount_point / filename).resolve()
        if not path.is_relative_to(self.mount_point.resolve()):
            raise ValueError("Nieprawidłowa ścieżka pliku")
        return path

    def write_file(self, filename, data):
        if not self.is_mounted():
            raise RuntimeError("Karta SD nie jest zamontowana")
        path = self._path(filename)
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp = path.with_suffix(path.suffix + ".tmp")
        with tmp.open("w", encoding="utf-8") as handle:
            json.dump(data, handle, ensure_ascii=False, indent=2)
            handle.flush()
            os.fsync(handle.fileno())
        tmp.replace(path)

    def read_file(self, filename):
        if not self.is_mounted():
            return {}
        path = self._path(filename)
        if not path.is_file():
            return {}
        try:
            with path.open(encoding="utf-8") as handle:
                data = json.load(handle)
            return data if isinstance(data, dict) else {}
        except (OSError, json.JSONDecodeError):
            return {}
