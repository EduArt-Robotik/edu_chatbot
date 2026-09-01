FROM ros:jazzy-ros-base AS base

ENV USER=user
ENV DEBIAN_FRONTEND=noninteractive

# Rename the current user
RUN usermod -l $USER ubuntu \
  && groupmod -n $USER ubuntu \
  && usermod -d /home/$USER -m $USER \
  && usermod -c "user" $USER \
  && echo "$USER ALL=(ALL) NOPASSWD:ALL" > /etc/sudoers.d/$USER \
  && chmod 0440 /etc/sudoers.d/$USER

USER root

# Install packages
RUN apt-get update \
  && apt-get install -y --no-install-recommends \
  python3-pip

RUN pip install --break-system-packages --ignore-installed \
    rapidfuzz

RUN apt-get clean && rm -rf /var/lib/apt/lists/*

# Set permissions for the cache directory
RUN mkdir -p /home/user/data && chown -R user:user /home/user/data

# User space configuration
USER $USER

# Activate color output in terminal
RUN echo "export TERM=xterm-256color" >> /home/$USER/.bashrc \
  && echo "export PS1=\"\[\e[96m\]CHATBOT CONTROLLER \[\e[0m\]${debian_chroot:+($debian_chroot)}\[\e[32;1m\]\u@\h\[\e[0m\]:\[\e[34;1m\]\w \$\[\e[0m\]\"" >> /home/$USER/.bashrc

ENV TERM=xterm-256color
ENV color_prompt=yes

FROM base AS build

# Set up ROS workspace and build the package
RUN mkdir -p /home/$USER/ros2_ws/src
RUN mkdir -p /home/$USER/tmp

# Fetch external dependencies
WORKDIR /home/$USER/tmp
RUN git clone https://github.com/mgonzs13/whisper_ros.git -b 4.0.7 --depth 1
RUN cp -R /home/$USER/tmp/whisper_ros/whisper_msgs /home/$USER/ros2_ws/src/whisper_msgs

RUN git clone https://github.com/mgonzs13/audio_common.git -b 4.0.10 --depth 1
RUN cp -R /home/$USER/tmp/audio_common/audio_common_msgs /home/$USER/ros2_ws/src/audio_common_msgs

RUN git clone https://github.com/EduArt-Robotik/pib-backend.git -b feat/EduArt_chatbot --depth 1
RUN cp -R /home/$USER/tmp/pib-backend/ros_packages/datatypes /home/$USER/ros2_ws/src/datatypes
RUN rm -rf /home/$USER/tmp/

WORKDIR /home/$USER/ros2_ws
COPY --chown=$USER ./edu_chatbot_controller /home/$USER/ros2_ws/src/edu_chatbot_controller
COPY --chown=$USER ./edu_chatbot_msgs /home/$USER/ros2_ws/src/edu_chatbot_msgs

RUN bash -c "source /opt/ros/$ROS_DISTRO/setup.bash && colcon build --symlink-install"

FROM build AS final

# Source ROS files
RUN echo "source /opt/ros/$ROS_DISTRO/setup.bash" >> /home/$USER/.bashrc
RUN echo "source ~/ros2_ws/install/setup.bash" >> /home/$USER/.bashrc

# Add entry point
COPY --chown=$USER ./edu_chatbot_controller/docker/entrypoint /home/$USER/
RUN chmod a+x /home/$USER/entrypoint
ENTRYPOINT [ "/home/user/entrypoint" ]