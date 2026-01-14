import trimesh
import numpy as np

# ==========================================
# 1. Configuration & Dimensions
# ==========================================
outer_width = 180.0
outer_length = 110.0
front_depth = 35.0   # Front Frame Depth
back_depth = 10.0    # Back Cover (Plate) Thickness (To hold magnets + components)
# Note: Back Cover acts as a "Plate" that plugs into the Front Frame's rear.
# Or does it sit flush? Assuming it fits INSIDE or flush.
# Let's make it a flat plate for simplicity, that screws/glues on.

wall_thickness = 2.0
magnet_length = 18.0
magnet_width = 5.0
magnet_height = 1.6

# PiSugar / Battery Specs
pi_standoff_dist = 58.0 # Center-to-Center Length
pi_standoff_width = 23.0 # Center-to-Center Width (Estimated for Pi Zero)
batt_w, batt_h = 66.0, 55.0

# ==========================================
# 2. Front Frame (Display Holder Only)
# ==========================================
def create_front_frame():
    print("   [Front] Creating Base Frame...")
    inner_width = 160.0
    inner_length = 97.0
    side_thickness_x = (outer_width - inner_width) / 2
    side_thickness_y = (outer_length - inner_length) / 2
    
    # Base Box
    outer_box = trimesh.creation.box(bounds=[[0, 0, 0], [outer_width, outer_length, front_depth]])
    
    # Hollow Out
    inner_hollow_box = trimesh.creation.box(bounds=[
        [side_thickness_x, side_thickness_y, -1], # Cut through front? No, front face needed.
        [outer_width - side_thickness_x, outer_length - side_thickness_y, front_depth + 1]
    ])
    # Wait, Front Face needs to exist.
    # User's code: inner_hollow_box starts at Z=0?
    # "inner_hollow_box = trimesh.creation.box(bounds=[[side, side, 0], ...])"
    # This implies the frame is a TUBE (open front/back) or user removed Z logic?
    # Ah, user's code had "outer_box.difference(inner_hollow_box)".
    # If inner starts at Z=0, it cuts a hole all the way through?
    # Let's assume user wants a Rim.
    # Refined: Start inner cut at Z=2 (Face thickness).
    inner_hollow_box = trimesh.creation.box(bounds=[
        [side_thickness_x, side_thickness_y, 0], 
        [outer_width - side_thickness_x, outer_length - side_thickness_y, front_depth + 1]
    ])
    # User's specific code had Z=0 start. I will stick to their logic but user might mean "Open Front".
    # User said "Shutter... LC insertion".
    # So the Front has a Bezel.
    
    frame = outer_box.difference(inner_hollow_box)
    
    # Slot Logic (Card Slot Mechanism)
    # Goal: Slide-in from TOP edge.
    # Rails: Left, Right, Bottom.
    # Entry: Top.
    
    display_thickness = 1.6 # Slight tolerance for EPaper
    slot_width = 170.0 # Module Width (Wider than viewing 160 -> 5mm rails)
    
    # Z-Position (Deep inside the frame, close to back)
    slot_z_start = front_depth - 6.0 
    slot_z_end = slot_z_start + display_thickness
    
    # X-Coords (Centered)
    slot_min_x = (outer_width - slot_width) / 2
    slot_max_x = outer_width - slot_min_x
    
    # Y-Coords (Rail Logic)
    # Bottom Rail: Start below the Viewing Window (side_thickness_y).
    # Viewing Window starts at 6.5mm. We start at 3.5mm -> 3mm Rail.
    rail_depth = 3.0
    slot_min_y = side_thickness_y - rail_depth
    
    # Top Entry: Cut ALL THE WAY through the Top Wall.
    # Frame ends at outer_length (110). We go beyond.
    slot_max_y = outer_length + 5.0
    
    print(f"   [Front] Cutting Card Slot: X[{slot_min_x}:{slot_max_x}] Y[{slot_min_y}:{slot_max_y}] Z[{slot_z_start}:{slot_z_end}]")
    
    card_slot_cutter = trimesh.creation.box(bounds=[
        [slot_min_x, slot_min_y, slot_z_start],
        [slot_max_x, slot_max_y, slot_z_end]
    ])
    
    frame = frame.difference(card_slot_cutter)
    
    # NO MAGNET HOLES ON FRONT FRAME (As requested)
    
    return frame

