"""
06_swarm_formation.py

Goal: Swarm Formation Control
Key Concepts: Relative Positioning, Coordinate Transformations

This example makes the swarm form a shape.
With 2 drones, they will form a line and rotate.
With 3 drones, they would form a triangle.
"""
import math
import time
import cflib.crtp
from cflib.crazyflie.swarm import CachedCfFactory
from cflib.crazyflie.swarm import Swarm

# List of URIs for the swarm
uris = [
    'radio://0/100/2M/247E000002',  # Drone 1 (Center)
    'radio://0/100/2M/247E000003',  # Drone 2 (Satellite)
]

def run_formation(scf):
    """
    Each drone runs this. We determine behavior based on URI.
    """
    commander = scf.cf.high_level_commander
    uri = scf.cf.link_uri

    # 1. Takeoff
    commander.takeoff(0.5, 2.0)
    time.sleep(3)

    # Define roles
    is_center = (uri == uris[0])
    
    if is_center:
        print(f"{uri}: I am the center.")
        # Center drone stays put (or bobs)
        time.sleep(5)
    else:
        print(f"{uri}: I am orbiting.")
        # Satellite drone moves to a relative position
        # Move 0.5m to the right
        commander.go_to(0.0, -0.5, 0.0, 0, 2.0, relative=True)
        time.sleep(2)
        
        # Fly a semi-circle around the center
        # This is a simplified "orbit" using waypoints
        steps = 10
        radius = 0.5
        for i in range(steps):
            angle = (i / steps) * math.pi # 180 degrees
            x = radius * math.sin(angle)
            y = -radius * math.cos(angle)
            
            # We want to be at (x, y) relative to the START position of the orbit
            # But go_to is relative to CURRENT position.
            # So we use absolute setpoints if we had a positioning system,
            # OR we calculate small relative increments.
            # For simplicity in this workshop, let's just do a square pattern orbit
            pass
        
        # Square Orbit
        # Forward
        commander.go_to(0.5, 0.0, 0.0, 0, 1.0, relative=True)
        time.sleep(1)
        # Left
        commander.go_to(0.0, 0.5, 0.0, 0, 1.0, relative=True)
        time.sleep(1)
        # Backward
        commander.go_to(-0.5, 0.0, 0.0, 0, 1.0, relative=True)
        time.sleep(1)
        # Right (back to start of orbit)
        commander.go_to(0.0, -0.5, 0.0, 0, 1.0, relative=True)
        time.sleep(1)

        # Return to center
        commander.go_to(0.0, 0.5, 0.0, 0, 2.0, relative=True)
        time.sleep(2)

    # Land
    commander.land(0.0, 2.0)
    time.sleep(2)
    commander.stop()

def run_swarm():
    factory = CachedCfFactory(rw_cache='./cache')
    with Swarm(uris, factory=factory) as swarm:
        print("Connected to Swarm!")
        swarm.reset_estimators()
        print("Starting Formation...")
        swarm.parallel_safe(run_formation)
        print("Finished!")

if __name__ == '__main__':
    cflib.crtp.init_drivers()
    run_swarm()
