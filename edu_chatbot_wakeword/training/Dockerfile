FROM nvidia/cuda:13.3.1-cudnn-runtime-ubuntu26.04 AS base

# Install packages
RUN apt-get update && \
    export DEBIAN_FRONTEND=noninteractive && \
    apt-get install -y \
    git \
    python3-pip \
    python3-dev \
    portaudio19-dev \
    espeak-ng \
    libsndfile1 \
    ffmpeg \
    sox

RUN apt-get update && \
  export DEBIAN_FRONTEND=noninteractive && \
  apt-get install -y \
  build-essential && \
  rm -rf /var/lib/apt/lists/*

RUN pip install --break-system-packages --ignore-installed \
  openwakeword \
  livekit-wakeword[train,eval,export]

# Enable color on command prompt
ENV TERM=xterm-256color
ENV color_prompt=yes