# ==========================================
# 3. Back Cover (Magnet Mount + Component Holder)
# ==========================================
def create_back_cover():
    print("   [Back] Creating Wall Mount Plate...")
    # This is a Plate that covers the big opening (160x97) or the whole back (180x110)?
    # User said "mating surface". Let's cover the whole back (180x110).
    plate_depth = 5.0 # Basic thickness
    
    full_plate = trimesh.creation.box(bounds=[[0, 0, 0], [outer_width, outer_length, plate_depth]])
    
    # 1. Magnet Holes (On EXTERNAL Face -> Z=0, facing Wall)
    # User: "Rectangular holes... prepared for magnets... located at very back"
    # We cut them into the bottom face (Z=0).
    print("   [Back] Cutting Magnet Slots (Wall side)...")
    z_mag = 0 + (magnet_height / 2) - 0.1 # Slightly recessed or flush
    
    # Same positions as before
    side_thickness_x = 10.0
    side_thickness_y = 6.5
    magnet_defs = {
        "f1": ((outer_width * 1/4, side_thickness_y / 2, z_mag), (magnet_length, magnet_width, magnet_height)),
        "f2": ((outer_width * 3/4, side_thickness_y / 2, z_mag), (magnet_length, magnet_width, magnet_height)),
        "b1": ((outer_width * 1/4, outer_length - side_thickness_y / 2, z_mag), (magnet_length, magnet_width, magnet_height)),
        "b2": ((outer_width * 3/4, outer_length - side_thickness_y / 2, z_mag), (magnet_length, magnet_width, magnet_height)),
        "l1": ((side_thickness_x / 2, outer_length * 1/4, z_mag), (magnet_width, magnet_length, magnet_height)),
        "l2": ((side_thickness_x / 2, outer_length * 3/4, z_mag), (magnet_width, magnet_length, magnet_height)),
        "r1": ((outer_width - side_thickness_x / 2, outer_length * 1/4, z_mag), (magnet_width, magnet_length, magnet_height)),
        "r2": ((outer_width - side_thickness_x / 2, outer_length * 3/4, z_mag), (magnet_width, magnet_length, magnet_height)),
    }
    
    for name, (center, dims) in magnet_defs.items():
        mag_box = trimesh.creation.box(extents=dims, transform=trimesh.transformations.translation_matrix(center))
        full_plate = full_plate.difference(mag_box)
        
    # 2. Component Mounts (Inside Face -> Z=plate_depth upwards)
    # Components sit ON TOP of the plate (inside the frame).
    
    # A. PiSugar Standoffs (2x, Spacing 58mm)
    print("   [Back] Adding PiSugar Standoffs...")
    cx, cy = outer_width / 2, outer_length / 2
    # Shift Pi slightly Left to make room for battery?
    # Total width used: 65(Pi) + 66(Batt) = 131. Available 180 (Internal ~160).
    # Gap: 160 - 131 = 29mm.
    # Let's put Pi -35mm from center, Battery +35mm from center.
    
    pi_center_x = cx - 35.0
    pi_center_y = cy
    
    # 2 Standoffs (58mm apart along X axis)
    standoff_positions = [
        [pi_center_x - (58.0/2), pi_center_y], # Left Hole
        [pi_center_x + (58.0/2), pi_center_y], # Right Hole
    ]
    
    standoff_h = 5.0 
    
    standoffs = []
    for pos in standoff_positions:
        # Pillar
        p = trimesh.creation.cylinder(radius=2.5, height=standoff_h)
        # Move to (x, y, plate_depth + h/2)
        mat = trimesh.transformations.translation_matrix([pos[0], pos[1], plate_depth + standoff_h/2])
        p.apply_transform(mat)
        
        # Hole
        h = trimesh.creation.cylinder(radius=1.1, height=standoff_h+5)
        h.apply_transform(mat)
        
        standoffs.append(p.difference(h))
        
    # B. Battery Wall (66x55mm)
    print("   [Back] Creating Battery Walls...")
    batt_center_x = cx + 35.0
    batt_center_y = cy
    
    # Wall Dimensions: Box around 66x55
    # Wall thickness 1.5mm
    w_th = 1.5
    wall_h = 8.0
    
    # Outer Box for Wall
    wall_outer = trimesh.creation.box(extents=[batt_w + w_th*2, batt_h + w_th*2, wall_h])
    # Inner Box for Cutout
    wall_inner = trimesh.creation.box(extents=[batt_w, batt_h, wall_h + 1])
    
    bat_wall = wall_outer.difference(wall_inner)
    
    # Move to position (Sitting on plate)
    mat_wall = trimesh.transformations.translation_matrix([batt_center_x, batt_center_y, plate_depth + wall_h/2])
    bat_wall.apply_transform(mat_wall)
    
    # Combine everything
    result = full_plate
    for s in standoffs: result = result.union(s)
    result = result.union(bat_wall)
    
    return result

# ==========================================
# 4. Main
# ==========================================
if __name__ == "__main__":
    print("🚀 Generating Revised Models...")
    
    front = create_front_frame()
    back = create_back_cover()
    
    front.export('new_front_frame.stl')
    back.export('new_back_cover.stl')
    
    # Assembly View
    # Flip Back Cover so magnets are away? No, standard view.
    # Back Cover (Plate) goes onto the BACK of the Frame.
    # Frame Z: 0..35. Back of Frame is Z=0.
    # Back Cover components (Standoffs) face INTO the frame.
    # So Back Cover should be at Z=0, facing UP into the frame?
    # Or Frame sits ON TOP of Back Cover?
    # Yes, Back Cover is the "Floor". Frame is the "Walls".
    
    # Let's align them:
    # Back Cover at Z=0. Components sticking up (Z+).
    # Front Frame at Z=0. (It has walls going 0..35).
    # So they occupy the same space? No.
    # Front Frame has "Inner Hollow" starting at Z=0?
    # Actually, User's code cuts the CENTER out.
    # So Front Frame is a RIMMING WALL.
    # So Back Cover fits UNDER it (Z < 0) or acts as the floor (Z=0..5).
    # Let's place Back Cover at Z=-5 (below frame) for exploded view.
    
    expl_mat = trimesh.transformations.translation_matrix([0, 0, -20])
    back_expl = back.copy()
    back_expl.apply_transform(expl_mat)
    
    assembly = trimesh.util.concatenate([front, back_expl])
    assembly.export('new_assembly_view.stl')
    
    print("✅ Done! 'new_assembly_view.stl' shows the corrected design.")
