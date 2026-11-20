"""
DeepShield — PowerPoint Presentation Builder
6-slide minimalistic dark-mode deck
"""

from pptx import Presentation
from pptx.util import Inches, Pt, Emu
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN
from pptx.util import Inches, Pt
import os

# ─── Color Palette ──────────────────────────────────────────────────────────
BG_DARK      = RGBColor(0x0D, 0x0F, 0x14)   # near-black background
BG_CARD      = RGBColor(0x14, 0x18, 0x22)   # card background
ACCENT_CYAN  = RGBColor(0x00, 0xD4, 0xFF)   # electric cyan
ACCENT_PURPLE= RGBColor(0x7C, 0x3A, 0xFF)   # deep purple
WHITE        = RGBColor(0xFF, 0xFF, 0xFF)
LIGHT_GRAY   = RGBColor(0xA8, 0xB4, 0xC8)
DARK_LINE    = RGBColor(0x1E, 0x25, 0x35)
RED_ALERT    = RGBColor(0xFF, 0x3B, 0x3B)
GREEN_OK     = RGBColor(0x00, 0xE5, 0x7A)

SLIDE_W = Inches(13.33)
SLIDE_H = Inches(7.5)


def new_prs():
    prs = Presentation()
    prs.slide_width  = SLIDE_W
    prs.slide_height = SLIDE_H
    return prs


def blank_slide(prs):
    layout = prs.slide_layouts[6]  # completely blank
    return prs.slides.add_slide(layout)


def fill_bg(slide, color=BG_DARK):
    bg = slide.background
    fill = bg.fill
    fill.solid()
    fill.fore_color.rgb = color


def add_rect(slide, left, top, width, height, fill_color, alpha=None, line_color=None, line_width=Pt(0)):
    shape = slide.shapes.add_shape(1, left, top, width, height)  # MSO_SHAPE_TYPE.RECTANGLE
    shape.fill.solid()
    shape.fill.fore_color.rgb = fill_color
    if line_color:
        shape.line.color.rgb = line_color
        shape.line.width = line_width
    else:
        shape.line.fill.background()
    return shape


def add_text(slide, text, left, top, width, height,
             font_size=Pt(14), bold=False, color=WHITE,
             align=PP_ALIGN.LEFT, italic=False, wrap=True):
    txBox = slide.shapes.add_textbox(left, top, width, height)
    tf = txBox.text_frame
    tf.word_wrap = wrap
    p = tf.paragraphs[0]
    p.alignment = align
    run = p.add_run()
    run.text = text
    run.font.size = font_size
    run.font.bold = bold
    run.font.italic = italic
    run.font.color.rgb = color
    return txBox


def add_label_value(slide, label, value, left, top, width,
                    label_color=ACCENT_CYAN, value_color=WHITE,
                    label_size=Pt(9), value_size=Pt(13)):
    txBox = slide.shapes.add_textbox(left, top, width, Inches(0.5))
    tf = txBox.text_frame
    tf.word_wrap = True

    p = tf.paragraphs[0]
    r1 = p.add_run()
    r1.text = label.upper() + "  "
    r1.font.size = label_size
    r1.font.bold = True
    r1.font.color.rgb = label_color

    r2 = p.add_run()
    r2.text = value
    r2.font.size = value_size
    r2.font.color.rgb = value_color


def add_accent_line(slide, left, top, width, color=ACCENT_CYAN, height=Pt(2.5)):
    bar = slide.shapes.add_shape(1, left, top, width, int(height))
    bar.fill.solid()
    bar.fill.fore_color.rgb = color
    bar.line.fill.background()


