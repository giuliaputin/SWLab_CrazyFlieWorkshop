# Crazyflie Workshop Examples

This directory contains code examples for the TU Delft Swarming Lab workshop.

## Prerequisites

1. **Python**: Ensure Python 3.7+ is installed.
2. **cflib**: Install the Crazyflie Python library:
   ```bash
   pip install cflib
   ```
3. **Crazyradio**: Ensure you have a Crazyradio PA plugged in and drivers installed.

## Examples

### 1. Basic Flight (`01_basic_flight.py`)
Connects to a single drone, takes off, hovers, and lands.
**Usage**:
```bash
python 01_basic_flight.py
```
*Note: Check the URI in the file matches your drone.*

### 2. Trajectory (`02_trajectory.py`)
Flies a square pattern using low-level position setpoints. Demonstrates coordinate systems.
**Usage**:
```bash
python 02_trajectory.py
```

### 3. Swarm Test (`03_swarm_test.py`)
Controls two drones simultaneously to take off and land. Useful for verifying connection and basic swarm setup.
**Usage**:
1. Edit the `uris` list in the file to match your two drones.
2. Run:
   ```bash
   python 03_swarm_test.py
   ```

### 4. Swarm Dance (`04_swarm_dance.py`)
Advanced example where drones perform a synchronized circle pattern and bob up and down.
**Usage**:
```bash
python 04_swarm_dance.py
```

### 5. Keyboard Control (`05_keyboard_control.py`)
Control the drone using your keyboard.
**Controls**:
- **Arrow Keys**: Move Forward/Backward/Left/Right
- **W/S**: Up/Down
- **A/D**: Rotate Yaw
- **Space**: Land/Stop
**Usage**:
```bash
python 05_keyboard_control.py
```

### 6. Swarm Formation (`06_swarm_formation.py`)
Drones take off and form a shape (line/triangle) and rotate.
**Usage**:
```bash
python 06_swarm_formation.py
```

python 06_swarm_formation.py
```

### 7. PID Tuning (`07_pid_tuning.py`)
Tune the drone's Roll PID controller in real-time.
**Controls**:
- **Enter**: Takeoff
- **Space**: Land
- **1/2**: Decrease/Increase Roll KP
- **3/4**: Decrease/Increase Roll KI
- **5/6**: Decrease/Increase Roll KD
**Usage**:
```bash
python 07_pid_tuning.py
```

python 07_pid_tuning.py
```

### 8. Leader-Follower Tuning (`08_leader_follower_tuning.py`)
Control one drone (Leader) with keyboard, while the second drone (Follower) chases it.
Tune the **Following Gain** (P-gain) in real-time to see how it affects tracking performance.
**Controls**:
- **Arrow Keys**: Move Leader
- **W/S**: Leader Up/Down
- **1/2**: Decrease/Increase Following Gain
**Usage**:
```bash
python 08_leader_follower_tuning.py
```

## Advanced: On-board App Layer Programming

For advanced control or high-frequency loops (e.g., 1kHz), running code on the drone's microcontroller is preferred over Python scripts (which are limited by radio latency).

Bitcraze provides the **App Layer** to write custom C/C++ code without modifying the core firmware.

### How to get started with App Layer:

1. **Clone the Firmware**:
   ```bash
   git clone --recursive https://github.com/bitcraze/crazyflie-firmware.git
   cd crazyflie-firmware
   ```

2. **Explore Examples**:
   Check `examples/app_hello_world` in the firmware repository.

3. **Create your App**:
   You can create a standalone folder for your app (out of tree).
   Structure:
   ```
   my_app/
   ├── Makefile
   └── src/
       └── app.c
   ```

4. **Makefile**:
   ```makefile
   APP=1
   APP_STACKSIZE=300
   
   VPATH += src/
   PROJ_OBJ += app.o
   
   CRAZYFLIE_BASE=../crazyflie-firmware
   include $(CRAZYFLIE_BASE)/Makefile
   ```

5. **Build and Flash**:
   ```bash
   make
   make cload
   ```

### Why App Layer?
- **Low Latency**: Run control loops at 1kHz.
- **Robustness**: Drone continues to fly even if radio connection is lost (if programmed to do so).
- **Access**: Direct access to sensors and expansion decks (Flow deck, etc.).

For more details, see the [Bitcraze App Layer Documentation](https://www.bitcraze.io/documentation/repository/crazyflie-firmware/master/functional-areas/app_layer/).
