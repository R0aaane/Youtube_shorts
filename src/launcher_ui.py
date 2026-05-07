from __future__ import annotations

import json
import queue
import subprocess
import sys
import threading
import tkinter as tk
from pathlib import Path
from tkinter import messagebox, ttk


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONFIG = PROJECT_ROOT / "configs" / "food_duel.json"
DEFAULT_METADATA = PROJECT_ROOT / "output" / "metadata" / "food_duel.json"
FOOD_OPTIONS = ("pizza", "burger", "sushi", "ice_cream")
NUMERIC_FIELDS = {
    "duel_left_hp": int,
    "duel_right_hp": int,
    "duel_ball_radius": int,
    "base_damage": int,
    "duel_speed_scale": float,
    "duel_charge_speed": int,
    "duel_burger_charge_hp_cost": int,
    "duel_cheese_damage": int,
    "duel_cheese_projectile_speed": int,
    "random_seed": int,
}


class LauncherApp(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("Food Skill Battle Launcher")
        self.geometry("980x760")
        self.minsize(900, 680)
        self.output_queue: queue.Queue[str] = queue.Queue()
        self.running_process: subprocess.Popen[str] | None = None

        self.config_var = tk.StringVar(value=str(DEFAULT_CONFIG))
        self.metadata_var = tk.StringVar(value=str(DEFAULT_METADATA))
        self.status_var = tk.StringVar(value="Ready")
        self.config_fields: dict[str, tk.Variable] = {
            "duel_left_food": tk.StringVar(value="pizza"),
            "duel_right_food": tk.StringVar(value="sushi"),
            "duel_left_hp": tk.StringVar(value="700"),
            "duel_right_hp": tk.StringVar(value="680"),
            "duel_ball_radius": tk.StringVar(value="70"),
            "base_damage": tk.StringVar(value="24"),
            "duel_speed_scale": tk.StringVar(value="0.62"),
            "duel_charge_speed": tk.StringVar(value="760"),
            "duel_burger_charge_hp_cost": tk.StringVar(value="40"),
            "duel_cheese_damage": tk.StringVar(value="10"),
            "duel_cheese_projectile_speed": tk.StringVar(value="840"),
            "random_seed": tk.StringVar(value="607"),
            "audio_enabled": tk.BooleanVar(value=True),
        }

        self._build_ui()
        self.load_config_to_form(show_error=False)
        self.after(100, self._drain_output)

    def _build_ui(self) -> None:
        padding = {"padx": 12, "pady": 8}
        root = ttk.Frame(self)
        root.pack(fill=tk.BOTH, expand=True)

        controls = ttk.LabelFrame(root, text="Commands")
        controls.pack(fill=tk.X, **padding)

        config_row = ttk.Frame(controls)
        config_row.pack(fill=tk.X, **padding)
        ttk.Label(config_row, text="Config").pack(side=tk.LEFT)
        ttk.Entry(config_row, textvariable=self.config_var).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=8)
        ttk.Button(config_row, text="Load", command=self.load_config_to_form).pack(side=tk.LEFT, padx=4)
        ttk.Button(config_row, text="Save", command=self.save_config_from_form).pack(side=tk.LEFT, padx=4)

        metadata_row = ttk.Frame(controls)
        metadata_row.pack(fill=tk.X, **padding)
        ttk.Label(metadata_row, text="Metadata").pack(side=tk.LEFT)
        ttk.Entry(metadata_row, textvariable=self.metadata_var).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=8)

        button_row = ttk.Frame(controls)
        button_row.pack(fill=tk.X, **padding)
        buttons = [
            ("Preview", self.run_preview),
            ("Generate Video", self.run_generate_video),
            ("Encode MP4 Only", self.run_make_video),
            ("Upload Dry Run", self.run_upload_dry_run),
            ("YouTube Upload", self.run_upload),
            ("Stop", self.stop_process),
        ]
        for label, command in buttons:
            ttk.Button(button_row, text=label, command=command).pack(side=tk.LEFT, padx=4)

        editor = ttk.LabelFrame(root, text="Food Duel Config")
        editor.pack(fill=tk.X, **padding)

        matchup_row = ttk.Frame(editor)
        matchup_row.pack(fill=tk.X, **padding)
        ttk.Label(matchup_row, text="Left").pack(side=tk.LEFT)
        ttk.Combobox(
            matchup_row,
            textvariable=self.config_fields["duel_left_food"],
            values=FOOD_OPTIONS,
            width=10,
            state="readonly",
        ).pack(side=tk.LEFT, padx=6)
        ttk.Label(matchup_row, text="Right").pack(side=tk.LEFT, padx=(16, 0))
        ttk.Combobox(
            matchup_row,
            textvariable=self.config_fields["duel_right_food"],
            values=FOOD_OPTIONS,
            width=10,
            state="readonly",
        ).pack(side=tk.LEFT, padx=6)
        ttk.Checkbutton(matchup_row, text="Audio", variable=self.config_fields["audio_enabled"]).pack(side=tk.LEFT, padx=16)

        grid = ttk.Frame(editor)
        grid.pack(fill=tk.X, **padding)
        labels = [
            ("Left HP", "duel_left_hp"),
            ("Right HP", "duel_right_hp"),
            ("Radius", "duel_ball_radius"),
            ("Base Damage", "base_damage"),
            ("Speed Scale", "duel_speed_scale"),
            ("Charge Speed", "duel_charge_speed"),
            ("Burger HP Cost", "duel_burger_charge_hp_cost"),
            ("Cheese Damage", "duel_cheese_damage"),
            ("Cheese Speed", "duel_cheese_projectile_speed"),
            ("Seed", "random_seed"),
        ]
        for index, (label, key) in enumerate(labels):
            row = index // 5
            col = (index % 5) * 2
            ttk.Label(grid, text=label).grid(row=row, column=col, sticky=tk.W, padx=(0, 4), pady=4)
            ttk.Entry(grid, textvariable=self.config_fields[key], width=10).grid(row=row, column=col + 1, sticky=tk.W, padx=(0, 14), pady=4)

        status_row = ttk.Frame(root)
        status_row.pack(fill=tk.X, **padding)
        ttk.Label(status_row, text="Status:").pack(side=tk.LEFT)
        ttk.Label(status_row, textvariable=self.status_var).pack(side=tk.LEFT, padx=8)

        log_frame = ttk.LabelFrame(root, text="Log")
        log_frame.pack(fill=tk.BOTH, expand=True, **padding)
        self.log_text = tk.Text(log_frame, wrap=tk.WORD, height=20)
        scrollbar = ttk.Scrollbar(log_frame, command=self.log_text.yview)
        self.log_text.configure(yscrollcommand=scrollbar.set)
        self.log_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    def command_path(self, relative_path: str) -> str:
        return str(PROJECT_ROOT / relative_path)

    def resolve_config_path(self) -> Path:
        path = Path(self.config_var.get())
        return path if path.is_absolute() else PROJECT_ROOT / path

    def load_config_to_form(self, show_error: bool = True) -> None:
        try:
            config_path = self.resolve_config_path()
            data = json.loads(config_path.read_text(encoding="utf-8"))
            for key, variable in self.config_fields.items():
                if key not in data:
                    continue
                if isinstance(variable, tk.BooleanVar):
                    variable.set(bool(data[key]))
                else:
                    variable.set(str(data[key]))
            self.status_var.set("Config loaded")
        except Exception as exc:
            if show_error:
                messagebox.showerror("Load Config", f"Could not load config:\n{exc}")
            self.status_var.set("Load failed")

    def save_config_from_form(self) -> bool:
        try:
            config_path = self.resolve_config_path()
            data = json.loads(config_path.read_text(encoding="utf-8"))
            data["duel_left_food"] = str(self.config_fields["duel_left_food"].get())
            data["duel_right_food"] = str(self.config_fields["duel_right_food"].get())
            data["audio_enabled"] = bool(self.config_fields["audio_enabled"].get())
            for key, caster in NUMERIC_FIELDS.items():
                raw_value = str(self.config_fields[key].get()).strip()
                data[key] = caster(raw_value)
            if data["duel_left_food"] == data["duel_right_food"]:
                raise ValueError("Left and Right foods must be different.")
            config_path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
            self.status_var.set("Config saved")
            self._append_log(f"\nSaved config: {config_path}\n")
            return True
        except Exception as exc:
            messagebox.showerror("Save Config", f"Could not save config:\n{exc}")
            self.status_var.set("Save failed")
            return False

    def run_preview(self) -> None:
        if not self.save_config_from_form():
            return
        self.start_command([sys.executable, self.command_path("src/simulate.py"), "--config", self.config_var.get(), "--window"])

    def run_generate_video(self) -> None:
        if not self.save_config_from_form():
            return
        self.start_command([sys.executable, self.command_path("src/generate_video.py"), "--config", self.config_var.get()])

    def run_make_video(self) -> None:
        if not self.save_config_from_form():
            return
        self.start_command([sys.executable, self.command_path("src/make_video.py"), "--config", self.config_var.get()])

    def run_upload_dry_run(self) -> None:
        self.start_command(
            [
                sys.executable,
                self.command_path("src/upload_youtube.py"),
                "--metadata",
                self.metadata_var.get(),
                "--dry-run",
            ]
        )

    def run_upload(self) -> None:
        if not messagebox.askyesno("YouTube Upload", "Upload this video as private?"):
            return
        self.start_command(
            [
                sys.executable,
                self.command_path("src/upload_youtube.py"),
                "--metadata",
                self.metadata_var.get(),
                "--privacy",
                "private",
            ]
        )

    def start_command(self, command: list[str]) -> None:
        if self.running_process is not None and self.running_process.poll() is None:
            messagebox.showwarning("Running", "A command is already running.")
            return
        self.status_var.set("Running")
        self._append_log("\n> " + " ".join(command) + "\n")
        thread = threading.Thread(target=self._run_command, args=(command,), daemon=True)
        thread.start()

    def _run_command(self, command: list[str]) -> None:
        try:
            self.running_process = subprocess.Popen(
                command,
                cwd=PROJECT_ROOT,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                encoding="utf-8",
                errors="replace",
            )
            assert self.running_process.stdout is not None
            for line in self.running_process.stdout:
                self.output_queue.put(line)
            return_code = self.running_process.wait()
            self.output_queue.put(f"\n[exit code {return_code}]\n")
            self.output_queue.put("__STATUS_DONE__" if return_code == 0 else "__STATUS_FAILED__")
        except Exception as exc:
            self.output_queue.put(f"\nLauncher error: {exc}\n")
            self.output_queue.put("__STATUS_FAILED__")
        finally:
            self.running_process = None

    def stop_process(self) -> None:
        if self.running_process is None or self.running_process.poll() is not None:
            self.status_var.set("Ready")
            return
        self.running_process.terminate()
        self.status_var.set("Stopping")

    def _drain_output(self) -> None:
        while True:
            try:
                message = self.output_queue.get_nowait()
            except queue.Empty:
                break
            if message == "__STATUS_DONE__":
                self.status_var.set("Done")
            elif message == "__STATUS_FAILED__":
                self.status_var.set("Failed")
            else:
                self._append_log(message)
        self.after(100, self._drain_output)

    def _append_log(self, message: str) -> None:
        self.log_text.insert(tk.END, message)
        self.log_text.see(tk.END)


def main() -> None:
    app = LauncherApp()
    app.mainloop()


if __name__ == "__main__":
    main()
