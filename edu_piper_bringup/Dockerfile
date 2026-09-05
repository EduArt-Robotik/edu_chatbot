ARG BASE_IMAGE=edu_ros_base:latest
FROM ${BASE_IMAGE} AS deps

SHELL ["/bin/bash", "-c"]

USER root

# Copy sources and import dependencies via vcs
WORKDIR /root/ros2_ws
COPY edu_piper_bringup/dependencies.repos src/dependencies.repos
RUN vcs import src < src/dependencies.repos

# Install ROS dependencies
RUN apt-get update && \
    rosdep update --include-eol-distros && \
    rosdep install --from-paths src --ignore-src -r -y && \
    rm -rf /var/lib/apt/lists/*

# Build the workspace with colcon
FROM deps AS builder
ARG CMAKE_BUILD_TYPE=Release

RUN source /opt/ros/${ROS_DISTRO}/setup.bash && \
    colcon build --symlink-install --cmake-args -DCMAKE_BUILD_TYPE=${CMAKE_BUILD_TYPE}

# Copy and build edu_piper_bringup package after the rest of the workspace to avoid rebuilding the entire workspace if edu_piper_bringup changes
COPY edu_piper_bringup /root/ros2_ws/edu_piper_bringup
RUN source /opt/ros/${ROS_DISTRO}/setup.bash && \
    colcon build --packages-select edu_piper_bringup --symlink-install --cmake-args -DCMAKE_BUILD_TYPE=${CMAKE_BUILD_TYPE}

FROM builder AS final

# Source the workspace on login
RUN echo "source /root/ros2_ws/install/setup.bash" >> ~/.bashrc

# Activate color output in terminal
RUN echo "export TERM=xterm-256color" >> /root/.bashrc \
  && echo "export PS1=\"\[\e[96m\]PIPER \[\e[0m\]\${debian_chroot:+(\$debian_chroot)}\[\e[32;1m\]\u@\h\[\e[0m\]:\[\e[34;1m\]\w \$\[\e[0m\]\"" >> /root/.bashrc

ENV TERM=xterm-256color
ENV color_prompt=yes

CMD ["bash"]
