FROM ros:jazzy-ros-core

USER ubuntu

# Install packages
RUN export DEBIAN_FRONTEND=noninteractive
#RUN apt-get update \
# && apt-get install -y --no-install-recommends

# Activate color output in terminal
RUN echo "export ENV TERM=xterm-256color" >> /home/$USER/.bashrc \
  && echo "export PS1=\"\[\e[96m\]DOCKER \[\e[0m\]${debian_chroot:+($debian_chroot)}\[\e[32;1m\]\u@\h\[\e[0m\]:\[\e[34;1m\]\w \$\[\e[0m\]\"" >> /home/$USER/.bashrc

ENV TERM=xterm-256color
ENV color_prompt=yes

# Source ROS files
RUN echo "source /opt/ros/jazzy/setup.bash" >> /home/$USER/.bashrc

# Save some space in the final image
RUN apt-get clean && rm -rf /var/lib/apt/lists/*

# Add entry point
#COPY --chown=$USER entrypoint /home/$USER/
#RUN chmod a+x /home/$USER/entrypoint
#ENTRYPOINT [ "/home/user/entrypoint" ]