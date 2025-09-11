import json
import math
import time
import tkinter as tk
from pathlib import Path
from tkinter import messagebox, simpledialog

from platformdirs import user_config_path

from registers import BY_NAME
from service import VSensorService, Quality


CONFIG_FILE_OLD = Path(__file__).with_name("gui_app_config.json")
CONFIG_FILE = user_config_path("vsensor") / "gui.json"
DEFAULT_REGISTERS: list[str] = []  # explicit start list
DEFAULT_INTERVAL = 0.5


class DashboardApp:
    """Minimalistic Tkinter dashboard for V-Sensor registers."""

    def __init__(self) -> None:
        self.root = tk.Tk()
        self.root.title("VSensor Dashboard")
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

        self.config = self.load_config()
        self.selected = self.config.get("registers", DEFAULT_REGISTERS)
        self.poll_interval = self.config.get("poll_interval", DEFAULT_INTERVAL)
        self.update_interval = int(self.poll_interval * 1000)

        self.service = VSensorService(registers=self.selected, interval=self.poll_interval)

        self.banner_var = tk.StringVar(value="")
        self.banner = tk.Label(self.root, textvariable=self.banner_var, bg="red", fg="white")

        self.cards_frame = tk.Frame(self.root)
        self.cards_frame.pack(fill="both", expand=True)

        self.cards: dict[str, dict[str, tk.Variable]] = {}

        self.create_menu()
        self.create_cards()
        self.after_id: int | None = None
        self.schedule_update()

    # ------------------------------------------------------------------
    def create_menu(self) -> None:
        menubar = tk.Menu(self.root)
        settings = tk.Menu(menubar, tearoff=False)
        settings.add_command(label="Select Registers", command=self.select_registers)
        settings.add_command(label="Poll Interval", command=self.change_interval)
        menubar.add_cascade(label="Settings", menu=settings)
        self.root.config(menu=menubar)

    # ------------------------------------------------------------------
    def load_config(self) -> dict:
        if CONFIG_FILE.exists():
            try:
                with open(CONFIG_FILE, "r", encoding="utf-8") as fh:
                    return json.load(fh)
            except Exception:
                return {}
        if CONFIG_FILE_OLD.exists():
            try:
                with open(CONFIG_FILE_OLD, "r", encoding="utf-8") as fh:
                    data = json.load(fh)
                CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
                with open(CONFIG_FILE, "w", encoding="utf-8") as fh:
                    json.dump(data, fh, indent=2)
                CONFIG_FILE_OLD.unlink()
                return data
            except Exception:
                return {}
        return {}

    def save_config(self) -> None:
        data = {"registers": self.selected, "poll_interval": self.poll_interval}
        try:
            CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
            with open(CONFIG_FILE, "w", encoding="utf-8") as fh:
                json.dump(data, fh, indent=2)
        except Exception:
            pass

    # ------------------------------------------------------------------
    def create_cards(self) -> None:
        for widget in self.cards_frame.winfo_children():
            widget.destroy()
        self.cards.clear()

        count = len(self.selected)
        columns = max(1, math.ceil(math.sqrt(count)))
        rows = math.ceil(count / columns)
        for c in range(columns):
            self.cards_frame.grid_columnconfigure(c, weight=1)
        for r in range(rows):
            self.cards_frame.grid_rowconfigure(r, weight=1)

        for idx, name in enumerate(self.selected):
            spec = BY_NAME.get(name)
            if not spec:
                continue
            row, col = divmod(idx, columns)
            frame = tk.Frame(self.cards_frame, relief=tk.RIDGE, borderwidth=2, padx=4, pady=4)
            frame.grid(row=row, column=col, padx=5, pady=5, sticky="nsew")
            frame.bind("<Button-1>", lambda _e, n=name: self.edit_value(n))

            tk.Label(frame, text=name, font=("Arial", 10, "bold")).pack()
            value_var = tk.StringVar(value="--")
            tk.Label(frame, textvariable=value_var, font=("Arial", 14)).pack()
            unit = spec.get("unit", "")
            tk.Label(frame, text=unit).pack()
            ts_var = tk.StringVar(value="")
            tk.Label(frame, textvariable=ts_var, font=("Arial", 8)).pack()
            status_var = tk.StringVar(value="")
            status_lbl = tk.Label(frame, textvariable=status_var)
            status_lbl.pack(fill="x")

            self.cards[name] = {
                "value": value_var,
                "timestamp": ts_var,
                "status": status_var,
                "status_label": status_lbl,
            }

    # ------------------------------------------------------------------
    def schedule_update(self) -> None:
        if self.after_id is not None:
            self.root.after_cancel(self.after_id)
        self.after_id = self.root.after(self.update_interval, self.update_cards)

    def update_cards(self) -> None:
        if not self.service.last_poll_ok():
            self.banner_var.set("Connection error")
            if not self.banner.winfo_ismapped():
                self.banner.pack(fill="x")
        elif self.banner.winfo_ismapped():
            self.banner.pack_forget()
        entries = self.service.get_all_entries()
        for name, widgets in self.cards.items():
            entry = entries.get(name)
            if entry is None:
                quality = Quality.ERROR
                value = None
                ts = None
            else:
                quality = entry["quality"]
                value = entry["value"]
                ts = entry["timestamp"]
            spec = BY_NAME.get(name, {})
            fmt = spec.get("format")
            if value is None:
                value_str = "--"
            elif fmt:
                try:
                    value_str = fmt.format(value)
                except Exception:
                    value_str = str(value)
            else:
                value_str = str(value)
            widgets["value"].set(value_str)
            if ts is not None:
                widgets["timestamp"].set(time.strftime("%H:%M:%S", time.localtime(ts)))
            else:
                widgets["timestamp"].set("")
            widgets["status"].set(quality.value)
            color = {Quality.OK: "green", Quality.STALE: "yellow", Quality.ERROR: "red"}[quality]
            widgets["status_label"].configure(bg=color)
        self.schedule_update()

    # ------------------------------------------------------------------
    def select_registers(self) -> None:
        top = tk.Toplevel(self.root)
        top.title("Select Registers")
        lb = tk.Listbox(top, selectmode=tk.MULTIPLE)
        names = sorted(BY_NAME)
        for idx, name in enumerate(names):
            lb.insert(tk.END, name)
            if name in self.selected:
                lb.selection_set(idx)
        lb.pack(fill="both", expand=True)

        def apply() -> None:
            sel = [names[i] for i in lb.curselection()]
            if not sel:
                messagebox.showwarning("No Selection", "Select at least one register")
                return
            self.selected = sel
            self.service.stop()
            self.service.configure(registers=self.selected)
            self.service.start()
            self.create_cards()
            self.save_config()
            top.destroy()

        tk.Button(top, text="Apply", command=apply).pack()

    # ------------------------------------------------------------------
    def change_interval(self) -> None:
        new_val = simpledialog.askfloat(
            "Poll Interval", "Interval in seconds", initialvalue=self.poll_interval, minvalue=0.1
        )
        if new_val is None:
            return
        self.poll_interval = new_val
        self.update_interval = int(self.poll_interval * 1000)
        self.service.stop()
        self.service.configure(interval=self.poll_interval)
        self.service.start()
        self.save_config()
        self.schedule_update()

    # ------------------------------------------------------------------
    def edit_value(self, name: str) -> None:
        spec = BY_NAME.get(name)
        if not spec:
            return
        if spec.get("rw", "R") == "R":
            messagebox.showinfo("Read Only", f"{name} is read-only")
            return
        current = self.service.read_register(name)
        prompt = simpledialog.askstring(
            "Write Register", f"New value for {name}", initialvalue="" if current is None else str(current)
        )
        if prompt is None:
            return
        try:
            value: int | float
            if spec.get("type") == "float32":
                value = float(prompt)
            else:
                value = int(prompt)
        except ValueError:
            messagebox.showerror("Invalid", "Could not parse value")
            return
        if not self.service.write_register(name, value):
            messagebox.showerror("Error", "Write failed")

    # ------------------------------------------------------------------
    def on_close(self) -> None:
        self.service.stop()
        self.save_config()
        self.root.destroy()

    # ------------------------------------------------------------------
    def run(self) -> None:
        self.root.mainloop()


if __name__ == "__main__":
    DashboardApp().run()
