import trimesh
import numpy as np

# --- 1. Dimensions (Must match Front Frame) ---
outer_width = 180.0
outer_length = 110.0
wall_thickness = 2.0  # Thickness of the outer walls
base_thickness = 2.0  # Thickness of the bottom floor

# PiSugar 3 Plus (5000mAh) Accommodation
# User: "Z axis stack height is 20mm. Secure 35mm height."
internal_depth = 35.0 
outer_height = internal_depth + base_thickness 

# Battery Dimensions (User Provided)
batt_w = 56.0
batt_l = 68.0
batt_tolerance = 1.0 # Extra gap
holder_wall_h = 4.0 # Height of the battery retention wall

# Magnet Dimensions (Rectangular)
magnet_length = 18.0
magnet_width = 5.0
magnet_height = 1.6

# --- 2. Create Base Box ---
print("1. Creating Back Cover Box...")
# The full solid block
full_box = trimesh.creation.box(bounds=[
    [0, 0, 0], 
    [outer_width, outer_length, outer_height]
])

# The hollow cutout (leaving walls and floor)
hollow_cutout = trimesh.creation.box(bounds=[
    [wall_thickness, wall_thickness, base_thickness],
    [outer_width - wall_thickness, outer_length - wall_thickness, outer_height + 1.0] # +1 to cut through top
])

back_cover = full_box.difference(hollow_cutout)

# --- 3. Magnet Holes (Wall Mounting - Bottom Face) ---
print("2. Cutting Wall-Mount Magnet Holes (Bottom)...")
# User: "Opposite side... reset switch pressing side" -> Bottom Exterior (Z=0).
z_center = magnet_height / 2 

side_thickness_x = 10.0
side_thickness_y = 6.5

magnet_defs = {
    # Front/Back are along X-axis (Top/Bottom strips)
    "front_1": {"center": (outer_width * 1/4, side_thickness_y / 2, z_center), "dims": (magnet_length, magnet_width, magnet_height)},
    "front_2": {"center": (outer_width * 3/4, side_thickness_y / 2, z_center), "dims": (magnet_length, magnet_width, magnet_height)},
    "back_1": {"center": (outer_width * 1/4, outer_length - (side_thickness_y / 2), z_center), "dims": (magnet_length, magnet_width, magnet_height)},
    "back_2": {"center": (outer_width * 3/4, outer_length - (side_thickness_y / 2), z_center), "dims": (magnet_length, magnet_width, magnet_height)},
    # Left/Right are along Y-axis (Side strips)
    "left_1": {"center": (side_thickness_x / 2, outer_length * 1/4, z_center), "dims": (magnet_width, magnet_length, magnet_height)},
    "left_2": {"center": (side_thickness_x / 2, outer_length * 3/4, z_center), "dims": (magnet_width, magnet_length, magnet_height)},
    "right_1": {"center": (outer_width - (side_thickness_x / 2), outer_length * 1/4, z_center), "dims": (magnet_width, magnet_length, magnet_height)},
    "right_2": {"center": (outer_width - (side_thickness_x / 2), outer_length * 3/4, z_center), "dims": (magnet_width, magnet_length, magnet_height)},
}

for name, spec in magnet_defs.items():
    mag_tool = trimesh.creation.box(
        extents=spec["dims"], 
        transform=trimesh.transformations.translation_matrix(spec["center"])
    )
    back_cover = back_cover.difference(mag_tool)


# --- 4. Compartments & Precision Mounting ---
print("3. Creating Dual Compartments & Precision Mounting...")

cx = outer_width / 2
cy = outer_length / 2

# Dimensions
sugar_w = 65.0  # Width (X)
sugar_l = 56.5  # Height (Y)  (User Update: 56.5mm)
batt_w = 68.0   # Width (X)
batt_l = 56.0   # Height (Y)
wall_h = 20.0   # User: "Z stack is 20mm" -> Make walls 20mm high to protect stack
gap = 10.0      # Wire gap

margin_x = 5.0
margin_y = 5.0

# --- A. PiSugar Holder (Left) & Mounting Holes ---
sugar_x_center = wall_thickness + margin_x + (sugar_w / 2)
sugar_y_center = (outer_length - wall_thickness - margin_y) - (sugar_l / 2)

