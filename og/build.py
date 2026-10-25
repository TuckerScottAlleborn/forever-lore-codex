"""Builds the link-preview image and the icons.

  python og/build.py

Writes, relative to the repo root:
  og.png                             preview image for Discord and other embeds (from og/card.html)
  favicon.ico, apple-touch-icon.png  raster copies of the hand-written favicon.svg
Rendering uses headless Edge; icons use Pillow.
"""
import shutil
import subprocess
import tempfile
import time
from pathlib import Path

from PIL import Image, ImageDraw

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
EDGE = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"


def render(src: Path, out: Path) -> None:
    out.unlink(missing_ok=True)
    profile = tempfile.mkdtemp(prefix="og-edge-")
    try:
        subprocess.run([
            EDGE, "--headless=new", f"--user-data-dir={profile}", "--no-first-run", "--disable-gpu",
            "--hide-scrollbars", "--force-device-scale-factor=1", "--window-size=1200,630",
            "--virtual-time-budget=5000", f"--screenshot={out}", src.as_uri(),
        ], check=True, capture_output=True, timeout=90)
        # msedge.exe can return before its headless child has written the file
        for _ in range(40):
            if out.exists():
                break
            time.sleep(0.5)
    finally:
        shutil.rmtree(profile, ignore_errors=True)
    if not out.exists():
        raise SystemExit(f"render failed: {out}")
    print("rendered", out.relative_to(ROOT))


def bez(p0, p1, p2, p3, n=24):
    """Points along a cubic Bezier, for drawing favicon.svg's curves with Pillow."""
    pts = []
    for i in range(n + 1):
        t = i / n
        a, b, c, e = (1 - t) ** 3, 3 * (1 - t) ** 2 * t, 3 * (1 - t) * t ** 2, t ** 3
        pts.append((a * p0[0] + b * p1[0] + c * p2[0] + e * p3[0], a * p0[1] + b * p1[1] + c * p2[1] + e * p3[1]))
    return pts


def icons() -> None:
    # same geometry as favicon.svg (a 64-unit box)
    glass = (bez((18.5, 14), (18.5, 25), (29.5, 27.5), (29.5, 32)) + bez((29.5, 32), (29.5, 36.5), (18.5, 39), (18.5, 50))
             + bez((45.5, 50), (45.5, 39), (34.5, 36.5), (34.5, 32)) + bez((34.5, 32), (34.5, 27.5), (45.5, 25), (45.5, 14)))
    sand_top = [(22.5, 20), (41.5, 20)] + bez((41.5, 20), (39.5, 25), (34, 27.5), (32, 31.5)) + bez((32, 31.5), (30, 27.5), (24.5, 25), (22.5, 20))
    sand_bottom = bez((21.5, 50), (22.5, 43.5), (28, 40.5), (32, 39.7)) + bez((32, 39.7), (36, 40.5), (41.5, 43.5), (42.5, 50))

    def draw(size: int) -> Image.Image:
        k = size * 4 / 64
        s = round(64 * k)
        im = Image.new("RGBA", (s, s), (0, 0, 0, 0))
        d = ImageDraw.Draw(im)
        pts = lambda ps: [(x * k, y * k) for x, y in ps]
        d.rounded_rectangle([0, 0, s - 1, s - 1], radius=12 * k, fill="#0d0c14")
        d.rectangle(pts([(14, 9), (50, 14)]), fill="#f4c76b")
        d.rectangle(pts([(14, 50), (50, 55)]), fill="#f4c76b")
        d.line(pts(glass + glass[:1]), fill="#cf9a52", width=round(3 * k), joint="curve")
        d.polygon(pts(sand_top), fill="#f4c76b")
        d.polygon(pts(sand_bottom), fill="#f4c76b")
        d.line(pts([(32, 31), (32, 40)]), fill="#f4c76b", width=max(1, round(1.6 * k)))
        return im.resize((size, size), Image.LANCZOS)

    draw(180).save(ROOT / "apple-touch-icon.png")
    draw(64).save(ROOT / "favicon.ico", sizes=[(16, 16), (32, 32), (48, 48), (64, 64)])
    print("wrote favicon.ico, apple-touch-icon.png")


def main() -> None:
    icons()
    render(HERE / "card.html", ROOT / "og.png")


if __name__ == "__main__":
    main()
