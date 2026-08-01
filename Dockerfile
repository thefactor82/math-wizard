FROM python:3.11-slim

ENV USER="user"
ENV HOME_DIR="/home/${USER}"
ENV WORK_DIR="${HOME_DIR}/hostcwd" \
    SRC_DIR="${HOME_DIR}/src" \
    PATH="${HOME_DIR}/.local/bin:${PATH}"
ENV LANG="en_US.UTF-8" \
    LANGUAGE="en_US.UTF-8" \
    LC_ALL="en_US.UTF-8"

RUN apt update -qq > /dev/null \
    && DEBIAN_FRONTEND=noninteractive apt install -qq --yes --no-install-recommends \
    locales \
    autoconf \
    automake \
    build-essential \
    ccache \
    cmake \
    gettext \
    git \
    libffi-dev \
    libltdl-dev \
    libncurses5-dev \
    libncursesw5-dev \
    libssl-dev \
    libtinfo5 \
    libtool \
    openjdk-17-jdk \
    patch \
    pkg-config \
    sudo \
    unzip \
    zip \
    zlib1g-dev \
    && locale-gen en_US.UTF-8 \
    && apt-get purge -y --auto-remove -o APT::AutoRemove::RecommendsImportant=false \
    && rm -rf /var/lib/apt/lists/*

RUN useradd --create-home --shell /bin/bash ${USER}
RUN usermod -append --groups sudo ${USER}
RUN echo "%sudo ALL=(ALL) NOPASSWD: ALL" >> /etc/sudoers

# Cython must stay below 3.0 (p4a recipes break with Cython 3+).
RUN pip install --upgrade \
    buildozer \
    "Cython<0.30" \
    virtualenv \
    pip \
    appdirs \
    packaging \
    colorama \
    jinja2 \
    toml \
    build

USER ${USER}
WORKDIR ${WORK_DIR}

ENTRYPOINT ["buildozer"]
