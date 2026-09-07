FROM edu_ros_base:latest AS base

USER root

# Install Python dependencies
RUN pip install --break-system-packages --ignore-installed \
    openwakeword

USER $USER

RUN echo "export PS1=\"\[\e[96m\]CHATBOT WAKEWORD \[\e[0m\]${debian_chroot:+($debian_chroot)}\[\e[32;1m\]\u@\h\[\e[0m\]:\[\e[34;1m\]\w \$\[\e[0m\]\"" >> /home/$USER/.bashrc

FROM base AS build

# Fetch external dependencies
WORKDIR /home/$USER/tmp
RUN git clone https://github.com/mgonzs13/audio_common.git -b 4.0.10 --depth 1 \
  && mkdir -p /home/$USER/ros2_ws/src \
  && cp -R /home/$USER/tmp/audio_common/audio_common_msgs /home/$USER/ros2_ws/src/audio_common_msgs \
  && rm -rf /home/$USER/tmp

WORKDIR /home/$USER/ros2_ws
COPY --chown=$USER ./edu_chatbot_wakeword /home/$USER/ros2_ws/src/edu_chatbot_wakeword

RUN bash -c "source /opt/ros/$ROS_DISTRO/setup.bash && colcon build --symlink-install"

FROM build AS final

# Source ROS files
RUN echo "source /opt/ros/$ROS_DISTRO/setup.bash" >> /home/$USER/.bashrc \
  && echo "source ~/ros2_ws/install/setup.bash" >> /home/$USER/.bashrc

# Add entry point
COPY --chown=$USER ./edu_chatbot_wakeword/docker/entrypoint /home/$USER/
RUN chmod a+x /home/$USER/entrypoint
ENTRYPOINT [ "/home/user/entrypoint" ]