# -*- coding: utf-8 -*-
"""
MuleNet v6 - Citi x NPCI Drunix Hackathon 2026 (Track: AI & Fraud Detection)
11 main slides + 1 appendix (Q&A backup), python-pptx, 16:9.

v6 changes vs v5:
  - slide 2: real, sourced numbers fill the callout - UPI fraud losses of
    Rs 1,087 crore in FY 2023-24 (up from Rs 573 crore in FY 2022-23),
    Finance Ministry data tabled in Parliament 2024 / PwC India analysis of
    RBI data; 13.4 lakh reported cases
  - slides 2 + 3: DPDP Act, 2023 citation (ss. 4-6: consent and purpose
    limitation) replaces the red [VERIFY] placeholder
  - appendix item updated to the next genuinely open legal question (s. 7)
  - everything else unchanged: no invented facts, no shadows, no pills,
    plain grey page numbers, speaker notes with judge Q&A

Run:  pip install python-pptx matplotlib
      python build_mulenet_v6.py
Output: MuleNet_v6.pptx  (+ two PNGs in assets/)
"""
import os
import re

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch

from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.shapes import MSO_SHAPE, MSO_CONNECTOR
from pptx.enum.dml import MSO_LINE_DASH_STYLE
from pptx.oxml import parse_xml
from pptx.oxml.ns import nsdecls, qn

# ---------------- palette ----------------
NAVY   = RGBColor(0x0B, 0x25, 0x45)
BLUE   = RGBColor(0x1F, 0x5F, 0xBF)
GREY   = RGBColor(0xEE, 0xF1, 0xF5)
TINT   = RGBColor(0xEA, 0xF1, 0xFB)
ORANGE = RGBColor(0xE8, 0x59, 0x0C)   # mule accounts / flagged rings only
RED    = RGBColor(0xC0, 0x00, 0x00)   # [VERIFY: ...] only
WHITE  = RGBColor(0xFF, 0xFF, 0xFF)
INK2   = RGBColor(0x3D, 0x50, 0x6B)
FAINT  = RGBColor(0x8A, 0x94, 0xA6)
LINE   = RGBColor(0xC9, 0xD2, 0xDE)

HEX_NAVY, HEX_BLUE, HEX_ORANGE = "#0B2545", "#1F5FBF", "#E8590C"
HEX_LINE, HEX_PANEL, HEX_INK2, HEX_FAINT = "#C9D2DE", "#F7F9FC", "#3D506B", "#8A94A6"

SERIF, SANS = "Georgia", "Calibri"
W, H, M = 13.333, 7.5, 0.5
VER = re.compile(r"(\[VERIFY[^\]]*\])")

# ---------------- illustrations (drawn at build time) ----------------
os.makedirs("assets", exist_ok=True)
plt.rcParams["font.family"] = ["Calibri", "DejaVu Sans"]

def draw_hero(path):
    """Title illustration: two banks, ordinary accounts, one orange mule ring."""
    fig = plt.figure(figsize=(5.93, 4.4), dpi=300)
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, 10); ax.set_ylim(0, 7.4); ax.axis("off")
    for bx, label in ((0.25, "Bank A"), (5.4, "Bank B")):
        ax.add_patch(FancyBboxPatch((bx, 0.3), 4.35, 6.7,
                     boxstyle="round,pad=0.12,rounding_size=0.18",
                     fc=HEX_PANEL, ec=HEX_LINE, lw=1.4, ls=(0, (5, 4)),
                     zorder=1))
        ax.text(bx + 0.32, 6.6, label, fontsize=12, color=HEX_NAVY,
                weight="bold", zorder=5)
    normal = [(1.5, 4.9), (1.2, 3.2), (2.9, 2.1), (1.9, 2.9),
              (6.4, 5.2), (7.6, 5.8), (6.1, 1.9), (8.6, 4.4), (8.9, 2.3)]
    edges = [((1.5, 4.9), (2.6, 5.6)), ((1.5, 4.9), (1.2, 3.2)),
             ((1.2, 3.2), (2.9, 2.1)), ((2.9, 2.1), (3.6, 3.9)),
             ((1.9, 2.9), (2.9, 2.1)), ((2.9, 2.1), (6.1, 1.9)),
             ((6.4, 5.2), (7.6, 5.8)), ((6.4, 5.2), (6.1, 1.9)),
             ((6.1, 1.9), (7.2, 1.6)), ((8.9, 2.3), (7.2, 1.6)),
             ((8.6, 4.4), (8.9, 2.3)), ((7.6, 5.8), (8.6, 4.4))]
    for p1, p2 in edges:
        ax.plot([p1[0], p2[0]], [p1[1], p2[1]], color=HEX_LINE, lw=1.1,
                zorder=2)
    ring = [(2.6, 5.6), (3.6, 3.9), (6.2, 3.0), (7.2, 1.6)]
    for i in range(4):
        p1, p2 = ring[i], ring[(i + 1) % 4]
        ax.plot([p1[0], p2[0]], [p1[1], p2[1]], color=HEX_ORANGE, lw=2.4,
                zorder=3, solid_capstyle="round")
    ax.scatter(*zip(*normal), s=150, c=HEX_BLUE, edgecolors="white",
               linewidths=1.2, zorder=4)
    ax.scatter(*zip(*ring), s=220, c=HEX_ORANGE, edgecolors="white",
               linewidths=1.2, zorder=5)
    ax.annotate("payment", xy=(2.35, 5.85), xytext=(0.45, 7.05),
                fontsize=12, color=HEX_INK2,
                arrowprops=dict(arrowstyle="->", color=HEX_INK2, lw=1.4),
                zorder=6)
    ax.text(4.95, 3.62, "flagged ring", fontsize=12, color=HEX_ORANGE,
            weight="bold", ha="center", va="center", zorder=6,
            bbox=dict(fc="white", ec="none", pad=2))
    fig.savefig(path, dpi=300)
    plt.close(fig)