p_inner_w = sugar_w + 1.0 # Tolerance
p_inner_l = sugar_l + 1.0
p_wall = 2.0

# 1. The Box
sugar_box_outer = trimesh.creation.box(bounds=[
    [sugar_x_center - p_inner_w/2 - p_wall, sugar_y_center - p_inner_l/2 - p_wall, base_thickness],
    [sugar_x_center + p_inner_w/2 + p_wall, sugar_y_center + p_inner_l/2 + p_wall, base_thickness + wall_h]
])
sugar_box_inner = trimesh.creation.box(bounds=[
    [sugar_x_center - p_inner_w/2, sugar_y_center - p_inner_l/2, base_thickness],
    [sugar_x_center + p_inner_w/2, sugar_y_center + p_inner_l/2, base_thickness + wall_h + 1]
])
sugar_frame = sugar_box_outer.difference(sugar_box_inner)
back_cover = back_cover.union(sugar_frame)

# 2. Precision Mounting Standoffs (4 Holes)
# User Data: X_dist = 57.5, Y_dist = 48.8
# Centered on sugar_x_center, sugar_y_center
hole_dx = 57.5
hole_dy = 48.8
standoff_h = 5.0 # Height of standoff base
hole_rad = 1.1 # 2.2mm dia

offsets = [
    (-hole_dx/2, -hole_dy/2),
    (hole_dx/2, -hole_dy/2),
    (-hole_dx/2, hole_dy/2),
    (hole_dx/2, hole_dy/2)
]

print("   - Adding Precision Standoffs (57.5 x 48.8)...")
for off in offsets:
    sx = sugar_x_center + off[0]
    sy = sugar_y_center + off[1]
    
    # Standoff Pillar
    pillar = trimesh.creation.cylinder(radius=2.5, height=standoff_h + base_thickness)
    pillar.apply_transform(trimesh.transformations.translation_matrix([sx, sy, (standoff_h + base_thickness)/2]))
    back_cover = back_cover.union(pillar)
    
    # Screw Hole
    shole = trimesh.creation.cylinder(radius=hole_rad, height=standoff_h + base_thickness + 2)
    shole.apply_transform(trimesh.transformations.translation_matrix([sx, sy, (standoff_h + base_thickness)/2]))
    back_cover = back_cover.difference(shole)


# --- B. Battery Holder (Right) ---
batt_start_x = (sugar_x_center + p_inner_w/2 + p_wall) + gap
batt_x_center = batt_start_x + (batt_w / 2)
batt_y_center = sugar_y_center 

b_inner_w = batt_w + 1.0 
b_inner_l = batt_l + 1.0
b_wall = 2.0

batt_box_outer = trimesh.creation.box(bounds=[
    [batt_x_center - b_inner_w/2 - b_wall, batt_y_center - b_inner_l/2 - b_wall, base_thickness],
    [batt_x_center + b_inner_w/2 + b_wall, batt_y_center + b_inner_l/2 + b_wall, base_thickness + wall_h]
])
batt_box_inner = trimesh.creation.box(bounds=[
    [batt_x_center - b_inner_w/2, batt_y_center - b_inner_l/2, base_thickness],
    [batt_x_center + b_inner_w/2, batt_y_center + b_inner_l/2, base_thickness + wall_h + 1]
])
batt_frame = batt_box_outer.difference(batt_box_inner)
back_cover = back_cover.union(batt_frame)


# --- 5. SWAPPED Controls (USB Right, Reset Left) ---
# Previous: USB Left, Reset Right.
# User: "Swap them".

# A. USB-C Port -> RIGHT of PiSugar Area
# Sugar Right Edge X = sugar_x_center + (sugar_w / 2)
sugar_right_edge_x = sugar_x_center + (sugar_w / 2)

# User defined USB area as "8mm to 15mm". 
# Now relative to RIGHT edge? Or just MIRRORED layout?
# Assume Mirrored: 8-15mm from the RIGHT EDGE of the PiSugar PCB.
port_center_offset_from_right = 11.5
port_x = sugar_right_edge_x - port_center_offset_from_right
port_y = outer_length 
port_z = base_thickness + wall_h + 1.0 # 21mm high usually. 

print(f"   - Cutting USB-C Port (Right Side) at X={port_x:.1f}")

