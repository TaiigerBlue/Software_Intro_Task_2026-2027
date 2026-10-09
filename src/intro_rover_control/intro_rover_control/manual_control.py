"""Keyboard teleop that publishes sensor_msgs/JointState on /joint_states.

Controls (focus the terminal running this node):
  a / d     previous / next joint
  w / s     increase / decrease selected joint (radians)
  r         reset all joints to 0
  q         quit
"""

import sys
import termios
import threading
import tty

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import JointState

from intro_rover_control.joint_names import JOINT_NAMES


class ManualControl(Node):
    def __init__(self):
        super().__init__('manual_control')
        self.publisher_ = self.create_publisher(JointState, 'joint_states', 10)
        self.positions = [0.0] * len(JOINT_NAMES)
        self.index = 0
        self.step = 0.1  # rad per keypress
        self.create_timer(0.05, self.publish_state)  # 20 Hz
        self.get_logger().info(
            'Manual control ready. a/d=joint, w/s=move, r=reset, q=quit'
        )
        self.get_logger().info(f'Selected: {JOINT_NAMES[self.index]}')

    def publish_state(self):
        msg = JointState()
        msg.header.stamp = self.get_clock().now().to_msg()
        msg.name = list(JOINT_NAMES)
        msg.position = list(self.positions)
        self.publisher_.publish(msg)

    def handle_key(self, key: str) -> bool:
        """Return False to shut down."""
        if key in ('q', 'Q'):
            return False
        if key in ('a', 'A'):
            self.index = (self.index - 1) % len(JOINT_NAMES)
            self.get_logger().info(f'Selected: {JOINT_NAMES[self.index]}')
        elif key in ('d', 'D'):
            self.index = (self.index + 1) % len(JOINT_NAMES)
            self.get_logger().info(f'Selected: {JOINT_NAMES[self.index]}')
        elif key in ('w', 'W'):
            self.positions[self.index] += self.step
            self.get_logger().info(
                f'{JOINT_NAMES[self.index]} = {self.positions[self.index]:.2f} rad'
            )
        elif key in ('s', 'S'):
            self.positions[self.index] -= self.step
            self.get_logger().info(
                f'{JOINT_NAMES[self.index]} = {self.positions[self.index]:.2f} rad'
            )
        elif key in ('r', 'R'):
            self.positions = [0.0] * len(JOINT_NAMES)
            self.get_logger().info('Reset all joints to 0')
        return True


def _keyboard_loop(node: ManualControl, stop_event: threading.Event):
    fd = sys.stdin.fileno()
    old = termios.tcgetattr(fd)
    try:
        tty.setcbreak(fd)
        while rclpy.ok() and not stop_event.is_set():
            ch = sys.stdin.read(1)
            if not node.handle_key(ch):
                stop_event.set()
                break
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old)


def main(args=None):
    rclpy.init(args=args)
    node = ManualControl()
    stop_event = threading.Event()
    thread = threading.Thread(
        target=_keyboard_loop, args=(node, stop_event), daemon=True
    )
    thread.start()
    try:
        while rclpy.ok() and not stop_event.is_set():
            rclpy.spin_once(node, timeout_sec=0.1)
    except KeyboardInterrupt:
        pass
    finally:
        stop_event.set()
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