def draw_strip(path):
    """Wide sketch: an injected ring hopping across three simulated banks."""
    fig = plt.figure(figsize=(12.33, 1.3), dpi=300)
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, 12.33); ax.set_ylim(0, 1.3); ax.axis("off")
    for bx, label in ((0.1, "Bank A"), (4.36, "Bank B"), (8.62, "Bank C")):
        ax.add_patch(FancyBboxPatch((bx, 0.08), 3.6, 1.14,
                     boxstyle="round,pad=0.06,rounding_size=0.12",
                     fc=HEX_PANEL, ec=HEX_LINE, lw=1.2, ls=(0, (5, 4)),
                     zorder=1))
        ax.text(bx + 0.15, 1.0, label, fontsize=12, color=HEX_NAVY,
                weight="bold", zorder=5)
    for pts in ([(0.8, 0.45), (1.5, 0.8), (2.6, 0.4)],
                [(5.0, 0.45), (7.0, 0.8)],
                [(9.3, 0.5), (11.4, 0.45), (10.6, 0.9)]):
        ax.scatter(*zip(*pts), s=110, c=HEX_BLUE, edgecolors="white",
                   linewidths=1.0, zorder=4)
    ring_pts = [(1.9, 0.55), (5.6, 0.78), (10.0, 0.55)]
    for i in range(2):
        p1, p2 = ring_pts[i], ring_pts[i + 1]
        ax.annotate("", xy=p2, xytext=p1,
                    arrowprops=dict(arrowstyle="-|>", color=HEX_ORANGE,
                                    lw=2.2, mutation_scale=16), zorder=3)
    ax.scatter(*zip(*ring_pts), s=190, c=HEX_ORANGE, edgecolors="white",
               linewidths=1.0, zorder=4)
    ax.text(0.18, 0.14, "victim pays", fontsize=12, color=HEX_INK2, zorder=5)
    ax.text(12.23, 0.14, "illustrative sketch (not data)", fontsize=12,
            color=HEX_FAINT, ha="right", zorder=5)
    fig.savefig(path, dpi=300)
    plt.close(fig)

HERO = os.path.join("assets", "hero_network.png")
STRIP = os.path.join("assets", "ring_strip.png")
draw_hero(HERO)
draw_strip(STRIP)

# ---------------- deck helpers ----------------
prs = Presentation()
prs.slide_width, prs.slide_height = Inches(W), Inches(H)
BLANK = prs.slide_layouts[6]

def new():
    s = prs.slides.add_slide(BLANK)
    s.background.fill.solid()
    s.background.fill.fore_color.rgb = WHITE
    return s

def _runs(p, text, size, color, bold, italic, font):
    for part in VER.split(text):
        if not part:
            continue
        if VER.fullmatch(part):
            r = p.add_run(); r.text = part
            f = r.font
            f.name = font; f.size = Pt(size); f.bold = True; f.italic = True
            f.color.rgb = RED
        else:
            r = p.add_run(); r.text = part
            f = r.font
            f.name = font; f.size = Pt(size); f.bold = bold; f.italic = italic
            f.color.rgb = color

def tx(s, x, y, w, h, text, size=18, color=NAVY, bold=False, italic=False,
       font=SANS, align=PP_ALIGN.LEFT, anchor=MSO_ANCHOR.TOP, spacing=1.0):
    tb = s.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    tf = tb.text_frame
    tf.word_wrap = True
    tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
    tf.vertical_anchor = anchor
    for i, ln in enumerate(text.split("\n")):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.alignment = align
        p.line_spacing = spacing
        _runs(p, ln, size, color, bold, italic, font)
    return tb

def rich(s, x, y, w, h, runs, align=PP_ALIGN.LEFT, anchor=MSO_ANCHOR.TOP,
         spacing=1.0):
    tb = s.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    tf = tb.text_frame
    tf.word_wrap = True
    tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
    tf.vertical_anchor = anchor
    p = tf.paragraphs[0]
    p.alignment = align
    p.line_spacing = spacing
    for t, size, color, bold in runs:
        r = p.add_run(); r.text = t
        f = r.font
        f.name = SANS; f.size = Pt(size); f.bold = bold; f.color.rgb = color
    return tb

def _strip_style(sp):
    st = sp._element.find(qn('p:style'))
    if st is not None:
        sp._element.remove(st)

def rect(s, x, y, w, h, fill=GREY, line=None, lw=1.0, dash=None):
    sp = s.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(x), Inches(y),
                            Inches(w), Inches(h))
    sp.shadow.inherit = False
    _strip_style(sp)
    if fill is None:
        sp.fill.background()
    else:
        sp.fill.solid(); sp.fill.fore_color.rgb = fill
    if line is None:
        sp.line.fill.background()
    else:
        sp.line.color.rgb = line; sp.line.width = Pt(lw)
        if dash:
            sp.line.dash_style = dash
    return sp

def node(s, cx, cy, d, fill=BLUE, line=None, lw=1.0):
    sp = s.shapes.add_shape(MSO_SHAPE.OVAL, Inches(cx - d/2), Inches(cy - d/2),
                            Inches(d), Inches(d))
    sp.shadow.inherit = False
    _strip_style(sp)
    if fill is None:
        sp.fill.background()
    else:
        sp.fill.solid(); sp.fill.fore_color.rgb = fill
    if line is None:
        sp.line.fill.background()
    else:
        sp.line.color.rgb = line; sp.line.width = Pt(lw)
    return sp

def seg(s, x1, y1, x2, y2, color=BLUE, w=1.5, arrowhead=False):
    c = s.shapes.add_connector(MSO_CONNECTOR.STRAIGHT, Inches(x1), Inches(y1),
                               Inches(x2), Inches(y2))
    c.shadow.inherit = False
    _strip_style(c)
    c.line.color.rgb = color; c.line.width = Pt(w)
    if arrowhead:
        ln = c.line._get_or_add_ln()
        ln.append(parse_xml('<a:tailEnd %s type="triangle" w="med" len="med"/>'
                            % nsdecls('a')))
    return c

def path(s, pts, color=BLUE, w=1.5):
    for i in range(len(pts) - 1):
        seg(s, pts[i][0], pts[i][1], pts[i+1][0], pts[i+1][1], color, w,
            arrowhead=(i == len(pts) - 2))

