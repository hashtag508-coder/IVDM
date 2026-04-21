import threading
import os
import webbrowser
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.scrollview import ScrollView
from kivy.uix.progressbar import ProgressBar
from kivy.clock import Clock
from kivy.core.window import Window
from flask import Flask, render_template, request, jsonify
import yt_dlp

Window.clearcolor = (0.06, 0.06, 0.06, 1)

flask_app = Flask(__name__)
DOWNLOAD_DIR = "/sdcard/IVDM"
os.makedirs(DOWNLOAD_DIR, exist_ok=True)
progress_data = {}

def progress_hook(d):
    if d["status"] == "downloading":
        p = d.get("_percent_str", "0%").strip().replace("%", "")
        try:
            progress_data["percent"] = float(p)
            progress_data["status"] = "downloading"
        except:
            pass
    elif d["status"] == "finished":
        progress_data["status"] = "done"
        progress_data["percent"] = 100

def download_video(url, quality):
    try:
        progress_data["status"] = "downloading"
        progress_data["percent"] = 0
        fmt = "bestvideo[ext=mp4]+bestaudio/best" if quality == "best" else "worst"
        ydl_opts = {
            "outtmpl": os.path.join(DOWNLOAD_DIR, "%(title)s.%(ext)s"),
            "progress_hooks": [progress_hook],
            "format": fmt,
            "noplaylist": True,
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        progress_data["status"] = "done"
    except Exception as e:
        progress_data["status"] = "error"
        progress_data["message"] = str(e)

class IVDMLayout(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(orientation="vertical", padding=20, spacing=12, **kwargs)
        self.quality = "best"

        title = Label(text="[b]⚡ IVDM[/b]", markup=True, font_size=28,
                     color=(0.42, 0.39, 1, 1), size_hint_y=None, height=50)
        self.add_widget(title)

        sub = Label(text="Internet Video Download Manager",
                   font_size=13, color=(0.6, 0.6, 0.6, 1),
                   size_hint_y=None, height=25)
        self.add_widget(sub)

        self.url_input = TextInput(
            hint_text="Paste video URL here...",
            multiline=False, font_size=15,
            background_color=(0.1, 0.1, 0.18, 1),
            foreground_color=(1, 1, 1, 1),
            hint_text_color=(0.4, 0.4, 0.4, 1),
            size_hint_y=None, height=50,
            padding=[12, 12]
        )
        self.add_widget(self.url_input)

        q_layout = BoxLayout(size_hint_y=None, height=45, spacing=10)
        self.best_btn = Button(text="Best Quality",
                              background_color=(0.42, 0.39, 1, 1),
                              font_size=14)
        self.small_btn = Button(text="Smallest",
                               background_color=(0.15, 0.15, 0.25, 1),
                               font_size=14)
        self.best_btn.bind(on_press=lambda x: self.set_quality("best"))
        self.small_btn.bind(on_press=lambda x: self.set_quality("worst"))
        q_layout.add_widget(self.best_btn)
        q_layout.add_widget(self.small_btn)
        self.add_widget(q_layout)

        dl_btn = Button(text="⬇  DOWNLOAD",
                       background_color=(0.42, 0.39, 1, 1),
                       font_size=16, bold=True,
                       size_hint_y=None, height=55)
        dl_btn.bind(on_press=self.start_download)
        self.add_widget(dl_btn)

        self.status_label = Label(text="Ready",
                                 color=(0.6, 0.6, 0.6, 1),
                                 font_size=13,
                                 size_hint_y=None, height=30)
        self.add_widget(self.status_label)

        self.progress = ProgressBar(max=100, value=0,
                                   size_hint_y=None, height=15)
        self.add_widget(self.progress)

        self.files_label = Label(text="Downloaded files will appear here",
                                color=(0.5, 0.5, 0.5, 1),
                                font_size=12, text_size=(Window.width-40, None),
                                halign="left")
        self.add_widget(self.files_label)
        self.load_files()

    def set_quality(self, q):
        self.quality = q
        if q == "best":
            self.best_btn.background_color = (0.42, 0.39, 1, 1)
            self.small_btn.background_color = (0.15, 0.15, 0.25, 1)
        else:
            self.best_btn.background_color = (0.15, 0.15, 0.25, 1)
            self.small_btn.background_color = (0.42, 0.39, 1, 1)

    def start_download(self, instance):
        url = self.url_input.text.strip()
        if not url:
            self.status_label.text = "Please enter a URL!"
            return
        self.status_label.text = "Starting download..."
        self.progress.value = 0
        t = threading.Thread(target=download_video, args=(url, self.quality), daemon=True)
        t.start()
        Clock.schedule_interval(self.check_progress, 1)

    def check_progress(self, dt):
        status = progress_data.get("status", "")
        percent = progress_data.get("percent", 0)
        self.progress.value = percent
        if status == "downloading":
            self.status_label.text = f"Downloading... {percent:.1f}%"
        elif status == "done":
            self.status_label.text = "✅ Download Complete!"
            self.load_files()
            return False
        elif status == "error":
            self.status_label.text = "❌ " + progress_data.get("message", "Error")
            return False

    def load_files(self):
        if os.path.exists(DOWNLOAD_DIR):
            files = os.listdir(DOWNLOAD_DIR)
            if files:
                self.files_label.text = "📁 Downloads:\n" + "\n".join(files[-5:])
            else:
                self.files_label.text = "No downloads yet"

class IVDMApp(App):
    def build(self):
        self.title = "IVDM"
        return IVDMLayout()

if __name__ == "__main__":
    IVDMApp().run()
