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
    
    # 1. ADD INTERNAL RAIL BLOCKS (Critical Fix)
    # The box inner width (176mm) is wider than the slot (170mm).
    # Without these blocks, the slot cuts air and screen falls in.
    # We add 8mm wide blocks on Left/Right walls to narrow the opening to 160mm (Window Width).
    # Then we cut the 170mm Slot INTO these blocks, creating a 5mm "U-Channel".
    
    rail_block_w = 8.0
    rail_block_z = 3.0 # Thickness of the backing rail (how strong it is) -> User said "1.2mm plate"? 
    # Let's make it robust (full depth of slot + backing).
    # It needs to exist from Front Face down to some depth.
    # Front Face Z = total_depth.
    # We place blocks flush with Front Face (internal).
    
    # Left Block
    b_left = trimesh.creation.box(bounds=[
        [wall_thickness, 0, total_depth - 10.0], # Start 10mm deep
        [wall_thickness + rail_block_w, outer_length, total_depth - 1.5] # Touch Front Face
    ])
    # Right Block
    b_right = trimesh.creation.box(bounds=[
        [outer_width - wall_thickness - rail_block_w, 0, total_depth - 10.0],
        [outer_width - wall_thickness, outer_length, total_depth - 1.5]
    ])
    
    body = body.union([b_left, b_right])
    
    # 2. Viewing Window (160x97)
    window_w = 160.0
    window_l = 97.0
    wx_min = (outer_width - window_w) / 2
    wy_min = (outer_length - window_l) / 2
    
    window_cutter = trimesh.creation.box(bounds=[
        [wx_min, wy_min, total_depth - 5.0], # Cut through front face
        [outer_width - wx_min, outer_length - wy_min, total_depth + 1.0]
    ])
    body = body.difference(window_cutter)
    
    # 3. Card Slot Cutter (The Slide-in Mechanism)
    # Rail inside the tub walls.
    # Slot Width: 170mm (5mm wider than window on each side -> Rails)
    slot_w = 170.0
    slot_gap_z = 1.2 # User Request: 1.2mm Gap (Tight fit for 1mm screen)
    
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
    print("   [Front] Side Rails & Slot Created.")

    # ------------------------------------------
    # C. Back Features (Mounts on Floor)
    # ------------------------------------------
    print("   [Back] Creating Internal Mounts...")
    
    # Internal Coordinate System: Z = floor_thickness (Surface of floor)
    floor_z = floor_thickness
    
    cx = outer_width / 2
    cy = outer_length / 2
    
    # 1. PiSugar Standoffs (Left Side -> Moved to TOP)
    # User Request: "Attached to the top so it can connect to charging port"
    
    # Y-Position: Align Top Edge of PiSugar with Top Wall (minus gap)
    # PiSugar Length = 56.5. Top Wall Y = outer_length (110).
    # Margin = 1.0mm
    ps_top_y = outer_length - wall_thickness - 1.0
    ps_cy = ps_top_y - (sugar_l / 2)
    
    # X-Position: Keep at Left (cx - 35) or user said "one container... put board...".
    # Previous X was cx - 35. Let's keep it to allow room for battery on right.
    ps_cx = cx - 35.0
    
    # Standard Pi Zero Mounts: 57.5 x 48.8
    standoff_dx = 57.5 
    standoff_dy = 48.8
    standoff_h = 12.0 # User Request: 12mm Height
    
    standoffs = []
    # 4 Holes (User Request: "4 holes")
    for sx in [-1, 1]:
        for sy in [-1, 1]:
            hx = ps_cx + (sx * standoff_dx / 2)
            hy = ps_cy + (sy * standoff_dy / 2)
            
            # Post
            post = trimesh.creation.cylinder(radius=2.5, height=standoff_h)
            post.apply_transform(trimesh.transformations.translation_matrix([hx, hy, floor_z + standoff_h/2]))
            
            # Hole (Screw thread size, approx 2.2mm dia -> 1.1 rad)
            hole = trimesh.creation.cylinder(radius=1.1, height=standoff_h + 5)
            hole.apply_transform(trimesh.transformations.translation_matrix([hx, hy, floor_z + standoff_h/2]))
            
            standoffs.append(post.difference(hole))
        
    for s in standoffs: body = body.union(s)
    
    # 2. Battery Walls (Right Side)
    # User Request: "Position slightly higher" (Higher than Center)
    # Center = cy. Top = ps_cy.
    # Let's move it UP by 15mm from Center.
    batt_cx = cx + 35.0
    batt_cy = cy + 15.0 
    
    bw_th = 1.5
    b_outer = trimesh.creation.box(extents=[batt_w + bw_th*2, batt_h + bw_th*2, comp_wall_h])
    b_outer.apply_transform(trimesh.transformations.translation_matrix([batt_cx, batt_cy, floor_z + comp_wall_h/2]))
    
    b_inner = trimesh.creation.box(extents=[batt_w, batt_h, comp_wall_h + 10])
    b_inner.apply_transform(trimesh.transformations.translation_matrix([batt_cx, batt_cy, floor_z + comp_wall_h/2]))
    
    body = body.union(b_outer.difference(b_inner))
    
    # 3. Wire Cutout for Battery (User Request: "5mm hole for wires")
    # Cut through the Left Wall of battery holder (Facing PiSugar)
    # Wall is at batt_cx - (batt_w/2) - bw_th
    # Let's just cut a box overlapping the left wall.
    wire_w = 10.0 # Depth of cut (through wall)
    wire_h = 5.0 # Width of cut (User said 5mm)
    wire_z_h = comp_wall_h + 5.0 # Cut from top to bottom? Or a slot?
    # User said "hole in wall". A slot from top is easiest for assembly.
    
    wire_cut = trimesh.creation.box(extents=[wire_w, wire_h, wire_z_h])
    # Position: Left edge of battery box
    wc_x = batt_cx - (batt_w/2) - bw_th
    wc_y = batt_cy # Center of battery Y
    wc_z = floor_z + comp_wall_h/2 + 2.0 # Higher up? Or floor level?
    # Let's make it a full slot from top of wall down to floor + 2mm (retain battery but allow wire)
    # Actually, wire enters from top. Just cut the Wall Height.
    wire_cut.apply_transform(trimesh.transformations.translation_matrix([wc_x, wc_y, floor_z + comp_wall_h/2]))
    
    body = body.difference(wire_cut)
    
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
        
    # 2. USB Port (Top Wall) - UPDATED SIZE & HEIGHT
    # User Request: 13mm (W) x 6mm (H)
    # Align Height with "Top of Standoffs".
    # PCB sits ON standoff (Z = floor_z + standoff_h).
    # USB Port sits ON PCB.
    # Center of Port (Height 6mm) is PCB_Surface + 3mm.
    port_x = (ps_cx + sugar_w/2) - 11.5
    port_z_center = floor_z + standoff_h + 3.0 
    
    # Cutout
    usb_cut = trimesh.creation.box(extents=[13.0, 10.0, 6.0]) # W=13, Depth=10, H=6
    usb_cut.apply_transform(trimesh.transformations.translation_matrix([port_x, outer_length, port_z_center]))
    body = body.difference(usb_cut)
    
    # 3. Reset Button (Back Face Flexure)
    # Restore Flexure Mechanism (Ring Cut + Nub)
    btn_x = (ps_cx - sugar_w/2) + 10.0
    btn_y = (ps_cy + sugar_l/2) - 15.0 
    
    # Specs
    btn_rad = 4.0
    slot = 1.0
    nub_h = 10.0 # User Request: 10mm Height to reach PCB
    
    # A. Ring Cut (Cut through floor)
    ring = trimesh.creation.cylinder(radius=btn_rad + slot, height=floor_thickness + 2)
    ring.apply_transform(trimesh.transformations.translation_matrix([btn_x, btn_y, floor_thickness/2]))
    inner = trimesh.creation.cylinder(radius=btn_rad, height=floor_thickness + 2)
    inner.apply_transform(trimesh.transformations.translation_matrix([btn_x, btn_y, floor_thickness/2]))
    cut = ring.difference(inner)
    
    # B. Hinge (Top side - keeps button attached to body)
    hinge = trimesh.creation.box(extents=[6.0, 3.0, floor_thickness + 2])
    hinge.apply_transform(trimesh.transformations.translation_matrix([btn_x, btn_y + btn_rad, floor_thickness/2]))
    
    final_cut = cut.difference(hinge)
    body = body.difference(final_cut)
    
    # C. Nub (Pushed button part - protrudes outwards? Or inwards?)
    # Usually protrudes OUT for finger press, or IN to hit switch?
    # Logic in back_cover: nub at z = base + nub_h/2. -> "Inside" the box (Z+).
    # Ah, the button press is EXTERNAL, pushing the nub INTERNAL to hit the switch.
    # So Nub should be on the INSIDE face (Z = floor_thickness).
    nub = trimesh.creation.cylinder(radius=1.5, height=nub_h)
    nub.apply_transform(trimesh.transformations.translation_matrix([btn_x, btn_y, floor_thickness + nub_h/2]))
    body = body.union(nub)
    
    # D. Groove (Tactile mark on outside?)
    # logic: Z = 0.4. Outside face is Z=0.
    groove = trimesh.creation.box(extents=[6.0, 2.0, 0.8])
    groove.apply_transform(trimesh.transformations.translation_matrix([btn_x, btn_y + btn_rad, 0.4]))
    body = body.difference(groove)
    
    return body

# ==========================================
# 3. Export
# ==========================================
if __name__ == "__main__":
    final_model = create_unibody_frame()
    final_model.export("unibody_frame.stl")
    print("✅ Created 'unibody_frame.stl'. Single Piece. Slide-in Ready.")