def title(s, kick, text):
    """Section kicker (small, blue) stacked above the Georgia sentence title."""
    tb = s.shapes.add_textbox(Inches(M), Inches(0.2), Inches(W - 2*M),
                              Inches(1.42))
    tf = tb.text_frame
    tf.word_wrap = True
    tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
    p1 = tf.paragraphs[0]
    r = p1.add_run(); r.text = kick
    f = r.font
    f.name = SANS; f.size = Pt(12); f.bold = True; f.color.rgb = BLUE
    p2 = tf.add_paragraph()
    p2.space_before = Pt(6)
    p2.line_spacing = 1.0
    r = p2.add_run(); r.text = text
    f = r.font
    f.name = SERIF; f.size = Pt(30); f.bold = True; f.color.rgb = NAVY

def pnum(s, n):
    tx(s, 12.23, 7.12, 0.6, 0.28, str(n), size=11, color=FAINT,
       align=PP_ALIGN.RIGHT)

def source(s, text):
    tx(s, M, 6.98, 11.4, 0.3, text, size=11, color=FAINT)

def notes(s, text):
    s.notes_slide.notes_text_frame.text = text

def bullet(s, x, y, w, text, size=18, h=0.8):
    node(s, x + 0.05, y + 0.13, 0.10, fill=BLUE)
    tx(s, x + 0.28, y, w - 0.28, h, text, size=size, spacing=1.08)

def table(s, x, y, widths, header, rows, row_hs, header_h=0.55, fsize=15,
          hsize=14, col_tint=None, row_tint=None):
    total_w = sum(widths)
    body_h = sum(row_hs)
    if col_tint:
        for ci, fill in col_tint.items():
            rect(s, x + sum(widths[:ci]), y + header_h, widths[ci], body_h,
                 fill=fill)
    if row_tint:
        for ri, fill in row_tint.items():
            rect(s, x, y + header_h + sum(row_hs[:ri]), total_w, row_hs[ri],
                 fill=fill)
    rect(s, x, y, total_w, header_h, fill=GREY)
    cx = x
    for cw, htxt in zip(widths, header):
        tx(s, cx + 0.14, y, cw - 0.28, header_h, htxt, size=hsize, bold=True,
           color=BLUE if htxt == "MuleNet" else NAVY, anchor=MSO_ANCHOR.MIDDLE)
        cx += cw
    seg(s, x, y + header_h, x + total_w, y + header_h, LINE, 1.0)
    ry = y + header_h
    for row, rh in zip(rows, row_hs):
        cx = x
        for ci, cell in enumerate(row):
            tx(s, cx + 0.14, ry + 0.10, widths[ci] - 0.28, rh - 0.18, cell,
               size=fsize, bold=(ci == 0), anchor=MSO_ANCHOR.TOP, spacing=1.05)
            cx += widths[ci]
        ry += rh
        seg(s, x, ry, x + total_w, ry, LINE, 0.75)

# ================= SLIDE 1 - TITLE =================
s = new()
tx(s, 0.7, 1.3, 6.2, 1.15, "MuleNet", size=58, bold=True, font=SERIF)
tx(s, 0.7, 2.58, 5.9, 1.05,
   "Catching money-mule rings across banks without sharing customer data",
   size=20, color=INK2, spacing=1.12)
tx(s, 0.7, 4.25, 6.0, 0.35, "Team: [TEAM NAME]", size=18, bold=True)
tx(s, 0.7, 4.68, 6.0, 0.35, "Kaustubh Handore  ·  Astha Sonwane", size=18)
tx(s, 0.7, 5.11, 6.0, 0.35, "Track: AI & Fraud Detection", size=18)
tx(s, 0.7, 5.54, 6.0, 0.35, "Citi × NPCI Drunix Hackathon 2026", size=18,
   color=INK2)
tx(s, 0.7, 6.15, 6.0, 0.6,
   "In this deck: problem → today's defences → our approach → data & model "
   "→ evaluation → risks → plan", size=13, color=INK2, spacing=1.1)
s.shapes.add_picture(HERO, Inches(6.9), Inches(1.3), width=Inches(5.93))
tx(s, 6.9, 5.88, 5.93, 0.5,
   "An ordinary payment in Bank A — the laundering ring behind it crosses "
   "banks.", size=13, color=INK2)
pnum(s, 1)
notes(s, "Good morning, we are [TEAM NAME] - Kaustubh Handore and Astha "
         "Sonwane. We are pitching MuleNet, a federated graph model that "
         "catches money-mule rings spread across banks. The picture on the "
         "right is the whole idea: an ordinary payment lands in one bank, but "
         "the ring behind it crosses banks. Banks never share customer data, "
         "only model updates. In the next five minutes we cover the problem, "
         "our approach, and how we plan to prove it. Likely judge question: "
         "why graphs? Short answer: laundering is a chain of accounts, and "
         "chains are exactly what graphs represent.")

# ================= SLIDE 2 - PROBLEM =================
s = new()
title(s, "01 · THE PROBLEM",
      "Fraud money leaves through chains of mule accounts that span banks")
flow = [
    (1.7, "1 · Victim pays",
     "A real customer sends money to what looks like an ordinary payee",
     None),
    (2.95, "2 · Funds hop through mule accounts",
     "Money moves quickly across accounts recruited for laundering",
     ORANGE),
    (4.2, "3 · Cash-out",
     "Money exits through withdrawals or purchases and is hard to trace",
     None),
]
for i, (fy, head, sub, edge) in enumerate(flow):
    rect(s, M, fy, 5.9, 0.9,
         fill=WHITE if edge else GREY, line=edge, lw=1.5 if edge else 1.0)
    if i == 1:
        rich(s, 0.7, fy + 0.12, 5.5, 0.3,
             [("2 · Funds hop through ", 15, NAVY, True),
              ("mule accounts", 15, ORANGE, True)])
    else:
        tx(s, 0.7, fy + 0.12, 5.5, 0.3, head, size=15, bold=True)
    tx(s, 0.7, fy + 0.46, 5.5, 0.3, sub, size=13, color=INK2)
