
from flask import Flask, render_template, request, jsonify
import yt_dlp, os, threading

app = Flask(__name__)
DOWNLOAD_DIR = os.path.expanduser("~/storage/downloads/IVDM")
os.makedirs(DOWNLOAD_DIR, exist_ok=True)
progress = {}

def dl(url, tid, quality):
    try:
        progress[tid] = {"status":"downloading","percent":0}
        def hook(d):
            if d["status"] == "downloading":
                p = d.get("_percent_str","0%").strip().replace("%","")
                try: progress[tid]["percent"] = float(p)
                except: pass
            elif d["status"] == "finished":
                progress[tid] = {"status":"finished","percent":100}
        fmt = "bestvideo[ext=mp4]+bestaudio/best" if quality=="best" else "worst"
        ydl_opts = {"outtmpl":os.path.join(DOWNLOAD_DIR,"%(title)s.%(ext)s"),"progress_hooks":[hook],"format":fmt,"noplaylist":True}
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        progress[tid]["status"] = "done"
    except Exception as e:
        progress[tid] = {"status":"error","message":str(e)}

@app.route("/")
def index():
    url = request.args.get("url","")
    return render_template("index.html", url=url)

@app.route("/download", methods=["POST"])
def start():
    data = request.json
    url = data.get("url","")
    if not url: return jsonify({"error":"No URL"}), 400
    tid = str(len(progress)+1)
    threading.Thread(target=dl, args=(url,tid,data.get("quality","best")), daemon=True).start()
    return jsonify({"task_id":tid})

@app.route("/progress/<tid>")
def get_progress(tid):
    return jsonify(progress.get(tid,{"status":"not found"}))

@app.route("/downloads")
def downloads():
    files = []
    if os.path.exists(DOWNLOAD_DIR):
        for f in os.listdir(DOWNLOAD_DIR):
            size = os.path.getsize(os.path.join(DOWNLOAD_DIR,f))
            files.append({"name":f,"size":round(size/1024/1024,2)})
    return jsonify(files)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080, debug=False)
