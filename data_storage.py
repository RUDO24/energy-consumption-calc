import json
import os
from typing import List
from models import Settings, Device, AppData
DATA_FILE = "data.json"
def _device_from_dict(d: dict) -> Device:
    return Device(
        location=d.get("location", ""),
        type=d.get("type", ""),
        name=d.get("name", ""),
        power=float(d.get("power", 0)),
        time_from=int(d.get("time_from", 2)),
        time_to=int(d.get("time_to", 2)),
    )
def _device_to_dict(device: Device) -> dict:
    return {
        "location": device.location,
        "type": device.type,
        "name": device.name,
        "power": device.power,
        "time_from": device.time_from,
        "time_to": device.time_to,
    }
def load_data() -> AppData:
    """Загрузка данных из файла JSON или создание пустых данных."""
    if not os.path.exists(DATA_FILE):
        settings = Settings()
        devices: List[Device] = []
        return AppData(settings=settings, devices=devices)

    with open(DATA_FILE, "r", encoding="utf-8") as f:
        raw = json.load(f)

    settings_raw = raw.get("settings", {})
    settings = Settings(
        object_name=settings_raw.get("object_name", ""),
        max_power=float(settings_raw.get("max_power", 0)),
    )

    devices_raw = raw.get("devices", [])
    devices = [_device_from_dict(d) for d in devices_raw]

    return AppData(settings=settings, devices=devices)
def save_data(app_data: AppData) -> None:
    """Сохранение данных в JSON."""
    data = {
        "settings": {
            "object_name": app_data.settings.object_name,
            "max_power": app_data.settings.max_power,
        },
        "devices": [_device_to_dict(d) for d in app_data.devices],
    }

    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)