seg(s, 3.45, 2.62, 3.45, 2.93, BLUE, 1.5, arrowhead=True)
tx(s, 3.62, 2.64, 1.8, 0.26, "payment", size=12, color=INK2)
seg(s, 3.45, 3.87, 3.45, 4.18, BLUE, 1.5, arrowhead=True)
tx(s, 3.62, 3.89, 2.0, 0.26, "rapid transfers", size=12, color=INK2)
bullet(s, M, 5.42, 6.1, "Each bank sees only its own slice of the chain",
       h=0.45)
bullet(s, M, 6.02, 6.1,
       "Pooling customer data across banks conflicts with the DPDP Act, 2023 "
       "(ss. 4-6: consent and purpose limitation)", h=0.8)

rect(s, 7.1, 1.7, 5.73, 4.9, fill=GREY)
tx(s, 7.4, 2.05, 5.15, 0.3, "UPI FRAUD, FY 2023-24", size=13, bold=True,
   color=INK2)
tx(s, 7.4, 2.45, 5.15, 0.8, "\u20b91,087 cr", size=40, bold=True, color=BLUE)
tx(s, 7.4, 3.35, 5.15, 0.55,
   "UPI fraud losses in 2023-24, up from \u20b9573 crore in 2022-23",
   size=14, color=INK2, spacing=1.05)
tx(s, 7.4, 4.3, 5.15, 0.45, "13.4 lakh", size=22, bold=True, color=BLUE)
tx(s, 7.4, 4.78, 5.15, 0.3, "reported UPI fraud cases in the same year",
   size=13, color=INK2)
tx(s, 7.4, 5.35, 5.15, 0.6,
   "We will re-check both figures against the RBI Annual Report before the "
   "finale.", size=13, color=INK2, italic=True)
source(s, "Source: Finance Ministry data tabled in Parliament, 2024; PwC "
          "India analysis of RBI data")
pnum(s, 2)
notes(s, "Let us walk the money first. A real customer pays an ordinary-looking "
         "payee, the funds hop through recruited mule accounts, and cash-out "
         "happens fast. Each bank holds one slice of that chain, so no single "
         "bank can see the whole ring. The number on the right is from "
         "government data tabled in Parliament in 2024: UPI fraud losses "
         "reached 1,087 crore rupees in FY 2023-24, up from 573 crore the year "
         "before - we will re-verify it against the RBI Annual Report before "
         "the finale. The obvious fix, pooling all customer data, runs into "
         "the DPDP Act. Judge question we expect: how current is this number? "
         "Answer: FY 2023-24 is the latest full year in that data release, and "
         "we will refresh it if newer official figures are published.")

# ================= SLIDE 3 - TODAY'S DEFENCES =================
s = new()
title(s, "02 · TODAY'S DEFENCES", "Today's defences each miss the network")
table(s, M, 1.75, [2.9, 4.4, 5.03],
      ["Approach", "How it works", "Why it misses mule rings"],
      [["Rule engines",
        "Hand-written thresholds and blacklists, updated after new fraud is seen",
        "Rules encode past patterns; a new ring shape passes until someone rewrites the rules"],
       ["Single-transaction ML (XGBoost etc.)",
        "Scores each payment on its own features, one payment at a time",
        "Every hop looks ordinary alone, so the ring shape never shows up in one record"],
       ["Centralised data pooling",
        "Banks upload raw customer data into one shared store",
        "Conflicts with the DPDP Act, 2023 (ss. 4-6: consent and purpose limitation), so it is not deployable"]],
      row_hs=[1.15, 1.15, 1.3])
tx(s, M, 6.2, 12.33, 0.4,
   "Every option either sees too little, or asks for data banks cannot legally share.",
   size=18, bold=True)
pnum(s, 3)
notes(s, "Three families of defences exist today. Rule engines encode "
         "yesterday's fraud, so new ring shapes pass until someone rewrites "
         "them. Single-transaction models score each payment in isolation, and "
         "every individual hop looks ordinary on its own. Centralised pooling "
         "would see the ring but demands data banks cannot legally share - "
         "DPDP sections 4 to 6 are the consent and purpose-limitation "
         "provisions, now cited on the slide. Judge question: why not just add "
         "more rules? Answer: rules are per-pattern, rings are per-structure, "
         "and structure is exactly what our model represents.")

# ================= SLIDE 4 - FEDERATED ROUND =================
s = new()
title(s, "03 · OUR APPROACH",
      "MuleNet: banks train one shared model, and no customer data leaves")
tx(s, M, 1.62, 6.0, 0.3, "One federated training round", size=14, bold=True,
   color=INK2)
steps = [
    "Each bank builds a graph from its own transactions",
    "A GNN trains locally inside the bank",
    "Only model weight updates are sent out",
    "The server averages the updates (FedAvg)",
    "The global model returns; scoring runs inside each bank",
]
for i, st in enumerate(steps):
    yy = 2.05 + i * 1.0
    tx(s, M, yy - 0.03, 0.6, 0.45, str(i + 1), size=20, bold=True, color=BLUE)
    tx(s, 1.2, yy, 5.55, 0.9, st, size=18, spacing=1.08)

for i, bk in enumerate(("Bank A", "Bank B", "Bank C")):
    by = 1.8 + i * 0.98
    rect(s, 7.2, by, 2.2, 0.8, fill=WHITE, line=LINE, lw=1.25)
    tx(s, 7.4, by + 0.1, 1.9, 0.28, bk, size=14, bold=True)
    tx(s, 7.4, by + 0.42, 1.9, 0.26, "local GNN training", size=12, color=INK2)
rect(s, 10.05, 2.2, 2.78, 1.05, fill=GREY)
tx(s, 10.25, 2.32, 2.4, 0.55, "Secure aggregation server", size=14, bold=True,
   spacing=1.0)
tx(s, 10.25, 2.9, 2.4, 0.26, "FedAvg averaging", size=12, color=INK2)
tx(s, 10.05, 1.88, 2.9, 0.26, "receives: weight updates only", size=12,
   color=INK2)
for y1, y2 in ((2.2, 2.5), (3.18, 2.72), (4.16, 2.95)):
    seg(s, 9.4, y1, 10.02, y2, BLUE, 1.5, arrowhead=True)