usb_tool = trimesh.creation.box(extents=[9.0, 20.0, 6.0]) 
usb_tool.apply_transform(trimesh.transformations.translation_matrix([port_x, outer_length, port_z]))
back_cover = back_cover.difference(usb_tool)


# B. Reset Button -> LEFT of PiSugar Area
# Previous: X = Left Edge + 55 (Right side).
# New: X = Left Edge + 10mm.
sugar_left_edge_x = sugar_x_center - (sugar_w / 2)
btn_x = sugar_left_edge_x + 10.0
# Y Position: 15mm from Top.
sugar_top_edge_y = sugar_y_center + (sugar_l / 2)
btn_y = sugar_top_edge_y - 15.0

print(f"   - Creating Button (Left Side) at X={btn_x:.1f}, Y={btn_y:.1f}")

# Flexure Logic
btn_radius = 4.0
slot_width = 1.0
nub_height = 1.5 

slot_outer_r = btn_radius + slot_width
slot_inner_r = btn_radius

# Button location is on the FLOOR (Z=0).
# Flexure cuts through Base.
cut_cyl = trimesh.creation.cylinder(radius=slot_outer_r, height=base_thickness + 2.0)
cut_cyl.apply_transform(trimesh.transformations.translation_matrix([btn_x, btn_y, base_thickness/2]))

ring_tool = trimesh.creation.cylinder(radius=slot_outer_r, height=base_thickness + 2.0)
inner_tool = trimesh.creation.cylinder(radius=slot_inner_r - 0.2, height=base_thickness + 4.0) 
ring_cutout = ring_tool.difference(inner_tool)

hinge = trimesh.creation.box(extents=[4.0, slot_width * 3, base_thickness + 2.0])
hinge.apply_transform(trimesh.transformations.translation_matrix([btn_x, btn_y + btn_radius, base_thickness/2]))

final_cutout = ring_cutout.difference(hinge)
final_cutout.apply_transform(trimesh.transformations.translation_matrix([btn_x, btn_y, base_thickness/2]))

back_cover = back_cover.difference(final_cutout)

nub = trimesh.creation.cylinder(radius=1.5, height=nub_height)
nub.apply_transform(trimesh.transformations.translation_matrix([btn_x, btn_y, base_thickness + (nub_height/2)]))
back_cover = back_cover.union(nub)

flex_cut = trimesh.creation.box(extents=[4.0, slot_width * 4, 1.0])
flex_cut.apply_transform(trimesh.transformations.translation_matrix([btn_x, btn_y + btn_radius, 0.5]))
back_cover = back_cover.difference(flex_cut)


# --- 6. Revive Mating Lip (Top Rim Step) ---
# User: "Front joining part... LCD insertion... revive it."
# We cut a "Step" on the top rim, 2mm wide, 2mm deep (from top).
print("   - Creating Mating Lip/Step on Rim...")
# Cut: Box(Outer) - Box(Outer - 2mm). 
# Assume Step Down on Outer Edge (Outer Lip removed)
lip_outer = trimesh.creation.box(bounds=[
    [0, 0, outer_height - 2.0],
    [outer_width, outer_length, outer_height + 1.0]
])
lip_inner = trimesh.creation.box(bounds=[
    [1.0, 1.0, outer_height - 3.0], # 1mm Step Inside
    [outer_width - 1.0, outer_length - 1.0, outer_height + 2.0]
])
lip_tool = lip_outer.difference(lip_inner)
back_cover = back_cover.difference(lip_tool)


# --- 7. Export ---
file_name = 'back_cover_pisugar_plus.stl'
print(f"4. Exporting to {file_name}...")
back_cover.export(file_name)
print("\n✅ Back Cover Model Generation Complete!")
outer_width = 180.0
outer_length = 110.0
wall_thickness = 2.0  # Thickness of the outer walls
base_thickness = 2.0  # Thickness of the bottom floor

# PiSugar 3 Plus (5000mAh) Accommodation
# Battery accounts for significant depth. 
# PiZero (5mm) + PiSugar PCB (5mm) + Battery (10mm approx) + Clearance
# Let's set internal depth to 20mm to be safe for 5000mAh.
# PiSugar 3 Plus (5000mAh) Accommodation
# User: "Z axis stack height is 20mm. Secure 35mm height."
internal_depth = 35.0 
outer_height = internal_depth + base_thickness 
outer_height = internal_depth + base_thickness

