ARG BASE_IMAGE=edu_ros_base:latest
FROM ${BASE_IMAGE} AS base

USER root

# Install Python packages for RAG
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

USER $USER

# Activate color output in terminal
RUN echo "export TERM=xterm-256color" >> /home/$USER/.bashrc \
  && echo "export PS1=\"\[\e[96m\]CHATBOT RAG \[\e[0m\]${debian_chroot:+($debian_chroot)}\[\e[32;1m\]\u@\h\[\e[0m\]:\[\e[34;1m\]\w \$\[\e[0m\]\"" >> /home/$USER/.bashrc

FROM base AS build

# Set up ROS workspace and build the package
RUN mkdir -p /home/$USER/ros2_ws/src
WORKDIR /home/$USER/ros2_ws
COPY --chown=$USER ./edu_chatbot_rag /home/$USER/ros2_ws/src/edu_chatbot_rag
COPY --chown=$USER ./edu_chatbot_msgs /home/$USER/ros2_ws/src/edu_chatbot_msgs

RUN bash -c "source /opt/ros/$ROS_DISTRO/setup.bash && colcon build --symlink-install"

FROM build AS final

# Source ROS files
RUN echo "source /opt/ros/$ROS_DISTRO/setup.bash" >> /home/$USER/.bashrc \
  && echo "source ~/ros2_ws/install/setup.bash" >> /home/$USER/.bashrc

# Add entry point
COPY --chown=$USER ./edu_chatbot_rag/docker/entrypoint /home/$USER/
RUN chmod a+x /home/$USER/entrypoint
ENTRYPOINT [ "/home/user/entrypoint" ]