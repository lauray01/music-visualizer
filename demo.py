import os, sys, stat, shutil, subprocess, threading, traceback
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import librosa
import librosa.display

import tkinter as tk
from tkinter import filedialog, messagebox

APP_TITLE = "UP Audio Visualizer"
ABOUT_TEXT = (
    "UP Audio Visualizer\n"
)

AUDIO_FILTERS = [
    ("Audio files", "*.wav *.flac *.mp3 *.ogg *.m4a *.aac *.aiff *.aif *.aifc"),
    ("All files", "*.*"),
]

# ---------- FFmpeg discovery (for MP3/OGG/M4A via audioread) ----------
def _bundle_dir() -> Path:
    if getattr(sys, "_MEIPASS", None):  # PyInstaller onefile/onedir
        return Path(sys._MEIPASS)
    if getattr(sys, "frozen", False):   # other freezers
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent  # running from source

def ensure_ffmpeg(log=print) -> bool:
    """Try to make ffmpeg/ffprobe available on PATH; return True if usable."""
    IS_WIN = (os.name == "nt")
    IS_MAC = (sys.platform == "darwin")

    ffm = "ffmpeg.exe" if IS_WIN else "ffmpeg"
    ffp = "ffprobe.exe" if IS_WIN else "ffprobe"

    # Candidate dirs: next to script/exe, its parent, macOS Resources
    dirs = []
    bd = _bundle_dir()
    dirs += [bd, bd.parent]
    if IS_MAC:
        dirs.append(bd.parent.parent / "Resources")

    # If both binaries live in any candidate dir, prepend it to PATH
    for d in dirs:
        f1, f2 = d / ffm, d / ffp
        if f1.exists() and f2.exists():
            for p in (f1, f2):
                try:
                    mode = os.stat(p).st_mode
                    if not (mode & stat.S_IXUSR):
                        os.chmod(p, mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
                except Exception:
                    pass
            os.environ["PATH"] = str(d) + os.pathsep + os.environ.get("PATH", "")
            break

    def _ok(cmd):
        try:
            subprocess.run([cmd, "-version"], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=3)
            return True
        except Exception:
            return False

    has = _ok("ffmpeg") and _ok("ffprobe")
    if has:
        log("[✓] FFmpeg detected.")
    else:
        log("[!] FFmpeg not found; MP3/OGG/M4A decoding may fail. Install FFmpeg or place ffmpeg/ffprobe next to this script.")
    return has

# ---------- Analysis ----------
def analyze(audio_path: Path, log_cb=print):
    # Ensure FFmpeg is reachable for compressed formats (safe to call always)
    ensure_ffmpeg(log_cb)

    audio_path = audio_path.expanduser().resolve(strict=True)
    out_dir = audio_path.parent
    out_prefix = audio_path.stem

    def out(name: str) -> Path:
        return out_dir / f"{out_prefix}_{name}.png"

    log_cb(f"[i] Audio: {audio_path}")
    log_cb(f"[i] Output dir: {out_dir}")

    # getting information about the audio file
    y, sr = librosa.load(str(audio_path), sr=None, mono=True)

    

# ---------- UI ----------
class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title(APP_TITLE)
        self.geometry("760x360")
        self.configure(bg="#1e1e1e")
        self._build_menu()
        self._build_ui()

    def _build_menu(self):
        m = tk.Menu(self)
        helpm = tk.Menu(m, tearoff=0)
        helpm.add_command(label="About", command=lambda: messagebox.showinfo("About", ABOUT_TEXT))
        m.add_cascade(label="Help", menu=helpm)
        self.config(menu=m)

    def _build_ui(self):
       frame = tk.Frame(self, bg="#1e1e1e")

    def _log(self, msg: str):
        self.log_box.insert("end", msg + "\n")
        self.log_box.see("end")
        self.update_idletasks()

    def _log_async(self, msg: str):
        self.after(0, lambda: self._log(msg))

    def _on_create(self):
        path = self.path_var.get().strip()
        if not path:
            messagebox.showwarning("Missing file", "Choose an audio file first.")
            return
        p = Path(path)

        def worker():
            try:
                self._log_async("- Running...")
                analyze(p, log_cb=self._log_async)
                self._log_async("- Done.")
            except Exception as e:
                tb = "".join(traceback.format_exception(e))
                def show_err():
                    self._log(f"! Error:\n{tb}")
                    messagebox.showerror("Error", str(e))
                self.after(0, show_err)

        threading.Thread(target=worker, daemon=True).start()

if __name__ == "__main__":
    App().mainloop()