rect(s, 10.05, 4.15, 2.78, 0.95, fill=GREY)
tx(s, 10.25, 4.28, 2.4, 0.3, "Global model", size=14, bold=True)
tx(s, 10.25, 4.62, 2.4, 0.26, "aggregated from all banks", size=12,
   color=INK2)
seg(s, 11.44, 3.25, 11.44, 4.13, BLUE, 1.5, arrowhead=True)
tx(s, 9.35, 3.58, 1.95, 0.26, "averaged weights (FedAvg)", size=12,
   color=INK2, align=PP_ALIGN.RIGHT)
path(s, [(11.44, 5.10), (11.44, 5.55), (8.3, 5.55), (8.3, 4.60)])
tx(s, 8.45, 5.64, 4.0, 0.26, "updated global model returns to every bank",
   size=12, color=INK2)
pnum(s, 4)
notes(s, "Here is one training round. Each bank builds a graph from its own "
         "transactions and trains a graph neural network locally. Only the "
         "weight updates leave the bank, the server averages them with FedAvg, "
         "and the improved global model comes back for scoring inside each "
         "bank. No raw transaction and no account identity ever crosses the "
         "boundary. Judge question: what exactly is inside a weight update? "
         "Answer: numbers describing how the model should change, not "
         "transactions - and the next slide shows precisely what is shared "
         "and what is not.")

# ================= SLIDE 5 - ARCHITECTURE =================
s = new()
title(s, "04 · ARCHITECTURE",
      "Architecture: what stays in the bank and what is shared")
for i, bk in enumerate(("Bank A", "Bank B", "Bank C")):
    by = 1.65 + i * 1.10
    rect(s, M, by, 3.4, 0.95, fill=GREY)
    tx(s, 0.7, by + 0.12, 3.0, 0.3, bk, size=14, bold=True)
    tx(s, 0.7, by + 0.46, 3.0, 0.3,
       "transactions · local graph · local GNN", size=12, color=INK2)
chain5 = [
    (4.55, 1.75, "Secure aggregation server"),
    (6.85, 1.55, "Global model"),
    (8.90, 1.55, "Scoring API"),
    (11.05, 1.78, "Drunix / NPCI layer"),
]
for cx, cw, label in chain5:
    rect(s, cx, 2.4, cw, 1.1, fill=GREY)
    tx(s, cx + 0.08, 2.4, cw - 0.16, 1.1, label, size=13, bold=True,
       align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE, spacing=1.0)
for y1 in (2.125, 3.225, 4.325):
    seg(s, 3.9, y1, 4.52, 2.95, BLUE, 1.5, arrowhead=True)
seg(s, 6.30, 2.95, 6.82, 2.95, BLUE, 1.5, arrowhead=True)
seg(s, 8.40, 2.95, 8.87, 2.95, BLUE, 1.5, arrowhead=True)
seg(s, 10.45, 2.95, 11.02, 2.95, BLUE, 1.5, arrowhead=True)
tx(s, 4.0, 4.5, 2.4, 0.26, "model weight updates only", size=12, color=INK2)
tx(s, 5.70, 2.06, 1.9, 0.26, "averaged global model", size=12, color=INK2,
   align=PP_ALIGN.CENTER)
tx(s, 7.90, 2.06, 1.5, 0.26, "model parameters", size=12, color=INK2,
   align=PP_ALIGN.CENTER)
tx(s, 9.95, 2.06, 1.9, 0.26, "risk score + ring flag", size=12, color=INK2,
   align=PP_ALIGN.CENTER)
rect(s, 11.0, 4.3, 1.83, 1.35, fill=WHITE, line=LINE, lw=1.25)
tx(s, 11.12, 4.42, 1.6, 0.28, "Decision", size=13, bold=True)
tx(s, 11.12, 4.74, 1.6, 0.55, "allow / step-up verification / block",
   size=12, color=INK2, spacing=1.0)
tx(s, 11.12, 5.28, 1.6, 0.3, "flagged ring → analysts", size=12, color=ORANGE,
   bold=True)
seg(s, 11.94, 3.5, 11.94, 4.28, BLUE, 1.5, arrowhead=True)
tx(s, 10.0, 3.72, 1.75, 0.26, "payment decision", size=12, color=INK2,
   align=PP_ALIGN.RIGHT)
rect(s, M, 5.85, 6.0, 1.0, fill=GREY)
tx(s, 0.7, 5.98, 5.6, 0.28, "Stays inside the bank", size=14, bold=True)
tx(s, 0.7, 6.32, 5.6, 0.28,
   "raw transactions · account identities · local graph", size=13,
   color=INK2)
rect(s, 6.83, 5.85, 6.0, 1.0, fill=GREY)
tx(s, 7.03, 5.98, 5.6, 0.28, "Shared", size=14, bold=True, color=BLUE)
tx(s, 7.03, 6.32, 5.6, 0.28,
   "model weights · boundary-node embeddings · no raw data", size=13,
   color=INK2)
pnum(s, 5)
notes(s, "This is the full architecture. The banks keep transactions, account "
         "identities and the local graph. What travels is only model weight "
         "updates, and on the way back the global model serves scoring through "
         "an API so the decision fits inside the payment flow. The Drunix and "
         "NPCI layer turns the score into allow, step-up verification, or "
         "block, and analysts additionally receive the flagged ring. Judge "
         "question: where does cross-bank context enter if edges between banks "
         "stay local? Answer: boundary-node embeddings, and we flag that as a "
         "main risk later in the deck.")

# ================= SLIDE 6 - DATA AND MODEL =================
s = new()
title(s, "05 · DATA & MODEL",
      "Data and model: PaySim, split across simulated banks")
rect(s, M, 1.65, 5.9, 3.35, fill=GREY)
tx(s, 0.8, 1.82, 5.3, 0.32, "Data", size=18, bold=True)
tx(s, 0.8, 2.25, 2.6, 0.55, "~6.36M", size=30, bold=True, color=BLUE,
   font=SERIF)
tx(s, 0.8, 2.82, 2.5, 0.3, "transactions over 30 days", size=13, color=INK2)
tx(s, 3.7, 2.25, 2.5, 0.55, "~0.13%", size=30, bold=True, color=BLUE,
   font=SERIF)