# ════════════════════════════════════════════════════════════════════════════
# SLIDE 1 — Title
# ════════════════════════════════════════════════════════════════════════════
def slide_title(prs):
    slide = blank_slide(prs)
    fill_bg(slide, BG_DARK)

    # Left vertical accent bar
    add_rect(slide, Inches(0), Inches(0), Inches(0.06), SLIDE_H, ACCENT_CYAN)

    # Subtle grid dot background texture (horizontal lines)
    for i in range(1, 8):
        add_rect(slide, Inches(0.06), Inches(i * 0.9), SLIDE_W, Pt(0.5), DARK_LINE)

    # Big glowing title word
    add_text(slide, "DEEP", Inches(1.1), Inches(1.6), Inches(6), Inches(1.6),
             font_size=Pt(88), bold=True, color=WHITE, align=PP_ALIGN.LEFT)
    add_text(slide, "SHIELD", Inches(1.1), Inches(2.7), Inches(7), Inches(1.6),
             font_size=Pt(88), bold=True, color=ACCENT_CYAN, align=PP_ALIGN.LEFT)

    # Tagline
    add_text(slide, "AI-Powered Deepfake & Image Manipulation Detection",
             Inches(1.1), Inches(4.4), Inches(8), Inches(0.6),
             font_size=Pt(18), color=LIGHT_GRAY, align=PP_ALIGN.LEFT)

    # Cyan divider
    add_accent_line(slide, Inches(1.1), Inches(5.1), Inches(5), ACCENT_CYAN, Pt(2))

    # Bottom meta info
    add_text(slide, "Forensic Image Intelligence Suite  •  v1.0  •  Local Deployment",
             Inches(1.1), Inches(5.4), Inches(10), Inches(0.5),
             font_size=Pt(10), color=LIGHT_GRAY, align=PP_ALIGN.LEFT)

    # Right side — tag badge
    add_rect(slide, Inches(10.2), Inches(3.1), Inches(2.5), Inches(0.55), ACCENT_PURPLE)
    add_text(slide, "HEURISTIC · FORENSIC · REAL-TIME",
             Inches(10.2), Inches(3.1), Inches(2.5), Inches(0.55),
             font_size=Pt(8), bold=True, color=WHITE, align=PP_ALIGN.CENTER)

    return slide


# ════════════════════════════════════════════════════════════════════════════
# SLIDE 2 — The Problem
# ════════════════════════════════════════════════════════════════════════════
def slide_problem(prs):
    slide = blank_slide(prs)
    fill_bg(slide, BG_DARK)

    add_rect(slide, Inches(0), Inches(0), Inches(0.06), SLIDE_H, RED_ALERT)

    # Section label
    add_text(slide, "01 / PROBLEM STATEMENT", Inches(0.4), Inches(0.3), Inches(6), Inches(0.4),
             font_size=Pt(9), color=LIGHT_GRAY, bold=True)

    # Title
    add_text(slide, "The Deepfake\nThreat Landscape",
             Inches(0.4), Inches(0.7), Inches(7), Inches(1.5),
             font_size=Pt(40), bold=True, color=WHITE)
    add_accent_line(slide, Inches(0.4), Inches(2.3), Inches(3.5), RED_ALERT)

    # Stats — 3 big number cards
    stats = [
        ("500K+",  "Deepfake videos\ndetected online (2023)"),
        ("96%",    "Of victims are\nnon-consenting women"),
        ("2.7×",   "Increase in deepfake\nfraud cases YoY"),
    ]
    card_left = [Inches(0.4), Inches(4.5), Inches(8.6)]
    for i, (num, desc) in enumerate(stats):
        add_rect(slide, card_left[i], Inches(2.7), Inches(3.8), Inches(2.0), BG_CARD)
        add_accent_line(slide, card_left[i], Inches(2.7), Inches(3.8), RED_ALERT, Pt(3))
        add_text(slide, num, card_left[i] + Inches(0.2), Inches(2.9), Inches(3.5), Inches(0.9),
                 font_size=Pt(42), bold=True, color=RED_ALERT)
        add_text(slide, desc, card_left[i] + Inches(0.2), Inches(3.75), Inches(3.4), Inches(0.8),
                 font_size=Pt(11), color=LIGHT_GRAY)

    # Bottom statement
    add_rect(slide, Inches(0.4), Inches(5.1), Inches(12.5), Inches(1.7), BG_CARD)
    add_text(slide,
             "Generative AI tools (GANs, Diffusion Models) have made it trivially easy to create "
             "convincing fake faces. Traditional detection methods fail at scale. DeepShield "
             "uses multi-signal forensic analysis to fight back.",
             Inches(0.7), Inches(5.25), Inches(12.0), Inches(1.4),
             font_size=Pt(13), color=WHITE)

    return slide


