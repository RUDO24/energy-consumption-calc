import tkinter as tk
from tkinter import ttk, messagebox
from typing import Optional, List
from models import Settings, Device, AppData
from data_storage import load_data, save_data
from analysis import calculate_total_power, get_top_devices, calculate_load_by_hour, get_recommendations
import matplotlib
matplotlib.use('TkAgg')
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import numpy as np
LOCATIONS = [
    "Коридор",
    "Прихожая",
    "Ванная",
    "Туалет",
    "Кухня",
    "Зал",
    "Спальня",
    "Детская",
    "Балкон",
]
TYPES = [
    "Освещение",
    "Бытовой прибор",
    "Вентиляция",
    "Обогрев",
]
class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Калькулятор потребления электроэнергии")
        self.geometry("900x600")
        self.app_data: AppData = load_data()

        self.frame_settings = ttk.LabelFrame(self, text="Исходные данные")
        self.frame_summary = ttk.LabelFrame(self, text="Суммарно")
        self.frame_devices = ttk.LabelFrame(self, text="Список электроприборов")

        self.frame_settings.pack(fill="x", padx=10, pady=5)
        self.frame_summary.pack(fill="x", padx=10, pady=5)
        self.frame_devices.pack(fill="both", expand=True, padx=10, pady=5)

        self._init_settings_block()
        self._init_summary_block()
        self._init_devices_block()

        self.update_summary()

    def _init_settings_block(self):
        self.label_object_name = ttk.Label(self.frame_settings, text="Объект: ")
        self.label_object_name_value = ttk.Label(self.frame_settings, text="")
        self.label_max_power = ttk.Label(self.frame_settings, text="Максимальная мощность (кВт): ")
        self.label_max_power_value = ttk.Label(self.frame_settings, text="")

        self.button_edit_settings = ttk.Button(
            self.frame_settings, text="Редактировать", command=self.open_settings_window
        )

        self.label_object_name.grid(row=0, column=0, sticky="w", padx=5, pady=2)
        self.label_object_name_value.grid(row=0, column=1, sticky="w", padx=5, pady=2)
        self.label_max_power.grid(row=1, column=0, sticky="w", padx=5, pady=2)
        self.label_max_power_value.grid(row=1, column=1, sticky="w", padx=5, pady=2)
        self.button_edit_settings.grid(row=0, column=2, rowspan=2, padx=10, pady=2)

        self.refresh_settings_labels()
    def refresh_settings_labels(self):
        s = self.app_data.settings
        self.label_object_name_value.config(text=s.object_name or "(не задано)")
        self.label_max_power_value.config(text=str(s.max_power))
    def open_settings_window(self):
        win = tk.Toplevel(self)
        win.title("Редактирование исходных данных")

        ttk.Label(win, text="Название объекта:").grid(row=0, column=0, sticky="w", padx=5, pady=5)
        entry_name = ttk.Entry(win, width=40)
        entry_name.grid(row=0, column=1, padx=5, pady=5)

        ttk.Label(win, text="Максимальная мощность (кВт):").grid(
            row=1, column=0, sticky="w", padx=5, pady=5
        )
        entry_power = ttk.Entry(win, width=20)
        entry_power.grid(row=1, column=1, padx=5, pady=5)

        entry_name.insert(0, self.app_data.settings.object_name)
        entry_power.insert(0, str(self.app_data.settings.max_power))
        def on_save():
            name = entry_name.get().strip()
            try:
                max_power = float(entry_power.get().replace(",", "."))
            except ValueError:
                messagebox.showerror("Ошибка", "Максимальная мощность должна быть числом.")
                return

            self.app_data.settings = Settings(object_name=name, max_power=max_power)
            save_data(self.app_data)
            self.refresh_settings_labels()
            self.update_summary()
            win.destroy()
        def on_cancel():
            win.destroy()
        ttk.Button(win, text="Сохранить", command=on_save).grid(
            row=2, column=0, padx=5, pady=10
        )
        ttk.Button(win, text="Отменить", command=on_cancel).grid(
            row=2, column=1, padx=5, pady=10
        )
    def _init_summary_block(self):
        self.label_total_power = ttk.Label(self.frame_summary, text="Суммарная мощность (кВт):")
        self.label_total_power_value = ttk.Label(self.frame_summary, text="0")

        self.label_total_power.grid(row=0, column=0, sticky="w", padx=5, pady=2)
        self.label_total_power_value.grid(row=0, column=1, sticky="w", padx=5, pady=2)
    def update_summary(self):
        total_power = calculate_total_power(self.app_data.devices) / 1000
        self.label_total_power_value.config(text=str(total_power))
    def _init_devices_block(self):
        columns = ("location", "type", "name", "power", "time")
        self.tree = ttk.Treeview(
            self.frame_devices, columns=columns, show="headings", selectmode="extended"
        )

        self.tree.heading("location", text="Расположение")
        self.tree.heading("type", text="Тип")
        self.tree.heading("name", text="Название")
        self.tree.heading("power", text="Мощность, Вт")
        self.tree.heading("time", text="Время работы")

        self.tree.column("location", width=100)
        self.tree.column("type", width=120)
        self.tree.column("name", width=200)
        self.tree.column("power", width=100)
        self.tree.column("time", width=160)

        self.tree.pack(fill="both", expand=True, padx=5, pady=5)

        btn_frame = ttk.Frame(self.frame_devices)
        btn_frame.pack(fill="x", padx=5, pady=5)

        self.btn_add = ttk.Button(btn_frame, text="Добавить", command=self.open_add_device_window)
        self.btn_edit = ttk.Button(
            btn_frame, text="Редактировать выбранный", command=self.open_edit_device_window
        )
        self.btn_delete = ttk.Button(
            btn_frame, text="Удалить выбранный", command=self.delete_selected_devices
        )
        self.btn_analyze = ttk.Button(
            btn_frame, text="Анализ потребления", command=self.open_recommendations_window
        )

        self.btn_add.pack(side="left", padx=5)
        self.btn_edit.pack(side="left", padx=5)
        self.btn_delete.pack(side="left", padx=5)
        self.btn_analyze.pack(side="right", padx=5)

        self.tree.bind("<<TreeviewSelect>>", self.on_tree_select)

        self.refresh_devices_table()
    def refresh_devices_table(self):
        for row in self.tree.get_children():
            self.tree.delete(row)

        for idx, d in enumerate(self.app_data.devices):
            time_str = f"{d.time_from}:00–{d.time_to}:00"
            self.tree.insert(
                "", "end", iid=str(idx),
                values=(d.location, d.type, d.name, d.power, time_str)
            )

        self.on_tree_select(None)

    def on_tree_select(self, event):
        selected = self.tree.selection()
        if len(selected) == 1:
            self.btn_edit.state(["!disabled"])
        else:
            self.btn_edit.state(["disabled"])
        if len(selected) >= 1:
            self.btn_delete.state(["!disabled"])
        else:
            self.btn_delete.state(["disabled"])
    def get_selected_indices(self) -> List[int]:
        selected = self.tree.selection()
        return [int(iid) for iid in selected]
    def open_add_device_window(self):
        self._open_device_window()
    def open_edit_device_window(self):
        indices = self.get_selected_indices()
        if len(indices) != 1:
            return
        idx = indices[0]
        device = self.app_data.devices[idx]
        self._open_device_window(device=device, index=idx)
    def _open_device_window(self, device: Optional[Device] = None, index: Optional[int] = None):
        win = tk.Toplevel(self)
        if device is None:
            win.title("Добавление прибора")
        else:
            win.title("Редактирование прибора")

        ttk.Label(win, text="Расположение:").grid(row=0, column=0, sticky="w", padx=5, pady=5)
        cb_location = ttk.Combobox(win, values=LOCATIONS, state="readonly")
        cb_location.grid(row=0, column=1, padx=5, pady=5)

        ttk.Label(win, text="Тип:").grid(row=1, column=0, sticky="w", padx=5, pady=5)
        cb_type = ttk.Combobox(win, values=TYPES, state="readonly")
        cb_type.grid(row=1, column=1, padx=5, pady=5)

        ttk.Label(win, text="Название:").grid(row=2, column=0, sticky="w", padx=5, pady=5)
        entry_name = ttk.Entry(win, width=30)
        entry_name.grid(row=2, column=1, padx=5, pady=5)

        ttk.Label(win, text="Мощность (Вт):").grid(row=3, column=0, sticky="w", padx=5, pady=5)
        entry_power = ttk.Entry(win, width=10)
        entry_power.grid(row=3, column=1, padx=5, pady=5)

        ttk.Label(win, text="Время работы с (час):").grid(
            row=4, column=0, sticky="w", padx=5, pady=5
        )
        cb_from = ttk.Combobox(win, values=list(range(0, 24)), state="readonly", width=5)
        cb_from.grid(row=4, column=1, padx=5, pady=5)

        ttk.Label(win, text="Время работы до (час):").grid(
            row=5, column=0, sticky="w", padx=5, pady=5
        )
        cb_to = ttk.Combobox(win, values=list(range(2, 25)), state="readonly", width=5)
        cb_to.grid(row=5, column=1, padx=5, pady=5)

        if device is not None:
            cb_location.set(device.location)
            cb_type.set(device.type)
            entry_name.insert(0, device.name)
            entry_power.insert(0, str(device.power))
            cb_from.set(device.time_from)
            cb_to.set(device.time_to)
        else:
            cb_location.current(0)
            cb_type.current(0)
            cb_from.set(2)
            cb_to.set(2)
        def on_save():
            location = cb_location.get()
            dev_type = cb_type.get()
            name = entry_name.get().strip()
            if not name:
                messagebox.showerror("Ошибка", "Название прибора не может быть пустым.")
                return
            try:
                power = float(entry_power.get().replace(",", "."))
            except ValueError:
                messagebox.showerror("Ошибка", "Мощность должна быть числом.")
                return
            try:
                time_from = int(cb_from.get())
                time_to = int(cb_to.get())
            except ValueError:
                messagebox.showerror("Ошибка", "Время работы должно быть числом.")
                return

            if time_from > time_to:
                messagebox.showerror("Ошибка", "Время 'с' не может быть больше времени 'до'.")
                return

            new_device = Device(
                location=location,
                type=dev_type,
                name=name,
                power=power,
                time_from=time_from,
                time_to=time_to,
            )

            if device is None:
                self.app_data.devices.append(new_device)
            else:
                self.app_data.devices[index] = new_device

            save_data(self.app_data)
            self.refresh_devices_table()
            self.update_summary()
            win.destroy()

        ttk.Button(win, text="Сохранить", command=on_save).grid(
            row=6, column=0, padx=5, pady=10
        )
        ttk.Button(win, text="Отмена", command=win.destroy).grid(
            row=6, column=1, padx=5, pady=10
        )
    def delete_selected_devices(self):
        indices = sorted(self.get_selected_indices(), reverse=True)
        if not indices:
            return

        if not messagebox.askyesno("Подтверждение", "Удалить выбранные приборы?"):
            return

        for idx in indices:
            if 0 <= idx < len(self.app_data.devices):
                self.app_data.devices.pop(idx)

        save_data(self.app_data)
        self.refresh_devices_table()
        self.update_summary()
    def open_recommendations_window(self):
        win = tk.Toplevel(self)
        win.title("Рекомендации")
        win.geometry("900x700")

        recs = get_recommendations(self.app_data.settings, self.app_data.devices)

        rec_frame = ttk.LabelFrame(win, text="Рекомендации")
        rec_frame.pack(fill="x", padx=10, pady=5)

        text = tk.Text(rec_frame, width=80, height=4)
        text.pack(fill="x", padx=5, pady=5)
        for r in recs:
            text.insert("end", f"- {r}\n")
        text.config(state="disabled")

        load_frame = ttk.LabelFrame(win, text="График нагрузки за сутки")
        load_frame.pack(fill="both", expand=True, padx=10, pady=5)

        if self.app_data.settings.max_power > 0 and self.app_data.devices:
            load = [x / 1000.0 for x in calculate_load_by_hour(self.app_data.devices)]
            hours = np.arange(2, 25)

            fig1 = Figure(figsize=(10, 4))
            ax1 = fig1.add_subplot(111)
            ax1.plot(hours, load, 'b-', linewidth=2, marker='o')
            ax1.axhline(y=self.app_data.settings.max_power, color='r', linestyle='--',
                        label=f'Макс. мощность {self.app_data.settings.max_power:.1f} кВт')
            ax1.set_xlabel('Часы')
            ax1.set_ylabel('Мощность, кВт')
            ax1.set_title('Нагрузка за сутки')
            ax1.grid(True, alpha=0.3)
            ax1.legend()

            canvas1 = FigureCanvasTkAgg(fig1, load_frame)
            canvas1.draw()
            canvas1.get_tk_widget().pack(fill="both", expand=True)
        else:
            ttk.Label(load_frame, text="Недостаточно данных для построения графика").pack(pady=20)

        hist_frame = ttk.LabelFrame(win, text="Топ-5 самых энергоёмких приборов")
        hist_frame.pack(fill="both", padx=10, pady=5)

        top5 = get_top_devices(self.app_data.devices, 5)
        if top5:
            powers = [d.power for d in top5]
            names = [d.name[:12] + '..' if len(d.name) > 12 else d.name for d in top5]

            fig2 = Figure(figsize=(10, 4))
            ax2 = fig2.add_subplot(111)
            bars = ax2.bar(range(len(powers)), powers, color='orange', alpha=0.7)
            ax2.set_xlabel('Приборы')
            ax2.set_ylabel('Мощность, Вт')
            ax2.set_title('Топ-5 приборов по мощности')
            ax2.set_xticks(range(len(names)))
            ax2.set_xticklabels(names, rotation=0, ha='right')
            ax2.tick_params(axis='x', labelsize=9)
            ax2.grid(True, alpha=0.3)

            for bar, power in zip(bars, powers):
                height = bar.get_height()
                ax2.text(bar.get_x() + bar.get_width() / 2., height,
                         f'{power:.1f}', ha='center', va='bottom')

            canvas2 = FigureCanvasTkAgg(fig2, hist_frame)
            canvas2.draw()
            canvas2.get_tk_widget().pack(fill="both", expand=True)
        else:
            ttk.Label(hist_frame, text="Нет приборов для анализа").pack(pady=20)
if __name__ == "__main__":
    app = App()
    app.mainloop()