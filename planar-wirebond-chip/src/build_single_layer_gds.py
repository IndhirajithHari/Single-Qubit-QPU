#!/usr/bin/env python3
"""
build_single_layer_gds.py
-------------------------
Author: Indhirajith
License: Open Source
Agent 2: [GDS_Layout_Engineer]

Generates the single-planar-layer lithography layout strictly on GDS Layer (1, 0)
for a 5.0 mm x 5.0 mm Silicon transmon qubit die with perimeter GSG wire-bonding
launchers, crossover-free CPW routing, capacitive coupling gaps, and alignment fiducials.
"""

import os
import json
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.gridspec import GridSpec
import gdstk

def build_single_layer_chip():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    workspace_dir = os.path.dirname(script_dir)
    specs_path = os.path.join(workspace_dir, "specs", "architecture.json")
    build_dir = os.path.join(workspace_dir, "build")
    os.makedirs(build_dir, exist_ok=True)

    with open(specs_path, "r") as f:
        specs = json.load(f)

    die_w = specs["substrate"]["die_dimensions_um"]["width_x"]
    die_h = specs["substrate"]["die_dimensions_um"]["length_y"]
    gds_layer = specs["metallization"]["gds_layer"]
    gds_datatype = specs["metallization"]["gds_datatype"]

    lib = gdstk.Library(name="PlanarQubitChipLib")
    cell = lib.new_cell("PLANAR_QUBIT_CHIP_L1")

    # -------------------------------------------------------------
    # 1. Geometry Definitions & Cutout Collections
    # -------------------------------------------------------------
    # We maintain two lists:
    #   - etch_clearance_polygons: subtracted from the continuous ground plane
    #   - active_metal_polygons: added directly on Layer (1, 0)
    etch_clearances = []
    active_metals = []

    # -------------------------------------------------------------
    # A. Central Transmon Qubit Pocket & Capacitor Pads
    # -------------------------------------------------------------
    pock_spec = specs["central_transmon_qubit"]["pocket"]
    pock_w = pock_spec["width_x_um"]
    pock_h = pock_spec["height_y_um"]
    pock_cx = pock_spec["center_x_um"]
    pock_cy = pock_spec["center_y_um"]

    pock_xmin = pock_cx - pock_w / 2.0
    pock_xmax = pock_cx + pock_w / 2.0
    pock_ymin = pock_cy - pock_h / 2.0
    pock_ymax = pock_cy + pock_h / 2.0

    # Etched pocket in ground plane
    pocket_polygon = gdstk.rectangle((pock_xmin, pock_ymin), (pock_xmax, pock_ymax))
    etch_clearances.append(pocket_polygon)

    # Shunting capacitor pads
    pads_spec = specs["central_transmon_qubit"]["shunting_capacitor_pads"]
    pad_w = pads_spec["pad_width_x_um"]
    pad_h = pads_spec["pad_height_y_um"]
    inter_gap = pads_spec["inter_pad_gap_um"]

    # Left Pad (Pad 1)
    pad1_xmax = pock_cx - inter_gap / 2.0
    pad1_xmin = pad1_xmax - pad_w
    pad1_ymin = pock_cy - pad_h / 2.0
    pad1_ymax = pock_cy + pad_h / 2.0
    pad1_poly = gdstk.rectangle((pad1_xmin, pad1_ymin), (pad1_xmax, pad1_ymax), layer=gds_layer, datatype=gds_datatype)
    active_metals.append(pad1_poly)

    # Right Pad (Pad 2)
    pad2_xmin = pock_cx + inter_gap / 2.0
    pad2_xmax = pad2_xmin + pad_w
    pad2_ymin = pock_cy - pad_h / 2.0
    pad2_ymax = pock_cy + pad_h / 2.0
    pad2_poly = gdstk.rectangle((pad2_xmin, pad2_ymin), (pad2_xmax, pad2_ymax), layer=gds_layer, datatype=gds_datatype)
    active_metals.append(pad2_poly)

    # Central Josephson Junction bridge (2 um wide bridge bridging 20 um gap)
    jj_bridge_w = 4.0
    jj_poly = gdstk.rectangle((pad1_xmax, pock_cy - jj_bridge_w / 2.0),
                              (pad2_xmin, pock_cy + jj_bridge_w / 2.0),
                              layer=gds_layer, datatype=gds_datatype)
    active_metals.append(jj_poly)

    # -------------------------------------------------------------
    # B. Perimeter GSG Wire-Bond Launchers
    # -------------------------------------------------------------
    gsg_spec = specs["gsg_wirebond_launchers"]
    pad_sw = gsg_spec["signal_pad_width_um"] # 150 um
    pad_sl = gsg_spec["signal_pad_length_um"] # 150 um
    pad_sg = gsg_spec["lateral_ground_gap_um"] # 90 um
    taper_len = gsg_spec["taper_length_um"] # 250 um
    cpw_w = specs["coplanar_waveguides"]["center_conductor_width_W_um"] # 10 um
    cpw_s = specs["coplanar_waveguides"]["dielectric_gap_S_um"] # 6 um

    # Helper function to generate a GSG launcher
    def create_gsg_launcher(cx, edge_y, orientation="north"):
        """
        orientation:
          'north': launcher at bottom edge (y=200), pointing +y into chip
          'south': launcher at top edge (y=4800), pointing -y into chip
        """
        if orientation == "north":
            # Signal landing pad box
            sig_box = gdstk.rectangle((cx - pad_sw / 2.0, edge_y),
                                      (cx + pad_sw / 2.0, edge_y + pad_sl),
                                      layer=gds_layer, datatype=gds_datatype)
            # Etched slot clearance around landing pad
            slot_clearance = gdstk.rectangle((cx - pad_sw / 2.0 - pad_sg, edge_y - 50.0),
                                             (cx + pad_sw / 2.0 + pad_sg, edge_y + pad_sl),
                                             layer=gds_layer, datatype=gds_datatype)
            # Taper
            y_start = edge_y + pad_sl
            y_end = y_start + taper_len
            # Center signal taper polygon
            sig_taper = gdstk.Polygon([
                (cx - pad_sw / 2.0, y_start),
                (cx + pad_sw / 2.0, y_start),
                (cx + cpw_w / 2.0, y_end),
                (cx - cpw_w / 2.0, y_end)
            ], layer=gds_layer, datatype=gds_datatype)
            # Etched slot taper clearance
            slot_taper = gdstk.Polygon([
                (cx - pad_sw / 2.0 - pad_sg, y_start),
                (cx + pad_sw / 2.0 + pad_sg, y_start),
                (cx + cpw_w / 2.0 + cpw_s, y_end),
                (cx - cpw_w / 2.0 - cpw_s, y_end)
            ], layer=gds_layer, datatype=gds_datatype)

            return sig_box, slot_clearance, sig_taper, slot_taper, (cx, y_end)

        else: # 'south'
            sig_box = gdstk.rectangle((cx - pad_sw / 2.0, edge_y - pad_sl),
                                      (cx + pad_sw / 2.0, edge_y),
                                      layer=gds_layer, datatype=gds_datatype)
            slot_clearance = gdstk.rectangle((cx - pad_sw / 2.0 - pad_sg, edge_y - pad_sl),
                                             (cx + pad_sw / 2.0 + pad_sg, edge_y + 50.0),
                                             layer=gds_layer, datatype=gds_datatype)
            y_start = edge_y - pad_sl
            y_end = y_start - taper_len
            sig_taper = gdstk.Polygon([
                (cx - pad_sw / 2.0, y_start),
                (cx + pad_sw / 2.0, y_start),
                (cx + cpw_w / 2.0, y_end),
                (cx - cpw_w / 2.0, y_end)
            ], layer=gds_layer, datatype=gds_datatype)
            slot_taper = gdstk.Polygon([
                (cx - pad_sw / 2.0 - pad_sg, y_start),
                (cx + pad_sw / 2.0 + pad_sg, y_start),
                (cx + cpw_w / 2.0 + cpw_s, y_end),
                (cx - cpw_w / 2.0 - cpw_s, y_end)
            ], layer=gds_layer, datatype=gds_datatype)

            return sig_box, slot_clearance, sig_taper, slot_taper, (cx, y_end)

    # Launcher 1: XY Drive (Bottom-Left: cx=1200, edge_y=200)
    l1_sig, l1_slot, l1_staper, l1_slottaper, l1_end = create_gsg_launcher(1200.0, 200.0, "north")
    active_metals.extend([l1_sig, l1_staper])
    etch_clearances.extend([l1_slot, l1_slottaper])

    # Launcher 2: Flux / Control (Bottom-Center: cx=2500, edge_y=200)
    l2_sig, l2_slot, l2_staper, l2_slottaper, l2_end = create_gsg_launcher(2500.0, 200.0, "north")
    active_metals.extend([l2_sig, l2_staper])
    etch_clearances.extend([l2_slot, l2_slottaper])

    # Launcher 3: Readout Resonator (Top-Right: cx=3800, edge_y=4800)
    l3_sig, l3_slot, l3_staper, l3_slottaper, l3_end = create_gsg_launcher(3800.0, 4800.0, "south")
    active_metals.extend([l3_sig, l3_staper])
    etch_clearances.extend([l3_slot, l3_slottaper])

    # -------------------------------------------------------------
    # C. Crossover-Free Planar CPW Routing
    # -------------------------------------------------------------
    def add_cpw_path(waypoints, line_w=10.0, gap_s=6.0):
        """Creates center conductor and clearance slot polygons from waypoints."""
        # Center conductor
        path_sig = gdstk.FlexPath(waypoints, line_w, layer=gds_layer, datatype=gds_datatype)
        sig_polys = path_sig.to_polygons()
        # Etched clearance slot
        total_w = line_w + 2.0 * gap_s
        path_slot = gdstk.FlexPath(waypoints, total_w, layer=gds_layer, datatype=gds_datatype)
        slot_polys = path_slot.to_polygons()
        return sig_polys, slot_polys

    # --- Line 1: XY Drive CPW ---
    # From l1_end (1200, 600) -> (1200, 2500) -> terminates at (2235, 2500)
    # Pad 1 starts at 2250, so coupling gap = 15 um. Pocket edge at 2200.
    xy_waypoints = [
        l1_end,
        (1200.0, 2500.0),
        (2235.0, 2500.0)
    ]
    xy_sig_polys, xy_slot_polys = add_cpw_path(xy_waypoints, cpw_w, cpw_s)
    active_metals.extend(xy_sig_polys)
    etch_clearances.extend(xy_slot_polys)

    # --- Line 2: Flux / Fast-Z CPW ---
    # From l2_end (2500, 600) -> (2500, 2310)
    # Approaches pocket bottom (y=2320) with capacitive gap / proximity termination at (2500, 2310)
    flux_waypoints = [
        l2_end,
        (2500.0, 2310.0)
    ]
    flux_sig_polys, flux_slot_polys = add_cpw_path(flux_waypoints, cpw_w, cpw_s)
    active_metals.extend(flux_sig_polys)
    etch_clearances.extend(flux_slot_polys)

    # --- Line 3: Readout Resonator (lambda/4 Meander) ---
    # From l3_end (3800, 4400) -> meanders down to (2762, 2500)
    # Pad 2 ends at 2750, so coupling gap = 12 um. Pocket edge at 2800.
    # Total path length tuned to exactly 4260 um.
    readout_waypoints = [
        l3_end,            # (3800, 4400)
        (3800.0, 4100.0),  # dy = 300
        (3930.0, 4100.0),  # dx = 130
        (3930.0, 3500.0),  # dy = 600
        (3200.0, 3500.0),  # dx = 730
        (3200.0, 2900.0),  # dy = 600
        (3730.0, 2900.0),  # dx = 530
        (3730.0, 2500.0),  # dy = 400
        (2762.0, 2500.0)   # dx = 968 (Total = 300+130+600+730+600+530+400+968 = 4258 um ~ 4.26 mm)
    ]
    ro_sig_polys, ro_slot_polys = add_cpw_path(readout_waypoints, cpw_w, cpw_s)
    active_metals.extend(ro_sig_polys)
    etch_clearances.extend(ro_slot_polys)

    # -------------------------------------------------------------
    # D. Lithographic Alignment Crosshairs & Visual Landing Markers
    # -------------------------------------------------------------
    fid_coords = specs["alignment_fiducials"]["corner_coordinates_um"]
    cross_span = specs["alignment_fiducials"]["crosshair_outer_span_um"] # 120 um
    cross_w = specs["alignment_fiducials"]["crosshair_stroke_um"] # 10 um

    for fx, fy in fid_coords:
        # Crosshair on Layer (1, 0)
        ch_h = gdstk.rectangle((fx - cross_span / 2.0, fy - cross_w / 2.0),
                               (fx + cross_span / 2.0, fy + cross_w / 2.0),
                               layer=gds_layer, datatype=gds_datatype)
        ch_v = gdstk.rectangle((fx - cross_w / 2.0, fy - cross_span / 2.0),
                               (fx + cross_w / 2.0, fy + cross_span / 2.0),
                               layer=gds_layer, datatype=gds_datatype)
        # Clear ring around fiducials so they stand out in lithography
        fid_ring = gdstk.rectangle((fx - cross_span / 2.0 - 20, fy - cross_span / 2.0 - 20),
                                   (fx + cross_span / 2.0 + 20, fy + cross_span / 2.0 + 20))
        fid_cross = gdstk.boolean(ch_h, ch_v, "or", layer=gds_layer, datatype=gds_datatype)
        fid_moat = gdstk.boolean(fid_ring, fid_cross, "not")
        etch_clearances.extend(fid_moat)
        active_metals.extend(fid_cross)

    # Bond pad target center markers (fine etch crosshair on signal pad)
    for cx, cy_center in [(1200.0, 275.0), (2500.0, 275.0), (3800.0, 4725.0)]:
        mk_h = gdstk.rectangle((cx - 25.0, cy_center - 2.0), (cx + 25.0, cy_center + 2.0))
        mk_v = gdstk.rectangle((cx - 2.0, cy_center - 25.0), (cx + 2.0, cy_center + 25.0))
        etch_clearances.extend([mk_h, mk_v])

    # Ground-stitching perimeter landing zone indicators (etched demarcation lines on ground plane)
    stitch_flank_w = gsg_spec["ground_flanking_zones"]["pad_width_um"] # 200 um
    stitch_flank_l = gsg_spec["ground_flanking_zones"]["pad_length_um"] # 250 um
    for cx, cy_base, orient in [(1200.0, 200.0, "north"), (2500.0, 200.0, "north"), (3800.0, 4800.0, "south")]:
        y_sign = 1.0 if orient == "north" else -1.0
        # Left flank demarcation outline
        left_fx = cx - pad_sw / 2.0 - pad_sg - stitch_flank_w / 2.0
        # Right flank demarcation outline
        right_fx = cx + pad_sw / 2.0 + pad_sg + stitch_flank_w / 2.0
        for fx in [left_fx, right_fx]:
            box_min = (fx - stitch_flank_w / 2.0, cy_base if orient == "north" else cy_base - stitch_flank_l)
            box_max = (fx + stitch_flank_w / 2.0, cy_base + stitch_flank_l if orient == "north" else cy_base)
            # Etch four corner ticks for ground stitch placement
            tick1 = gdstk.rectangle((box_min[0], box_min[1]), (box_min[0] + 15.0, box_min[1] + 3.0))
            tick2 = gdstk.rectangle((box_max[0] - 15.0, box_min[1]), (box_max[0], box_min[1] + 3.0))
            tick3 = gdstk.rectangle((box_min[0], box_max[1] - 3.0), (box_min[0] + 15.0, box_max[1]))
            tick4 = gdstk.rectangle((box_max[0] - 15.0, box_max[1] - 3.0), (box_max[0], box_max[1]))
            etch_clearances.extend([tick1, tick2, tick3, tick4])

    # -------------------------------------------------------------
    # E. Continuous Ground Plane with Subtractive Etching
    # -------------------------------------------------------------
    ground_rect = gdstk.rectangle((0.0, 0.0), (die_w, die_h), layer=gds_layer, datatype=gds_datatype)

    # Boolean difference: ground_rect NOT etch_clearances
    ground_plane_polys = gdstk.boolean(ground_rect, etch_clearances, "not", layer=gds_layer, datatype=gds_datatype)

    # Add ground plane and all active metal features to cell
    cell.add(*ground_plane_polys)
    cell.add(*active_metals)

    # Write GDS
    gds_filename = os.path.join(build_dir, "planar_chip_layer1.gds")
    lib.write_gds(gds_filename)
    print(f"[AGENT 2] Successfully generated: {gds_filename}")
    print(f"[AGENT 2] Total polygons on Layer (1, 0): {len(cell.polygons)}")

    # -------------------------------------------------------------
    # 2. Publication-Grade Multi-Panel Matplotlib Visualization
    # -------------------------------------------------------------
    render_annotated_layout(specs, xy_waypoints, flux_waypoints, readout_waypoints, build_dir)