# ════════════════════════════════════════════════════════════════════════════
# SLIDE 3 — Tech Stack
# ════════════════════════════════════════════════════════════════════════════
def slide_stack(prs):
    slide = blank_slide(prs)
    fill_bg(slide, BG_DARK)

    add_rect(slide, Inches(0), Inches(0), Inches(0.06), SLIDE_H, ACCENT_CYAN)
    add_text(slide, "02 / TECHNOLOGY STACK", Inches(0.4), Inches(0.3), Inches(6), Inches(0.4),
             font_size=Pt(9), color=LIGHT_GRAY, bold=True)
    add_text(slide, "What Powers\nDeepShield",
             Inches(0.4), Inches(0.7), Inches(6), Inches(1.5),
             font_size=Pt(40), bold=True, color=WHITE)
    add_accent_line(slide, Inches(0.4), Inches(2.3), Inches(3), ACCENT_CYAN)

    # 2-column tech cards
    left_col = [
        ("BACKEND",   "FastAPI + Uvicorn",    "Async REST API, ASGI server, zero-overhead routing"),
        ("DETECTION", "OpenCV + NumPy",        "ELA, FFT, Haar Cascade face detection, pixel math"),
        ("AI LAYER",  "PyTorch + HuggingFace", "ViT model ready (disabled) · Transformers pipeline"),
    ]
    right_col = [
        ("IMAGE I/O",  "Pillow (PIL)",          "JPEG round-trip compression for ELA forensics"),
        ("FRONTEND",   "HTML5 / CSS3 / JS",     "Vanilla SPA served by FastAPI StaticFiles"),
        ("OVERRIDE",   "suspicious_list.txt",   "Filename-pattern override system · fnmatch wildcards"),
    ]

    for i, (label, tech, desc) in enumerate(left_col):
        y = Inches(2.55) + i * Inches(1.45)
        add_rect(slide, Inches(0.4), y, Inches(5.9), Inches(1.25), BG_CARD)
        add_accent_line(slide, Inches(0.4), y, Inches(5.9), ACCENT_CYAN, Pt(2.5))
        add_text(slide, label, Inches(0.65), y + Inches(0.08), Inches(2), Inches(0.3),
                 font_size=Pt(8), bold=True, color=ACCENT_CYAN)
        add_text(slide, tech, Inches(0.65), y + Inches(0.32), Inches(5.5), Inches(0.38),
                 font_size=Pt(16), bold=True, color=WHITE)
        add_text(slide, desc, Inches(0.65), y + Inches(0.72), Inches(5.5), Inches(0.45),
                 font_size=Pt(10), color=LIGHT_GRAY)

    for i, (label, tech, desc) in enumerate(right_col):
        y = Inches(2.55) + i * Inches(1.45)
        add_rect(slide, Inches(6.9), y, Inches(5.9), Inches(1.25), BG_CARD)
        add_accent_line(slide, Inches(6.9), y, Inches(5.9), ACCENT_PURPLE, Pt(2.5))
        add_text(slide, label, Inches(7.15), y + Inches(0.08), Inches(2), Inches(0.3),
                 font_size=Pt(8), bold=True, color=ACCENT_PURPLE)
        add_text(slide, tech, Inches(7.15), y + Inches(0.32), Inches(5.5), Inches(0.38),
                 font_size=Pt(16), bold=True, color=WHITE)
        add_text(slide, desc, Inches(7.15), y + Inches(0.72), Inches(5.5), Inches(0.45),
                 font_size=Pt(10), color=LIGHT_GRAY)

    return slide


# ════════════════════════════════════════════════════════════════════════════
# SLIDE 4 — How It Works
# ════════════════════════════════════════════════════════════════════════════
def slide_how(prs):
    slide = blank_slide(prs)
    fill_bg(slide, BG_DARK)

    add_rect(slide, Inches(0), Inches(0), Inches(0.06), SLIDE_H, ACCENT_PURPLE)
    add_text(slide, "03 / DETECTION PIPELINE", Inches(0.4), Inches(0.3), Inches(6), Inches(0.4),
             font_size=Pt(9), color=LIGHT_GRAY, bold=True)
    add_text(slide, "3-Layer Forensic\nAnalysis Engine",
             Inches(0.4), Inches(0.7), Inches(7), Inches(1.5),
             font_size=Pt(40), bold=True, color=WHITE)
    add_accent_line(slide, Inches(0.4), Inches(2.3), Inches(3.5), ACCENT_PURPLE)

    layers = [
        ("ELA",  "Error Level Analysis",
         "Re-saves image at JPEG quality=90 and compares pixel-level compression differences. "
         "A manipulated face has a different compression history than the background — ELA exposes it.",
         ACCENT_CYAN),
        ("FFT",  "Fast Fourier Transform",
         "Converts the face crop into the frequency domain. GAN/Diffusion upsampling leaves "
         "periodic checkerboard peaks (Crest Factor > 9.0) invisible to the human eye.",
         ACCENT_PURPLE),
        ("GEO",  "Geometry & Symmetry",
         "Measures facial symmetry MAE. Perfect mirrors (MAE < 4) = copy-paste fake. "
         "Also checks Laplacian blur ratio at face borders to detect blending seams.",
         RGBColor(0xFF, 0x8C, 0x00)),
    ]

    for i, (tag, name, desc, color) in enumerate(layers):
        y = Inches(2.6) + i * Inches(1.5)
        # Number badge
        add_rect(slide, Inches(0.4), y, Inches(0.7), Inches(1.2), color)
        add_text(slide, f"0{i+1}", Inches(0.4), y + Inches(0.22), Inches(0.7), Inches(0.7),
                 font_size=Pt(26), bold=True, color=BG_DARK, align=PP_ALIGN.CENTER)
        # Card
        add_rect(slide, Inches(1.2), y, Inches(11.7), Inches(1.2), BG_CARD)
        add_text(slide, f"{tag}  ·  {name}",
                 Inches(1.45), y + Inches(0.1), Inches(11.2), Inches(0.4),
                 font_size=Pt(14), bold=True, color=color)
        add_text(slide, desc,
                 Inches(1.45), y + Inches(0.5), Inches(11.2), Inches(0.65),
                 font_size=Pt(11), color=LIGHT_GRAY)

    return slide


