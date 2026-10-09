"""RViz + robot_state_publisher + optional dance node (no slider GUI).

For keyboard manual control, start this launch then in a *second* Ubuntu
terminal run:
  ros2 run intro_rover_control manual_control
"""

import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, LogInfo, OpaqueFunction
from launch.substitutions import Command, LaunchConfiguration
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue


def generate_launch_description():
    mode_arg = DeclareLaunchArgument(
        'mode',
        default_value='manual',
        description="Control mode: 'manual' (run keyboard node yourself) or 'dance'",
    )

    def launch_setup(context, *args, **kwargs):
        mode = LaunchConfiguration('mode').perform(context)

        desc_share = get_package_share_directory('intro_rover_description')
        urdf_path = os.path.join(desc_share, 'urdf', 'intro_rover_description.urdf')
        rviz_config = os.path.join(desc_share, 'rviz', 'display.rviz')
        robot_description = ParameterValue(Command(['cat ', urdf_path]), value_type=str)

        nodes = [
            Node(
                package='robot_state_publisher',
                executable='robot_state_publisher',
                name='robot_state_publisher',
                parameters=[{'robot_description': robot_description}],
            ),
            Node(
                package='rviz2',
                executable='rviz2',
                name='rviz2',
                output='screen',
                arguments=['-d', rviz_config],
            ),
        ]

        if mode == 'dance':
            nodes.append(
                Node(
                    package='intro_rover_control',
                    executable='dance',
                    name='dance',
                    output='screen',
                )
            )
            nodes.append(LogInfo(msg='Dance mode: publishing /joint_states from dance node'))
        else:
            nodes.append(
                LogInfo(
                    msg=(
                        'Manual mode: in another Ubuntu terminal run: '
                        'source /opt/ros/jazzy/setup.bash && '
                        'source ~/Software_Intro_Task_2026-2027/install/setup.bash && '
                        'ros2 run intro_rover_control manual_control'
                    )
                )
            )

        return nodes

    return LaunchDescription([mode_arg, OpaqueFunction(function=launch_setup)])
