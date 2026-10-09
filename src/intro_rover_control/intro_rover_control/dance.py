"""Timed 'dance' that publishes JointState as a function of time."""

import math

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import JointState

from intro_rover_control.joint_names import JOINT_NAMES


class Dance(Node):
    def __init__(self):
        super().__init__('dance')
        self.publisher_ = self.create_publisher(JointState, 'joint_states', 10)
        self.t0 = self.get_clock().now()
        self.create_timer(0.05, self.tick)  # 20 Hz
        self.get_logger().info('Dance started — arm waves, wheels spin')

    def tick(self):
        t = (self.get_clock().now() - self.t0).nanoseconds * 1e-9
        positions = []
        for name in JOINT_NAMES:
            if name.endswith('_wheel'):
                # Continuous spin
                positions.append(t * 2.0)
            elif name.endswith('_swerve_yaw'):
                # Gentle steer wiggle
                positions.append(0.4 * math.sin(t))
            elif name == 'shoulder_yaw':
                positions.append(0.6 * math.sin(0.7 * t))
            elif name == 'shoulder_pitch':
                positions.append(0.5 * math.sin(0.9 * t + 0.5))
            elif name == 'elbow_pitch':
                positions.append(0.7 * math.sin(1.1 * t + 1.0))
            elif name == 'elbow_roll':
                positions.append(0.5 * math.sin(1.3 * t))
            elif name == 'wrist_pitch':
                positions.append(0.4 * math.sin(1.5 * t + 0.2))
            elif name == 'wrist_roll':
                positions.append(t * 1.5)
            else:
                positions.append(0.0)

        msg = JointState()
        msg.header.stamp = self.get_clock().now().to_msg()
        msg.name = list(JOINT_NAMES)
        msg.position = positions
        self.publisher_.publish(msg)


def main(args=None):
    rclpy.init(args=args)
    node = Dance()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