def render_annotated_layout(specs, xy_pts, flux_pts, ro_pts, build_dir):
    """Generates build/chip_layout_annotated.png (3-panel publication layout)."""
    fig = plt.figure(figsize=(18, 9), facecolor="#0B1015")
    gs = GridSpec(2, 2, width_ratios=[1.2, 1.0], height_ratios=[1.0, 1.0], figure=fig,
                  wspace=0.18, hspace=0.28)

    ax_full = fig.add_subplot(gs[:, 0])      # Panel A: Full 5 mm x 5 mm die
    ax_launch = fig.add_subplot(gs[0, 1])    # Panel B: Perimeter GSG Zoom
    ax_qubit = fig.add_subplot(gs[1, 1])     # Panel C: Central Transmon Zoom

    # Styling helper
    metal_color = "#38BDF8"       # Bright cyan-blue for superconducting metal
    metal_dark = "#1E293B"        # Dark slate for ground plane fill
    etch_color = "#030712"        # Pure deep black for etched silicon
    accent_gold = "#F59E0B"       # Gold for wirebond targets & JJ
    accent_green = "#10B981"      # Green for CPWs
    text_color = "#F3F4F6"

    # =============================================================
    # PANEL A: FULL DIE VIEW (5 mm x 5 mm)
    # =============================================================
    ax_full.set_facecolor(metal_dark)
    ax_full.set_xlim(-200, 5200)
    ax_full.set_ylim(-200, 5200)
    ax_full.set_aspect("equal")

    # Silicon substrate boundary
    ax_full.add_patch(patches.Rectangle((0, 0), 5000, 5000, facecolor=metal_dark,
                                        edgecolor="#475569", linewidth=2.0, zorder=1))

    # Corner dicing marks / alignment crosshairs
    for cx, cy in [(350, 350), (4650, 350), (4650, 4650), (350, 4650)]:
        ax_full.plot([cx - 60, cx + 60], [cy, cy], color=metal_color, lw=2.0, zorder=5)
        ax_full.plot([cx, cx], [cy - 60, cy + 60], color=metal_color, lw=2.0, zorder=5)

    # Launchers 1, 2, 3 (Signal pads & ground cutouts)
    # Launcher 1 (XY)
    ax_full.add_patch(patches.Rectangle((1200 - 165, 150), 330, 200, facecolor=etch_color, zorder=2))
    ax_full.add_patch(patches.Rectangle((1200 - 75, 200), 150, 150, facecolor=accent_gold, zorder=3))
    # Launcher 2 (Flux)
    ax_full.add_patch(patches.Rectangle((2500 - 165, 150), 330, 200, facecolor=etch_color, zorder=2))
    ax_full.add_patch(patches.Rectangle((2500 - 75, 200), 150, 150, facecolor=accent_gold, zorder=3))
    # Launcher 3 (Readout)
    ax_full.add_patch(patches.Rectangle((3800 - 165, 4650), 330, 200, facecolor=etch_color, zorder=2))
    ax_full.add_patch(patches.Rectangle((3800 - 75, 4650), 150, 150, facecolor=accent_gold, zorder=3))

    # CPW Feedlines (Center conductors)
    xy_x, xy_y = zip(*xy_pts)
    flux_x, flux_y = zip(*flux_pts)
    ro_x, ro_y = zip(*ro_pts)

    ax_full.plot(xy_x, xy_y, color=accent_green, lw=2.0, zorder=4, label=r"XY Drive CPW (50 $\Omega$)")
    ax_full.plot(flux_x, flux_y, color="#EC4899", lw=2.0, zorder=4, label=r"Flux / Z CPW (50 $\Omega$)")
    ax_full.plot(ro_x, ro_y, color="#A855F7", lw=2.5, zorder=4, label=r"Readout Resonator ($\lambda/4$, 7.05 GHz)")

    # Central Qubit Pocket
    ax_full.add_patch(patches.Rectangle((2500 - 300, 2500 - 180), 600, 360,
                                        facecolor=etch_color, edgecolor=metal_color, lw=1.5, zorder=2))
    # Qubit pads
    ax_full.add_patch(patches.Rectangle((2250, 2435), 240, 130, facecolor=metal_color, zorder=3))
    ax_full.add_patch(patches.Rectangle((2510, 2435), 240, 130, facecolor=metal_color, zorder=3))

    # Zoom Callout Boxes
    zoom_b_rect = patches.Rectangle((1200 - 250, 100), 500, 600, fill=False,
                                    edgecolor="#F59E0B", lw=2.0, linestyle="--", zorder=6)
    zoom_c_rect = patches.Rectangle((2150, 2250), 700, 500, fill=False,
                                    edgecolor="#38BDF8", lw=2.0, linestyle="--", zorder=6)
    ax_full.add_patch(zoom_b_rect)
    ax_full.add_patch(zoom_c_rect)

    # Labels and Annotations
    ax_full.text(1200, 420, "GSG Launch 1\n(XY Drive)", color="#F59E0B", fontsize=10,
                 fontweight="bold", ha="center", zorder=7)
    ax_full.text(2500, 420, "GSG Launch 2\n(Flux / Z)", color="#F59E0B", fontsize=10,
                 fontweight="bold", ha="center", zorder=7)
    ax_full.text(3800, 4550, "GSG Launch 3\n(Readout)", color="#F59E0B", fontsize=10,
                 fontweight="bold", ha="center", zorder=7)
    ax_full.text(2500, 2730, "Central Transmon Qubit (Q0)\n[5.00 GHz, L_J=12 nH]",
                 color=metal_color, fontsize=10, fontweight="bold", ha="center", zorder=7)
    ax_full.text(4100, 3300, r"Meandered $\lambda/4$" + "\nCPW Resonator\n(L = 4.26 mm)",
                 color="#C084FC", fontsize=9, ha="center", zorder=7)

    ax_full.set_title("Panel A: Full 5.0 mm x 5.0 mm Single-Planar Silicon Qubit Die\n[Fabrication GDS Layer (1, 0) | No TSVs | No Crossovers]",
                      color=text_color, fontsize=12, fontweight="bold", pad=12)
    ax_full.set_xlabel("X Coordinate ($\\mu$m)", color=text_color, fontsize=10)
    ax_full.set_ylabel("Y Coordinate ($\\mu$m)", color=text_color, fontsize=10)
    ax_full.tick_params(colors=text_color, labelsize=9)
    ax_full.grid(True, color="#334155", ls=":", alpha=0.5)
    ax_full.legend(loc="upper left", facecolor="#1E293B", edgecolor="#475569", labelcolor=text_color, fontsize=9)

    # =============================================================
    # PANEL B: GSG WIRE-BOND LAUNCH PAD ZOOM
    # =============================================================
    ax_launch.set_facecolor(metal_dark)
    ax_launch.set_xlim(950, 1450)
    ax_launch.set_ylim(100, 650)
    ax_launch.set_aspect("equal")

    # Etched dielectric slot (bare silicon)
    ax_launch.add_patch(patches.Rectangle((1200 - 165, 120), 330, 230, facecolor=etch_color, zorder=2))
    # Taper slot
    taper_slot_poly = patches.Polygon([
        (1200 - 165, 350), (1200 + 165, 350),
        (1200 + 11, 600), (1200 - 11, 600)
    ], facecolor=etch_color, zorder=2)
    ax_launch.add_patch(taper_slot_poly)

    # Signal landing pad (150 x 150 um)
    sig_pad_patch = patches.Rectangle((1200 - 75, 200), 150, 150, facecolor=accent_gold,
                                      edgecolor="#FDE68A", lw=1.5, zorder=3)
    ax_launch.add_patch(sig_pad_patch)

    # Signal taper (150 um -> 10 um)
    sig_taper_poly = patches.Polygon([
        (1200 - 75, 350), (1200 + 75, 350),
        (1200 + 5, 600), (1200 - 5, 600)
    ], facecolor=metal_color, edgecolor="#7DD3FC", lw=1.0, zorder=3)
    ax_launch.add_patch(sig_taper_poly)

    # CPW stem entering die
    ax_launch.plot([1200, 1200], [600, 650], color=accent_green, lw=3.0, zorder=4)

    # Target bond landing circle and crosshair
    ax_launch.plot([1200 - 30, 1200 + 30], [275, 275], color="#1E293B", lw=2.0, zorder=5)
    ax_launch.plot([1200, 1200], [275 - 30, 275 + 30], color="#1E293B", lw=2.0, zorder=5)

    # Flanking ground stitching targets (2 wires per flank)
    for g_cx in [1200 - 165 - 60, 1200 + 165 + 60]:
        ax_launch.add_patch(patches.Rectangle((g_cx - 40, 200), 80, 150, fill=False,
                                              edgecolor="#10B981", lw=1.8, linestyle="--", zorder=4))
        # 2 stitch bond landing dots per flank
        ax_launch.scatter([g_cx, g_cx], [240, 310], color="#10B981", s=40, zorder=5)

    # Annotations
    ax_launch.annotate("Signal Bond Pad\n150 $\\mu$m x 150 $\\mu$m", xy=(1200, 275), xytext=(1320, 220),
                       color="#FDE68A", fontsize=9, fontweight="bold",
                       arrowprops=dict(arrowstyle="->", color="#FDE68A", lw=1.5), zorder=6)
    ax_launch.annotate("Ground Gap\nS = 90 $\\mu$m", xy=(1200 - 120, 275), xytext=(980, 310),
                       color="#E2E8F0", fontsize=8,
                       arrowprops=dict(arrowstyle="->", color="#E2E8F0", lw=1.0), zorder=6)
    ax_launch.annotate("50 $\\Omega$ Linear Taper\n(250 $\\mu$m length)", xy=(1200, 480), xytext=(1310, 490),
                       color="#38BDF8", fontsize=9, fontweight="bold",
                       arrowprops=dict(arrowstyle="->", color="#38BDF8", lw=1.2), zorder=6)
    ax_launch.annotate("Ground Stitching Zones\n(2x parallel return wires)", xy=(1200 - 225, 275), xytext=(960, 140),
                       color="#34D399", fontsize=8, fontweight="bold",
                       arrowprops=dict(arrowstyle="->", color="#34D399", lw=1.2), zorder=6)

    ax_launch.set_title("Panel B: Perimeter 50 $\\Omega$ GSG Launch Pad Zoom\n[Impedance-Matched Taper: W/S = 150/90 $\\to$ 10/6]",
                        color=text_color, fontsize=11, fontweight="bold", pad=8)
    ax_launch.set_xlabel("X Coordinate ($\\mu$m)", color=text_color, fontsize=9)
    ax_launch.set_ylabel("Y Coordinate ($\\mu$m)", color=text_color, fontsize=9)
    ax_launch.tick_params(colors=text_color, labelsize=8)
    ax_launch.grid(True, color="#334155", ls=":", alpha=0.5)

    # =============================================================
    # PANEL C: CENTRAL TRANSMON QUBIT ZOOM
    # =============================================================
    ax_qubit.set_facecolor(metal_dark)
    ax_qubit.set_xlim(2150, 2850)
    ax_qubit.set_ylim(2260, 2740)
    ax_qubit.set_aspect("equal")

    # Etched Qubit Pocket
    ax_qubit.add_patch(patches.Rectangle((2200, 2320), 600, 360, facecolor=etch_color,
                                         edgecolor="#64748B", lw=2.0, zorder=2))

    # Capacitor Pads (Metal on Silicon)
    # Pad 1 (Left)
    ax_qubit.add_patch(patches.Rectangle((2250, 2435), 240, 130, facecolor=metal_color,
                                         edgecolor="#7DD3FC", lw=1.5, zorder=3))
    # Pad 2 (Right)
    ax_qubit.add_patch(patches.Rectangle((2510, 2435), 240, 130, facecolor=metal_color,
                                         edgecolor="#7DD3FC", lw=1.5, zorder=3))

    # Josephson Junction Bridge (Center gap = 20 um)
    ax_qubit.add_patch(patches.Rectangle((2490, 2496), 20, 8, facecolor=accent_gold,
                                         edgecolor="#FDE68A", lw=1.0, zorder=4))
    ax_qubit.scatter([2500], [2500], color="#EF4444", s=50, marker="x", zorder=5)

    # Coupling feedline stubs
    # XY Drive stub (terminates at x=2235, gap = 15 um to Pad 1 at x=2250)
    ax_qubit.plot([2150, 2235], [2500, 2500], color=accent_green, lw=3.0, zorder=4)
    # Flux control stub (approaches pocket bottom at y=2320)
    ax_qubit.plot([2500, 2500], [2260, 2310], color="#EC4899", lw=3.0, zorder=4)
    # Readout resonator tip (terminates at x=2762, gap = 12 um to Pad 2 at x=2750)
    ax_qubit.plot([2850, 2762], [2500, 2500], color="#A855F7", lw=3.0, zorder=4)

    # Dimension and Coupling Annotations
    ax_qubit.annotate("Pad 1 ($C_{q}$)\n240 x 130 $\\mu$m", xy=(2370, 2500), xytext=(2280, 2610),
                      color="#E0F2FE", fontsize=9, fontweight="bold", ha="center",
                      arrowprops=dict(arrowstyle="->", color="#E0F2FE", lw=1.2), zorder=6)
    ax_qubit.annotate("Pad 2 ($C_{q}$)\n240 x 130 $\\mu$m", xy=(2630, 2500), xytext=(2720, 2610),
                      color="#E0F2FE", fontsize=9, fontweight="bold", ha="center",
                      arrowprops=dict(arrowstyle="->", color="#E0F2FE", lw=1.2), zorder=6)
    ax_qubit.annotate("Josephson Junction Bridge\n$L_J = 12.0$ nH (Gap 20 $\\mu$m)", xy=(2500, 2500), xytext=(2500, 2370),
                      color="#FDE68A", fontsize=9, fontweight="bold", ha="center",
                      arrowprops=dict(arrowstyle="->", color="#FDE68A", lw=1.5), zorder=6)
    ax_qubit.annotate("XY Coupling Gap\n(15 $\\mu$m open stub)", xy=(2242, 2500), xytext=(2170, 2650),
                      color="#86EFAC", fontsize=8, fontweight="bold",
                      arrowprops=dict(arrowstyle="->", color="#86EFAC", lw=1.2), zorder=6)
    ax_qubit.annotate("Readout Coupling Gap\n(12 $\\mu$m open stub)", xy=(2756, 2500), xytext=(2760, 2370),
                      color="#D8B4FE", fontsize=8, fontweight="bold",
                      arrowprops=dict(arrowstyle="->", color="#D8B4FE", lw=1.2), zorder=6)

    ax_qubit.set_title("Panel C: Central Floating Transmon Qubit Zoom\n[Etched Pocket 600x360 $\\mu$m | Capacitive Coupling Gaps]",
                       color=text_color, fontsize=11, fontweight="bold", pad=8)
    ax_qubit.set_xlabel("X Coordinate ($\\mu$m)", color=text_color, fontsize=9)
    ax_qubit.set_ylabel("Y Coordinate ($\\mu$m)", color=text_color, fontsize=9)
    ax_qubit.tick_params(colors=text_color, labelsize=8)
    ax_qubit.grid(True, color="#334155", ls=":", alpha=0.5)

    img_filename = os.path.join(build_dir, "chip_layout_annotated.png")
    plt.savefig(img_filename, dpi=300, bbox_inches="tight", facecolor=fig.get_facecolor())
    plt.close()
    print(f"[AGENT 2] Successfully rendered layout image: {img_filename}")


if __name__ == "__main__":
    build_single_layer_chip()
