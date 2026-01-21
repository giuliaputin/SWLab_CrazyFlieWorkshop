"""
17_Mech_Pilot_EasyMatch.py

Goal: "Mech Pilot" with RELAXED alignment logic.
Changes:
- Alignment is now "rough" (arms just need to be horizontal-ish).
- Removed strict pixel distance matching.
- Retained Safety features (Safe-Start, Soft-Start).
- High Contrast GUI.

Prerequisites:
    pip install opencv-python mediapipe cflib numpy
"""
import logging
import time
import math
import cv2
import mediapipe as mp
import numpy as np
from enum import Enum

import cflib.crtp
from cflib.crazyflie import Crazyflie
from cflib.crazyflie.syncCrazyflie import SyncCrazyflie
from cflib.utils import uri_helper

# --- CONFIGURATION ---
URI = uri_helper.uri_from_env(default='radio://0/80/2M/247E000044')

# Physics
MAX_VEL_Y   = 0.6   
MAX_VEL_Z   = 0.3   
LIMIT_Z_MAX = 1.6   
BASE_SENSITIVITY = 1.5 

# Colors
C_NEON_GRN = (0, 255, 0)
C_NEON_RED = (0, 0, 255)
C_CYAN     = (255, 255, 0)
C_WHITE    = (255, 255, 255)

logging.basicConfig(level=logging.ERROR)

class State(Enum):
    ALIGNMENT = 0
    STANDBY = 1
    FLYING = 2
    DISARMED = 3

class MechPilot:
    def __init__(self):
        self.mp_pose = mp.solutions.pose
        self.pose = self.mp_pose.Pose(
            model_complexity=1, 
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5
        )
        self.mp_draw = mp.solutions.drawing_utils
        
    def process(self, frame):
        h, w, _ = frame.shape
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = self.pose.process(rgb)
        
        joints = {}
        pose_type = "NONE"
        cmd_vel = (0,0,0)
        landmarks_raw = None

        if results.pose_landmarks:
            landmarks_raw = results.pose_landmarks
            lm = results.pose_landmarks.landmark
            
            # Extract Joints
            joints = {
                'n':  (int(lm[0].x * w), int(lm[0].y * h)),
                'lw': (int(lm[15].x * w), int(lm[15].y * h)),
                'rw': (int(lm[16].x * w), int(lm[16].y * h)),
                'ls': (int(lm[11].x * w), int(lm[11].y * h)),
                'rs': (int(lm[12].x * w), int(lm[12].y * h))
            }

            # 1. Kill Switch (X-Pose)
            wrist_dist = math.hypot(joints['lw'][0]-joints['rw'][0], joints['lw'][1]-joints['rw'][1])
            if wrist_dist < w * 0.15:
                return "X_POSE", (0,0,0), joints, landmarks_raw

            # 2. Hands Up (Launch Pose)
            if joints['lw'][1] < joints['n'][1] and joints['rw'][1] < joints['n'][1]:
                pose_type = "Y_POSE"

            # --- FLIGHT CONTROLS ---
            # Roll (Tilt Right = Fly Right)
            dy = joints['rw'][1] - joints['lw'][1]
            dx = joints['rw'][0] - joints['lw'][0]
            angle = math.degrees(math.atan2(dy, dx)) if dx != 0 else 0
            
            roll_input = np.clip(angle / 45.0, -1.0, 1.0)
            
            # Height
            avg_wrist_y = (joints['lw'][1] + joints['rw'][1]) / 2
            avg_shldr_y = (joints['ls'][1] + joints['rs'][1]) / 2
            height_input = (avg_shldr_y - avg_wrist_y) / (h * 0.2)
            height_input = np.clip(height_input, -1.0, 1.0)
            
            # Deadzones
            if abs(roll_input) < 0.15: roll_input = 0
            if abs(height_input) < 0.2: height_input = 0
            
            vy = roll_input * MAX_VEL_Y * BASE_SENSITIVITY
            vz = height_input * MAX_VEL_Z
            cmd_vel = (0, vy, vz)

        return pose_type, cmd_vel, joints, landmarks_raw

    def draw_skeleton(self, frame, landmarks):
        if landmarks:
            self.mp_draw.draw_landmarks(
                frame, landmarks, self.mp_pose.POSE_CONNECTIONS,
                self.mp_draw.DrawingSpec(color=C_NEON_GRN, thickness=2, circle_radius=2),
                self.mp_draw.DrawingSpec(color=C_WHITE, thickness=2, circle_radius=2)
            )

def draw_ghost_template(frame, matched=False):
    h, w, _ = frame.shape
    cx, cy = w//2, h//2 - 50
    span = int(w * 0.25)
    
    color = C_NEON_GRN if matched else C_WHITE
    thick = 5 if matched else 2
    
    # Points
    p_neck = (cx, cy - 50)
    p_hip  = (cx, cy + 150)
    p_lw   = (cx - span, cy - 50)
    p_rw   = (cx + span, cy - 50)
    
    cv2.line(frame, p_neck, p_hip, color, thick)
    cv2.line(frame, p_lw, p_rw, color, thick)
    
    # Draw large target circles
    cv2.circle(frame, p_lw, 40, color, 2)
    cv2.circle(frame, p_rw, 40, color, 2)

    if not matched:
        cv2.putText(frame, "EXTEND ARMS TO SIDES", (cx-200, cy-150), cv2.FONT_HERSHEY_SIMPLEX, 0.8, C_WHITE, 2)