# Battery Dimensions (User Provided)
batt_w = 56.0
batt_l = 68.0
batt_tolerance = 1.0 # Extra gap
holder_wall_h = 4.0 # Height of the battery retention wall

# Magnet Dimensions (Rectangular)
magnet_length = 18.0
magnet_width = 5.0
magnet_height = 1.6
# Magnet z-position in Front Frame was 0.8 (half of 1.6). 
# Since Back Cover meets Front Frame face-to-face, we need holes on the mating surface.
# Mating surface is at Z = outer_height (top of walls).

# --- 2. Create Base Box ---
print("1. Creating Back Cover Box...")
# The full solid block
full_box = trimesh.creation.box(bounds=[
    [0, 0, 0], 
    [outer_width, outer_length, outer_height]
])

# The hollow cutout (leaving walls and floor)
hollow_cutout = trimesh.creation.box(bounds=[
    [wall_thickness, wall_thickness, base_thickness],
    [outer_width - wall_thickness, outer_length - wall_thickness, outer_height + 1.0] # +1 to cut through top
])

back_cover = full_box.difference(hollow_cutout)

# --- 3. Magnet Holes (Mirrored from Front Frame) ---
print("2. Cutting Magnet Holes on Rim...")
# Front Frame Logic:
# side_thickness_x = (180 - 160)/2 = 10
# side_thickness_y = (110 - 97)/2 = 6.5
side_thickness_x = 10.0
side_thickness_y = 6.5

# Magnet definitions (Positions relative to Frame Origin (0,0))
# The Back Cover aligns with Frame. 
# Holes should be cut into the TOP RIM (z=outer_height) downwards.
# Magnet definitions (Positions relative to Frame Origin (0,0))
# User: "8 wall-fixing magnet grooves... opposite side... reset switch pressing side"
# Interpretation: Magnets go on the BOTTOM EXTERIOR (Z=0) to stick to a Wall.
magnet_depth = magnet_height # 1.6mm deep hole
z_top = magnet_height # Used for cutting FROM bottom (Z=0) UP.
z_center = magnet_height / 2 

magnet_defs = {
    # Front/Back are along X-axis (Top/Bottom strips)
    "front_1": {"center": (outer_width * 1/4, side_thickness_y / 2, z_center), "dims": (magnet_length, magnet_width, magnet_height)},
    "front_2": {"center": (outer_width * 3/4, side_thickness_y / 2, z_center), "dims": (magnet_length, magnet_width, magnet_height)},
    "back_1": {"center": (outer_width * 1/4, outer_length - (side_thickness_y / 2), z_center), "dims": (magnet_length, magnet_width, magnet_height)},
    "back_2": {"center": (outer_width * 3/4, outer_length - (side_thickness_y / 2), z_center), "dims": (magnet_length, magnet_width, magnet_height)},
    # Left/Right are along Y-axis (Side strips)
    "left_1": {"center": (side_thickness_x / 2, outer_length * 1/4, z_center), "dims": (magnet_width, magnet_length, magnet_height)},
    "left_2": {"center": (side_thickness_x / 2, outer_length * 3/4, z_center), "dims": (magnet_width, magnet_length, magnet_height)},
    "right_1": {"center": (outer_width - (side_thickness_x / 2), outer_length * 1/4, z_center), "dims": (magnet_width, magnet_length, magnet_height)},
    "right_2": {"center": (outer_width - (side_thickness_x / 2), outer_length * 3/4, z_center), "dims": (magnet_width, magnet_length, magnet_height)},
}

