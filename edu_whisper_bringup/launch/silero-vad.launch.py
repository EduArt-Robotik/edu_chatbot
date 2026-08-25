import os
from launch_ros.actions import Node
from launch import LaunchDescription
from launch.substitutions import LaunchConfiguration
from ament_index_python.packages import get_package_share_directory


def generate_launch_description():

    config_dir = os.path.join(get_package_share_directory("edu_whisper_bringup"), "config")

    silero_vad_params_file = LaunchConfiguration(
        "silero_vad_params_file",
        default=os.path.join(config_dir, "silero_vad.yaml"),
    )

    return LaunchDescription(
        [
            Node(
                package="whisper_ros",
                executable="silero_vad_node",
                name="silero_vad_node",
                namespace="whisper",
                parameters=[silero_vad_params_file],
                remappings=[("audio", "/audio/in")],
            ),
        ]
    )
