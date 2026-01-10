import trimesh
import numpy as np

# --- 1. Dimensions (Fixed Specs) ---
outer_width = 180.0
outer_length = 110.0
wall_thickness = 2.0 
base_thickness = 2.0 

# User Requirement: 35mm Internal Depth
internal_depth = 35.0 
outer_height = internal_depth + base_thickness 

# Components Dims
sugar_w = 65.0
sugar_l = 56.5 
batt_w = 68.0
batt_l = 56.0
comp_wall_h = 20.0 # Height of internal walls
gap = 10.0

# --- 2. Create Base Box ---
print("1. Creating Back Cover Box (35mm Depth)...")
full_box = trimesh.creation.box(bounds=[
    [0, 0, 0], 
    [outer_width, outer_length, outer_height]
])
hollow_cutout = trimesh.creation.box(bounds=[
    [wall_thickness, wall_thickness, base_thickness],
    [outer_width - wall_thickness, outer_length - wall_thickness, outer_height + 1.0]
])
back_cover = full_box.difference(hollow_cutout)

# --- 3. Wall Magnets (Bottom Face Z=0) ---
print("2. Cutting Magnet Grooves on Bottom...")
magnet_dims = [18.0, 5.0, 1.6] # L, W, D
z_cut = magnet_dims[2] / 2 # Center of cut (0 to 1.6)

# Standard Magnets positions (Mirrored from Front logic but on Bottom)
# Frame Rim Widths: X=10, Y=6.5
sx = 10.0
sy = 6.5
mag_positions = [
    # Top/Bottom Strips (Front/Back in Y)
    [outer_width * 0.25, sy/2], [outer_width * 0.75, sy/2],
    [outer_width * 0.25, outer_length - sy/2], [outer_width * 0.75, outer_length - sy/2],
    # Left/Right Strips
    [sx/2, outer_length * 0.25], [sx/2, outer_length * 0.75],
    [outer_width - sx/2, outer_length * 0.25], [outer_width - sx/2, outer_length * 0.75]
]

for pos in mag_positions:
    # Determine orientation (Long along strip)
    # If Y is near 0 or Max, it's Top/Bottom strip -> Long X
    is_tb = (pos[1] < 15) or (pos[1] > outer_length - 15)
    dims = [magnet_dims[0], magnet_dims[1], magnet_dims[2]] if is_tb else [magnet_dims[1], magnet_dims[0], magnet_dims[2]]
    
    tool = trimesh.creation.box(extents=dims)
    tool.apply_transform(trimesh.transformations.translation_matrix([pos[0], pos[1], z_cut]))
    back_cover = back_cover.difference(tool)

# --- 4. Internal Compartments ---
print("3. Creating Dual Compartments & Mounting...")
cx = outer_width / 2
cy = outer_length / 2

# Margins
margin_x = 5.0
margin_y = 5.0

# A. PiSugar Holder (Left)
# Left-Top alignment
ps_cx = wall_thickness + margin_x + (sugar_w / 2)
ps_cy = (outer_length - wall_thickness - margin_y) - (sugar_l / 2)

# Create Walls
ps_outer = trimesh.creation.box(extents=[sugar_w + 4, sugar_l + 4, comp_wall_h])
ps_outer.apply_transform(trimesh.transformations.translation_matrix([ps_cx, ps_cy, base_thickness + comp_wall_h/2]))
ps_inner = trimesh.creation.box(extents=[sugar_w + 1, sugar_l + 1, comp_wall_h + 2])
ps_inner.apply_transform(trimesh.transformations.translation_matrix([ps_cx, ps_cy, base_thickness + comp_wall_h/2]))
back_cover = back_cover.union(ps_outer.difference(ps_inner))

# B. Precision Standoffs (PiSugar)
# Spacing: 57.5 (X) x 48.8 (Y)
dx = 57.5
dy = 48.8
standoff_h = 5.0
hole_rad = 1.1 # 2.2mm dia

print(f"   - Standoffs at {dx}x{dy} around ({ps_cx:.1f}, {ps_cy:.1f})")
for sx in [-1, 1]:
    for sy in [-1, 1]:
        hx = ps_cx + sx * (dx/2)
        hy = ps_cy + sy * (dy/2)
        
        # Pillar
        cyl = trimesh.creation.cylinder(radius=2.5, height=standoff_h + base_thickness)
        cyl.apply_transform(trimesh.transformations.translation_matrix([hx, hy, (standoff_h + base_thickness)/2]))
        back_cover = back_cover.union(cyl)
        
        # Hole
        h_tool = trimesh.creation.cylinder(radius=hole_rad, height=standoff_h + base_thickness + 2)
        h_tool.apply_transform(trimesh.transformations.translation_matrix([hx, hy, (standoff_h + base_thickness)/2]))
        back_cover = back_cover.difference(h_tool)

