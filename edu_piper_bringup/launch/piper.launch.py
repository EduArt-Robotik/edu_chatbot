import os
from launch_ros.actions import Node
from launch import LaunchDescription
from launch.conditions import IfCondition
from launch.substitutions import LaunchConfiguration, PythonExpression
from ament_index_python.packages import get_package_share_directory


def generate_launch_description():

    config_dir = os.path.join(get_package_share_directory("edu_piper_bringup"), "config")

    piper_params_file = LaunchConfiguration(
        "piper_params_file",
        default=os.path.join(config_dir, "piper.yaml"),
    )

    audio_player_params_file = LaunchConfiguration(
        "audio_player_params_file",
        default=os.path.join(config_dir, "audio_player.yaml"),
    )

    return LaunchDescription(
        [
            Node(
                package="piper_ros",
                executable="piper_node",
                name="piper_node",
                namespace="piper",
                parameters=[piper_params_file],
                remappings=[("audio", "/audio/out")],
            ),
            Node(
                package="audio_common",
                executable="audio_player_node",
                name="player_node",
                namespace="audio",
                parameters=[audio_player_params_file],
                remappings=[("audio", "out")],
                condition=IfCondition(
                    PythonExpression(
                        [LaunchConfiguration("launch_audio_player", default="True")]
                    )
                ),
            ),
        ]
    )