def check_loose_alignment(joints, frame_shape):
    """ 
    New 'Rough' Alignment Logic.
    Does NOT require matching specific pixels.
    Just checks if arms are roughly extended to the sides.
    """
    if not joints: return False
    
    h, w, _ = frame_shape
    
    lw = joints['lw']
    rw = joints['rw']
    ls = joints['ls']
    rs = joints['rs']
    
    # Check 1: Horizontal Spread
    # Hands should be far apart (at least 40% of screen width)
    spread = abs(lw[0] - rw[0])
    is_wide_enough = spread > (w * 0.4)
    
    # Check 2: Level with Shoulders
    # Hands should be roughly at shoulder height (within a vertical band)
    # Band is +/- 15% of screen height (very generous)
    l_level = abs(lw[1] - ls[1]) < (h * 0.15)
    r_level = abs(rw[1] - rs[1]) < (h * 0.15)
    
    return (is_wide_enough and l_level and r_level)

def run_app(scf):
    cf = scf.cf
    commander = cf.commander
    pilot = MechPilot()
    
    cap = cv2.VideoCapture(0)
    cv2.namedWindow('MECH PILOT', cv2.WINDOW_NORMAL)
    cv2.setWindowProperty('MECH PILOT', cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)
    
    state = State.ALIGNMENT
    match_start_time = 0
    SCAN_DURATION = 1.5 # Faster scan for better UX
    
    takeoff_time = 0
    z_pos = 0.0
    last_time = time.time()
    
    print("System Online.")

    try:
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret: break
            frame = cv2.flip(frame, 1)
            h, w, _ = frame.shape
            
            pose, raw_cmd, joints, landmarks = pilot.process(frame)
            vx, vy, vz = raw_cmd
            
            current_time = time.time()
            dt = current_time - last_time
            last_time = current_time

            if landmarks:
                pilot.draw_skeleton(frame, landmarks)
            else:
                cv2.putText(frame, "STEP IN FRAME", (20, h//2), cv2.FONT_HERSHEY_SIMPLEX, 1, C_NEON_RED, 2)

            # --- STATE MACHINE ---

            if state == State.ALIGNMENT:
                # Draw visual guide
                draw_ghost_template(frame, matched=False)
                
                # Check "Loose" Alignment
                is_aligned = check_loose_alignment(joints, frame.shape)
                
                if is_aligned:
                    # Draw Matched Overlay
                    draw_ghost_template(frame, matched=True)
                    
                    if match_start_time == 0: match_start_time = current_time
                    progress = (current_time - match_start_time) / SCAN_DURATION
                    
                    # Bar
                    bw = 300
                    bx = w//2 - bw//2
                    by = h//2 + 100
                    cv2.rectangle(frame, (bx, by), (bx+int(bw*progress), by+30), C_NEON_GRN, -1)
                    
                    if progress >= 1.0:
                        state = State.STANDBY
                else:
                    match_start_time = 0
            
            elif state == State.STANDBY:
                cv2.putText(frame, "READY", (w//2-50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, C_CYAN, 2)
                cv2.putText(frame, "RAISE HANDS TO LAUNCH", (w//2-250, h-50), cv2.FONT_HERSHEY_SIMPLEX, 0.8, C_WHITE, 2)
                
                if pose == "Y_POSE":
                    print("LAUNCHING...")
                    cf.platform.send_arming_request(True)
                    time.sleep(1.0)
                    commander.send_setpoint(0,0,0,0)
                    for z in range(10):
                        commander.send_position_setpoint(0,0, z/20.0 + 0.1, 0)
                        time.sleep(0.05)
                    state = State.FLYING
                    takeoff_time = current_time
                    z_pos = 0.5
            
            elif state == State.FLYING:
                if pose == "X_POSE":
                    state = State.DISARMED
                    break
                
                # Soft Start
                flight_time = current_time - takeoff_time
                ramp = 0.1 + (flight_time/5.0)*0.9 if flight_time < 5.0 else 1.0
                
                safe_vy = vy * ramp
                safe_vz = vz * ramp
                
                z_pos += safe_vz * dt
                if z_pos > LIMIT_Z_MAX: z_pos = LIMIT_Z_MAX
                if z_pos < 0.2: z_pos = 0.2
                
                commander.send_velocity_world_setpoint(0, safe_vy, safe_vz, 0)
                
                cv2.putText(frame, "FLIGHT ACTIVE", (20, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, C_NEON_GRN, 2)
                cv2.putText(frame, "CROSS ARMS TO LAND", (20, h-50), cv2.FONT_HERSHEY_SIMPLEX, 0.8, C_NEON_RED, 2)

            cv2.imshow('MECH PILOT', frame)
            if cv2.waitKey(5) & 0xFF == 27: break

    finally:
        print("Landing...")
        commander.send_stop_setpoint()
        cf.platform.send_arming_request(False)
        cap.release()
        cv2.destroyAllWindows()

if __name__ == '__main__':
    cflib.crtp.init_drivers()
    print(f"Connecting to {URI}...")
    with SyncCrazyflie(URI, cf=Crazyflie(rw_cache='./cache')) as scf:
        print("Connected.")
        run_app(scf)