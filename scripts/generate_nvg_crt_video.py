"""
Generates an authentic 30fps MP4 and animated GIF video of the
Tactical Aerospace HUD in NVG-Green with CRT Scanlines active.
"""
import math
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import imageio
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
OUTPUT_DIR = BASE_DIR / "ui" / "mobile_pwa"
ARTIFACT_DIR = Path(r"C:\Users\aikel\.gemini\antigravity\brain\d7e346aa-2266-4255-a2c5-b348b70c3fd6")

WIDTH = 540
HEIGHT = 960
FPS = 30
DURATION_SEC = 5.0
TOTAL_FRAMES = int(FPS * DURATION_SEC)  # 150 frames

# Color Palette: NVG Military Green
NVG_BG = (3, 8, 4)
NVG_MAIN = (0, 255, 102)
NVG_BRIGHT = (180, 255, 210)
NVG_DIM = (0, 136, 51)
NVG_BORDER = (0, 187, 68)
NVG_CAUTION = (255, 170, 0)
NVG_DANGER = (255, 51, 51)

def get_font(size: int, bold: bool = False):
    try:
        font_name = "consola.ttf" if bold else "cour.ttf"
        return ImageFont.truetype(font_name, size)
    except:
        return ImageFont.load_default()

font_tiny = get_font(12)
font_sm = get_font(14, bold=True)
font_md = get_font(18, bold=True)
font_lg = get_font(28, bold=True)
font_xl = get_font(36, bold=True)