tx(s, 3.7, 2.82, 2.5, 0.3, "flagged as fraud", size=13, color=INK2)
tx(s, 3.7, 3.12, 2.6, 0.55, "[VERIFY against downloaded file]", size=12,
   spacing=1.0)
bullet(s, 0.8, 3.9, 5.3, "We assign accounts to 3–4 simulated banks",
       size=15, h=0.42)
bullet(s, 0.8, 4.4, 5.3,
       "We inject synthetic multi-hop mule rings that cross banks, because "
       "public data has few real rings", size=15, h=0.55)
rect(s, 6.73, 1.65, 6.1, 3.35, fill=GREY)
tx(s, 7.03, 1.82, 5.5, 0.32, "Model", size=18, bold=True)
tx(s, 7.03, 2.25, 5.5, 0.3, "Accounts are nodes; transactions are edges",
   size=16, bold=True)
tx(s, 7.03, 2.7, 5.5, 0.55,
   "Node features: amount, velocity, balance change, counterparty count, "
   "hop depth", size=15, spacing=1.05)
tx(s, 7.03, 3.45, 5.5, 0.55,
   "GraphSAGE, 2 layers, with class-weighted loss for the fraud imbalance",
   size=15, spacing=1.05)
tx(s, 7.03, 4.2, 5.5, 0.55,
   "Federated with Flower: the server averages weight updates (FedAvg)",
   size=15, spacing=1.05)
s.shapes.add_picture(STRIP, Inches(M), Inches(5.15), width=Inches(12.33))
tx(s, M, 6.52, 9.5, 0.35,
   "Public simulated data is a stand-in; real cross-bank data is not "
   "available to us.", size=16, italic=True)
source(s, "Source: PaySim synthetic financial dataset, as distributed "
          "[VERIFY: confirm transaction count and fraud rate against the "
          "downloaded file]")
pnum(s, 6)
notes(s, "We train and test on PaySim, a public simulator with about 6.36 "
         "million transactions over 30 days, around 0.13 percent flagged as "
         "fraud; we will verify both numbers against the file we download. We "
         "split accounts across three or four simulated banks and inject "
         "multi-hop rings that cross banks, because public data contains few "
         "real rings - the strip at the bottom is a sketch of that, not real "
         "output. The model is a two-layer GraphSAGE with a class-weighted "
         "loss for the imbalance, federated with Flower. Judge question: is "
         "PaySim good enough? Honest answer: it is a stand-in, and the slide "
         "says so in plain words.")

# ================= SLIDE 7 - COMPARISON TABLE =================
s = new()
title(s, "06 · HOW WE DIFFER",
      "How MuleNet differs from a typical fraud model")
table(s, M, 1.75, [2.3, 4.6, 5.43],
      ["Dimension", "Typical approach", "MuleNet"],
      [["What it looks at", "One payment in isolation",
        "The network around it: accounts and the links between them"],
       ["Whose data", "One bank's own customers only",
        "Many banks at once, without sharing raw data"],
       ["Privacy", "Not a design constraint; pooling is the usual shortcut",
        "Designed in: only model weight updates ever leave"],
       ["Output", "A verdict for the payment",
        "A verdict plus the ring graph for analysts"],
       ["Model", "Rules or boosted trees on flat features",
        "Federated GraphSAGE on account graphs"]],
      row_hs=[0.85] * 5, header_h=0.6, col_tint={2: TINT})
pnum(s, 7)
notes(s, "This table is the honest comparison. The key rows are data and "
         "privacy: typical models see one bank's data, and pooling is the "
         "usual shortcut that data-protection law now blocks. MuleNet sees the "
         "network around a payment, learns from many banks at once, and only "
         "weight updates ever leave. The output differs too: we return a "
         "verdict plus the ring graph. Judge question: does federated training "
         "cost accuracy? Answer: usually a little, and our evaluation plan on "
         "the next slides is built to measure and report that gap.")

# ================= SLIDE 8 - INNOVATION x SCALE x IMPACT =================
s = new()
title(s, "07 · HACKATHON THEME", "Innovation, scale and impact")
cols = [
    (0.5, "Innovation",
     ["Federated learning plus graph neural networks, aimed at mule rings "
      "that cross banks",
      "The ring structure is the signal - it lives between banks, not inside "
      "one",
      "Federation makes that structure legal to learn from"]),
    (4.71, "Scale",
     ["A new bank joins by training locally and sending only weight updates",
      "No central data lake is created at any point",
      "Per-round cost grows with model size, not with data size"]),
    (8.92, "Impact",
     ["Earlier detection of laundering chains as they form",
      "Analysts receive the ring graph, not just a verdict",
      "Designed to fit data-protection rules from the start"]),
]
for cx, head, lines in cols:
    tx(s, cx, 1.85, 3.9, 0.45, head, size=20, bold=True, color=BLUE,
       font=SERIF)
    for li, ln in enumerate(lines):
        bullet(s, cx, 3.15 + li * 1.1, 3.85, ln, size=17, h=0.78)
# small glyphs: mini graph / growing bars / check circle (bare, no badges)
node(s, 0.65, 2.85, 0.12, fill=BLUE)
node(s, 0.95, 2.6, 0.12, fill=BLUE)
node(s, 1.25, 2.85, 0.12, fill=BLUE)
seg(s, 0.65, 2.85, 0.95, 2.6, BLUE, 1.2)
seg(s, 0.95, 2.6, 1.25, 2.85, BLUE, 1.2)
seg(s, 0.65, 2.85, 1.25, 2.85, BLUE, 1.2)
for bx, by, bh in ((4.85, 2.72, 0.22), (5.06, 2.60, 0.34), (5.27, 2.48, 0.46)):
    rect(s, bx, by, 0.16, bh, fill=BLUE)
node(s, 9.26, 2.71, 0.42, fill=None, line=BLUE, lw=2.0)
seg(s, 9.15, 2.71, 9.24, 2.80, BLUE, 2.0)
seg(s, 9.24, 2.80, 9.40, 2.62, BLUE, 2.0)
for vx in (4.51, 8.72):
    seg(s, vx, 1.9, vx, 6.3, LINE, 0.75)
