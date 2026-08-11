FROM ros:jazzy-ros-base

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
    ollama \
    chromadb \
    pypdf2 \
    pymupdf \
    python-docx \
    python-pptx \
    llama-index \
    llama-index-readers-file \
    llama-index-embeddings-ollama \
    llama-index-vector-stores-chroma

RUN apt-get clean && rm -rf /var/lib/apt/lists/*

# User space configuration
USER $USER

# Activate color output in terminal
RUN echo "export TERM=xterm-256color" >> /home/$USER/.bashrc \
  && echo "export PS1=\"\[\e[96m\]CHATBOT \[\e[0m\]${debian_chroot:+($debian_chroot)}\[\e[32;1m\]\u@\h\[\e[0m\]:\[\e[34;1m\]\w \$\[\e[0m\]\"" >> /home/$USER/.bashrc

ENV TERM=xterm-256color
ENV color_prompt=yes

# Set up ROS workspace and build the package
RUN mkdir -p /home/$USER/ros2_ws/src
WORKDIR /home/$USER/ros2_ws
COPY --chown=$USER . /home/$USER/ros2_ws/src/edu_chatbot_ros2
RUN bash -c "source /opt/ros/$ROS_DISTRO/setup.bash && colcon build --symlink-install"

# Source ROS files
RUN echo "source /opt/ros/$ROS_DISTRO/setup.bash" >> /home/$USER/.bashrc
RUN echo "source ~/ros2_ws/install/setup.bash" >> /home/$USER/.bashrc

# Add entry point
COPY --chown=$USER ./docker/entrypoint /home/$USER/
RUN chmod a+x /home/$USER/entrypoint
ENTRYPOINT [ "/home/user/entrypoint" ]