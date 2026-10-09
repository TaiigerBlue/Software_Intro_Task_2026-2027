# Space Concordia Robotics: Software Intro Task 2026–2027

**Solution by Christopher Nemer** ([TaiigerBlue](https://github.com/TaiigerBlue))

This fork completes the Software Intro Task. The workspace is built on **Ubuntu 24.04 (WSL2) with ROS 2 Jazzy and Gazebo Harmonic**. It has two packages:

| Package | Type | What it does |
|---|---|---|
| `intro_rover_description` | `ament_cmake` | Rover URDF and meshes, the RViz launch and config, the Gazebo launch and world |
| `intro_rover_control` | `ament_python` | Keyboard manual control, the dance node, and the `/joint_states` → Gazebo adapter |

All control goes through one interface: **`sensor_msgs/JointState` on `/joint_states`**. The same control nodes drive the rover in both RViz and Gazebo.

---

## Quick start

```bash
# Prerequisites: ROS 2 Jazzy desktop, ros-jazzy-ros-gz, ros-jazzy-joint-state-publisher-gui
git clone https://github.com/TaiigerBlue/Software_Intro_Task_2026-2027.git
cd Software_Intro_Task_2026-2027
source /opt/ros/jazzy/setup.bash
colcon build --symlink-install
source install/setup.bash
```

| Demo | Command |
|---|---|
| RViz with joint sliders (step 3) | `ros2 launch intro_rover_description display.launch.py` |
| RViz with dance (step 4) | `ros2 launch intro_rover_control control.launch.py mode:=dance` |
| RViz with keyboard (step 4) | `ros2 launch intro_rover_control control.launch.py`, then in a 2nd terminal `ros2 run intro_rover_control manual_control` |
| Gazebo with dance (step 5) | `ros2 launch intro_rover_description gazebo.launch.py mode:=dance` |
| Gazebo with keyboard (step 5) | `ros2 launch intro_rover_description gazebo.launch.py`, then in a 2nd terminal `ros2 run intro_rover_control manual_control` |

**Keyboard controls** (the terminal running `manual_control` must be focused, not RViz or Gazebo):

| Key | Action |
|---|---|
| `a` / `d` | Select the previous / next joint |
| `w` / `s` | Move the selected joint +/− 0.1 rad |
| `r` | Reset all joints to 0 |
| `q` | Quit |

---

## 1. Creating a local repository
I forked the upstream repo to `TaiigerBlue/Software_Intro_Task_2026-2027` and cloned it into WSL2 Ubuntu 24.04. The original repo is kept as the `upstream` remote. A `.gitignore` keeps `build/`, `install/`, and `log/` out of version control.

## 2. Fixing `intro_rover_description`
The package built, but it didn't install anything, so `robot_state_publisher`, RViz, and Gazebo couldn't find the URDF or the meshes at runtime.

- **`CMakeLists.txt`**: added an `install(DIRECTORY urdf meshes launch rviz worlds DESTINATION share/${PROJECT_NAME})` rule. That way, the `package://intro_rover_description/...` mesh paths resolve from the install space.
- **`package.xml`**: added runtime dependencies (`robot_state_publisher`, `joint_state_publisher_gui`, `rviz2`, `ros_gz_sim`, `ros_gz_bridge`).
- **URDF**: added `<limit effort velocity>` and `<dynamics damping>` to the joints so they're usable for simulation and control (see step 5 for the Gazebo additions).

## 3. Visualizing in RViz
`launch/display.launch.py` starts three nodes:
- `robot_state_publisher`, which gets the URDF *contents* as `robot_description` (not the file path),
- `joint_state_publisher_gui`, which gives a slider for every movable joint,
- `rviz2`, loaded with the saved config `rviz/display.rviz` (Fixed Frame `base_link`, with a RobotModel display on `/robot_description`).

## 4. Control infrastructure (`intro_rover_control`)
Both nodes publish `sensor_msgs/JointState` on `/joint_states` at 20 Hz for all 14 joints. The joint list is defined once, in `joint_names.py`: the 6 arm joints (shoulder yaw/pitch, elbow pitch/roll, wrist pitch/roll) plus 4 swerve-yaw and 4 wheel joints.

- **`manual_control`** (step 4.1): a keyboard teleop node. It reads keys directly from the terminal in cbreak mode on its own thread, so no extra teleop package is needed. The selected joint moves 0.1 rad per keypress.
- **`dance`** (step 4.2): joint positions are *functions of time*. The arm joints follow sine waves with different frequencies and phases, the swerve modules wiggle at ±0.4 rad, and the wheels and wrist roll spin continuously.
- **`launch/control.launch.py`**: runs `robot_state_publisher` and RViz *without* the slider GUI (it would fight with the control nodes over `/joint_states`). `mode:=dance` also starts the dance node, and `mode:=manual` (the default) expects `manual_control` in a second terminal.

## 5. Simulation in Gazebo Harmonic
`launch/gazebo.launch.py` spawns the rover in `worlds/empty.sdf` and drives it with **the same step 4 nodes, unchanged**:

```
manual_control / dance
        │  sensor_msgs/JointState on /joint_states
        ▼
joint_state_to_gz            (intro_rover_control)
        │  std_msgs/Float64 on /cmd_pos/<joint>   (one topic per joint)
        ▼
ros_gz_bridge                (ROS Float64 → gz.msgs.Double)
        ▼
gz::sim::systems::JointPositionController   (one plugin per joint, in the URDF)
```

What the launch file does:
- Starts Gazebo Harmonic through `ros_gz_sim`'s `gz_sim.launch.py` and spawns the rover from the URDF (spawn height set by `z:=`, default 0.35 m).
- Rewrites `package://intro_rover_description/` mesh URIs to absolute `file://` paths, because Gazebo can't resolve `package://`. It also sets `GZ_SIM_RESOURCE_PATH`.
- Runs `robot_state_publisher` with `use_sim_time`, the `/cmd_pos/*` bridge, and the `joint_state_to_gz` adapter.
- `mode:=dance` starts the dance node about 5 s after launch so the model has time to load. Other arguments are `world:=` and `z:=`.

**Why `JointPositionController` instead of `gz_ros2_control`?** Using a small adapter plus the bridge kept step 4's `/joint_states` interface exactly as it was, and it needed no extra controller configuration. `gz_ros2_control` with a `ros2_control` controller manager would be the next step for a real drivetrain (velocity control on the wheels and swerve kinematics).

## Notes and known limitations
- The meshes are detailed (about 30 MB of STL), so Gazebo's first load is slow. Simplified collision meshes would speed up the simulation.
- The wheels are position-controlled for the demo. The rover moves its joints in place rather than driving around the world.
- Don't run the RViz slider GUI and the control nodes at the same time, since both publish `/joint_states`.
- Tested on Windows 11 with WSL2 (WSLg for the GUIs), Ubuntu 24.04.5, ROS 2 Jazzy, and Gazebo Harmonic 8.15.

---

<details>
<summary>Original task description</summary>

### 1. Creating a local repository
1.1. Make sure that your GitHub account is connected to your computer.
1.2. Fork this repository into your GitHub account.
1.3. Clone your fork of this repository onto your personal machine.

### 2. Fix the intro_rover_description ROS2 package
2.1. Apply the changes necessary to the files of the package in order to get it to work properly within ROS2.

### 3. Visualize the robot in RViz
3.1. Create a launch file to visualize the rover in the RViz software.

### 4. Create a Ros2 infrastructure to control the rover in RViz
4.1. Create a node to manually control each joint of the rover.
4.2. Create a node to make the rover dance. This should be a reprogrammed sequence or a function of the joint states over time.

### 5. Simulate the robot in Gazebo Harmonic
5.1. Create a launch file that spawns the rover in a Gazebo world. Please make sure to use Gazebo Harmonic as this version of Gazebo works better with ROS2 Jazzy.
5.2. Control the rover with the control infrastructure built in part 4. and see it move in the Gazebo world.

### 6. Be ready to present your solution
6.1. Modify this README.md file in your forked workspace presenting your solutions.
6.2. Run and present your workspace to the Software Manager.
</details>