magnet_defs = {
    # Front/Back are along X-axis (Top/Bottom strips)
    "front_1": {"center": (outer_width * 1/4, side_thickness_y / 2, z_center), "dims": (magnet_length, magnet_width, magnet_height)},
    "front_2": {"center": (outer_width * 3/4, side_thickness_y / 2, z_center), "dims": (magnet_length, magnet_width, magnet_height)},
    "back_1": {"center": (outer_width * 1/4, outer_length - (side_thickness_y / 2), z_center), "dims": (magnet_length, magnet_width, magnet_height)},
    "back_2": {"center": (outer_width * 3/4, outer_length - (side_thickness_y / 2), z_center), "dims": (magnet_length, magnet_width, magnet_height)},
    # Left/Right are along Y-axis (Side strips)
    "left_1": {"center": (side_thickness_x / 2, outer_length * 1/4, z_center), "dims": (magnet_width, magnet_length, magnet_height)},
    "left_2": {"center": (side_thickness_x / 2, outer_length * 3/4, z_center), "dims": (magnet_width, magnet_length, magnet_height)},
    "right_1": {"center": (outer_width - (side_thickness_x / 2), outer_length * 1/4, z_center), "dims": (magnet_width, magnet_length, magnet_height)},
    "right_2": {"center": (outer_width - (side_thickness_x / 2), outer_length * 3/4, z_center), "dims": (magnet_width, magnet_length, magnet_height)},
}

for name, spec in magnet_defs.items():
    # Create the subtraction volume
    mag_tool = trimesh.creation.box(
        extents=spec["dims"], 
        transform=trimesh.transformations.translation_matrix(spec["center"])
    )
    back_cover = back_cover.difference(mag_tool)


# --- 4. Side-by-Side Compartments (PiSugar + Battery) ---
print("3. Creating Dual Compartments (PiSugar Left, Battery Right)...")

# Define Center References (Fixed NameError)
cx = outer_width / 2
cy = outer_length / 2

# Dims
sugar_w = 65.0  # Width (X)
sugar_l = 57.0  # Height (Y)
batt_w = 68.0   # Width (X)
batt_l = 56.0   # Height (Y)
wall_h = 10.0
gap = 10.0      # Wire gap between them

# Layout Strategy:
# 1. PiSugar: Top-Left aligned.
#    - Left Edge = wall_thickness + 2mm margin
#    - Top Edge = outer_length - wall_thickness - 2mm margin
# 2. Battery: Top-Right aligned (relative to PiSugar)
#    - Left Edge = PiSugar Right + gap

margin_x = 5.0 # Margin from Case Left Wall
margin_y = 5.0 # Margin from Case Top Wall

# --- A. PiSugar Holder (Left) ---
sugar_x_center = wall_thickness + margin_x + (sugar_w / 2)
sugar_y_center = (outer_length - wall_thickness - margin_y) - (sugar_l / 2)

p_inner_w = sugar_w + 0.5
p_inner_l = sugar_l + 0.5
p_wall = 2.0

sugar_box_outer = trimesh.creation.box(bounds=[
    [sugar_x_center - p_inner_w/2 - p_wall, sugar_y_center - p_inner_l/2 - p_wall, base_thickness],
    [sugar_x_center + p_inner_w/2 + p_wall, sugar_y_center + p_inner_l/2 + p_wall, base_thickness + wall_h]
])
sugar_box_inner = trimesh.creation.box(bounds=[
    [sugar_x_center - p_inner_w/2, sugar_y_center - p_inner_l/2, base_thickness],
    [sugar_x_center + p_inner_w/2, sugar_y_center + p_inner_l/2, base_thickness + wall_h + 1]
])
sugar_frame = sugar_box_outer.difference(sugar_box_inner)
back_cover = back_cover.union(sugar_frame)

# --- B. Battery Holder (Right) ---
# Start X = PiSugar Right Wall + Gap
batt_start_x = (sugar_x_center + p_inner_w/2 + p_wall) + gap
batt_x_center = batt_start_x + (batt_w / 2)
batt_y_center = sugar_y_center # Align centers vertically (Top alignment similar)

b_inner_w = batt_w + 1.0 # Loose fit
b_inner_l = batt_l + 1.0
b_wall = 2.0

batt_box_outer = trimesh.creation.box(bounds=[
    [batt_x_center - b_inner_w/2 - b_wall, batt_y_center - b_inner_l/2 - b_wall, base_thickness],
    [batt_x_center + b_inner_w/2 + b_wall, batt_y_center + b_inner_l/2 + b_wall, base_thickness + wall_h]
])
batt_box_inner = trimesh.creation.box(bounds=[
    [batt_x_center - b_inner_w/2, batt_y_center - b_inner_l/2, base_thickness],
    [batt_x_center + b_inner_w/2, batt_y_center + b_inner_l/2, base_thickness + wall_h + 1]
])
batt_frame = batt_box_outer.difference(batt_box_inner)
back_cover = back_cover.union(batt_frame)


