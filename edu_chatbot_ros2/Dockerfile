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
#RUN apt-get update \
# && apt-get install -y --no-install-recommends

# Save some space in the final image
RUN apt-get clean && rm -rf /var/lib/apt/lists/*

# User space configuration
USER $USER

# Activate color output in terminal
RUN echo "export ENV TERM=xterm-256color" >> /home/$USER/.bashrc \
  && echo "export PS1=\"\[\e[96m\]DOCKER \[\e[0m\]${debian_chroot:+($debian_chroot)}\[\e[32;1m\]\u@\h\[\e[0m\]:\[\e[34;1m\]\w \$\[\e[0m\]\"" >> /home/$USER/.bashrc

ENV TERM=xterm-256color
ENV color_prompt=yes

# Source ROS files
RUN echo "source /opt/ros/jazzy/setup.bash" >> /home/$USER/.bashrc

# Add entry point
#COPY --chown=$USER entrypoint /home/$USER/
#RUN chmod a+x /home/$USER/entrypoint
#ENTRYPOINT [ "/home/user/entrypoint" ]