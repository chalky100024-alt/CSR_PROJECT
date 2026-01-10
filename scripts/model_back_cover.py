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
print("3. Creating PiSugar Holder (65x57mm) & Reset Button...")

# Updated Parameters from User
# PiSugar Size: 65mm (Width/X) x 57mm (Height/Y)
batt_w = 65.0
batt_l = 57.0 
# Note: User said "65mm Wide, 57mm High" (Landscape).
# Code variable naming: batt_w (X size), batt_l (Y size).
# Confirming orientation aligns with X-axis (180mm).

batt_tolerance = 0.5 # Snug fit
holder_wall_h = 10.0 # Clear PiSugar height

# 1. Base Wall
holder_inner_w = batt_w + batt_tolerance
holder_inner_l = batt_l + batt_tolerance
holder_thickness = 2.0

holder_box_outer = trimesh.creation.box(bounds=[
    [cx - holder_inner_w/2 - holder_thickness, cy - holder_inner_l/2 - holder_thickness, base_thickness],
    [cx + holder_inner_w/2 + holder_thickness, cy + holder_inner_l/2 + holder_thickness, base_thickness + holder_wall_h]
])

holder_box_inner = trimesh.creation.box(bounds=[
    [cx - holder_inner_w/2, cy - holder_inner_l/2, base_thickness],
    [cx + holder_inner_w/2, cy + holder_inner_l/2, base_thickness + holder_wall_h + 1]
])

holder_frame = holder_box_outer.difference(holder_box_inner)
back_cover = back_cover.union(holder_frame)

# 2. Reset Button (Flexure)
# Location: 15mm from Top, 10mm from Left (relative to PiSugar)
# Top-Left defined as:
# Top = cy + batt_l/2 = cy + 28.5
# Left = cx - batt_w/2 = cx - 32.5

# Button Position
btn_x = (cx - holder_inner_w/2) + 10.0
btn_y = (cy + holder_inner_l/2) - 15.0

print(f"   - Creating Button at X={btn_x:.1f}, Y={btn_y:.1f}")

# Flexure Design:
# A circular pad (radius 4mm) surrounded by a 'C' shaped slot.
# Or a 'U' slot.
# Slot Width: 1.0mm
# Button Diameter: 6.0mm
btn_radius = 4.0
slot_width = 1.0
nub_height = 1.5 # Height of the nub pushing the switch (on inside)

# A. The Slot (Cutout)
# Create a Ring/Arc cutout
# Simpler: Create a Cylinder (Outer) - Cylinder (Inner) -> Tube?
# If we cut a full circle, the button falls out.
# tailored 'C' shape: 270 degrees.
# Trimesh doesn't have easy Arc primitives.
# Workaround: Difference of Cylinders + Union of "Bridge"

slot_outer_r = btn_radius + slot_width
slot_inner_r = btn_radius

# Cut Cylinder
cut_cyl = trimesh.creation.cylinder(radius=slot_outer_r, height=base_thickness + 2.0)
cut_cyl.apply_transform(trimesh.transformations.translation_matrix([btn_x, btn_y, base_thickness/2]))

# Keep Cylinder (The button itself, effectively)
# Actually, we subtract the "Ring" area.
# Ring = OuterCyl - InnerCyl.
ring_tool = trimesh.creation.cylinder(radius=slot_outer_r, height=base_thickness + 2.0)
inner_tool = trimesh.creation.cylinder(radius=slot_inner_r - 0.2, height=base_thickness + 4.0) # 0.2 clearance
ring_cutout = ring_tool.difference(inner_tool)

# Add a "Bridge" to prevent button falling out (The Hinge)
# Bridge width: 3mm approx.
# Position: Towards the "Top" (or direction of least stress).
# Let's put hinge at TOP (+Y relative to button).
hinge = trimesh.creation.box(extents=[4.0, slot_width * 3, base_thickness + 2.0])
hinge.apply_transform(trimesh.transformations.translation_matrix([btn_x, btn_y + btn_radius, base_thickness/2]))

final_cutout = ring_cutout.difference(hinge)
final_cutout.apply_transform(trimesh.transformations.translation_matrix([btn_x, btn_y, base_thickness/2]))

back_cover = back_cover.difference(final_cutout)

# B. The Tactile Nub (Inside)
# Small cylinder on top of the button pad to press the switch.
nub = trimesh.creation.cylinder(radius=1.5, height=nub_height)
# Position: On top of the floor (base_thickness), centered on button
nub.apply_transform(trimesh.transformations.translation_matrix([btn_x, btn_y, base_thickness + (nub_height/2)]))

back_cover = back_cover.union(nub)

# C. Thinning the Hinged Area (Optional)
# Make the button pad slightly thinner from the OUTSIDE to identify it?
# Or thinning the hinge from inside for flexibility?
# PLA is stiff. 2mm hinge is very stiff.
# Let's cut a "Flex Groove" on the Hinge from the bottom (Z=0).
flex_cut = trimesh.creation.box(extents=[4.0, slot_width * 4, 1.0]) # Cut 1mm deep
flex_cut.apply_transform(trimesh.transformations.translation_matrix([btn_x, btn_y + btn_radius, 0.5])) # Z=0.5 center means cut 0 to 1.0
back_cover = back_cover.difference(flex_cut)

print("   - Flexure Button Created.")

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
