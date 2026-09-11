import tkinter as tk
from tkinter import filedialog, messagebox
import threading
import urllib.request
import os
import re

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
}

def extract_urls(text):
    return re.findall(r'https://cdn\.discordapp\.com/emojis/\S+', text)

def download_urls(urls, out_dir, log, btn, done_label):
    success = 0
    fail = 0
    for url in urls:
        url = url.strip()
        if not url:
            continue
        try:
            emoji_id = url.split("/emojis/")[1].split(".webp")[0]
            animated = "animated=true" in url
            ext = ".gif" if animated else ".webp"
            filename = os.path.join(out_dir, f"{emoji_id}{ext}")
            download_url = url.replace(".webp?size=96&animated=true", ".gif?size=96") if animated else url
            req = urllib.request.Request(download_url, headers=HEADERS)
            with urllib.request.urlopen(req) as resp:
                with open(filename, "wb") as f:
                    f.write(resp.read())
            log(f"  {emoji_id}{ext}")
            success += 1
        except Exception as e:
            log(f"  FAILED {url.split('/emojis/')[1][:20]}... ({e})")
            fail += 1

    done_label.config(text=f"Done. {success} saved, {fail} failed.")
    btn.config(state="normal", text="Download")

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Emoji Downloader")
        self.resizable(False, False)
        self.configure(bg="#1e1f22")

        self.out_dir = os.path.join(os.path.expanduser("~"), "Downloads", "emojis")

        pad = {"padx": 14, "pady": 6}

        # Header
        tk.Label(self, text="Emoji Downloader", font=("Segoe UI", 13, "bold"),
                 bg="#1e1f22", fg="#ffffff").pack(anchor="w", padx=14, pady=(14, 2))
        tk.Label(self, text="Paste Discord emoji links below, one per line or space-separated.",
                 font=("Segoe UI", 9), bg="#1e1f22", fg="#8b8e95").pack(anchor="w", padx=14)

        # Text box
        text_frame = tk.Frame(self, bg="#2b2d31", bd=0)
        text_frame.pack(fill="both", expand=True, padx=14, pady=(10, 4))
        self.text = tk.Text(text_frame, width=62, height=10, font=("Consolas", 9),
                            bg="#2b2d31", fg="#dcddde", insertbackground="#ffffff",
                            relief="flat", bd=6, wrap="word", undo=True)
        self.text.pack(fill="both", expand=True)
        self.text.bind("<Control-a>", lambda e: (self.text.tag_add("sel", "1.0", "end"), "break"))

        # Output folder row
        folder_frame = tk.Frame(self, bg="#1e1f22")
        folder_frame.pack(fill="x", padx=14, pady=(4, 2))
        tk.Label(folder_frame, text="Save to:", font=("Segoe UI", 9),
                 bg="#1e1f22", fg="#8b8e95").pack(side="left")
        self.folder_label = tk.Label(folder_frame, text=self.out_dir, font=("Segoe UI", 9),
                                     bg="#1e1f22", fg="#5865f2", cursor="hand2", anchor="w")
        self.folder_label.pack(side="left", padx=(6, 0))
        self.folder_label.bind("<Button-1>", self.pick_folder)

        # Log box
        log_frame = tk.Frame(self, bg="#111214", bd=0)
        log_frame.pack(fill="both", expand=True, padx=14, pady=(6, 4))
        self.log_box = tk.Text(log_frame, width=62, height=7, font=("Consolas", 8),
                               bg="#111214", fg="#5bc55b", insertbackground="#ffffff",
                               relief="flat", bd=6, state="disabled")
        self.log_box.pack(fill="both", expand=True)

        # Bottom row
        bottom = tk.Frame(self, bg="#1e1f22")
        bottom.pack(fill="x", padx=14, pady=(2, 14))

        self.done_label = tk.Label(bottom, text="", font=("Segoe UI", 9),
                                   bg="#1e1f22", fg="#8b8e95")
        self.done_label.pack(side="left")

        self.clear_btn = tk.Button(bottom, text="Clear", font=("Segoe UI", 9),
                                   bg="#2b2d31", fg="#dcddde", activebackground="#3a3c40",
                                   activeforeground="#ffffff", relief="flat", bd=0,
                                   padx=12, pady=5, cursor="hand2", command=self.clear_all)
        self.clear_btn.pack(side="right", padx=(6, 0))

        self.dl_btn = tk.Button(bottom, text="Download", font=("Segoe UI", 9, "bold"),
                                bg="#5865f2", fg="#ffffff", activebackground="#4752c4",
                                activeforeground="#ffffff", relief="flat", bd=0,
                                padx=14, pady=5, cursor="hand2", command=self.start_download)
        self.dl_btn.pack(side="right")

    def pick_folder(self, event=None):
        d = filedialog.askdirectory(initialdir=self.out_dir)
        if d:
            self.out_dir = d
            self.folder_label.config(text=d)

    def log(self, msg):
        self.log_box.config(state="normal")
        self.log_box.insert("end", msg + "\n")
        self.log_box.see("end")
        self.log_box.config(state="disabled")

    def clear_all(self):
        self.text.delete("1.0", "end")
        self.log_box.config(state="normal")
        self.log_box.delete("1.0", "end")
        self.log_box.config(state="disabled")
        self.done_label.config(text="")

    def start_download(self):
        raw = self.text.get("1.0", "end")
        urls = extract_urls(raw)
        if not urls:
            messagebox.showwarning("No links", "No Discord emoji URLs found.")
            return

        os.makedirs(self.out_dir, exist_ok=True)

        self.log_box.config(state="normal")
        self.log_box.delete("1.0", "end")
        self.log_box.config(state="disabled")
        self.done_label.config(text="")
        self.dl_btn.config(state="disabled", text="Downloading...")

        self.log(f"Saving to: {self.out_dir}")
        self.log(f"Found {len(urls)} URL(s)\n")

        t = threading.Thread(target=download_urls,
                             args=(urls, self.out_dir, self.log, self.dl_btn, self.done_label),
                             daemon=True)
        t.start()

if __name__ == "__main__":
    app = App()
    app.mainloop()
