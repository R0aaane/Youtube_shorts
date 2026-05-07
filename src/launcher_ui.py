from __future__ import annotations

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


class LauncherApp(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("YouTube Shorts Simulation Launcher")
        self.geometry("880x620")
        self.minsize(780, 520)
        self.output_queue: queue.Queue[str] = queue.Queue()
        self.running_process: subprocess.Popen[str] | None = None

        self.config_var = tk.StringVar(value=str(DEFAULT_CONFIG))
        self.metadata_var = tk.StringVar(value=str(DEFAULT_METADATA))
        self.status_var = tk.StringVar(value="Ready")

        self._build_ui()
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

        metadata_row = ttk.Frame(controls)
        metadata_row.pack(fill=tk.X, **padding)
        ttk.Label(metadata_row, text="Metadata").pack(side=tk.LEFT)
        ttk.Entry(metadata_row, textvariable=self.metadata_var).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=8)

        button_row = ttk.Frame(controls)
        button_row.pack(fill=tk.X, **padding)
        buttons = [
            ("簡易プレビュー", self.run_preview),
            ("フル生成", self.run_generate_video),
            ("MP4化のみ", self.run_make_video),
            ("Upload確認", self.run_upload_dry_run),
            ("YouTube Upload", self.run_upload),
            ("停止", self.stop_process),
        ]
        for label, command in buttons:
            ttk.Button(button_row, text=label, command=command).pack(side=tk.LEFT, padx=4)

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

    def run_preview(self) -> None:
        self.start_command([sys.executable, self.command_path("src/simulate.py"), "--config", self.config_var.get(), "--window"])

    def run_generate_video(self) -> None:
        self.start_command([sys.executable, self.command_path("src/generate_video.py"), "--config", self.config_var.get()])

    def run_make_video(self) -> None:
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
