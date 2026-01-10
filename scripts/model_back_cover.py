import trimesh
import numpy as np

# --- 1. Dimensions (Must match Front Frame) ---
outer_width = 180.0
outer_length = 110.0
wall_thickness = 2.0  # Thickness of the outer walls
base_thickness = 2.0  # Thickness of the bottom floor

# PiSugar 3 Plus (5000mAh) Accommodation
# Battery accounts for significant depth. 
# PiZero (5mm) + PiSugar PCB (5mm) + Battery (10mm approx) + Clearance
# Let's set internal depth to 20mm to be safe for 5000mAh.
internal_depth = 22.0 
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
magnet_depth = magnet_height # 1.6mm deep hole
z_top = outer_height
z_center = z_top - (magnet_height / 2) # Center of the magnet HOLE

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


# --- 4. PiSugar Holder & Flexure Button ---
print("3. Creating PiSugar Holder (Top Usage) & Reset Button...")

# Updated Parameters from User
# PiSugar Size: 65mm (Width/X) x 57mm (Height/Y)
batt_w = 65.0
batt_l = 57.0 
batt_tolerance = 0.5 
holder_wall_h = 10.0 

# 1. Base Wall
holder_inner_w = batt_w + batt_tolerance
holder_inner_l = batt_l + batt_tolerance
holder_thickness = 2.0

# [Position Adjustment]
# User request: "Use USB-C port at Left-Top (8~15mm) as Frame Charging Port"
# To make this accessible, we must MOVE the PiSugar to the Top Edge of the case.
holder_cx = cx
# Top of holder = Top of Case Wall
# cy is center (55). Top is 110. Wall is 2.
# Top Inside = 108.
# Holder Center Y = 108 - (inner_l / 2)
holder_cy = (outer_length - wall_thickness) - (holder_inner_l / 2)

print(f"   - Moving Holder to Top Edge: CY={holder_cy:.1f}")

holder_box_outer = trimesh.creation.box(bounds=[
    [holder_cx - holder_inner_w/2 - holder_thickness, holder_cy - holder_inner_l/2 - holder_thickness, base_thickness],
    [holder_cx + holder_inner_w/2 + holder_thickness, holder_cy + holder_inner_l/2 + holder_thickness, base_thickness + holder_wall_h]
])

holder_box_inner = trimesh.creation.box(bounds=[
    [holder_cx - holder_inner_w/2, holder_cy - holder_inner_l/2, base_thickness],
    [holder_cx + holder_inner_w/2, holder_cy + holder_inner_l/2, base_thickness + holder_wall_h + 1]
])

holder_frame = holder_box_outer.difference(holder_box_inner)
back_cover = back_cover.union(holder_frame)

# 2. Reset Button (Flexure)
# Location: 15mm from Top, 10mm from Left (relative to PiSugar)
# Relative to New Holder Position

# Button Position
btn_x = (holder_cx - holder_inner_w/2) + 10.0
btn_y = (holder_cy + holder_inner_l/2) - 15.0

print(f"   - Creating Button at X={btn_x:.1f}, Y={btn_y:.1f}")

# Flexure Design Parameters
btn_radius = 4.0
slot_width = 1.0
nub_height = 1.5 

# ... (Flexure Logic Same) ...
# Need to replace cx/cy with btn_x/btn_y in logic below (It uses btn_x/btn_y already)

slot_outer_r = btn_radius + slot_width
slot_inner_r = btn_radius

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

# 3. USB-C Charging Port Cutout
# Location: Left-Top Edge. 8mm to 15mm from Left.
# Dims: width=7mm (15-8). Let's make it 9mm for wiggle room.
# Height: USB-C is 3.2mm. Make slot 5mm.
# Depth: Through the Case Top Wall and Holder Top Wall.

# Port Center X (relative to PiSugar Left)
# PiSugar Left = holder_cx - holder_inner_w/2
port_start = 8.0
port_end = 15.0
port_center_offset = (port_start + port_end) / 2
port_width = (port_end - port_start) + 2.0 # +2mm tolerance = 9mm

port_x = (holder_cx - holder_inner_w/2) + port_center_offset
port_y = outer_length # Center of cutout on the WALL (Border)
port_z = base_thickness + holder_wall_h # Top of Holder Wall (PiSugar sits here?)
# Wait, PiSugar (PCB) sits ON TOP of battery?
# If holder walls are 10mm high, and battery is inside...
# The PiSugar PCB rests ON the wall rim? OR inside?
# If it rests on the rim, the USB port is at Z = base + 10mm + PCB_Thickness/2.
# Let's align cutout to Z = base + 10mm + 1.5mm.
port_z_center = base_thickness + holder_wall_h + 1.0

print(f"   - Cutting USB-C Port at X={port_x:.1f}, Z={port_z_center:.1f}")

# Create Cutout Box
# Length(Y) needs to pierce Case Wall (2mm) + Holder Wall (2mm) + Gap
usb_tool = trimesh.creation.box(extents=[port_width, 20.0, 6.0]) # 6mm high slot
usb_tool.apply_transform(trimesh.transformations.translation_matrix([port_x, outer_length, port_z_center]))

back_cover = back_cover.difference(usb_tool)


# --- 5. USB Port Cutout (Optional/Estimating) ---
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
