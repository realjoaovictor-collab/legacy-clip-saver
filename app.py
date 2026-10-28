"""
The Legacy Clip Saver — local app to download Instagram videos.

Usage:
    pip install flask yt-dlp
    python app.py
Then open http://localhost:5000 in your browser.

Private posts / when Instagram asks you to log in:
    set the BROWSER environment variable to the browser where you are
    logged in to Instagram (chrome, firefox, edge, safari, brave...).
    Example: BROWSER=chrome python app.py
"""
import os
import re
import shutil
import tempfile

from flask import Flask, abort, after_this_request, jsonify, request, send_file
import yt_dlp

app = Flask(__name__)
HERE = os.path.dirname(os.path.abspath(__file__))

INSTAGRAM_RE = re.compile(
    r"^https?://(www\.)?(instagram\.com|instagr\.am)/(p|reel|reels|tv|stories)/", re.I
)

# Sponsors shown in the footer: (image file next to app.py, name under the logo, website opened on click)
SPONSORS = [
    ("goblinbmx.png", "GoblinBMX", "https://goblinbmx.netlify.app"),
    ("ridenow.png", "RIDENOW", "https://ridenowstore.com/"),
    ("fisthandwear.png", "FISTHANDWEAR", "https://www.fisthandwear.eu/"),
]

PAGE = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>The Legacy Clip Saver</title>
<link rel="icon" href="/logo.jpg">
<link href="https://fonts.googleapis.com/css2?family=Bebas+Neue&family=Barlow:wght@400;600;700&display=swap" rel="stylesheet">
<style>
  :root { --bg:#0b0b14; --panel:#151530; --ink:#f4f1ea; --muted:#a6a3bd; --line:#2c2c52;
          --gold:#d4ad55; --purple:#7a3aa3; --lilac:#c49ae0; --err:#ff7a7a;
          --display:"Bebas Neue", Impact, "Arial Narrow", sans-serif; --body:Barlow, system-ui, sans-serif; }
  * { box-sizing:border-box; }
  body { margin:0; color:var(--ink); font-family:var(--body); overflow-x:hidden; padding:0 16px 32px;
    background:radial-gradient(circle at 15% 0%, rgba(43,71,184,.35), transparent 45%),
      radial-gradient(circle at 90% 100%, rgba(122,58,163,.3), transparent 45%),
      repeating-linear-gradient(-45deg, rgba(255,255,255,.025) 0 14px, transparent 14px 28px), var(--bg); }
  .tape { margin:10px -24px 0; height:30px; overflow:hidden; white-space:nowrap; background:var(--gold); color:var(--bg);
    font:22px/32px var(--display); letter-spacing:4px; transform:rotate(-1.5deg); }
  .tape.b { background:var(--purple); color:var(--ink); transform:rotate(1.5deg); margin-top:36px; }
  .tape span { display:inline-block; animation:roll 30s linear infinite; }
  @keyframes roll { to { transform:translateX(-50%); } }
  main { max-width:520px; margin:28px auto 0; display:flex; flex-direction:column; align-items:center; gap:18px; text-align:center; }
  .logo { width:168px; height:168px; border-radius:50%; object-fit:cover; border:4px solid var(--gold);
    box-shadow:0 0 0 6px var(--panel), 0 18px 50px rgba(0,0,0,.6); transform:rotate(-6deg); transition:transform .6s; }
  .logo:hover { transform:rotate(354deg); }
  h1 { margin:0; font:400 clamp(52px,14vw,78px)/.88 var(--display); letter-spacing:2px; transform:skew(-6deg); }
  h1 em { font-style:normal; color:var(--gold); }
  h1 em + em { color:var(--lilac); }
  .sub { margin:0; color:var(--muted); }
  .chips { display:flex; flex-wrap:wrap; gap:8px; justify-content:center; }
  .chip { font:18px/1 var(--display); letter-spacing:1.5px; padding:7px 12px 5px; border:1.5px solid var(--gold);
    color:var(--gold); border-radius:3px; transform:skew(-10deg); }
  .chip:nth-child(even) { border-color:var(--purple); color:var(--lilac); }
  .card { width:100%; background:var(--panel); border:1px solid var(--line); border-top:4px solid var(--gold);
    border-radius:10px; padding:20px 16px; text-align:left; display:flex; flex-direction:column; gap:10px; }
  label { font:22px var(--display); letter-spacing:1.5px; }
  input { width:100%; padding:15px 14px; font:16px var(--body); border-radius:8px; border:1.5px solid var(--line);
    background:var(--bg); color:var(--ink); }
  input:focus { outline:none; border-color:var(--gold); }
  button { padding:14px; border:0; border-radius:8px; cursor:pointer; font:28px/1 var(--display); letter-spacing:3px;
    color:var(--bg); background:var(--gold); transition:background .2s, transform .1s; }
  button:hover { background:var(--lilac); }
  button:active { transform:scale(.98); }
  button:disabled { opacity:.6; cursor:wait; }
  #status { min-height:1.4em; font-weight:600; color:var(--muted); }
  #status.ok { color:var(--gold); } #status.err { color:var(--err); }
  .wheel { display:inline-block; width:14px; height:14px; margin-right:6px; vertical-align:-2px;
    border:2px dashed var(--gold); border-radius:50%; animation:spin .8s linear infinite; }
  @keyframes spin { to { transform:rotate(360deg); } }
  small { color:var(--muted); font-size:.8rem; }
  .sponsors { max-width:520px; margin:36px auto 0; text-align:center; display:flex; flex-direction:column; gap:12px; }
  .sponsors h3 { margin:0; font:400 20px var(--display); letter-spacing:4px; color:var(--muted); }
  .sponsors h3::before, .sponsors h3::after { content:"—"; color:var(--gold); margin:0 10px; }
  .wall { display:grid; grid-template-columns:repeat(3, 1fr); gap:12px; }
  .sp { display:flex; flex-direction:column; align-items:center; gap:8px; background:transparent; border:1px solid var(--line);
    border-radius:10px; padding:14px 8px 10px; transition:border-color .2s, transform .2s; }
  .sp { text-decoration:none; } .sp:focus-visible { outline:2px solid var(--gold); outline-offset:2px; }
  .sp:hover { border-color:var(--gold); transform:translateY(-3px); }
  .sp img { width:100%; max-width:110px; aspect-ratio:1; object-fit:contain; }
  .sp span { font:16px var(--display); letter-spacing:1.5px; color:var(--gold); }