# ════════════════════════════════════════════════════════════════════════════
# SLIDE 5 — Scoring Criteria
# ════════════════════════════════════════════════════════════════════════════
def slide_scoring(prs):
    slide = blank_slide(prs)
    fill_bg(slide, BG_DARK)

    add_rect(slide, Inches(0), Inches(0), Inches(0.06), SLIDE_H, GREEN_OK)
    add_text(slide, "04 / SCORING CRITERIA", Inches(0.4), Inches(0.3), Inches(6), Inches(0.4),
             font_size=Pt(9), color=LIGHT_GRAY, bold=True)
    add_text(slide, "How the Threat\nScore is Calculated",
             Inches(0.4), Inches(0.7), Inches(7), Inches(1.5),
             font_size=Pt(40), bold=True, color=WHITE)
    add_accent_line(slide, Inches(0.4), Inches(2.3), Inches(4), GREEN_OK)

    # Formula box
    add_rect(slide, Inches(0.4), Inches(2.55), Inches(12.5), Inches(0.85), BG_CARD)
    add_text(slide, "COMPOSITE SCORE  =  ( ELA × 50% )  +  ( FFT × 30% )  +  ( GEOMETRY × 20% )",
             Inches(0.7), Inches(2.68), Inches(12.0), Inches(0.6),
             font_size=Pt(15), bold=True, color=ACCENT_CYAN, align=PP_ALIGN.CENTER)

    # Weight breakdown bars
    bars = [
        ("ELA — Error Level Analysis",  50, ACCENT_CYAN,
         "Most reliable signal. Detects compression history mismatch at splice boundaries."),
        ("FFT — Frequency Analysis",    30, ACCENT_PURPLE,
         "Catches periodic GAN checkerboard artifacts. Threshold: peak_ratio > 9.0."),
        ("GEOMETRY — Face Symmetry",    20, RGBColor(0xFF, 0x8C, 0x00),
         "Flags mirror fakes (MAE < 4) and blending seams (blur_ratio < 0.08)."),
    ]

    for i, (label, pct, color, note) in enumerate(bars):
        y = Inches(3.6) + i * Inches(1.1)
        add_text(slide, label, Inches(0.4), y, Inches(5), Inches(0.35),
                 font_size=Pt(11), bold=True, color=color)
        add_text(slide, note, Inches(0.4), y + Inches(0.35), Inches(8.5), Inches(0.45),
                 font_size=Pt(9.5), color=LIGHT_GRAY)
        # Bar track
        add_rect(slide, Inches(9.2), y + Inches(0.05), Inches(3.7), Inches(0.28), DARK_LINE)
        # Fill
        add_rect(slide, Inches(9.2), y + Inches(0.05), Inches(3.7 * pct / 100), Inches(0.28), color)
        add_text(slide, f"{pct}%", Inches(9.2 + 3.7 * pct / 100 + 0.05), y,
                 Inches(0.5), Inches(0.35),
                 font_size=Pt(11), bold=True, color=color)

    # Verdict bar
    add_rect(slide, Inches(0.4), Inches(6.55), Inches(5.8), Inches(0.65), RED_ALERT)
    add_text(slide, "≥ 65%  →  MANIPULATED (DEEPFAKE)",
             Inches(0.4), Inches(6.55), Inches(5.8), Inches(0.65),
             font_size=Pt(13), bold=True, color=WHITE, align=PP_ALIGN.CENTER)

    add_rect(slide, Inches(6.8), Inches(6.55), Inches(6.0), Inches(0.65), GREEN_OK)
    add_text(slide, "< 65%  →  ORIGINAL (AUTHENTIC)",
             Inches(6.8), Inches(6.55), Inches(6.0), Inches(0.65),
             font_size=Pt(13), bold=True, color=BG_DARK, align=PP_ALIGN.CENTER)

    return slide


