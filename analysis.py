from typing import List
from models import Settings, Device
def calculate_total_power(devices: List[Device]) -> float:
    """Суммарная мощность всех приборов."""
    return sum(d.power for d in devices)
def get_top_devices(devices: List[Device], n: int) -> List[Device]:
    """N самых мощных приборов."""
    return sorted(devices, key=lambda d: d.power, reverse=True)[:n]
def calculate_load_by_hour(devices: List[Device]) -> list:
    """Массив мощности по часам (2–24 включительно, 23 часа всего).
    :rtype: object
    """
    hours = list(range(2, 25))  # 2..24
    load = [0.0 for _ in hours]
    for d in devices:
        for h in hours:
            if d.time_from <= h <= d.time_to:
                idx = h - 2
                load[idx] += d.power
    return load
def get_recommendations(settings: Settings, devices: List[Device]) -> list:
    """Формирование текстовых рекомендаций по правилам из ТЗ."""
    recs = []

    if not devices or settings.max_power <= 0:
        recs.append("Недостаточно данных для анализа. Заполните исходные данные и добавьте приборы.")
        return recs

    total_power = calculate_total_power(devices)
    max_power = settings.max_power * 1000
    if total_power >= 0.8 * max_power:
        load = calculate_load_by_hour(devices)
        if load:
            max_load = max(load)
            max_hour_index = load.index(max_load)
            hour_from = 2 + max_hour_index
            hour_to = hour_from + 2 if hour_from + 2 <= 24 else 24
            recs.append(
                f"Ограничьте использование приборов с {hour_from}:00 до {hour_to}:00."
            )
        else:
            recs.append("Ограничьте использование приборов в часы максимальной нагрузки.")

    top1 = get_top_devices(devices, 1)
    if top1:
        d = top1[0]
        if d.power >= 0.5 * max_power:
            recs.append(f"Замените прибор «{d.name}» на более экономичный.")

    top3 = get_top_devices(devices, 3)
    if len(top3) == 3:
        sum_top3 = sum(d.power for d in top3)
        if sum_top3 >= 0.5 * max_power:
            names = [d.name for d in top3]
            recs.append(
                f"Не используйте одновременно приборы «{names[0]}», «{names[1]}» и «{names[2]}»."
            )

    if not recs:
        recs.append("Все хорошо, использование электроприборов оптимальное.")
    return recs