/* Title: soft float plus a light sheen sweeping across each word */
h1 { display:flex; flex-wrap:wrap; justify-content:center; column-gap:.22em; animation:float 6s ease-in-out infinite; }
h1 .the { flex-basis:100%; font-size:.42em; letter-spacing:.5em; color:var(--muted); margin-bottom:.12em; }
h1 .w { background-image:linear-gradient(110deg, var(--c) 42%, #fff6d8 50%, var(--c) 58%);
  background-size:300% 100%; background-position:100% 0; -webkit-background-clip:text; background-clip:text;
  color:transparent; animation:sheen 5s ease-in-out infinite; }
h1 .w.g { --c:var(--gold); } h1 .w.i { --c:var(--ink); animation-delay:.25s; } h1 .w.l { --c:var(--lilac); animation-delay:.5s; }
@keyframes sheen { 0%, 55% { background-position:100% 0; } 100% { background-position:0 0; } }
@keyframes float { 0%, 100% { transform:skew(-6deg) translateY(0); } 50% { transform:skew(-6deg) translateY(-4px); } }
/* Tapes: steady scroll plus a slow sway */
.tape span { animation:roll 18s linear infinite; }
.tape.b span { animation-direction:reverse; }
.tape { animation:sway 7s ease-in-out infinite; }
.tape.b { animation:swayb 7s ease-in-out infinite; }
@keyframes sway { 0%, 100% { transform:rotate(-1.5deg); } 50% { transform:rotate(-0.6deg) translateY(2px); } }
@keyframes swayb { 0%, 100% { transform:rotate(1.5deg); } 50% { transform:rotate(0.6deg) translateY(-2px); } }

/* Title v2: words drop in one by one, then hop in turn like a rider clearing a line, with the sheen on top */
h1 .the, h1 .w { display:inline-block; transform-origin:50% 100%; }
h1 .the { animation:drop .8s cubic-bezier(.2,1.4,.4,1) both, breathe 4s ease-in-out 1s infinite; }
h1 .w { animation:drop .8s cubic-bezier(.2,1.4,.4,1) var(--d) both,
  hop 4s ease-in-out calc(var(--d) + 1s) infinite,
  sheen 4s ease-in-out calc(var(--d) + 1s) infinite; }
h1 .w.g { --d:.2s; } h1 .w.i { --d:.4s; } h1 .w.l { --d:.6s; }
@keyframes drop { 0% { opacity:0; transform:translateY(-60px) rotate(-12deg) scale(.8); }
  70% { opacity:1; transform:translateY(4px) rotate(2deg) scale(1.03); } 100% { opacity:1; transform:none; } }
@keyframes hop { 0%, 30%, 100% { transform:none; } 8% { transform:translateY(-10px) rotate(-4deg); }
  16% { transform:translateY(0) scale(1.06, .94); } 22% { transform:none; } }
@keyframes breathe { 0%, 100% { letter-spacing:.5em; opacity:.85; } 50% { letter-spacing:.62em; opacity:1; } }

/* Tapes v2: always moving (scroll + sway + light sweep); page never scrolls sideways */
html, body { overflow-x:hidden; overflow-x:clip; }
.tape { position:relative; }
.tape::after { content:""; position:absolute; inset:0; pointer-events:none;
  background:linear-gradient(100deg, transparent 35%, rgba(255,255,255,.45) 50%, transparent 65%);
  background-size:250% 100%; animation:sweep 3.5s ease-in-out infinite; }
.tape.b::after { animation-delay:1.75s; }
.tape span { animation:roll 14s linear infinite !important; }
.tape.b span { animation-direction:reverse !important; }
.tape { animation:sway 5s ease-in-out infinite !important; }
.tape.b { animation:swayb 5s ease-in-out infinite !important; }
@keyframes sweep { 0% { background-position:150% 0; } 60%, 100% { background-position:-100% 0; } }
@keyframes sway { 0%, 100% { transform:rotate(-2deg); } 50% { transform:rotate(-0.4deg) translateY(3px); } }
@keyframes swayb { 0%, 100% { transform:rotate(2deg); } 50% { transform:rotate(0.4deg) translateY(-3px); } }

/* Sponsors: each logo floats and glows in turn, with a light sweep across the tile */
.sp { position:relative; overflow:hidden; }
.sp::after { content:""; position:absolute; inset:0; pointer-events:none;
  background:linear-gradient(110deg, transparent 35%, rgba(212,173,85,.28) 50%, transparent 65%);
  background-size:250% 100%; animation:sweep 4s ease-in-out var(--sd) infinite; }
.sp img { animation:spFloat 3.6s ease-in-out var(--sd) infinite, spGlow 3.6s ease-in-out var(--sd) infinite; }
.sp:nth-child(1) { --sd:0s; } .sp:nth-child(2) { --sd:.6s; } .sp:nth-child(3) { --sd:1.2s; }
.sp:hover img { animation-play-state:paused; transform:scale(1.1) rotate(-4deg); transition:transform .25s; }
@keyframes spFloat { 0%, 100% { transform:translateY(0) rotate(0); } 25% { transform:translateY(-6px) rotate(-3deg); }
  50% { transform:translateY(0) rotate(0); } 75% { transform:translateY(-3px) rotate(2deg); } }
@keyframes spGlow { 0%, 100% { filter:drop-shadow(0 0 0 rgba(212,173,85,0)); }
  50% { filter:drop-shadow(0 0 10px rgba(212,173,85,.55)); } }
@keyframes sweep { 0% { background-position:150% 0; } 60%, 100% { background-position:-100% 0; } }
</style>
</head>
<body>
  <div class="tape"><span>RIDE · SEND IT · STREET · PARK · DIRT · FLATLAND · RIDE · SEND IT · STREET · PARK · DIRT · FLATLAND · RIDE · SEND IT · STREET · PARK · DIRT · FLATLAND · </span></div>
  <main>
    <img class="logo" src="/logo.jpg" alt="Logo">
    <h1><span class="the">The</span><span class="w g">Legacy</span><span class="w i">Clip</span><span class="w l">Saver</span></h1>
    <p class="sub">Paste a Reel link and keep your tricks as MP4.</p>
    <div class="chips"><span class="chip">Street</span><span class="chip">Park</span><span class="chip">Dirt</span><span class="chip">Flatland</span><span class="chip">Race</span></div>
    <form class="card" id="f">
      <label for="url">Instagram link</label>
      <input id="url" type="url" placeholder="https://www.instagram.com/reel/..." required>
      <button id="btn" type="submit">Download clip</button>
      <div id="status" role="status"></div>
    </form>
    <small>Use it for your own videos or content you have permission to save.</small>
  </main>
  <footer class="sponsors">
    <h3>Sponsors</h3>
    <div class="wall">__SPONSORS__</div>
  </footer>
  <div class="tape b"><span>SAVE YOUR CLIPS · THE LEGACY · RIDE OR DIE · SAVE YOUR CLIPS · THE LEGACY · RIDE OR DIE · SAVE YOUR CLIPS · THE LEGACY · RIDE OR DIE · </span></div>
<script>
const f = document.getElementById('f'), btn = document.getElementById('btn'),
      st = document.getElementById('status'), inp = document.getElementById('url');
f.addEventListener('submit', async (e) => {
  e.preventDefault();
  btn.disabled = true; st.className = ''; st.innerHTML = '<span class="wheel"></span>Dropping in… this can take a few seconds.';
  try {
    const r = await fetch('/download', { method: 'POST',
      headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ url: inp.value.trim() }) });
    if (!r.ok) { const j = await r.json().catch(() => ({})); throw new Error(j.error || 'Download failed.'); }
    const blob = await r.blob();
    let name = 'instagram.mp4';
    const cd = r.headers.get('Content-Disposition') || '';
    const m = cd.match(/filename\\*?=(?:UTF-8'')?"?([^";]+)"?/i);
    if (m) name = decodeURIComponent(m[1]);
    const a = document.createElement('a');
    a.href = URL.createObjectURL(blob); a.download = name;
    document.body.appendChild(a); a.click(); a.remove();
    setTimeout(() => URL.revokeObjectURL(a.href), 5000);
    st.className = 'ok'; st.textContent = 'Clip saved: ' + name + ' 🤘';
  } catch (err) {
    st.className = 'err'; st.textContent = err.message;
  } finally { btn.disabled = false; }
});
</script>
</body>
</html>"""


def render_page():
    tiles = "".join(
        f'<a class="sp" href="{url}" target="_blank" rel="noopener" aria-label="{name} website">'
        f'<img src="/sponsors/{img}" alt="{name}"><span>{name}</span></a>'
        for img, name, url in SPONSORS
        if os.path.exists(os.path.join(HERE, img))
    )
    return PAGE.replace("__SPONSORS__", tiles)


@app.get("/")
def index():
    return render_page()


@app.get("/logo.jpg")
def logo():
    return send_file(os.path.join(HERE, "logo.jpg"))


@app.get("/sponsors/<name>")
def sponsor(name):
    # Only serve the sponsor images listed above, never other files in the folder
    allowed = {img for img, _, _ in SPONSORS}
    path = os.path.join(HERE, name)
    if name not in allowed or not os.path.exists(path):
        abort(404)
    return send_file(path)


@app.post("/download")
def download():
    url = (request.get_json(silent=True) or {}).get("url", "").strip()
    if not INSTAGRAM_RE.match(url):
        return jsonify(error="That's not an Instagram link. Use a Reel, post or story link."), 400

    tmp = tempfile.mkdtemp(prefix="insta_")
    opts = {
        "outtmpl": os.path.join(tmp, "%(uploader)s_%(id)s.%(ext)s"),
        "format": "best[ext=mp4]/best",
        "noplaylist": False,
        "quiet": True,
        "no_warnings": True,
    }
    browser = os.environ.get("BROWSER")
    if browser:
        opts["cookiesfrombrowser"] = (browser,)
    # On a server there is no browser: paste the contents of an Instagram
    # cookies.txt file into the COOKIES environment variable instead.
    cookies = os.environ.get("COOKIES")
    if cookies:
        cookie_path = os.path.join(tmp, "cookies.txt")
        with open(cookie_path, "w") as fh:
            fh.write(cookies.replace("\\n", "\n"))
        opts["cookiefile"] = cookie_path

    try:
        with yt_dlp.YoutubeDL(opts) as ydl:
            ydl.extract_info(url, download=True)
    except yt_dlp.utils.DownloadError as e:
        shutil.rmtree(tmp, ignore_errors=True)
        msg = str(e)
        if "login" in msg.lower() or "private" in msg.lower() or "rate" in msg.lower():
            msg = ("Instagram asked for a login. Log in to Instagram in your browser "
                   "and restart the app with BROWSER=chrome (or firefox, edge...).")
        return jsonify(error=msg.replace("ERROR: ", "")), 502

    videos = [f for f in os.listdir(tmp) if f.lower().endswith((".mp4", ".mov", ".webm", ".mkv"))]
    if not videos:
        shutil.rmtree(tmp, ignore_errors=True)
        return jsonify(error="No video found at that link (it may be a photo only)."), 404

    path = os.path.join(tmp, sorted(videos)[0])

    @after_this_request
    def cleanup(resp):
        resp.call_on_close(lambda: shutil.rmtree(tmp, ignore_errors=True))
        return resp

    return send_file(path, as_attachment=True, download_name=os.path.basename(path))


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    print(f"\n  The Legacy Clip Saver running at http://localhost:{port}\n")
    app.run(host="0.0.0.0", port=port)
