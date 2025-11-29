"""
08_leader_follower_tuning.py

Goal: Leader-Follower with Keyboard Control & Real-time Tuning
Key Concepts: Swarm, Shared State, P-Controller Tuning

Leader (Drone 1): Controlled by Keyboard (Arrow keys)
Follower (Drone 2): Follows Leader. You can tune the 'Following Gain' (P-gain).

Controls:
    Arrow Keys: Move Leader
    W/S: Leader Up/Down
    Space: Land All
    
    1 / 2: Decrease / Increase Following Gain (Responsiveness)
"""
import math
import time
import logging
from threading import Thread

import cflib.crtp
from cflib.crazyflie.log import LogConfig
from cflib.crazyflie.swarm import CachedCfFactory
from cflib.crazyflie.swarm import Swarm
from cflib.positioning.motion_commander import MotionCommander
from pynput import keyboard

# URIs
URI_LEADER = 'radio://0/80/2M/247E000006'
URI_FOLLOWER = 'radio://0/60/2M/247E000009'
uris = {URI_LEADER, URI_FOLLOWER}

# Global State
positions = {
    URI_LEADER: {'x': 0, 'y': 0, 'z': 0},
    URI_FOLLOWER: {'x': 0, 'y': 0, 'z': 0}
}

# Tuning Parameters
FOLLOW_GAIN = 1.0  # P-gain for following
FOLLOW_DIST = 0.4  # Target distance (m)

running = True
flying = True # Start flying immediately

def pos_callback(uri, data):
    positions[uri]['x'] = data['stateEstimate.x']
    positions[uri]['y'] = data['stateEstimate.y']
    positions[uri]['z'] = data['stateEstimate.z']

def start_logging(scf):
    log_conf = LogConfig(name='Position', period_in_ms=50)
    log_conf.add_variable('stateEstimate.x', 'float')
    log_conf.add_variable('stateEstimate.y', 'float')
    log_conf.add_variable('stateEstimate.z', 'float')
    scf.cf.log.add_config(log_conf)
    log_conf.data_received_cb.add_callback(lambda _, data, __: pos_callback(scf.cf.link_uri, data))
    log_conf.start()

def run_leader(scf):
    """
    Leader logic: Controlled by keyboard global variables (simulated here for simplicity)
    """
    # We reuse the keyboard controller logic but simplified for swarm context
    # Ideally we'd pass the controller instance, but for swarm.parallel_safe it's trickier.
    # We'll use a simple loop that reads global 'cmd_vel' set by keyboard thread.
    
    # We use the high level commander for takeoff/land
    hl_commander = scf.cf.high_level_commander
    hl_commander.takeoff(0.5, 2.0)
    time.sleep(3)
    
    while running and flying:
        # Apply velocity commands from keyboard (global cmd_vel)
        # Note: In a real robust app, use a thread-safe queue or object
        # We use the LOW LEVEL commander for velocity setpoints
        scf.cf.commander.send_velocity_world_setpoint(cmd_vel['vx'], cmd_vel['vy'], cmd_vel['vz'], cmd_vel['yaw'])
        time.sleep(0.1)
        
    hl_commander.land(0.0, 2.0)
    time.sleep(2)
    hl_commander.stop()

def run_follower(scf):
    """
    Follower logic: P-controller to chase Leader
    """
    hl_commander = scf.cf.high_level_commander
    hl_commander.takeoff(0.5, 2.0)
    time.sleep(3)
    
    while running and flying:
        # Get positions
        l_pos = positions[URI_LEADER]
        f_pos = positions[URI_FOLLOWER]
        
        # Calculate vector to leader
        dx = l_pos['x'] - f_pos['x']
        dy = l_pos['y'] - f_pos['y']
        dist = math.sqrt(dx**2 + dy**2)
        
        # Simple P-controller
        # We want to be at distance FOLLOW_DIST from leader
        # But for simplicity, let's just try to match position with an offset, 
        # or just move towards leader if far.
        
        # Strategy: Move towards leader to maintain FOLLOW_DIST
        if dist > FOLLOW_DIST:
            # Move towards leader
            # Velocity = Gain * Error
            # Error is (Distance - Target)
            error = dist - FOLLOW_DIST
            vel = FOLLOW_GAIN * error
            
            # Normalize direction
            vx = (dx / dist) * vel
            vy = (dy / dist) * vel
        else:
            # Too close or just right, stop (or back up)
            vx = 0
            vy = 0
            
        # Limit max velocity for safety
        MAX_VEL = 1.0
        vx = max(min(vx, MAX_VEL), -MAX_VEL)
        vy = max(min(vy, MAX_VEL), -MAX_VEL)
        
        scf.cf.commander.send_velocity_world_setpoint(vx, vy, 0, 0)
        time.sleep(0.1)

    hl_commander.land(0.0, 2.0)
    time.sleep(2)
    hl_commander.stop()

# Keyboard State
cmd_vel = {'vx': 0, 'vy': 0, 'vz': 0, 'yaw': 0}

def on_press(key):
    global flying, FOLLOW_GAIN
    VEL = 0.5
    
    try:
        if key == keyboard.Key.space:
            flying = False
            print("Landing...")
            
        # Leader Controls
        elif key == keyboard.Key.up: cmd_vel['vx'] = VEL
        elif key == keyboard.Key.down: cmd_vel['vx'] = -VEL
        elif key == keyboard.Key.left: cmd_vel['vy'] = VEL
        elif key == keyboard.Key.right: cmd_vel['vy'] = -VEL
        elif hasattr(key, 'char') and key.char == 'w': cmd_vel['vz'] = VEL
        elif hasattr(key, 'char') and key.char == 's': cmd_vel['vz'] = -VEL
        
        # Tuning
        elif hasattr(key, 'char') and key.char == '1':
            FOLLOW_GAIN -= 0.1
            print(f"Gain: {FOLLOW_GAIN:.1f}")
        elif hasattr(key, 'char') and key.char == '2':
            FOLLOW_GAIN += 0.1
            print(f"Gain: {FOLLOW_GAIN:.1f}")
            
    except AttributeError:
        pass

def on_release(key):
    try:
        if key == keyboard.Key.up or key == keyboard.Key.down: cmd_vel['vx'] = 0
        elif key == keyboard.Key.left or key == keyboard.Key.right: cmd_vel['vy'] = 0
        elif hasattr(key, 'char') and (key.char == 'w' or key.char == 's'): cmd_vel['vz'] = 0
    except: pass

def run_swarm_logic():
    factory = CachedCfFactory(rw_cache='./cache')
    with Swarm(uris, factory=factory) as swarm:
        print("Connected. Resetting estimators...")
        swarm.reset_estimators()
        swarm.parallel_safe(start_logging)
        print("Taking off immediately...")
        
        # We need to run specific functions for specific drones
        # Swarm library runs same func on all, so we dispatch inside
        def dispatch(scf):
            if scf.cf.link_uri == URI_LEADER:
                run_leader(scf)
            elif scf.cf.link_uri == URI_FOLLOWER:
                run_follower(scf)
                
        swarm.parallel_safe(dispatch)

if __name__ == '__main__':
    cflib.crtp.init_drivers()
    
    # Start Keyboard Listener
    listener = keyboard.Listener(on_press=on_press, on_release=on_release)
    listener.start()
    
    run_swarm_logic()
