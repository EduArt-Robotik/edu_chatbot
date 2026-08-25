import os
from launch import LaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.actions import IncludeLaunchDescription
from ament_index_python.packages import get_package_share_directory


def generate_launch_description():

    return LaunchDescription(
        [
            IncludeLaunchDescription(
                PythonLaunchDescriptionSource(
                    os.path.join(
                        get_package_share_directory("edu_piper_bringup"),
                        "launch",
                        "piper.launch.py",
                    )
                ),
                launch_arguments={
                    "piper_params_file": os.path.join(
                        get_package_share_directory("edu_piper_bringup"),
                        "config",
                        "piper_german.yaml",
                    ),
                }.items(),
            )
        ]
    )
