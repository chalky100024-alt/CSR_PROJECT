import trimesh
import numpy as np

# ==========================================
# 1. Configuration & Dimensions
# ==========================================
outer_width = 180.0
outer_length = 110.0
total_depth = 35.0   # Total Thickness (Back to Front)
wall_thickness = 2.0
floor_thickness = 2.0 # Back wall thickness

# Components (PiSugar)
sugar_w = 65.0
sugar_l = 56.5 
batt_w, batt_h = 66.0, 55.0 # Battery
comp_wall_h = 8.0 # Height of internal retention walls
magnet_dims = [18.0, 5.0, 1.6]

# ==========================================
# 2. Main Generation Function
# ==========================================
def create_unibody_frame():
    print("🚀 Creating Single-Piece Unibody Frame...")
    
    # ------------------------------------------
    # A. Base Block (The Container)
    # ------------------------------------------
    # Solid block
    body = trimesh.creation.box(bounds=[[0, 0, 0], [outer_width, outer_length, total_depth]])
    
    # Hollow it out (Creating the "Tub")
    # Leave floor_thickness at Z=0 (Back)
    # Leave wall_thickness on sides
    # Open at Front (Z=total_depth)? No, Front Face exists but has a Window.
    # So we leave Front Wall? 
    # User said "One container... front has screen slot".
    # Effectively, we hollow the INSIDE.
    
    hollow = trimesh.creation.box(bounds=[
        [wall_thickness, wall_thickness, floor_thickness],
        [outer_width - wall_thickness, outer_length - wall_thickness, total_depth - 1.5] # Leave 1.5mm Front Face
    ])
    
    body = body.difference(hollow)
    print("   [Base] Created Hollow Box.")

    # ------------------------------------------
    # B. Front Features (Window & Slot)
    # ------------------------------------------
    print("   [Front] Cutting Window & Rails...")
    
    # 1. Viewing Window (160x97)
    window_w = 160.0
    window_l = 97.0
    wx_min = (outer_width - window_w) / 2
    wy_min = (outer_length - window_l) / 2
    
    window_cutter = trimesh.creation.box(bounds=[
        [wx_min, wy_min, total_depth - 5.0], # Cut through front face
        [outer_width - wx_min, outer_length - wy_min, total_depth + 1.0]
    ])
    body = body.difference(window_cutter)
    
    # 2. Card Slot Cutter (The Slide-in Mechanism)
    # Rail inside the tub walls.
    # Slot Width: 170mm (5mm wider than window on each side -> Rails)
    slot_w = 170.0
    slot_gap_z = 2.0 # Thickness of the slot gap (screen thickness + tolerance)
    
    # Position: Just behind the Front Face
    # Front Face starts at Z = total_depth - 1.5
    # Slot should be at Z = total_depth - 1.5 - slot_gap_z
    slot_z_end = total_depth - 1.5
    slot_z_start = slot_z_end - slot_gap_z
    
    sx_min = (outer_width - slot_w) / 2
    
    # Y-Range:
    # Needs to cut Bottom Rail (start a bit higher than wall?)
    # Wall is at Y=0. Window starts at Y=6.5.
    # Rail Groove should start at Y=wall_thickness + 1.0 (approx 3.0)
    sy_min = wall_thickness + 1.5 
    
    # Top Entry: MUST cut through the Top Wall (Y=outer_length)
    sy_max = outer_length + 5.0 
    
    slot_cutter = trimesh.creation.box(bounds=[
        [sx_min, sy_min, slot_z_start],
        [outer_width - sx_min, sy_max, slot_z_end]
    ])
    
    body = body.difference(slot_cutter)
    print("   [Front] Slide-in Slot Created.")

    # ------------------------------------------
    # C. Back Features (Mounts on Floor)
    # ------------------------------------------
    print("   [Back] Creating Internal Mounts...")
    
    # Internal Coordinate System: Z = floor_thickness (Surface of floor)
    floor_z = floor_thickness
    
    cx = outer_width / 2
    cy = outer_length / 2
    
    # 1. PiSugar Standoffs (Left Side)
    # Shift logic from previous: Pi -35mm, Batt +35mm
    ps_cx = cx - 35.0
    ps_cy = cy
    
    standoff_dist = 58.0 # X-dist
    standoff_h = 5.0
    
    standoffs = []
    # Holes for standoff screws
    for sign in [-1, 1]:
        hx = ps_cx + (sign * standoff_dist / 2)
        hy = ps_cy 
        
        # Post
        post = trimesh.creation.cylinder(radius=2.5, height=standoff_h)
        post.apply_transform(trimesh.transformations.translation_matrix([hx, hy, floor_z + standoff_h/2]))
        
        # Hole
        hole = trimesh.creation.cylinder(radius=1.1, height=standoff_h + 5)
        hole.apply_transform(trimesh.transformations.translation_matrix([hx, hy, floor_z + standoff_h/2]))
        
        standoffs.append(post.difference(hole))
        
    for s in standoffs: body = body.union(s)
    
    # 2. Battery Walls (Right Side)
    batt_cx = cx + 35.0
    batt_cy = cy
    
    bw_th = 1.5
    b_outer = trimesh.creation.box(extents=[batt_w + bw_th*2, batt_h + bw_th*2, comp_wall_h])
    b_outer.apply_transform(trimesh.transformations.translation_matrix([batt_cx, batt_cy, floor_z + comp_wall_h/2]))
    
    b_inner = trimesh.creation.box(extents=[batt_w, batt_h, comp_wall_h + 10])
    b_inner.apply_transform(trimesh.transformations.translation_matrix([batt_cx, batt_cy, floor_z + comp_wall_h/2]))
    
    body = body.union(b_outer.difference(b_inner))
    
    # ------------------------------------------
    # D. Exterior Features (Magnets, Button, USB)
    # ------------------------------------------
    print("   [Ext] Cutting Magnets, USB, Reset...")
    
    # 1. Magnets (Bottom Face)
    # Standard locations
    mag_positions = [
        # Top/Bottom
        [outer_width * 0.25, 3.25], [outer_width * 0.75, 3.25],
        [outer_width * 0.25, outer_length - 3.25], [outer_width * 0.75, outer_length - 3.25],
        # Sides
        [5.0, outer_length * 0.25], [5.0, outer_length * 0.75],
        [outer_width - 5.0, outer_length * 0.25], [outer_width - 5.0, outer_length * 0.75]
    ]
    
    for (mx, my) in mag_positions:
        # Orient
        if my < 10 or my > outer_length - 10:
             dim = [magnet_dims[0], magnet_dims[1], magnet_dims[2]] # Long X
        else:
             dim = [magnet_dims[1], magnet_dims[0], magnet_dims[2]] # Long Y
             
        # Cut slightly into floor (Z=0 to 1.6)
        m_cut = trimesh.creation.box(extents=dim)
        m_cut.apply_transform(trimesh.transformations.translation_matrix([mx, my, dim[2]/2 - 0.1]))
        body = body.difference(m_cut)
        
    # 2. USB Port (Top Wall)
    # Aligned with PiSugar Right Edge
    # PiSugar Right Edge X approx = ps_cx + (sugar_w/2)
    port_x = (ps_cx + sugar_w/2) - 11.5
    port_z_center = floor_z + comp_wall_h + 2.0 # Approx height of USB port on Pi
    
    usb_cut = trimesh.creation.box(extents=[10.0, 10.0, 5.0]) # W, Depth(Cut through wall), H
    usb_cut.apply_transform(trimesh.transformations.translation_matrix([port_x, outer_length, port_z_center]))
    body = body.difference(usb_cut)
    
    # 3. Reset Button (Back Face Flexure)
    # Left of PiSugar
    btn_x = (ps_cx - sugar_w/2) + 10.0
    btn_y = (ps_cy + sugar_l/2) - 15.0 # Approx logic
    
    # Simple Hole (User wanted robust hole, not complex flexure maybe? 
    # But code had flexure. Let's do a simple hole for "RESET" access)
    # User said "reset button magnet groove".
    # I'll cut a hole through the floor.
    btn_hole = trimesh.creation.cylinder(radius=3.0, height=floor_thickness + 2)
    btn_hole.apply_transform(trimesh.transformations.translation_matrix([btn_x, btn_y, floor_thickness/2]))
    body = body.difference(btn_hole)
    
    return body

# ==========================================
# 3. Export
# ==========================================
if __name__ == "__main__":
    final_model = create_unibody_frame()
    final_model.export("unibody_frame.stl")
    print("✅ Created 'unibody_frame.stl'. Single Piece. Slide-in Ready.")
