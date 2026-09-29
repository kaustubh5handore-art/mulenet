"""Generate the repository QR code for slide 11 of the deck.

Usage:
    python make_qr.py https://github.com/<user>/<repo>

Writes assets/qr_repo.png; then rebuild the deck
(`python build_mulenet_v6.py`) and slide 11 will embed it automatically.
"""
import sys

import qrcode

if len(sys.argv) != 2:
    sys.exit("usage: python make_qr.py <repository url>")
url = sys.argv[1]
img = qrcode.make(url, box_size=10, border=2)
img.save("assets/qr_repo.png")
print(f"saved assets/qr_repo.png for {url}")
print("now rebuild the deck: python build_mulenet_v6.py")
