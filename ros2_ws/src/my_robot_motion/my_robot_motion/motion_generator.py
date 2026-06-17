import rclpy
from rclpy.node import Node
from sensor_msgs.msg import JointState
from std_msgs.msg import Header

class MotionGenerator(Node):
    def __init__(self):
        super().__init__('motion_generator')
        self.publisher_ = self.create_publisher(JointState, '/joint_states', 10)
        timer_period = 0.05  # 50 milliseconds (20 Hz)
        self.timer = self.create_timer(timer_period, self.timer_callback)
        
        # Define 5 keyframes (configurations) in joint space
        # Joint order: joint_1, joint_2, joint_3, left_finger_joint, right_finger_joint
        self.keyframes = [
            [0.0, 0.0, 0.0, 0.0, 0.0],
            [1.0, 0.5, -0.5, 0.02, 0.02],
            [-1.0, 1.0, -1.0, 0.04, 0.04],
            [0.0, -0.5, 0.5, 0.01, 0.01],
            [2.0, 0.0, 1.0, 0.0, 0.0]
        ]
        self.joint_names = [
            'joint_1',
            'joint_2',
            'joint_3',
            'left_finger_joint',
            'right_finger_joint'
        ]
        
        self.transition_time = 3.0  # seconds to transition between keyframes
        self.dt = timer_period
        self.elapsed_time = 0.0
        self.current_keyframe_idx = 0
        
        self.get_logger().info('Motion Generator node has been initialized. Publishing smooth joint trajectories.')
        
    def timer_callback(self):
        # Determine next keyframe index
        next_keyframe_idx = (self.current_keyframe_idx + 1) % len(self.keyframes)
        
        start_config = self.keyframes[self.current_keyframe_idx]
        end_config = self.keyframes[next_keyframe_idx]
        
        # Calculate interpolation factor (0.0 to 1.0)
        alpha = self.elapsed_time / self.transition_time
        if alpha > 1.0:
            alpha = 1.0
            
        # Linear interpolation
        current_positions = []
        for start_pos, end_pos in zip(start_config, end_config):
            pos = start_pos + (end_pos - start_pos) * alpha
            current_positions.append(pos)
            
        # Create and publish JointState message
        msg = JointState()
        msg.header = Header()
        msg.header.stamp = self.get_clock().now().to_msg()
        msg.name = self.joint_names
        msg.position = current_positions
        msg.velocity = []
        msg.effort = []
        
        self.publisher_.publish(msg)
        
        # Update elapsed time
        self.elapsed_time += self.dt
        if self.elapsed_time >= self.transition_time:
            self.elapsed_time = 0.0
            self.current_keyframe_idx = next_keyframe_idx

def main(args=None):
    rclpy.init(args=args)
    motion_generator = MotionGenerator()
    try:
        rclpy.spin(motion_generator)
    except KeyboardInterrupt:
        pass
    finally:
        motion_generator.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