# C. Battery Holder (Right)
# Right of PiSugar + Gap
batt_cx = (ps_cx + sugar_w/2 + 2) + gap + (batt_w/2) + 2
batt_cy = ps_cy 

b_outer = trimesh.creation.box(extents=[batt_w + 4, batt_l + 4, comp_wall_h])
b_outer.apply_transform(trimesh.transformations.translation_matrix([batt_cx, batt_cy, base_thickness + comp_wall_h/2]))
b_inner = trimesh.creation.box(extents=[batt_w + 1, batt_l + 1, comp_wall_h + 2])
b_inner.apply_transform(trimesh.transformations.translation_matrix([batt_cx, batt_cy, base_thickness + comp_wall_h/2]))
back_cover = back_cover.union(b_outer.difference(b_inner))


# --- 5. Controls (SWAPPED) ---
# USB -> Right of PiSugar
# Reset -> Left of PiSugar

# A. USB-C Port (Right Side)
# Target: ~11.5mm from RIGHT EDGE of PiSugar PCB
# PiSugar Right Edge X = ps_cx + (sugar_w / 2)
# Port X = Edge - 11.5
port_x = (ps_cx + sugar_w/2) - 11.5
port_y = outer_length # Top Wall
port_z = base_thickness + comp_wall_h + 1.0 # Rim height (approx 23mm)

print(f"   - USB Port at X={port_x:.1f} (Right side of PiSugar)")
usb_tool = trimesh.creation.box(extents=[9.0, 20.0, 6.0])
usb_tool.apply_transform(trimesh.transformations.translation_matrix([port_x, outer_length, port_z]))
back_cover = back_cover.difference(usb_tool)

# B. Reset Button (Left Side)
# Target: ~10mm from LEFT EDGE of PiSugar PCB
# PiSugar Left Edge X = ps_cx - (sugar_w / 2)
# Btn X = Edge + 10.0
btn_x = (ps_cx - sugar_w/2) + 10.0
# Y Position: 15mm from Top of PCB
# PiSugar Top Edge Y = ps_cy + (sugar_l / 2)
btn_y = (ps_cy + sugar_l/2) - 15.0

print(f"   - Reset Button at X={btn_x:.1f} (Left side of PiSugar)")

# Flexure (Floor Cut)
btn_rad = 4.0
slot = 1.0
nub_h = 1.5

# Ring Cut
ring = trimesh.creation.cylinder(radius=btn_rad + slot, height=base_thickness+2)
ring.apply_transform(trimesh.transformations.translation_matrix([btn_x, btn_y, base_thickness/2]))
inner = trimesh.creation.cylinder(radius=btn_rad, height=base_thickness+2)
inner.apply_transform(trimesh.transformations.translation_matrix([btn_x, btn_y, base_thickness/2]))
cut = ring.difference(inner)

# Hinge (Top side)
hinge = trimesh.creation.box(extents=[6.0, 3.0, base_thickness+2])
hinge.apply_transform(trimesh.transformations.translation_matrix([btn_x, btn_y + btn_rad, base_thickness/2]))
final_cut = cut.difference(hinge)
back_cover = back_cover.difference(final_cut)

# Nub
nub = trimesh.creation.cylinder(radius=1.5, height=nub_h)
nub.apply_transform(trimesh.transformations.translation_matrix([btn_x, btn_y, base_thickness + nub_h/2]))
back_cover = back_cover.union(nub)

# Groove
groove = trimesh.creation.box(extents=[6.0, 2.0, 0.8])
groove.apply_transform(trimesh.transformations.translation_matrix([btn_x, btn_y + btn_rad, 0.4]))
back_cover = back_cover.difference(groove)

# --- 6. Mating Lip (Step) ---
print("4. Creating Mating Lip...")
# Step down on Outer Rim (2mm deep)
lip_box = trimesh.creation.box(bounds=[
    [0, 0, outer_height - 2.0],
    [outer_width, outer_length, outer_height + 1.0]
])
lip_mask = trimesh.creation.box(bounds=[
    [1.0, 1.0, outer_height - 3.0],
    [outer_width - 1.0, outer_length - 1.0, outer_height + 2.0]
])
back_cover = back_cover.difference(lip_box.difference(lip_mask))

# --- 7. Export ---
print("5. Exporting...")
back_cover.export('back_cover_pisugar_plus.stl')
print("✅ DONE.")
