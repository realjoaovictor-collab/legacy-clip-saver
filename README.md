# The Legacy Clip Saver

Local app to download Instagram videos (Reels, posts, IGTV, stories).

## How to use (Windows, Mac or Linux)

1. Install Python 3.9+ (python.org).
2. In a terminal, inside this folder:
   ```
   pip install flask yt-dlp
   python app.py
   ```
3. Open **http://localhost:5000**, paste the link and tap **Download clip**.

To open it on your phone on the same Wi‑Fi, use `http://YOUR-COMPUTER-IP:5000`.

## On Android (no computer)

Install **Termux** (from F-Droid) and run:
```
pkg install python
pip install flask yt-dlp
python app.py
```
Then open `http://localhost:5000` in your phone's browser.

## Private videos or login errors

Instagram sometimes requires a login. Log in to Instagram in your browser and start the app like this:
```
BROWSER=chrome python app.py        # Mac/Linux
set BROWSER=chrome && python app.py # Windows
```
(`firefox`, `edge`, `brave` and `safari` also work).

## Sponsors

Sponsor logos (`goblinbmx.png`, `ridenow.png`, `fisthandwear.png`) sit next to `app.py`. To change a name, website or add a sponsor, edit the `SPONSORS` list at the top of `app.py`.

## If it stops working

Instagram changes often. Update yt-dlp:
```
pip install -U yt-dlp
```

> Use it for your own videos or content you have permission to save.

## Put it online (Render, free)

1. Create a free account on github.com and a new repository (e.g. `legacy-clip-saver`).
2. Upload every file from this folder to it (Add file → Upload files), including `Dockerfile`, `render.yaml` and all the images.
3. Create a free account on render.com, choose **New → Blueprint** and pick that repository. Render reads `render.yaml` and builds the app.
4. When it finishes, Render gives you a link like `https://legacy-clip-saver.onrender.com`. Open it on any phone.

The free plan sleeps after 15 minutes without visits, so the first open can take about a minute.

### If Instagram asks for a login on the server

Servers have no browser to borrow a login from. Export your Instagram cookies as a `cookies.txt` file (with a browser extension such as "Get cookies.txt LOCALLY"), copy its whole contents, and paste them into the `COOKIES` environment variable in Render (Environment tab). Treat that value like a password.
