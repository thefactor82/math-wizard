FROM python:3.11

RUN apt-get update && \
    apt-get install -y \
    git zip unzip openjdk-17-jdk wget \
    libffi-dev libssl-dev \
    python3-pip \
    build-essential \
    autoconf \
    automake \
    libtool \
    pkg-config \
    zlib1g-dev \
    libncurses5-dev \
    libsqlite3-dev \
    libgdbm-dev \
    libbz2-dev \
    libreadline-dev \
    liblzma-dev \
    libncursesw5-dev \
    libgdbm-compat-dev \
    libxml2-dev \
    libxslt1-dev \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --upgrade pip setuptools cython buildozer

ENV PATH="/root/.buildozer/android/platform/android-sdk/platform-tools/:$PATH"

WORKDIR /app

