import os
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription, TimerAction
from launch.launch_description_sources import AnyLaunchDescriptionSource
from launch_ros.actions import Node
from ament_index_python.packages import get_package_share_directory
from moveit_configs_builder import MoveItConfigsBuilder

def generate_launch_description():
    gazebo_pkg = get_package_share_directory('my_robot_gazebo')
    moveit_pkg = get_package_share_directory('my_robot_moveit_config')

    # Start simulator (starts Gazebo + parameter bridge)
    start_simulator = IncludeLaunchDescription(
        AnyLaunchDescriptionSource(
            os.path.join(gazebo_pkg, 'launch', 'start_simulator.launch.xml')
        )
    )

    # Spawn robot (delayed slightly to ensure Gazebo is ready)
    spawn_robot = TimerAction(
        period=5.0,
        actions=[
            IncludeLaunchDescription(
                AnyLaunchDescriptionSource(
                    os.path.join(gazebo_pkg, 'launch', 'spawn_robot.launch.xml')
                )
            )
        ]
    )

    # MoveIt Config with use_sim_time=True
    moveit_config = (
        MoveItConfigsBuilder("my_robot", package_name="my_robot_moveit_config")
        .robot_description(file_path="urdf/my_robot.urdf", package_name="my_robot_description")
        .robot_description_semantic(file_path="config/my_robot.srdf")
        .trajectory_execution(file_path="config/moveit_controllers.yaml")
        .planning_pipelines(pipelines=["ompl"])
        .to_moveit_configs()
    )

    moveit_params = moveit_config.to_dict()
    moveit_params['use_sim_time'] = True

    # Start MoveGroup
    run_move_group_node = Node(
        package="moveit_ros_move_group",
        executable="move_group",
        output="screen",
        parameters=[moveit_params],
    )

    # RViz2 with use_sim_time=True and MoveIt config
    rviz_base = os.path.join(moveit_pkg, "config", "moveit.rviz")
    run_rviz_node = Node(
        package="rviz2",
        executable="rviz2",
        name="rviz2",
        output="log",
        arguments=["-d", rviz_base],
        parameters=[
            moveit_config.robot_description,
            moveit_config.robot_description_semantic,
            moveit_config.planning_pipelines,
            moveit_config.robot_description_kinematics,
            {'use_sim_time': True}
        ],
    )

    # Delayed MoveIt to ensure robot is spawned and controllers are ready
    start_moveit = TimerAction(
        period=10.0,
        actions=[
            run_move_group_node,
            run_rviz_node
        ]
    )

    return LaunchDescription([
        start_simulator,
        spawn_robot,
        start_moveit
    ])
