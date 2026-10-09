"""Spawn intro_rover in Gazebo Harmonic; reuse part-4 /joint_states control.

Approach (Jazzy + Harmonic, without gz_ros2_control — not installed here):
  Part-4 nodes publish sensor_msgs/JointState on /joint_states.
  joint_state_to_gz republishes each position as std_msgs/Float64 on
  /cmd_pos/<joint>. ros_gz_bridge converts those to gz.msgs.Double for the
  gz-sim JointPositionController plugins embedded in the URDF.

Why not gz_ros2_control: package not installed and sudo apt is unavailable.
JointPositionController + Float64 bridge is the lightest documented Harmonic
path that keeps publishing JointState from part 4 unchanged.

Usage:
  ros2 launch intro_rover_description gazebo.launch.py
  # another terminal:
  ros2 run intro_rover_control manual_control

  # or:
  ros2 launch intro_rover_description gazebo.launch.py mode:=dance
"""

import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import (
    DeclareLaunchArgument,
    IncludeLaunchDescription,
    LogInfo,
    OpaqueFunction,
    SetEnvironmentVariable,
    TimerAction,
)
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue


JOINT_NAMES = [
    'shoulder_yaw',
    'shoulder_pitch',
    'elbow_pitch',
    'elbow_roll',
    'wrist_pitch',
    'wrist_roll',
    'fr_swerve_yaw',
    'fr_wheel',
    'br_swerve_yaw',
    'br_wheel',
    'fl_swerve_yaw',
    'fl_wheel',
    'bl_swerve_yaw',
    'bl_wheel',
]


def generate_launch_description():
    mode_arg = DeclareLaunchArgument(
        'mode',
        default_value='manual',
        description="Control mode: 'manual' or 'dance'",
    )
    world_arg = DeclareLaunchArgument(
        'world',
        default_value='empty.sdf',
        description='World SDF under intro_rover_description/worlds',
    )
    z_arg = DeclareLaunchArgument(
        'z',
        default_value='0.35',
        description='Spawn height (m)',
    )

    def launch_setup(context, *args, **kwargs):
        mode = LaunchConfiguration('mode').perform(context)
        world_name = LaunchConfiguration('world').perform(context)
        z = LaunchConfiguration('z').perform(context)

        desc_share = get_package_share_directory('intro_rover_description')
        urdf_path = os.path.join(desc_share, 'urdf', 'intro_rover_description.urdf')
        world_path = os.path.join(desc_share, 'worlds', world_name)
        pkg_ros_gz_sim = get_package_share_directory('ros_gz_sim')

        resource_path = desc_share
        existing = os.environ.get('GZ_SIM_RESOURCE_PATH', '')
        if existing:
            resource_path = resource_path + os.pathsep + existing

        with open(urdf_path, 'r', encoding='utf-8') as f:
            robot_description = f.read()
        # Gazebo cannot resolve package:// URIs; rewrite to absolute file:// paths
        robot_description = robot_description.replace(
            'package://intro_rover_description/',
            'file://' + desc_share.rstrip('/') + '/',
        )

        gz_sim = IncludeLaunchDescription(
            PythonLaunchDescriptionSource(
                os.path.join(pkg_ros_gz_sim, 'launch', 'gz_sim.launch.py')
            ),
            launch_arguments={'gz_args': f'-r {world_path}'}.items(),
        )

        robot_state_publisher = Node(
            package='robot_state_publisher',
            executable='robot_state_publisher',
            name='robot_state_publisher',
            output='screen',
            parameters=[{
                'robot_description': ParameterValue(robot_description, value_type=str),
                'use_sim_time': True,
            }],
        )

        spawn = TimerAction(
            period=3.0,
            actions=[
                Node(
                    package='ros_gz_sim',
                    executable='create',
                    name='spawn_intro_rover',
                    output='screen',
                    arguments=[
                        '-name', 'intro_rover',
                        '-topic', 'robot_description',
                        '-z', z,
                    ],
                )
            ],
        )

        bridge_args = [
            '/clock@rosgraph_msgs/msg/Clock[gz.msgs.Clock',
        ]
        for jn in JOINT_NAMES:
            bridge_args.append(
                f'/cmd_pos/{jn}@std_msgs/msg/Float64]gz.msgs.Double'
            )

        bridge = Node(
            package='ros_gz_bridge',
            executable='parameter_bridge',
            name='ros_gz_bridge',
            output='screen',
            arguments=bridge_args,
            parameters=[{'use_sim_time': True}],
        )

        adapter = Node(
            package='intro_rover_control',
            executable='joint_state_to_gz',
            name='joint_state_to_gz',
            output='screen',
            parameters=[{'use_sim_time': True}],
        )

        actions = [
            SetEnvironmentVariable('GZ_SIM_RESOURCE_PATH', resource_path),
            SetEnvironmentVariable('IGN_GAZEBO_RESOURCE_PATH', resource_path),
            gz_sim,
            robot_state_publisher,
            spawn,
            bridge,
            adapter,
        ]

        if mode == 'dance':
            actions.append(
                TimerAction(
                    period=5.0,
                    actions=[
                        Node(
                            package='intro_rover_control',
                            executable='dance',
                            name='dance',
                            output='screen',
                            parameters=[{'use_sim_time': True}],
                        )
                    ],
                )
            )
            actions.append(LogInfo(msg='Dance mode: dance node starts ~5s after launch'))
        else:
            actions.append(
                LogInfo(
                    msg=(
                        'Manual mode: after Gazebo is up, in another Ubuntu terminal:\n'
                        '  source /opt/ros/jazzy/setup.bash && '
                        'source ~/Software_Intro_Task_2026-2027/install/setup.bash && '
                        'ros2 run intro_rover_control manual_control'
                    )
                )
            )
        return actions

    return LaunchDescription([
        mode_arg,
        world_arg,
        z_arg,
        OpaqueFunction(function=launch_setup),
    ])
