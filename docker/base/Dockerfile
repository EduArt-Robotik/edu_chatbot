ARG ROS_DISTRO=jazzy

# ==============================================================================
# Base CPU stage: ROS 2 Jazzy, non-root user setup, audio and build tools
# ==============================================================================
FROM ros:${ROS_DISTRO}-ros-base AS base-cpu

ARG ROS_DISTRO
ENV USER=user
ENV DEBIAN_FRONTEND=noninteractive
ENV ROS_DISTRO=${ROS_DISTRO}

# Setup user with sudo rights
RUN usermod -l $USER ubuntu \
  && groupmod -n $USER ubuntu \
  && usermod -d /home/$USER -m $USER \
  && usermod -c "user" $USER \
  && echo "$USER ALL=(ALL) NOPASSWD:ALL" > /etc/sudoers.d/$USER \
  && chmod 0440 /etc/sudoers.d/$USER

USER root

# Install standard dependencies: Python build tools, ROS tools, audio utils
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3-pip \
    python3-vcstool \
    alsa-utils \
    libasound2-plugins \
    git \
    wget \
    ca-certificates \
    curl \
  && rosdep update --include-eol-distros \
  && apt-get clean \
  && rm -rf /var/lib/apt/lists/*

# Set permissions for the cache directory
RUN mkdir -p /home/$USER/data && chown -R $USER:$USER /home/$USER/data

# User space configuration
USER $USER
ENV TERM=xterm-256color
ENV color_prompt=yes

# ==============================================================================
# Base CUDA stage: base-cpu + NVIDIA CUDA Toolkit + cuDNN
# ==============================================================================
FROM base-cpu AS base-cuda

USER root

ARG CUDA_VERSION=13-2

RUN ARCH=$(dpkg --print-architecture) && \
    if [ "$ARCH" = "arm64" ]; then \
      CUDA_REPO_ARCH="sbsa"; \
    else \
      CUDA_REPO_ARCH="x86_64"; \
    fi && \
    wget -q https://developer.download.nvidia.com/compute/cuda/repos/ubuntu2404/${CUDA_REPO_ARCH}/cuda-keyring_1.1-1_all.deb && \
    dpkg -i cuda-keyring_1.1-1_all.deb && \
    rm cuda-keyring_1.1-1_all.deb && \
    apt-get update && \
    apt-get install -y --no-install-recommends \
      cuda-toolkit-${CUDA_VERSION} \
      libcudnn9-cuda-13 && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

ENV PATH=/usr/local/cuda/bin:${PATH}
ENV LD_LIBRARY_PATH=/usr/local/cuda/lib64:${LD_LIBRARY_PATH}

USER $USER

# ==============================================================================
# Base AMD stage: base-cpu (ROCm support placeholder if needed)
# ==============================================================================
FROM base-cpu AS base-amd
USER $USER
