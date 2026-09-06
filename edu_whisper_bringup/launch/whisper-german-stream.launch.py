import os
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from ament_index_python.packages import get_package_share_directory


def generate_launch_description():

    config_dir = os.path.join(get_package_share_directory("edu_whisper_bringup"), "config")

    return LaunchDescription(
        [
            IncludeLaunchDescription(
                PythonLaunchDescriptionSource(
                    os.path.join(
                        get_package_share_directory("edu_whisper_bringup"),
                        "launch",
                        "whisper.launch.py",
                    )
                ),
                launch_arguments={
                    "stream": "True",
                    "whisper_params_file": os.path.join(
                        config_dir, "whisper_german_stream.yaml"
                    ),
                }.items(),
            )
        ]
    )
