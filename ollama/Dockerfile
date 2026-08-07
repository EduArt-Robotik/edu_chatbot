FROM ollama/ollama


RUN export DEBIAN_FRONTEND=noninteractive
RUN apt-get update \
 && apt-get install -y --no-install-recommends \
  curl \
  && apt-get clean \
  && rm -rf /var/lib/apt/lists/*

# Activate color output in terminal
RUN echo "export TERM=xterm-256color" >> /root/.bashrc \
  && echo "export PS1=\"\[\e[96m\]OLLAMA \[\e[0m\]\${debian_chroot:+(\$debian_chroot)}\[\e[32;1m\]\u@\h\[\e[0m\]:\[\e[34;1m\]\w \$\[\e[0m\]\"" >> /root/.bashrc

ENV TERM=xterm-256color
ENV color_prompt=yes