# ════════════════════════════════════════════════════════════════════════════
# SLIDE 6 — Key Features & Demo
# ════════════════════════════════════════════════════════════════════════════
def slide_demo(prs):
    slide = blank_slide(prs)
    fill_bg(slide, BG_DARK)

    add_rect(slide, Inches(0), Inches(0), Inches(0.06), SLIDE_H, ACCENT_CYAN)
    add_text(slide, "05 / KEY FEATURES", Inches(0.4), Inches(0.3), Inches(6), Inches(0.4),
             font_size=Pt(9), color=LIGHT_GRAY, bold=True)
    add_text(slide, "Features &\nDemo",
             Inches(0.4), Inches(0.7), Inches(7), Inches(1.5),
             font_size=Pt(40), bold=True, color=WHITE)
    add_accent_line(slide, Inches(0.4), Inches(2.3), Inches(2.5), ACCENT_CYAN)

    features = [
        ("🖼",  "Image & Video Analysis",   "Supports JPG, PNG, MP4, MOV. Video sampled across 15 frames with temporal jitter detection."),
        ("📡",  "ELA + FFT Visualisations", "Real-time forensic heatmaps and frequency spectrum charts rendered in the browser."),
        ("🎯",  "Suspicious Override List",  "Add filenames to suspicious_list.txt — uploads match instantly flagged as DEEPFAKE. No restart needed."),
        ("⚡",  "100% Local Deployment",    "No cloud, no data leaks. Runs on localhost:8000 via FastAPI. Private and instant."),
        ("🤖",  "ViT ML Model Ready",       "HuggingFace 'umm-maybe/AI-image-detector' integrated — enable with one flag when hardware allows."),
        ("🛡",  "Multi-Signal Confidence",  "Three independent signals cross-validate each other. Threshold tuned to 65% to minimise false positives."),
    ]

    positions = [
        (Inches(0.4),  Inches(2.55)),
        (Inches(4.55), Inches(2.55)),
        (Inches(8.7),  Inches(2.55)),
        (Inches(0.4),  Inches(4.85)),
        (Inches(4.55), Inches(4.85)),
        (Inches(8.7),  Inches(4.85)),
    ]

    for i, (icon, title, desc) in enumerate(features):
        left, top = positions[i]
        add_rect(slide, left, top, Inches(3.9), Inches(1.95), BG_CARD)
        add_accent_line(slide, left, top, Inches(3.9), ACCENT_CYAN if i % 2 == 0 else ACCENT_PURPLE, Pt(2.5))
        add_text(slide, icon + "  " + title,
                 left + Inches(0.18), top + Inches(0.12), Inches(3.5), Inches(0.45),
                 font_size=Pt(12), bold=True, color=WHITE)
        add_text(slide, desc,
                 left + Inches(0.18), top + Inches(0.58), Inches(3.55), Inches(1.25),
                 font_size=Pt(9.5), color=LIGHT_GRAY)

    # CTA Footer
    add_rect(slide, Inches(0.4), Inches(7.0), Inches(12.5), Inches(0.35), ACCENT_CYAN)
    add_text(slide, "Live Demo  →  http://localhost:8000",
             Inches(0.4), Inches(7.0), Inches(12.5), Inches(0.35),
             font_size=Pt(12), bold=True, color=BG_DARK, align=PP_ALIGN.CENTER)

    return slide


# ════════════════════════════════════════════════════════════════════════════
# BUILD
# ════════════════════════════════════════════════════════════════════════════
if __name__ == "__main__":
    prs = new_prs()

    print("\n" + "="*55)
    print("     DeepShield — PPT Builder")
    print("="*55)

    print("  [1/6] Title slide...")
    slide_title(prs)
    print("  [2/6] Problem statement...")
    slide_problem(prs)
    print("  [3/6] Tech stack...")
    slide_stack(prs)
    print("  [4/6] How it works...")
    slide_how(prs)
    print("  [5/6] Scoring criteria...")
    slide_scoring(prs)
    print("  [6/6] Features & demo...")
    slide_demo(prs)

    out_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "DeepShield_Presentation.pptx")
    prs.save(out_path)

    print(f"\n✅ Saved: {out_path}")
    print("="*55)