# --- 5. USB-C Charging Port (Top Left) ---
# Location: 8mm ~ 15mm from Left of PiSugar PCB.
# PiSugar Left Edge = sugar_x_center - (sugar_w / 2)
sugar_left_edge_x = sugar_x_center - (sugar_w / 2)

port_start = 8.0
port_end = 15.0
port_w = (port_end - port_start) + 2.0 # 9mm
port_center_offset = (port_start + port_end) / 2

port_x = sugar_left_edge_x + port_center_offset
port_y = outer_length # On the Case Wall
port_z = base_thickness + wall_h + 1.0 # Rim height

print(f"   - Cutting USB-C Port at X={port_x:.1f}")

usb_tool = trimesh.creation.box(extents=[port_w, 20.0, 6.0]) # Changed port_width to port_w
usb_tool.apply_transform(trimesh.transformations.translation_matrix([port_x, outer_length, port_z]))
back_cover = back_cover.difference(usb_tool)


# --- 6. Reset Button (Right Side of PiSugar) ---
# User: "Reset button is Right side... 15mm from Top, 10mm from Left (of switch?)"
# Correction: "Reset to Right, Charging to Left".
# Let's place the button on the RIGHT side of the PiSugar PCB area.
# X = PiSugar Right Edge - 10mm? 
# Use "10mm from Left" logic mirrored?
# Let's place it at: X = sugar_left_edge_x + 55mm (Near right edge of 65mm PCB)
# Y = sugar_top_edge_y - 15mm.
sugar_top_edge_y = sugar_y_center + (sugar_l / 2)

btn_x = sugar_left_edge_x + 55.0 
btn_y = sugar_top_edge_y - 15.0

print(f"   - Creating Button at X={btn_x:.1f}, Y={btn_y:.1f}")

# Flexure Design Parameters
btn_radius = 4.0
slot_width = 1.0
nub_height = 1.5 

slot_outer_r = btn_radius + slot_width
slot_inner_r = btn_radius

cut_cyl = trimesh.creation.cylinder(radius=slot_outer_r, height=base_thickness + 2.0)
cut_cyl.apply_transform(trimesh.transformations.translation_matrix([btn_x, btn_y, base_thickness/2]))

ring_tool = trimesh.creation.cylinder(radius=slot_outer_r, height=base_thickness + 2.0)
inner_tool = trimesh.creation.cylinder(radius=slot_inner_r - 0.2, height=base_thickness + 4.0) 
ring_cutout = ring_tool.difference(inner_tool)

# Hinge at TOP (towards case wall)
hinge = trimesh.creation.box(extents=[4.0, slot_width * 3, base_thickness + 2.0])
hinge.apply_transform(trimesh.transformations.translation_matrix([btn_x, btn_y + btn_radius, base_thickness/2]))

final_cutout = ring_cutout.difference(hinge)
final_cutout.apply_transform(trimesh.transformations.translation_matrix([btn_x, btn_y, base_thickness/2]))

back_cover = back_cover.difference(final_cutout)

nub = trimesh.creation.cylinder(radius=1.5, height=nub_height)
nub.apply_transform(trimesh.transformations.translation_matrix([btn_x, btn_y, base_thickness + (nub_height/2)]))
back_cover = back_cover.union(nub)

flex_cut = trimesh.creation.box(extents=[4.0, slot_width * 4, 1.0])
flex_cut.apply_transform(trimesh.transformations.translation_matrix([btn_x, btn_y + btn_radius, 0.5]))
back_cover = back_cover.difference(flex_cut)

print("   - Flexure Button Created (Right Side).")


# --- 7. USB Port Cutout (Optional/Estimating) ---
# Pi Zero USB ports are on the bottom edge (when landscape).
# Assuming Pi is centered. 
# We need a slot on the "Bottom" wall (Y=0 side? No, depends on orientation)
# Let's assume user will route cable or use 90 deg adapter. 
# For now, just a plain box is safer, user can drill hole or print 90% fill.
# (Skipping dynamic port cutout to avoid misalignment - drilling is easier)


# --- 6. Export ---
file_name = 'back_cover_pisugar_plus.stl'
print(f"4. Exporting to {file_name}...")
back_cover.export(file_name)
print("\n✅ Back Cover Model Generation Complete!")
