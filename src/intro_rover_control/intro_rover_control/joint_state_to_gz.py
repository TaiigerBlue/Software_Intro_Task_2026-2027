"""Republish /joint_states as Float64 on /cmd_pos/<joint> for Gazebo Harmonic.

Part-4 nodes keep publishing sensor_msgs/JointState. Each Harmonic
JointPositionController plugin listens for gz.msgs.Double; ros_gz_bridge maps
ROS std_msgs/Float64 on /cmd_pos/<joint> to that Gazebo topic.
"""

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import JointState
from std_msgs.msg import Float64

from intro_rover_control.joint_names import JOINT_NAMES


class JointStateToGz(Node):
    def __init__(self):
        super().__init__('joint_state_to_gz')
        self._pubs = {
            name: self.create_publisher(Float64, f'cmd_pos/{name}', 10)
            for name in JOINT_NAMES
        }
        self.create_subscription(JointState, 'joint_states', self._on_js, 10)
        self.get_logger().info(
            f'Bridging /joint_states -> /cmd_pos/<joint> for {len(JOINT_NAMES)} joints'
        )

    def _on_js(self, msg: JointState):
        for name, position in zip(msg.name, msg.position):
            pub = self._pubs.get(name)
            if pub is None:
                continue
            out = Float64()
            out.data = float(position)
            pub.publish(out)


def main(args=None):
    rclpy.init(args=args)
    node = JointStateToGz()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == '__main__':
    main()
