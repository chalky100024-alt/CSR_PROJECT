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


# --- 4. Pi Zero & PiSugar Mounts (Standoffs) ---
print("3. Creating Mounting Standoffs for Pi Zero...")
# Pi Zero Dimensions: 65mm x 30mm
# Mounting Holes: 58mm x 23mm (M2.5 screws)
# Center the Pi in the middle of the case
pi_w, pi_h = 65.0, 30.0
hole_dist_x = 58.0
hole_dist_y = 23.0

# Center of case
cx = outer_width / 2
cy = outer_length / 2

# Standoff positions (4 corners)
standoff_positions = [
    [cx - hole_dist_x/2, cy - hole_dist_y/2],
    [cx + hole_dist_x/2, cy - hole_dist_y/2],
    [cx - hole_dist_x/2, cy + hole_dist_y/2],
    [cx + hole_dist_x/2, cy + hole_dist_y/2],
]

standoff_height = 8.0 # Raise Pi 8mm to fit Battery underneath?
# If battery is 5000mAh, it might be thick (10mm). 
# Let's make standoffs 10mm tall to be safe.
standoff_height = 10.0 
standoff_radius = 2.5 # 5mm diameter pillar
screw_hole_radius = 1.1 # for M2.5 screw (2.2mm dia hole usually fine for tapping)

standoffs = []
for pos in standoff_positions:
    # Cylinder Standoff
    # trimesh creates cylinder centered at (0,0,0) by default? No, it's Z aligned.
    # We need to move it to (pos[0], pos[1], base_thickness + height/2)
    
    # 1. Solid Pillar
    pillar = trimesh.creation.cylinder(radius=standoff_radius, height=standoff_height)
    # Move to correct Z (sitting on floor)
    # Floor is at Z=base_thickness. Pillar center Z is height/2. 
    # So Z = base_thickness + height/2
    z_pos = base_thickness + (standoff_height / 2)
    
    matrix = trimesh.transformations.translation_matrix([pos[0], pos[1], z_pos])
    pillar.apply_transform(matrix)
    
    # 2. Screw Hole (Subtraction)
    hole = trimesh.creation.cylinder(radius=screw_hole_radius, height=standoff_height + 2) # +2 for clearance
    hole.apply_transform(matrix)
    
    # 3. Final Standoff = Pillar - Hole
    final_standoff = pillar.difference(hole)
    standoffs.append(final_standoff)

# Union all standoffs to the case
print("   - Attaching 4 standoffs...")
for s in standoffs:
    back_cover = back_cover.union(s)

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