pnum(s, 8)
notes(s, "Innovation, scale and impact, in the hackathon's own terms. "
         "Innovation: federated learning plus graph models aimed exactly at "
         "cross-bank mule rings. Scale: a new bank joins by training locally, "
         "there is no central data lake, and per-round cost grows with model "
         "size rather than data size. Impact: earlier detection of laundering "
         "chains, and analysts receive the ring rather than a bare verdict. "
         "Judge question: what is the marginal cost of onboarding a bank? "
         "Answer: one local training setup, because nothing central has to be "
         "rebuilt.")

# ================= SLIDE 9 - EVALUATION PLAN =================
s = new()
title(s, "08 · EVALUATION PLAN", "How we will prove it works")
table(s, M, 1.75, [2.35, 2.55, 2.9],
      ["Model", "Data it sees", "What it shows"],
      [["Single-bank XGBoost", "One bank's transactions, flat features",
        "Baseline without graph structure"],
       ["Single-bank GNN", "One bank's transaction graph",
        "What graph structure alone adds"],
       ["Centralised GNN (upper bound)", "All banks' data pooled - not deployable",
        "The ceiling if privacy were ignored"],
       ["Federated GNN (ours)", "Local graphs; only weights shared",
        "The gap to the ceiling, reported honestly"]],
      row_hs=[0.85] * 4, fsize=14, row_tint={3: TINT})
tx(s, M, 5.85, 7.8, 0.7,
   "Metrics we will report: PR-AUC; recall at fixed precision; ring-level "
   "recall; false positives per 1,000 payments; scoring latency.",
   size=15, spacing=1.1)
rect(s, 8.6, 1.75, 4.23, 4.6, fill=GREY)
tx(s, 8.85, 1.98, 3.75, 0.32, "Demo plan", size=17, bold=True)
tx(s, 8.85, 2.38, 3.75, 0.28, "PLANNED - NOT YET RUN", size=13, bold=True,
   color=BLUE)
demo = [
    "1.  Score the same payments with one bank's own model alone",
    "2.  Score them again with the federated model",
    "3.  Show a ring that the single bank scores low and the federated model "
    "flags",
]
for i, d in enumerate(demo):
    tx(s, 8.85, 2.85 + i * 0.95, 3.75, 0.85, d, size=14, spacing=1.08)
tx(s, 8.85, 5.72, 3.75, 0.6,
   "And we will show why: the ring graph, and the edges that raised its "
   "score.", size=13, color=INK2, spacing=1.05)
pnum(s, 9)
notes(s, "Nothing on this slide has been run yet, and we label it planned for "
         "that reason. We will compare four models: single-bank XGBoost, "
         "single-bank GNN, a centralised GNN as the upper bound, and our "
         "federated model, and we will report the gap to that bound honestly. "
         "The metrics are PR-AUC, recall at fixed precision, ring-level "
         "recall, false positives per thousand payments, and scoring latency. "
         "The demo will show one ring that Bank A alone scores low and the "
         "federated model flags, and we will show why - the ring graph and the "
         "edges that raised its score. Judge question: what if the federated "
         "model cannot beat the single-bank baseline? Answer: then we report "
         "that, because a negative result measured properly is still useful "
         "evidence.")

# ================= SLIDE 10 - RISKS =================
s = new()
title(s, "09 · RISKS", "Main risks and how we handle them")
table(s, M, 1.75, [3.3, 4.1, 4.93],
      ["Risk", "Why it matters", "Our plan"],
      [["Cross-bank edges are split between banks",
        "A hop from Bank A to Bank B lives in neither local graph",
        "Exchange boundary-node embeddings across banks; fall back to a "
        "single-bank graph model if that fails"],
       ["Federated model may trail a centralised one",
        "Averaged updates can lose accuracy compared with pooled training",
        "Report the gap to the upper bound honestly; tune aggregation rounds "
        "and local epochs"],
       ["Simulated data may not match real fraud",
        "PaySim patterns differ from live UPI traffic",
        "Say so explicitly; test on injected rings and on PaySim's own fraud "
        "labels"],
       ["NPCI API access is not guaranteed",
        "The real-time path depends on sandbox approval",
        "Mock the API layer now and swap in the sandbox when access is "
        "granted"]],
      row_hs=[1.1] * 4, fsize=14)
pnum(s, 10)
notes(s, "Four risks we have planned around. Cross-bank edges are split "
         "between banks, so we will exchange boundary-node embeddings and can "
         "fall back to a single-bank graph model. The federated model may "
         "trail the centralised one, and we commit to reporting that gap "
         "rather than hiding it. PaySim is a stand-in for real traffic, so we "
         "test on injected rings and say clearly what it cannot show. And if "
         "NPCI sandbox access does not come through, the API layer is mocked "
         "and swappable. Judge question: which risk worries you most? Answer: "
         "honestly, data realism, which is why we scope our claims to what "
         "PaySim can support.")

# ================= SLIDE 11 - TIMELINE, TEAM, ASK =================
s = new()
title(s, "10 · PLAN & TEAM", "Plan from launch to finale")
seg(s, 0.7, 2.55, 12.4, 2.55, LINE, 1.5)
seg(s, 0.7, 2.55, 12.4, 2.55, LINE, 1.5, arrowhead=True)
seg(s, 2.9, 2.55, 10.3, 2.55, BLUE, 2.5)
node(s, 1.3, 2.55, 0.16, fill=NAVY)
node(s, 2.9, 2.55, 0.14, fill=BLUE)
node(s, 10.3, 2.55, 0.14, fill=BLUE)
node(s, 11.9, 2.55, 0.16, fill=NAVY)
tx(s, 0.85, 2.02, 1.6, 0.28, "9 Oct", size=14, bold=True)
tx(s, 0.85, 2.74, 1.6, 0.28, "Launch", size=13, color=INK2)
tx(s, 2.9, 2.02, 4.5, 0.28, "10 Oct – 22 Nov", size=14, bold=True)
tx(s, 2.9, 2.74, 4.5, 0.28, "Coding round", size=13, color=INK2)
tx(s, 11.15, 2.02, 1.6, 0.28, "4 Dec", size=14, bold=True)
tx(s, 11.15, 2.74, 1.7, 0.28, "Grand finale", size=13, color=INK2)
phases = ["1 · Baseline graph model", "2 · Federated training",
          "3 · Scoring API + explainability", "4 · Dashboard + Drunix",
          "5 · Testing and freeze"]
