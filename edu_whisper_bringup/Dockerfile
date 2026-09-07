ARG BASE_IMAGE=edu_ros_base:latest
FROM ${BASE_IMAGE} AS deps

SHELL ["/bin/bash", "-c"]

USER root

# Copy sources and import dependencies via vcs
WORKDIR /root/ros2_ws

COPY edu_whisper_bringup/dependencies.repos src/dependencies.repos
RUN vcs import src < src/dependencies.repos

COPY whisper_ros src/whisper_ros

# Install ROS dependencies
RUN apt-get update && \
    rosdep update --include-eol-distros && \
    rosdep install --from-paths src --ignore-src -r -y && \
    rm -rf /var/lib/apt/lists/*

# Fix: replace QoS settings for audio capturer node to make sure no audio chunks are lost
RUN grep -q 'rclcpp::SensorDataQoS()' \
        src/audio_common/audio_common/src/audio_common/audio_capturer_node.cpp \
    && sed -i \
        's/rclcpp::SensorDataQoS()/rclcpp::QoS(10).reliable()/' \
        src/audio_common/audio_common/src/audio_common/audio_capturer_node.cpp

# Build the workspace with colcon
FROM deps AS builder
ARG CMAKE_BUILD_TYPE=Release
ARG USE_CUDA=0

# whisper_cpp_vendor compiles ~20 minutes on jetson orin nano, building it separate to avoid rebuilding when other packages in the ws fail to build
RUN source /opt/ros/${ROS_DISTRO}/setup.bash && \
    if [ "$USE_CUDA" = "1" ]; then \
        colcon build --symlink-install --packages-select whisper_cpp_vendor --cmake-args -DGGML_CUDA=ON -DGGML_CUDA_NO_VMM=ON -DCMAKE_BUILD_TYPE=${CMAKE_BUILD_TYPE}; \
    else \
        colcon build --symlink-install --packages-select whisper_cpp_vendor --cmake-args -DGGML_CUDA=OFF -DCMAKE_BUILD_TYPE=${CMAKE_BUILD_TYPE}; \
    fi

RUN source /opt/ros/${ROS_DISTRO}/setup.bash && \
    if [ "$USE_CUDA" = "1" ]; then \
        colcon build --symlink-install --cmake-args -DGGML_CUDA=ON -DGGML_CUDA_NO_VMM=ON -DCMAKE_BUILD_TYPE=${CMAKE_BUILD_TYPE}; \
    else \
        colcon build --symlink-install --cmake-args -DCMAKE_BUILD_TYPE=${CMAKE_BUILD_TYPE}; \
    fi

# Copy and build edu_whisper_bringup package after the rest of the workspace to avoid rebuilding the entire workspace if edu_whisper_bringup changes
COPY edu_whisper_bringup /root/ros2_ws/edu_whisper_bringup
RUN source /opt/ros/${ROS_DISTRO}/setup.bash && \
    colcon build --packages-select edu_whisper_bringup --symlink-install --cmake-args -DCMAKE_BUILD_TYPE=${CMAKE_BUILD_TYPE}

FROM builder AS final

# Source the workspace on login
RUN echo "source /root/ros2_ws/install/setup.bash" >> ~/.bashrc

# Activate color output in terminal
RUN echo "export TERM=xterm-256color" >> /root/.bashrc \
  && echo "export PS1=\"\[\e[96m\]CHATBOT STT \[\e[0m\]\${debian_chroot:+(\$debian_chroot)}\[\e[32;1m\]\u@\h\[\e[0m\]:\[\e[34;1m\]\w \$\[\e[0m\]\"" >> /root/.bashrc

ENV TERM=xterm-256color
ENV color_prompt=yes

CMD ["bash"]
