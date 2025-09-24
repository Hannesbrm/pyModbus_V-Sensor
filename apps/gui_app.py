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
DEFAULT_CLIENT_CONFIG: dict[str, object] = {
    "method": "rtu",
    "port": "/dev/ttyUSB0",
    "baudrate": 9600,
    "parity": "N",
    "stopbits": 1,
    "host": "localhost",
    "tcp_port": 502,
    "device_id": 1,
    "timeout": 3.0,
}


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

        connection_cfg = self.config.get("connection", {})
        if not isinstance(connection_cfg, dict):
            connection_cfg = {}
        self.client_config: dict[str, object] = dict(DEFAULT_CLIENT_CONFIG)
        self.client_config.update(connection_cfg)

        self.service = VSensorService(
            registers=self.selected, interval=self.poll_interval, **self.client_config
        )

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
        settings.add_command(label="Connection…", command=self.configure_connection)
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
        data = {
            "registers": self.selected,
            "poll_interval": self.poll_interval,
            "connection": self.client_config,
        }
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
    def configure_connection(self) -> None:
        top = tk.Toplevel(self.root)
        top.title("Connection Settings")
        top.transient(self.root)
        top.grab_set()
        top.resizable(False, False)

        method_var = tk.StringVar(value=str(self.client_config.get("method", "rtu")))
        port_var = tk.StringVar(value=str(self.client_config.get("port", "")))
        baudrate_var = tk.StringVar(value=str(self.client_config.get("baudrate", "")))
        parity_var = tk.StringVar(value=str(self.client_config.get("parity", "N")))
        stopbits_var = tk.StringVar(value=str(self.client_config.get("stopbits", 1)))
        host_var = tk.StringVar(value=str(self.client_config.get("host", "")))
        tcp_port_var = tk.StringVar(value=str(self.client_config.get("tcp_port", "")))
        device_id_var = tk.StringVar(value=str(self.client_config.get("device_id", "")))
        timeout_var = tk.StringVar(value=str(self.client_config.get("timeout", "")))

        body = tk.Frame(top)
        body.pack(fill="both", expand=True, padx=10, pady=10)
        body.columnconfigure(1, weight=1)

        tk.Label(body, text="Method:").grid(row=0, column=0, sticky="w")
        method_menu = tk.OptionMenu(body, method_var, "rtu", "tcp")
        method_menu.grid(row=0, column=1, sticky="ew")

        rtu_frame = tk.LabelFrame(body, text="Serial (RTU)")
        rtu_opts = {"row": 1, "column": 0, "columnspan": 2, "sticky": "ew", "pady": (10, 0)}
        rtu_frame.grid(**rtu_opts)
        rtu_frame.columnconfigure(1, weight=1)

        tk.Label(rtu_frame, text="Port:").grid(row=0, column=0, sticky="w")
        tk.Entry(rtu_frame, textvariable=port_var).grid(row=0, column=1, sticky="ew")
        tk.Label(rtu_frame, text="Baudrate:").grid(row=1, column=0, sticky="w")
        tk.Entry(rtu_frame, textvariable=baudrate_var).grid(row=1, column=1, sticky="ew")
        tk.Label(rtu_frame, text="Parity:").grid(row=2, column=0, sticky="w")
        parity_menu = tk.OptionMenu(rtu_frame, parity_var, "N", "E", "O")
        parity_menu.grid(row=2, column=1, sticky="ew")
        tk.Label(rtu_frame, text="Stopbits:").grid(row=3, column=0, sticky="w")
        stopbits_menu = tk.OptionMenu(rtu_frame, stopbits_var, "1", "2")
        stopbits_menu.grid(row=3, column=1, sticky="ew")

        tcp_frame = tk.LabelFrame(body, text="TCP")
        tcp_opts = {"row": 2, "column": 0, "columnspan": 2, "sticky": "ew", "pady": (10, 0)}
        tcp_frame.grid(**tcp_opts)
        tcp_frame.columnconfigure(1, weight=1)

        tk.Label(tcp_frame, text="Host:").grid(row=0, column=0, sticky="w")
        tk.Entry(tcp_frame, textvariable=host_var).grid(row=0, column=1, sticky="ew")
        tk.Label(tcp_frame, text="Port:").grid(row=1, column=0, sticky="w")
        tk.Entry(tcp_frame, textvariable=tcp_port_var).grid(row=1, column=1, sticky="ew")

        general_frame = tk.LabelFrame(body, text="General")
        general_frame.grid(row=3, column=0, columnspan=2, sticky="ew", pady=(10, 0))
        general_frame.columnconfigure(1, weight=1)

        tk.Label(general_frame, text="Device ID:").grid(row=0, column=0, sticky="w")
        tk.Entry(general_frame, textvariable=device_id_var).grid(row=0, column=1, sticky="ew")
        tk.Label(general_frame, text="Timeout (s):").grid(row=1, column=0, sticky="w")
        tk.Entry(general_frame, textvariable=timeout_var).grid(row=1, column=1, sticky="ew")

        def update_frames(*_args: object) -> None:
            if method_var.get() == "rtu":
                rtu_frame.grid(**rtu_opts)
                tcp_frame.grid_remove()
            else:
                tcp_frame.grid(**tcp_opts)
                rtu_frame.grid_remove()

        method_var.trace_add("write", update_frames)
        update_frames()

        def apply() -> None:
            new_config = dict(DEFAULT_CLIENT_CONFIG)
            new_config.update(self.client_config)

            method = method_var.get()
            new_config["method"] = method

            port = port_var.get().strip()
            if port:
                new_config["port"] = port
            elif method == "rtu":
                messagebox.showerror("Invalid", "Port must not be empty for RTU")
                return

            baudrate_str = baudrate_var.get().strip()
            if baudrate_str:
                try:
                    baudrate = int(baudrate_str)
                    if baudrate <= 0:
                        raise ValueError
                except ValueError:
                    messagebox.showerror("Invalid", "Baudrate must be a positive integer")
                    return
                new_config["baudrate"] = baudrate
            elif method == "rtu":
                messagebox.showerror("Invalid", "Baudrate must be provided for RTU")
                return

            parity = parity_var.get()
            new_config["parity"] = parity

            try:
                stopbits = int(stopbits_var.get())
            except ValueError:
                messagebox.showerror("Invalid", "Stopbits must be 1 or 2")
                return
            if stopbits not in {1, 2}:
                messagebox.showerror("Invalid", "Stopbits must be 1 or 2")
                return
            new_config["stopbits"] = stopbits

            host = host_var.get().strip()
            if host:
                new_config["host"] = host
            elif method == "tcp":
                messagebox.showerror("Invalid", "Host must not be empty for TCP")
                return

            tcp_port_str = tcp_port_var.get().strip()
            if tcp_port_str:
                try:
                    tcp_port = int(tcp_port_str)
                    if tcp_port <= 0:
                        raise ValueError
                except ValueError:
                    messagebox.showerror("Invalid", "TCP port must be a positive integer")
                    return
                new_config["tcp_port"] = tcp_port
            elif method == "tcp":
                messagebox.showerror("Invalid", "TCP port must be provided for TCP")
                return

            device_id_str = device_id_var.get().strip()
            try:
                device_id = int(device_id_str)
                if device_id <= 0:
                    raise ValueError
            except ValueError:
                messagebox.showerror("Invalid", "Device ID must be a positive integer")
                return
            new_config["device_id"] = device_id

            timeout_str = timeout_var.get().strip()
            try:
                timeout = float(timeout_str)
                if timeout <= 0:
                    raise ValueError
            except ValueError:
                messagebox.showerror("Invalid", "Timeout must be a positive number")
                return
            new_config["timeout"] = timeout

            self.service.stop()
            self.service.configure(**new_config)
            self.service.start()
            self.client_config = new_config
            self.save_config()
            self.schedule_update()
            top.destroy()

        btn_frame = tk.Frame(top)
        btn_frame.pack(fill="x", padx=10, pady=(0, 10))
        tk.Button(btn_frame, text="Cancel", command=top.destroy).pack(side=tk.RIGHT)
        tk.Button(btn_frame, text="Apply", command=apply).pack(side=tk.RIGHT, padx=(0, 5))

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