for i, ph in enumerate(phases):
    px = 2.9 + i * 1.48
    rect(s, px, 3.2, 1.35, 0.85, fill=GREY)
    tx(s, px + 0.08, 3.28, 1.19, 0.7, ph, size=12, spacing=1.0)
    if i < 4:
        seg(s, px + 1.35, 3.62, px + 1.47, 3.62, BLUE, 1.25, arrowhead=True)
tx(s, M, 4.45, 3.0, 0.32, "Team", size=16, bold=True)
team = [("Kaustubh Handore", "Team lead · graph model"),
        ("Astha Sonwane", "Federated training · evaluation")]
for i, (nm, role) in enumerate(team):
    cx = 1.77 + i * 5.2
    rect(s, cx, 4.85, 4.6, 1.3, fill=GREY)
    tx(s, cx + 0.25, 5.08, 4.1, 0.3, nm, size=15, bold=True)
    tx(s, cx + 0.25, 5.48, 4.1, 0.3, role, size=13, color=INK2)
# QR - dashed placeholder until assets/qr_repo.png exists (python make_qr.py <url>)
if os.path.exists("assets/qr_repo.png"):
    s.shapes.add_picture("assets/qr_repo.png", Inches(11.68), Inches(4.85),
                         height=Inches(1.05))
    tx(s, 11.5, 5.98, 1.4, 0.3, "scan: code repo", size=12, color=FAINT,
       align=PP_ALIGN.CENTER)
else:
    rect(s, 11.68, 4.85, 1.05, 1.05, fill=WHITE, line=LINE, lw=1.25,
         dash=MSO_LINE_DASH_STYLE.DASH)
    tx(s, 11.68, 4.85, 1.05, 1.05, "QR", size=16, bold=True, color=FAINT,
       align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)
    tx(s, 11.5, 5.98, 1.4, 0.3, "[add repo link]", size=12, color=FAINT,
       align=PP_ALIGN.CENTER)
tx(s, M, 6.42, 11.0, 0.35,
   "Our ask: NPCI sandbox access, and feedback from Citi's fraud analysts "
   "during the coding round.", size=14, italic=True, color=INK2)
pnum(s, 11)
notes(s, "The plan against the real dates. Launch on 9 October; coding from "
         "10 October to 22 November, in five phases: baseline graph model, "
         "federated training, scoring API with explainability, dashboard with "
         "Drunix integration, then testing and freeze; grand finale on 4 "
         "December. The team: Kaustubh owns the graph model, Astha owns "
         "federated training and evaluation; the QR goes to our repository. "
         "And we end with a concrete ask - sandbox access and fraud-team "
         "feedback. Judge question: what is your first checkpoint? Answer: a "
         "working single-bank graph model early in the coding window, because "
         "everything federated builds on it.")

# ================= SLIDE 12 - APPENDIX (Q&A BACKUP) =================
s = new()
title(s, "APPENDIX · FOR Q&A ONLY",
      "Backup: method details and the legal questions we are checking")
panels = [
    (0.5, "FedAvg, in one line"),
    (4.71, "GraphSAGE, our configuration"),
    (8.92, "Legal questions we are checking"),
]
for px, head in panels:
    rect(s, px, 1.75, 3.9, 4.5, fill=GREY)
    tx(s, px + 0.25, 1.95, 3.4, 0.35, head, size=16, bold=True)
tx(s, 0.75, 2.55, 3.4, 0.45, "wₜ₊₁ = Σₖ (nₖ / n) · wₖ", size=18,
   font=SERIF, italic=True)
for i, ln in enumerate([
    "Each bank trains on its own data only",
    "The global update weights each bank by its share of training examples",
    "A standard, well-studied scheme - we add no new theory",
]):
    bullet(s, 0.75, 3.25 + i * 0.95, 3.4, ln, size=14, h=0.85)
for i, ln in enumerate([
    "2 layers; each node aggregates messages from sampled neighbours",
    "Mean aggregation, chosen for stability on skewed transaction graphs",
    "Hidden size and sampling depth tuned during the coding round",
]):
    bullet(s, 4.96, 2.55 + i * 1.15, 3.4, ln, size=14, h=1.0)
for i, ln in enumerate([
    "[VERIFY: whether fraud scoring can rely on 'legitimate uses' under "
    "s. 7, or needs fresh customer consent]",
    "[VERIFY: legal view on whether model weights and embeddings count as "
    "personal data]",
    "[VERIFY: RBI requirements on storage of payment system data]",
]):
    bullet(s, 9.17, 2.55 + i * 1.15, 3.4, ln, size=14, h=1.0)
tx(s, M, 6.5, 11.0, 0.35,
   "Backup for questions only — we skip this slide in the main run-through.",
   size=13, italic=True, color=INK2)
pnum(s, 12)
notes(s, "We keep this slide hidden unless a judge digs into the method. "
         "FedAvg: the server computes a weighted average of the banks' "
         "weights, weighted by each bank's share of training examples. "
         "GraphSAGE: two layers with neighbour sampling keeps the computation "
         "bounded inside each bank. The red items are legal checks we will "
         "complete before claiming compliance - we will not hand-wave them. "
         "Judge question: do weight updates leak personal data? Answer: that "
         "is exactly the open question we are getting a legal opinion on, and "
         "boundary-node embeddings are designed to be aggregated statistics "
         "rather than raw records.")

# ---------------- save ----------------
prs.core_properties.title = "MuleNet v6 — Citi × NPCI Drunix Hackathon 2026"
prs.core_properties.author = "Kaustubh Handore, Astha Sonwane"
prs.core_properties.subject = "AI & Fraud Detection track"
prs.save("MuleNet_v6.pptx")
print("Saved MuleNet_v6.pptx with %d slides" % len(prs.slides._sldIdLst))