def render_frame(frame_idx: int) -> np.ndarray:
    t = frame_idx / TOTAL_FRAMES
    angle_rad = 2 * math.pi * t

    # Dynamic variables
    price_fluct = math.sin(angle_rad * 3) * 14.5 + math.cos(angle_rad * 5) * 6.2
    current_price = 75894.22 + price_fluct
    pitch_y = math.sin(angle_rad) * 12.0
    pitch_roll = math.sin(angle_rad) * 2.8  # degrees
    reticle_scale = 1.0 + 0.05 * math.sin(angle_rad * 2)
    caution_blink = (frame_idx // 12) % 2 == 0
    scanline_wave_y = int((frame_idx * 7) % HEIGHT)

    # 1. Base Image
    img = Image.new("RGB", (WIDTH, HEIGHT), NVG_BG)
    draw = ImageDraw.Draw(img)

    # Outer border & bezel
    draw.rectangle([10, 10, WIDTH - 10, HEIGHT - 10], outline=NVG_BORDER, width=2)
    draw.rectangle([14, 14, WIDTH - 14, HEIGHT - 14], outline=NVG_DIM, width=1)

    # Header: Top Flight Annunciator
    draw.line([14, 52, WIDTH - 14, 52], fill=NVG_BORDER, width=1)
    draw.text((25, 24), "BTC-HUD // AVIONICS", fill=NVG_MAIN, font=font_sm)
    draw.text((230, 26), "FL-775", fill=NVG_DIM, font=font_tiny)
    
    # Live time calculation
    sec = int(10 + t * 5)
    draw.text((365, 24), f"14:28:{sec:02d}Z", fill=NVG_MAIN, font=font_sm)
    draw.rectangle([448, 22, 515, 42], outline=NVG_BORDER, width=1)
    draw.text((454, 25), "DATALINK", fill=NVG_MAIN, font=font_tiny)

    # Optics Ribbon
    draw.rectangle([14, 53, WIDTH - 14, 84], fill=(2, 16, 6))
    draw.line([14, 84, WIDTH - 14, 84], fill=NVG_BORDER, width=1)
    draw.text((25, 61), "OPTICS: NVG-GRN [ACTIVE]", fill=NVG_MAIN, font=font_tiny)
    draw.rectangle([215, 58, 305, 78], outline=NVG_MAIN, width=1, fill=(0, 40, 15))
    draw.text((222, 61), "CRT: ON", fill=NVG_MAIN, font=font_tiny)
    draw.text((370, 61), "AIRSPACE: LON/NY", fill=NVG_DIM, font=font_tiny)

    # Spot Telemetry Tape
    draw.rectangle([14, 85, WIDTH - 14, 150], fill=(2, 12, 5))
    draw.line([14, 150, WIDTH - 14, 150], fill=NVG_BORDER, width=1)
    draw.text((25, 93), "SPOT ALTITUDE TAPE", fill=NVG_DIM, font=font_tiny)
    draw.text((25, 108), f"${current_price:,.2f}", fill=NVG_BRIGHT, font=font_lg)
    draw.text((245, 118), "M+2.84", fill=NVG_MAIN, font=font_sm)
    draw.text((395, 96), "FEED: 1Hz STREAM", fill=NVG_DIM, font=font_tiny)
    draw.text((385, 116), "RADAR: AIR-GROUND", fill=NVG_MAIN, font=font_tiny)

    # MFD Selector Ribbon
    draw.rectangle([14, 151, WIDTH - 14, 185], fill=(1, 10, 4))
    draw.line([14, 185, WIDTH - 14, 185], fill=NVG_BORDER, width=1)
    draw.rectangle([22, 156, 120, 180], outline=NVG_MAIN, width=2, fill=(0, 45, 15))
    draw.text((30, 160), "[M1:COCKPIT]", fill=NVG_MAIN, font=font_tiny)
    draw.text((130, 160), "[M2:FLIR]", fill=NVG_DIM, font=font_tiny)
    draw.text((215, 160), "[M3:CONE]", fill=NVG_DIM, font=font_tiny)
    draw.text((300, 160), "[M4:GART]", fill=NVG_DIM, font=font_tiny)
    draw.text((385, 160), "[M5:TRAP]", fill=NVG_DIM, font=font_tiny)
    draw.text((465, 160), "[M6:TD9]", fill=NVG_DIM, font=font_tiny)

    # ==========================================
    # Pitch Ladder & Horizon Stage (Center)
    # ==========================================
    center_x = WIDTH // 2
    horizon_cy = 300 + pitch_y

    # Artificial Horizon Lines
    roll_rad = math.radians(pitch_roll)
    dx = math.cos(roll_rad)
    dy = math.sin(roll_rad)

    # +10 Degree rung
    r10_y = horizon_cy - 60
    draw.line([center_x - 70 * dx, r10_y - 70 * dy, center_x - 30 * dx, r10_y - 30 * dy], fill=NVG_DIM, width=1)
    draw.line([center_x + 30 * dx, r10_y + 30 * dy, center_x + 70 * dx, r10_y + 70 * dy], fill=NVG_DIM, width=1)
    draw.text((center_x - 95, r10_y - 6), "+10", fill=NVG_DIM, font=font_tiny)
    draw.text((center_x + 75, r10_y - 6), "+10", fill=NVG_DIM, font=font_tiny)

    # Zero Boresight Horizon Line
    draw.line([center_x - 110 * dx, horizon_cy - 110 * dy, center_x - 35 * dx, horizon_cy - 35 * dy], fill=NVG_MAIN, width=2)
    draw.line([center_x + 35 * dx, horizon_cy + 35 * dy, center_x + 110 * dx, horizon_cy + 110 * dy], fill=NVG_MAIN, width=2)
    # Center aircraft symbol
    draw.line([center_x - 14, horizon_cy, center_x + 14, horizon_cy], fill=NVG_BRIGHT, width=2)
    draw.line([center_x, horizon_cy - 6, center_x, horizon_cy + 6], fill=NVG_BRIGHT, width=2)

    # -10 Degree rung
    r_minus_y = horizon_cy + 60
    draw.line([center_x - 70 * dx, r_minus_y - 70 * dy, center_x - 30 * dx, r_minus_y - 30 * dy], fill=NVG_DIM, width=1)
    draw.line([center_x + 30 * dx, r_minus_y + 30 * dy, center_x + 70 * dx, r_minus_y + 70 * dy], fill=NVG_DIM, width=1)
    draw.text((center_x - 95, r_minus_y - 6), "-10", fill=NVG_DIM, font=font_tiny)
    draw.text((center_x + 75, r_minus_y - 6), "-10", fill=NVG_DIM, font=font_tiny)

    # Left Altitude Tape Numbers
    draw.text((25, 230), "79.0K", fill=NVG_DIM, font=font_tiny)
    draw.text((25, 265), "78.2K", fill=NVG_DIM, font=font_tiny)
    draw.text((25, 300), "75.8K <", fill=NVG_MAIN, font=font_sm)
    draw.text((25, 335), "75.1K", fill=NVG_DIM, font=font_tiny)
    draw.text((25, 370), "74.5K", fill=NVG_DIM, font=font_tiny)

    # Right Airspeed Tape Numbers
    draw.text((470, 230), "M 3.2", fill=NVG_DIM, font=font_tiny)
    draw.text((470, 265), "M 3.0", fill=NVG_DIM, font=font_tiny)
    draw.text((455, 300), "> M 2.8", fill=NVG_MAIN, font=font_sm)
    draw.text((470, 335), "M 2.5", fill=NVG_DIM, font=font_tiny)
    draw.text((470, 370), "M 2.2", fill=NVG_DIM, font=font_tiny)

    # Target Acquisition Reticle (Pulsing Locked Box)
    ret_w = int(220 * reticle_scale)
    ret_h = int(82 * reticle_scale)
    ret_x0 = center_x - ret_w // 2
    ret_y0 = 345 - ret_h // 2
    ret_x1 = center_x + ret_w // 2
    ret_y1 = 345 + ret_h // 2

    draw.rectangle([ret_x0, ret_y0, ret_x1, ret_y1], outline=NVG_MAIN, width=2, fill=(0, 25, 8))
    # Corner lock brackets
    draw.line([ret_x0 - 5, ret_y0, ret_x0 + 10, ret_y0], fill=NVG_BRIGHT, width=3)
    draw.line([ret_x0, ret_y0 - 5, ret_x0, ret_y0 + 10], fill=NVG_BRIGHT, width=3)
    draw.line([ret_x1 + 5, ret_y0, ret_x1 - 10, ret_y0], fill=NVG_BRIGHT, width=3)
    draw.line([ret_x1, ret_y0 - 5, ret_x1, ret_y0 + 10], fill=NVG_BRIGHT, width=3)
    draw.line([ret_x0 - 5, ret_y1, ret_x0 + 10, ret_y1], fill=NVG_BRIGHT, width=3)
    draw.line([ret_x0, ret_y1 + 5, ret_x0, ret_y1 - 10], fill=NVG_BRIGHT, width=3)
    draw.line([ret_x1 + 5, ret_y1, ret_x1 - 10, ret_y1], fill=NVG_BRIGHT, width=3)
    draw.line([ret_x1, ret_y1 + 5, ret_x1, ret_y1 - 10], fill=NVG_BRIGHT, width=3)

    draw.text((ret_x0 + 8, ret_y0 + 6), "TARGET: LIQ MAGNET", fill=NVG_MAIN, font=font_tiny)
    draw.text((ret_x1 - 65, ret_y0 + 6), "[LOCKED]", fill=NVG_BRIGHT, font=font_sm)
    draw.text((ret_x0 + 8, ret_y0 + 26), "$82,450.00", fill=NVG_BRIGHT, font=font_md)
    draw.text((ret_x0 + 8, ret_y0 + 54), "RANGE: +6.3%", fill=NVG_DIM, font=font_tiny)
    draw.text((ret_x1 - 130, ret_y0 + 54), "CONFLUENCE: 72/100", fill=NVG_MAIN, font=font_tiny)

    # Master Caution / Weapons Release Box
    draw.rectangle([25, 410, WIDTH - 25, 500], outline=NVG_CAUTION, width=2, fill=(18, 12, 0))
    if caution_blink:
        draw.polygon([(40, 432), (32, 446), (48, 446)], fill=NVG_DANGER)
        draw.text((55, 428), "▲ MASTER CAUTION // WEAPONS RELEASE", fill=NVG_CAUTION, font=font_sm)
    else:
        draw.text((55, 428), "  MASTER CAUTION // WEAPONS RELEASE", fill=NVG_CAUTION, font=font_sm)
    
    draw.rectangle([WIDTH - 150, 424, WIDTH - 40, 446], outline=NVG_CAUTION, fill=(0, 0, 0))
    draw.text((WIDTH - 142, 428), "0.75% RISK CAP", fill=NVG_MAIN, font=font_tiny)
    
    draw.text((40, 456), "GATE 4 INTERCEPT VETO: Overhead short pool ($82,450) yields RRR 1:2.14", fill=NVG_CAUTION, font=font_tiny)
    draw.text((40, 474), "!! MANDATORY RRR >= 1:3.0 RULE: ENFORCE RESTING DROP BIDS !!", fill=NVG_DANGER, font=font_tiny)

    # Tactical Mission Plan Card
    draw.rectangle([25, 515, WIDTH - 25, 665], outline=NVG_BORDER, width=2, fill=(2, 16, 6))
    draw.line([25, 545, WIDTH - 25, 545], fill=NVG_BORDER, width=1)
    draw.text((40, 524), "TACTICAL MISSION FLIGHT PLAN", fill=NVG_MAIN, font=font_sm)

    plan_rows = [
        ("DROP ZONE LIMIT:", "$75,900 – $76,400", NVG_MAIN),
        ("HARD-DECK (EJECT STOP):", "$75,183.42 (-1.42%)", NVG_DANGER),
        ("PRIMARY TARGET (1:2.5):", "$78,983.37", NVG_MAIN),
        ("SECONDARY TARGET (1:5.0):", "$81,697.62", NVG_MAIN),
        ("PAYLOAD SIZING (0.75% RISK):", "0.6908 BTC ($52,686)", NVG_BRIGHT)
    ]
    y_offset = 555
    for label, val, color in plan_rows:
        draw.text((40, y_offset), label, fill=NVG_DIM, font=font_tiny)
        draw.text((WIDTH - 255, y_offset), val, fill=color, font=font_sm)
        y_offset += 21

    # 4-Pillars Avionics Health Status
    draw.rectangle([25, 680, WIDTH - 25, 835], outline=NVG_BORDER, width=1, fill=(1, 12, 5))
    draw.text((40, 690), "AVIONICS SENSOR CONFLUENCE", fill=NVG_MAIN, font=font_sm)
    
    pillars = [
        ("ORDER FLOW SENSOR:", "20/25 [BULLISH ABSORPTION]", 20),
        ("DERIVATIVES RADAR:", "22/25 [SHORT SQUEEZE FUEL]", 22),
        ("MACRO FLIGHT PROFILE:", "18/25 [ABOVE 200D EMA]", 18),
        ("VOLATILITY COMPRESSION:", "21/25 [SQUEEZE <= 30%]", 21)
    ]
    py = 718
    for label, val, score in pillars:
        draw.text((40, py), label, fill=NVG_DIM, font=font_tiny)
        draw.text((215, py), val, fill=NVG_MAIN, font=font_tiny)
        # Visual progress bar
        bar_w = int((score / 25.0) * 80)
        draw.rectangle([WIDTH - 125, py + 2, WIDTH - 45, py + 10], outline=NVG_DIM, fill=(0, 20, 8))
        draw.rectangle([WIDTH - 125, py + 2, WIDTH - 125 + bar_w, py + 10], fill=NVG_MAIN)
        py += 26

    # Bottom Master Arm Line
    draw.rectangle([10, HEIGHT - 70, WIDTH - 10, HEIGHT - 10], outline=NVG_BORDER, width=2, fill=(0, 20, 6))
    red_blink = (frame_idx // 15) % 2 == 0
    dot_color = NVG_DANGER if red_blink else (100, 0, 0)
    draw.ellipse([30, HEIGHT - 46, 42, HEIGHT - 34], fill=dot_color)
    draw.text((55, HEIGHT - 45), "[MASTER ARM: DUMP MISSION AI TELEMETRY]", fill=NVG_MAIN, font=font_sm)
    draw.text((WIDTH - 90, HEIGHT - 43), "13-SEC", fill=NVG_DIM, font=font_tiny)

    # ==========================================
    # CRT Scanlines & Cathode Ray Tube Effect
    # ==========================================
    frame_arr = np.array(img, dtype=np.float32)

    # 1. Horizontal raster scanlines: darken alternate rows
    scanline_pattern = np.ones((HEIGHT, 1, 1), dtype=np.float32)
    # Every 3rd pixel gets darkened by 45%
    scanline_pattern[::3, :, :] = 0.55
    scanline_pattern[1::3, :, :] = 0.85
    frame_arr *= scanline_pattern

    # 2. Moving cathode electron beam wave
    beam_top = max(0, scanline_wave_y - 35)
    beam_bot = min(HEIGHT, scanline_wave_y + 35)
    if beam_bot > beam_top:
        beam_mult = 1.0 + 0.22 * np.sin(np.linspace(0, np.pi, beam_bot - beam_top)).reshape(-1, 1, 1)
        frame_arr[beam_top:beam_bot, :, :] *= beam_mult

    # 3. Vignette (curved tube edges)
    y_coords, x_coords = np.ogrid[:HEIGHT, :WIDTH]
    norm_x = (x_coords - WIDTH / 2) / (WIDTH / 2)
    norm_y = (y_coords - HEIGHT / 2) / (HEIGHT / 2)
    dist_sq = norm_x**2 + norm_y**2
    vignette = np.clip(1.0 - 0.28 * dist_sq, 0.55, 1.0)[:, :, np.newaxis]
    frame_arr *= vignette

    frame_arr = np.clip(frame_arr, 0, 255).astype(np.uint8)
    return frame_arr

def main():
    print(f"Generating NVG Green CRT Video ({TOTAL_FRAMES} frames @ {FPS} fps)...")
    frames = []
    for i in range(TOTAL_FRAMES):
        frame = render_frame(i)
        frames.append(frame)
        if (i + 1) % 30 == 0:
            print(f"  Rendered {i + 1}/{TOTAL_FRAMES} frames ({int((i + 1) / TOTAL_FRAMES * 100)}%)...")

    # Save MP4 video
    mp4_path = OUTPUT_DIR / "btc_nvg_crt_cockpit.mp4"
    print(f"Encoding MP4 to: {mp4_path}...")
    imageio.mimsave(str(mp4_path), frames, fps=FPS, codec="libx264", quality=8)
    print(f"MP4 successfully generated! Size: {mp4_path.stat().st_size / 1024:.1f} KB")

    # Also copy MP4 to artifact directory
    if ARTIFACT_DIR.exists():
        artifact_mp4 = ARTIFACT_DIR / "btc_nvg_crt_cockpit.mp4"
        artifact_mp4.write_bytes(mp4_path.read_bytes())
        print(f"Persisted to artifact: {artifact_mp4}")

    # Save animated GIF (sub-sampled for light web embedding: every 2nd frame at 15fps)
    gif_path = OUTPUT_DIR / "btc_nvg_crt_cockpit.gif"
    print(f"Encoding animated GIF to: {gif_path}...")
    gif_frames = [Image.fromarray(f).resize((360, 640), Image.Resampling.BILINEAR) for f in frames[::2]]
    gif_frames[0].save(
        str(gif_path),
        save_all=True,
        append_images=gif_frames[1:],
        duration=int(1000 / 15),
        loop=0,
        optimize=True
    )
    print(f"GIF successfully generated! Size: {gif_path.stat().st_size / 1024:.1f} KB")

    if ARTIFACT_DIR.exists():
        artifact_gif = ARTIFACT_DIR / "btc_nvg_crt_cockpit.gif"
        artifact_gif.write_bytes(gif_path.read_bytes())
        print(f"Persisted to artifact: {artifact_gif}")

if __name__ == "__main__":
    main()
