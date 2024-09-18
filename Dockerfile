FROM nvidia/cuda:11.8.0-runtime-ubuntu20.04 as cuda-base
FROM python:3.9
ENV PYTHONDONTWRITEBYTECODE=1

RUN apt-get update && apt-get install -y \
    curl \
    ca-certificates \
    sudo \
    bzip2 \
    libx11-6 \
    vim \
    build-essential \
    screen \
    unoconv \
    ffmpeg \
    libsndfile1 \
    rubberband-cli \
    && rm -rf /var/lib/apt/lists/*

## CUDA Home
#COPY --from=cuda-base /usr/local/cuda /usr/local/cuda
#COPY --from=cuda-base /usr/local/cuda-11.8 /usr/local/cuda-11.8
## CUdnn Home
##COPY --from=cuda-base /usr/lib/x86_64-linux-gnu /usr/lib/x86_64-linux-gnu
#
#ENV PATH=/usr/local/cuda/bin:${PATH}
#ENV LD_LIBRARY_PATH=/usr/local/cuda/lib64:/usr/local/cuda-11.8/targets/x86_64-linux/lib:/usr/local/lib/python3.9/site-packages/torch/lib:${LD_LIBRARY_PATH}

WORKDIR /app

COPY requirements.txt .
RUN python3 -m pip install --upgrade pip
RUN pip install --no-cache-dir ninja
RUN pip3 install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121
RUN pip3 install natten==0.17.1+torch240cu118 -f https://shi-labs.com/natten/wheels
RUN pip install --no-cache-dir -r requirements.txt
RUN pip uninstall -y pysoundfile soundfile
RUN pip install soundfile
RUN apt-get clean autoclean && apt-get autoremove --yes && rm -rf /var/lib/{apt,dpkg,cache,log}/

COPY . /app

CMD ["bash"]