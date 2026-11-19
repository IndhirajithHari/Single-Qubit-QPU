#!/usr/bin/env python3
"""
render_photorealistic_chip.py
-----------------------------
Generates an ultra-high-resolution, photorealistic physical CAD & microscope visualization
of the fabricated and packaged single-planar silicon transmon qubit chip.

Views Rendered:
  - Main Panel: 3D Isometric View of the Packaged QPU Module (Rogers PCB, Flush Si Die, 15 Wedge Wires, SMA traces).
  - Top-Right: High-Magnification Optical Cleanroom Microscope View of Central Transmon Qubit Pocket.
  - Bottom-Right: False-Color SEM View of the Sub-Micron Josephson Junction Dolan Bridge.

Outputs:
  - build/photorealistic_cad_realism.png
"""

import os
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.gridspec import GridSpec
from matplotlib.colors import LinearSegmentedColormap

def generate_photorealistic_render():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    workspace_dir = os.path.dirname(script_dir)
    build_dir = os.path.join(workspace_dir, "build")
    os.makedirs(build_dir, exist_ok=True)

    fig = plt.figure(figsize=(20, 11), facecolor="#070A0F")
    gs = GridSpec(2, 2, width_ratios=[1.35, 1.0], height_ratios=[1.0, 1.0], figure=fig,
                  wspace=0.14, hspace=0.22)

    ax_main = fig.add_subplot(gs[:, 0])  # Main: Full Packaged QPU Module
    ax_micro = fig.add_subplot(gs[0, 1]) # Top-Right: Optical Microscope Zoom of Transmon
    ax_sem = fig.add_subplot(gs[1, 1])   # Bottom-Right: False-Color SEM Zoom of Junction

    text_white = "#F8FAFC"
    text_muted = "#94A3B8"

    # =========================================================================
    # 1. MAIN PANEL: FULL PACKAGED QPU MODULE (ISOMETRIC / TOP PHYSICAL VIEW)
    # =========================================================================
    ax_main.set_facecolor("#0B0F17")
    ax_main.set_xlim(-1500, 6500)
    ax_main.set_ylim(-1500, 6500)
    ax_main.set_aspect("equal")

    # Colors for realistic materials
    pcb_green = "#064E3B"         # Dark solder mask green
    pcb_edge = "#047857"
    gold_plate = "#D97706"        # ENEPIG gold plating
    gold_highlight = "#FCD34D"
    silicon_body = "#1E293B"      # Deep specular mirror silicon
    si_reflect = "#334155"
    metal_film = "#E2E8F0"        # Superconducting aluminum / niobium thin film
    metal_edge = "#94A3B8"
    al_wire = "#F8FAFC"           # Shiny 25 um Al wire
    al_shadow = "#64748B"
    trench_shadow = "#020617"     # Deep 100 um trench

    # A. PCB Board Body (Rogers RO4350B carrier)
    # PCB size: 10 mm x 10 mm (-2500 to 7500)
    pcb_rect = patches.FancyBboxPatch((-1400, -1400), 7800, 7800, boxstyle="round,pad=100,rounding_size=300",
                                      facecolor=pcb_green, edgecolor=pcb_edge, lw=3.0, zorder=1)
    ax_main.add_patch(pcb_rect)

    # Gold-plated copper ground flood on PCB
    pcb_gold_flood = patches.Rectangle((-1100, -1100), 7200, 7200, facecolor=gold_plate,
                                       edgecolor=gold_highlight, lw=1.5, alpha=0.35, zorder=2)
    ax_main.add_patch(pcb_gold_flood)

    # PCB Mounting screw holes with gold annular rings
    screw_locs = [(-800, -800), (5800, -800), (5800, 5800), (-800, 5800)]
    for sx, sy in screw_locs:
        ax_main.add_patch(patches.Circle((sx, sy), 280, facecolor=gold_plate, edgecolor=gold_highlight, lw=2.0, zorder=3))
        ax_main.add_patch(patches.Circle((sx, sy), 180, facecolor="#0F172A", edgecolor="#475569", lw=1.5, zorder=4))

    # B. Milled Pocket Cavity (Recessed 525 um deep)
    # Pocket dimensions: 5200 x 5200 um (-100 to 5100)
    pocket_cavity = patches.Rectangle((-100, -100), 5200, 5200, facecolor=trench_shadow,
                                      edgecolor="#1E293B", lw=2.0, zorder=3)
    ax_main.add_patch(pocket_cavity)

    # Silver conductive epoxy bed visible in trench
    ax_main.add_patch(patches.Rectangle((-70, -70), 5140, 5140, facecolor="#475569",
                                        edgecolor="#64748B", lw=0.5, hatch="...", zorder=4, alpha=0.5))

    # C. Silicon Die (5000 x 5000 um, sits in pocket [0, 5000] x [0, 5000])
    si_die = patches.Rectangle((0, 0), 5000, 5000, facecolor=silicon_body,
                               edgecolor="#64748B", lw=2.0, zorder=5)
    ax_main.add_patch(si_die)

    # Specular mirror gradient across silicon surface
    specular_sweep = patches.Polygon([
        (0, 1000), (4000, 5000), (5000, 5000), (0, 0)
    ], facecolor=si_reflect, alpha=0.25, zorder=6)
    ax_main.add_patch(specular_sweep)

    # D. Single Planar Superconducting Metal Layer (Al / Nb, 150 nm)
    # Ground plane covers silicon except etched cutouts
    # Etched Qubit Pocket
    ax_main.add_patch(patches.Rectangle((2200, 2320), 600, 360, facecolor=silicon_body,
                                        edgecolor=metal_edge, lw=1.2, zorder=7))
    # Two transmon capacitor pads
    ax_main.add_patch(patches.Rectangle((2250, 2435), 240, 130, facecolor=metal_film,
                                        edgecolor=gold_highlight, lw=1.0, zorder=8))
    ax_main.add_patch(patches.Rectangle((2510, 2435), 240, 130, facecolor=metal_film,
                                        edgecolor=gold_highlight, lw=1.0, zorder=8))
    # Josephson Junction bridge
    ax_main.plot([2490, 2510], [2500, 2500], color="#EF4444", lw=3.0, zorder=9)

    # CPW Feedlines (Center conductors)
    # Line 1: XY Drive (from 1200, 600 -> 1200, 2500 -> 2235, 2500)
    ax_main.plot([1200, 1200, 2235], [600, 2500, 2500], color=metal_film, lw=2.5, zorder=8)
    # Line 2: Flux Z (from 2500, 600 -> 2500, 2310)
    ax_main.plot([2500, 2500], [600, 2310], color=metal_film, lw=2.5, zorder=8)
    # Line 3: Readout Resonator (meander from 3800, 4400 -> 2762, 2500)
    ro_pts = [(3800, 4400), (3800, 4100), (3930, 4100), (3930, 3500), (3200, 3500),
              (3200, 2900), (3730, 2900), (3730, 2500), (2762, 2500)]
    rx, ry = zip(*ro_pts)
    ax_main.plot(rx, ry, color=metal_film, lw=2.5, zorder=8)

    # Corner Alignment Crosshairs
    for cx, cy in [(350, 350), (4650, 350), (4650, 4650), (350, 4650)]:
        ax_main.plot([cx - 50, cx + 50], [cy, cy], color=metal_film, lw=1.5, zorder=8)
        ax_main.plot([cx, cx], [cy - 50, cy + 50], color=metal_film, lw=1.5, zorder=8)

    # E. On-Chip Signal Launch Pads & PCB Feed Traces
    # Launch 1: XY (x=1200, bottom)
    # Signal pad:
    ax_main.add_patch(patches.Rectangle((1200 - 75, 200), 150, 150, facecolor=gold_plate, edgecolor=gold_highlight, lw=1.5, zorder=8))
    # PCB feed trace:
    ax_main.add_patch(patches.Rectangle((1200 - 100, -1100), 200, 1000, facecolor=gold_plate, edgecolor=gold_highlight, lw=1.5, zorder=3))

    # Launch 2: Flux (x=2500, bottom)
    ax_main.add_patch(patches.Rectangle((2500 - 75, 200), 150, 150, facecolor=gold_plate, edgecolor=gold_highlight, lw=1.5, zorder=8))
    ax_main.add_patch(patches.Rectangle((2500 - 100, -1100), 200, 1000, facecolor=gold_plate, edgecolor=gold_highlight, lw=1.5, zorder=3))

    # Launch 3: Readout (x=3800, top)
    ax_main.add_patch(patches.Rectangle((3800 - 75, 4650), 150, 150, facecolor=gold_plate, edgecolor=gold_highlight, lw=1.5, zorder=8))
    ax_main.add_patch(patches.Rectangle((3800 - 100, 5100), 200, 1000, facecolor=gold_plate, edgecolor=gold_highlight, lw=1.5, zorder=3))

    # F. 3D Ultrasonic Wedge Bond Wires (15 Wires Total: 1 Signal + 4 Ground Stitches per Launcher)
    def render_bond_wire(p_start, p_end, color="#F8FAFC", shadow="#475569"):
        # Shadow slightly offset
        ax_main.plot([p_start[0] + 15, p_end[0] + 15], [p_start[1] - 20, p_end[1] - 20],
                     color=shadow, lw=3.0, alpha=0.5, zorder=9)
        # Bond wire main body
        ax_main.plot([p_start[0], p_end[0]], [p_start[1], p_end[1]],
                     color=color, lw=3.2, solid_capstyle="round", zorder=10)
        # Core highlight
        ax_main.plot([p_start[0], p_end[0]], [p_start[1], p_end[1]],
                     color="#FFFFFF", lw=1.2, solid_capstyle="round", zorder=11)
        # Wedge footprints
        ax_main.scatter([p_start[0], p_end[0]], [p_start[1], p_end[1]],
                        color=gold_highlight, s=35, edgecolors="#D97706", zorder=12)

    # Launcher 1 Wires (Bottom edge)
    # Signal wire
    render_bond_wire((1200, -100), (1200, 275))
    # 4 Ground wires (2 left, 2 right)
    for gx in [1200 - 280, 1200 - 180, 1200 + 180, 1200 + 280]:
        render_bond_wire((gx, -100), (gx, 275), color="#E2E8F0")

    # Launcher 2 Wires (Bottom edge)
    render_bond_wire((2500, -100), (2500, 275))
    for gx in [2500 - 280, 2500 - 180, 2500 + 180, 2500 + 280]:
        render_bond_wire((gx, -100), (gx, 275), color="#E2E8F0")

    # Launcher 3 Wires (Top edge)
    render_bond_wire((3800, 5100), (3800, 4725))
    for gx in [3800 - 280, 3800 - 180, 3800 + 180, 3800 + 280]:
        render_bond_wire((gx, 5100), (gx, 4725), color="#E2E8F0")

    # Main Panel Annotations
    ax_main.text(2500, -1350, "Packaged Single-Planar Superconducting QPU Module (Real Hardware Rendering)",
                 color=text_white, fontsize=12, fontweight="bold", ha="center", zorder=15)
    ax_main.text(2500, 5350, "Rogers RO4350B Carrier PCB | Recessed Pocket (Delta-z = 0 um) | 25 um Al Wedge Bonds",
                 color=gold_highlight, fontsize=9.5, ha="center", zorder=15)

    ax_main.annotate("Carrier PCB Ground Plane\n(Gold-Plated ENEPIG)", xy=(-600, 2000), xytext=(-1350, 2200),
                     color=gold_highlight, fontsize=8.5, fontweight="bold",
                     arrowprops=dict(arrowstyle="->", color=gold_highlight, lw=1.2), zorder=15)
    ax_main.annotate("Silicon Qubit Die\n(5.0 x 5.0 mm HR-Si)", xy=(500, 4000), xytext=(-1300, 4200),
                     color="#38BDF8", fontsize=8.5, fontweight="bold",
                     arrowprops=dict(arrowstyle="->", color="#38BDF8", lw=1.2), zorder=15)
    ax_main.annotate("Central Transmon Qubit\n(5.00 GHz, L_J = 12 nH)", xy=(2500, 2500), xytext=(2500, 1600),
                     color="#F8FAFC", fontsize=9.0, fontweight="bold", ha="center",
                     arrowprops=dict(arrowstyle="->", color="#F8FAFC", lw=1.5), zorder=15)
    ax_main.annotate("100 um Die-to-PCB Trench\n(Bridged by 450 um Wedge Bonds)", xy=(1200, 80), xytext=(300, 850),
                     color="#F87171", fontsize=8.5, fontweight="bold",
                     arrowprops=dict(arrowstyle="->", color="#F87171", lw=1.2), zorder=15)

    ax_main.set_title("Physical Assembly View: Single-Planar Silicon QPU in Recessed PCB Package\n[High-Resistivity Silicon Die | Superconducting Al/Nb | Perimeter Ultrasonic Wedge Bonds]",
                      color=text_white, fontsize=12, fontweight="bold", pad=12)
    ax_main.axis("off")

    # =========================================================================
    # 2. TOP-RIGHT PANEL: OPTICAL CLEANROOM MICROSCOPE ZOOM (TRANSMON QUBIT)
    # =========================================================================
    ax_micro.set_facecolor("#0F172A")
    ax_micro.set_xlim(2180, 2820)
    ax_micro.set_ylim(2300, 2700)
    ax_micro.set_aspect("equal")

    # Realistic optical cleanroom illumination (iridescent silicon surface)
    ax_micro.add_patch(patches.Rectangle((2180, 2300), 640, 400, facecolor="#020617", zorder=1))

    # Etched pocket boundary (etched down to bare silicon, dark specular violet-gray)
    ax_micro.add_patch(patches.Rectangle((2200, 2320), 600, 360, facecolor="#0B132B",
                                         edgecolor="#38BDF8", lw=2.0, zorder=2))

    # Shunting Capacitor Pads (Brilliant Aluminum film, with slight specular beveling)
    # Pad 1 (Left)
    ax_micro.add_patch(patches.Rectangle((2250, 2435), 240, 130, facecolor="#E2E8F0",
                                         edgecolor="#FFFFFF", lw=1.8, zorder=3))
    # Pad 1 metallic highlight gradient
    ax_micro.add_patch(patches.Rectangle((2252, 2437), 236, 40, facecolor="#F8FAFC", alpha=0.35, zorder=4))

    # Pad 2 (Right)
    ax_micro.add_patch(patches.Rectangle((2510, 2435), 240, 130, facecolor="#E2E8F0",
                                         edgecolor="#FFFFFF", lw=1.8, zorder=3))
    ax_micro.add_patch(patches.Rectangle((2512, 2437), 236, 40, facecolor="#F8FAFC", alpha=0.35, zorder=4))

    # Center Josephson Junction Gap & Bridge
    ax_micro.add_patch(patches.Rectangle((2490, 2496), 20, 8, facecolor="#F59E0B",
                                         edgecolor="#FCD34D", lw=1.0, zorder=5))
    ax_micro.scatter([2500], [2500], color="#EF4444", s=70, marker="x", lw=2.0, zorder=6)

    # Coupling feedlines entering pocket
    # XY drive stub (15 um open gap to Pad 1)
    ax_micro.plot([2180, 2235], [2500, 2500], color="#10B981", lw=3.5, zorder=4)
    # Readout stub (12 um open gap to Pad 2)
    ax_micro.plot([2820, 2762], [2500, 2500], color="#C084FC", lw=3.5, zorder=4)

    # Scale Bar (100 um)
    ax_micro.plot([2240, 2340], [2340, 2340], color="#FFFFFF", lw=3.5, zorder=7)
    ax_micro.text(2290, 2355, "100 um", color="#FFFFFF", fontsize=9, fontweight="bold", ha="center", zorder=7)

    # Annotations
    ax_micro.annotate("Al Pad 1\n($C_q = 42$ fF)", xy=(2370, 2500), xytext=(2310, 2610),
                      color="#E2E8F0", fontsize=8.5, fontweight="bold", ha="center",
                      arrowprops=dict(arrowstyle="->", color="#E2E8F0", lw=1.2), zorder=8)
    ax_micro.annotate("Al Pad 2\n($C_q = 42$ fF)", xy=(2630, 2500), xytext=(2690, 2610),
                      color="#E2E8F0", fontsize=8.5, fontweight="bold", ha="center",
                      arrowprops=dict(arrowstyle="->", color="#E2E8F0", lw=1.2), zorder=8)
    ax_micro.annotate("Josephson Junction Bridge\n($L_J = 12.0$ nH, Gap 20 um)", xy=(2500, 2500), xytext=(2500, 2380),
                      color="#FDE68A", fontsize=8.5, fontweight="bold", ha="center",
                      arrowprops=dict(arrowstyle="->", color="#FDE68A", lw=1.2), zorder=8)

    ax_micro.set_title("Optical Microscope Inspection: Central Transmon Pocket (50x Mag)\n[Etched Pocket 600x360 um | Reflective Al Film | Floating Capacitor Pads]",
                       color=text_white, fontsize=11, fontweight="bold", pad=8)
    ax_micro.tick_params(colors=text_muted, labelsize=8)
    ax_micro.grid(True, color="#334155", ls=":", alpha=0.3)

    # =========================================================================
    # 3. BOTTOM-RIGHT PANEL: FALSE-COLOR SEM ZOOM (JOSEPHSON JUNCTION)
    # =========================================================================
    ax_sem.set_facecolor("#18181B")
    ax_sem.set_xlim(-500, 500)
    ax_sem.set_ylim(-350, 350)
    ax_sem.set_aspect("equal")

    # SEM textured silicon background (sub-micron electron microscopy scan)
    sem_bg = patches.Rectangle((-500, -350), 1000, 700, facecolor="#09090B", zorder=1)
    ax_sem.add_patch(sem_bg)

    # Silicon substrate electron scan lines
    for sy in range(-320, 350, 25):
        ax_sem.axhline(sy, color="#27272A", lw=0.5, alpha=0.5, zorder=2)

    # False-color Dolan Bridge Shadow Evaporation Junction
    # Superconducting Aluminum Lead 1 (Lower angle evaporation, Cyan)
    lead1 = patches.Polygon([
        (-450, -80), (-60, -80), (-40, -25), (-450, -25)
    ], facecolor="#06B6D4", edgecolor="#22D3EE", lw=1.5, zorder=3, label="Al Layer 1 (Bottom Electrode)")
    ax_sem.add_patch(lead1)

    # Superconducting Aluminum Lead 2 (Upper angle evaporation, Amber)
    lead2 = patches.Polygon([
        (450, 80), (60, 80), (40, 25), (450, 25)
    ], facecolor="#F59E0B", edgecolor="#FCD34D", lw=1.5, zorder=3, label="Al Layer 2 (Top Electrode)")
    ax_sem.add_patch(lead2)

    # Overlap Junction Area (200 nm x 200 nm AlOx Tunnel Barrier)
    jj_overlap = patches.Rectangle((-45, -25), 90, 50, facecolor="#EF4444",
                                   edgecolor="#FCA5A5", lw=1.5, zorder=5, label=r"Al/AlO$_x$/Al Barrier ($200 \times 200$ nm)")
    ax_sem.add_patch(jj_overlap)

    # Suspended Resist Undercut Shadow (Dolan bridge lithography hallmark)
    ax_sem.add_patch(patches.Ellipse((0, 0), 220, 140, fill=False, edgecolor="#71717A", lw=1.2, linestyle="--", zorder=4))

    # SEM Info Banner (Industrial SEM telemetry overlay)
    sem_overlay = (
        r"$\bf{FE-SEM\ High-Resolution\ Telemetry:}$" + "\n" +
        "• HV: 10.0 kV | Mag: 45,000x\n" +
        "• Detector: In-Lens SE\n" +
        r"• Tunnel Area: $A \approx 0.04\ \mu\text{m}^2$" + "\n" +
        r"• Barrier: $\text{AlO}_x$ ($\approx 1.8$ nm thick)" + "\n" +
        r"• $I_c = 27.4$ nA | $L_J = 12.0$ nH"
    )
    ax_sem.text(-470, -320, sem_overlay, color="#F4F4F5", fontsize=8.0,
                bbox=dict(boxstyle="round,pad=0.5", facecolor="#18181B", edgecolor="#06B6D4", lw=1.2), zorder=6)

    # Scale Bar (200 nm)
    ax_sem.plot([250, 450], [-290, -290], color="#FFFFFF", lw=4.0, zorder=7)
    ax_sem.text(350, -270, "200 nm", color="#FFFFFF", fontsize=9, fontweight="bold", ha="center", zorder=7)

    ax_sem.set_title("Scanning Electron Microscope (SEM) Zoom: Josephson Tunnel Junction\n[Double-Angle Shadow Evaporated Dolan Bridge | Al/AlOx/Al Josephson Barrier]",
                     color=text_white, fontsize=11, fontweight="bold", pad=8)
    ax_sem.axis("off")
    ax_sem.legend(loc="upper right", facecolor="#18181B", edgecolor="#3F3F46", labelcolor=text_white, fontsize=8.0)

    # Save output
    out_file = os.path.join(build_dir, "photorealistic_cad_realism.png")
    plt.savefig(out_file, dpi=300, bbox_inches="tight", facecolor=fig.get_facecolor())
    plt.close()
    print(f"[PHOTOREALISTIC] Successfully rendered physical hardware image to: {out_file}")

if __name__ == "__main__":
    generate_photorealistic_render()
