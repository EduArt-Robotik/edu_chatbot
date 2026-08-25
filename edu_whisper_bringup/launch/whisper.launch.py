import os
from launch_ros.actions import Node
from launch import LaunchDescription
from launch.conditions import IfCondition, UnlessCondition
from launch.substitutions import LaunchConfiguration, PythonExpression
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from ament_index_python.packages import get_package_share_directory


def generate_launch_description():

    config_dir = os.path.join(get_package_share_directory("edu_whisper_bringup"), "config")

    stream_cmd = DeclareLaunchArgument(
        "stream",
        default_value="False",
        description="Whether to launch stream or server node",
    )

    whisper_params_file = LaunchConfiguration(
        "whisper_params_file",
        default=os.path.join(config_dir, "whisper.yaml"),
    )

    silero_vad_params_file = LaunchConfiguration(
        "silero_vad_params_file",
        default=os.path.join(config_dir, "silero_vad.yaml"),
    )

    audio_capturer_params_file = LaunchConfiguration(
        "audio_capturer_params_file",
        default=os.path.join(config_dir, "audio_capturer.yaml"),
    )

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
            stream_cmd,
            Node(
                package="whisper_ros",
                executable="whisper_server_node",
                name="whisper_node",
                namespace="whisper",
                parameters=[whisper_params_file],
                condition=UnlessCondition(
                    PythonExpression([LaunchConfiguration("stream")])
                ),
            ),
            Node(
                package="whisper_ros",
                executable="whisper_node",
                name="whisper_node",
                namespace="whisper",
                parameters=[whisper_params_file],
                condition=IfCondition(PythonExpression([LaunchConfiguration("stream")])),
            ),
            IncludeLaunchDescription(
                PythonLaunchDescriptionSource(
                    os.path.join(
                        get_package_share_directory("edu_whisper_bringup"),
                        "launch",
                        "silero-vad.launch.py",
                    )
                ),
                launch_arguments={
                    "silero_vad_params_file": silero_vad_params_file,
                }.items(),
            ),
            Node(
                package="audio_common",
                executable="audio_capturer_node",
                name="capturer_node",
                namespace="audio",
                parameters=[audio_capturer_params_file],
                remappings=[("audio", "in")],
                condition=IfCondition(
                    PythonExpression(
                        [LaunchConfiguration("launch_audio_capturer", default=True)]
                    )
                ),
            ),
        ]
    )
