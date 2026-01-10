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


# --- 4. Battery Holder with Integrated Mounting Tabs ---
print("3. Creating Battery Holder with Mounting Tabs...")

# Updated Parameters from User
# - Hole Distance: 58mm (X) x 23mm (Y) (Standard Pi Zero)
# - Hole Diameter: 2.2mm (Tight fit for M2.5)
# - Alignment: Top of Battery Wall (Z-axis)
batt_holder_h = 12.0 # Height to clear 5000mAh battery (approx 10mm + clearance)

# 1. Base Battery Holder Walls
holder_inner_w = batt_w + batt_tolerance
holder_inner_l = batt_l + batt_tolerance
holder_thickness = 2.0

holder_box_outer = trimesh.creation.box(bounds=[
    [cx - holder_inner_w/2 - holder_thickness, cy - holder_inner_l/2 - holder_thickness, base_thickness],
    [cx + holder_inner_w/2 + holder_thickness, cy + holder_inner_l/2 + holder_thickness, base_thickness + batt_holder_h]
])

holder_box_inner = trimesh.creation.box(bounds=[
    [cx - holder_inner_w/2, cy - holder_inner_l/2, base_thickness],
    [cx + holder_inner_w/2, cy + holder_inner_l/2, base_thickness + batt_holder_h + 1] # +1 for cutout
])

# The main frame
holder_frame = holder_box_outer.difference(holder_box_inner)

# 2. Mounting Tabs (Bridge Corners)
# We need to bridge from the Wall (X +/- ~30) to the Hole (X +/- 29, Y +/- 11.5)
# Since the holes are INSIDE the battery box area (X 58 vs 68), we must cantilever inwards.

hole_dist_x = 58.0
hole_dist_y = 23.0
hole_radius = 1.1 # 2.2mm dia

tab_size = 6.0 # Size of the square tab around the hole
tabs = []
holes = []

# Corner positions for holes
hole_positions = [
    [cx - hole_dist_x/2, cy - hole_dist_y/2],
    [cx + hole_dist_x/2, cy - hole_dist_y/2],
    [cx - hole_dist_x/2, cy + hole_dist_y/2],
    [cx + hole_dist_x/2, cy + hole_dist_y/2],
]

# Z-level for tabs: Flush with top of battery wall
z_tab_bottom = base_thickness + batt_holder_h - 2.0 # 2mm thick tab
z_tab_top = base_thickness + batt_holder_h

print(f"   - Mounting Tabs at Z={z_tab_top}mm (Top of Battery Wall)")

for h_pos in hole_positions:
    # A. Create Tab Block (centered on hole)
    # Make it large enough to touch the nearest wall.
    # Nearest wall is at X +/- (batt_w/2) = 28.
    # Hole X is 29. Wait.
    # Battery Length (X) is 68 -> Half is 34.
    # Hole X is 58/2 = 29.
    # So Hole is 5mm INSIDE the X-wall (34 - 29 = 5).
    # Battery Width (Y) is 56 -> Half is 28.
    # Hole Y is 23/2 = 11.5.
    # So Hole is 16.5mm INSIDE the Y-wall.
    
    # We need to connect the tab to the X-wall (closest).
    # Create a block from Hole center to Wall.
    
    # Simple Cube for the Tab surrounding the hole
    tab = trimesh.creation.box(extents=[tab_size, tab_size, 2.0]) # 2mm thick
    # Move to position
    tab.apply_transform(trimesh.transformations.translation_matrix([h_pos[0], h_pos[1], base_thickness + batt_holder_h - 1.0])) # Center Z at top-1mm
    
    # B. Bridge to Wall (Extension)
    # Determine direction to nearest X-wall
    x_dir = 1 if h_pos[0] > cx else -1
    wall_x = cx + x_dir * (holder_inner_w/2)  # Wait, W is 56? L is 68? Script says L=68 (Y) usually? 
    # Let's check dims: "batt_l = 68.0", "batt_w = 56.0".
    # User said "68, 56". Usually Length is longest.
    # In Step 1: outer_length = 110 (Y), outer_width = 180 (X).
    # So X-axis is "Width" (Long dimension of case).
    # Does "Battery L=68" align with Case X (180)? Yes, likely.
    # Does "Battery W=56" align with Case Y (110)? Yes.
    
    # So Battery is 68 (X) x 56 (Y).
    # Hole X = 29. Battery Wall X = 34. Diff = 5mm. Close.
    # Hole Y = 11.5. Battery Wall Y = 28. Diff = 16.5mm. Far.
    
    # So we bridge to the X-walls (Side walls relative to battery main axis).
    # Create bridge block
    bridge_len = (holder_inner_l / 2) - abs(h_pos[0] - cx) + 2 # +2 overlap
    # Actually simpler: Just make the tab hit the wall.
    # Let's just create a Union of the tab box and the frame.
    
    # Just add the tab specific for the hole
    holder_frame = holder_frame.union(tab)
    
    # C. Create Screw Hole Tool
    hole_tool = trimesh.creation.cylinder(radius=hole_radius, height=10.0) # Tall cutter
    # Move to Hole Position
    hole_tool.apply_transform(trimesh.transformations.translation_matrix([h_pos[0], h_pos[1], base_thickness + batt_holder_h]))
    
    back_cover = back_cover.difference(hole_tool)

# Connect tabs to walls (Simple Hull or manually extending)
# Since 'tab' is just a floating box near the wall inside the holder, we need to bridge it.
# Let's assume the Battery Holder WALL itself is thick enough? No, wall is 2mm.
# Gap is 5mm. We need a bridge.
# Better approach: Create a solid block filling the corner, then subtract battery shape? 
# No, battery is rectangular.
# Let's explicitly create bridges.
print("   - Creating Bridges to Walls...")
for h_pos in hole_positions:
    x_sign = 1 if h_pos[0] > cx else -1
    y_sign = 1 if h_pos[1] > cy else -1
    
    # Bridge to Closest Wall (X-face)
    # From HoleX to WallX
    # Dist = 5mm.
    bridge = trimesh.creation.box(extents=[abs((batt_l/2) - (hole_dist_x/2)) + 2, tab_size, 2.0])
    # Position: Midway between hole and wall
    mid_x = (h_pos[0] + (cx + x_sign * batt_l/2)) / 2
    bridge.apply_transform(trimesh.transformations.translation_matrix([mid_x, h_pos[1], base_thickness + batt_holder_h - 1.0]))
    holder_frame = holder_frame.union(bridge)

# Union the complex holder to the back cover
back_cover = back_cover.union(holder_frame)
    
# Re-cut holes to ensure they pierce the new bridge material
for h_pos in hole_positions:
     hole_tool = trimesh.creation.cylinder(radius=hole_radius, height=20.0)
     hole_tool.apply_transform(trimesh.transformations.translation_matrix([h_pos[0], h_pos[1], base_thickness]))
     back_cover = back_cover.difference(hole_tool)
     
# (Pi Standoffs Removed)

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
