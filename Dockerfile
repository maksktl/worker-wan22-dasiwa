# DaSiWa I2V Worker - Optimized Dockerfile
FROM wlsdml1114/multitalk-base:1.7 AS runtime

# Install Python dependencies
RUN pip install -U "huggingface_hub[hf_transfer]" && \
    pip install runpod websocket-client

# Install dependencies for model downloading
COPY builder/requirements.txt /requirements.txt
RUN pip install -r /requirements.txt && rm /requirements.txt

WORKDIR /

# Clone ComfyUI and install base requirements
RUN git clone --depth 1 https://github.com/comfyanonymous/ComfyUI.git && \
    cd /ComfyUI && \
    pip install -r requirements.txt

# Install only required custom nodes for DaSiWa I2V
# 1. WanVideoWrapper - обязателен для Wan 2.2
# 2. VideoHelperSuite - для VHS_VideoCombine (видео вывод)
# 3. KJNodes - может быть нужен для некоторых нод
RUN cd /ComfyUI/custom_nodes && \
    git clone --depth 1 https://github.com/kijai/ComfyUI-WanVideoWrapper && \
    cd ComfyUI-WanVideoWrapper && \
    pip install -r requirements.txt && \
    cd .. && \
    git clone --depth 1 https://github.com/Kosinkadink/ComfyUI-VideoHelperSuite && \
    cd ComfyUI-VideoHelperSuite && \
    pip install -r requirements.txt && \
    cd .. && \
    git clone --depth 1 https://github.com/kijai/ComfyUI-KJNodes && \
    cd ComfyUI-KJNodes && \
    pip install -r requirements.txt

# Download all models from Yandex.Disk
COPY builder/cache_models.py /cache_models.py
RUN python3 /cache_models.py && rm /cache_models.py

COPY . .
COPY extra_model_paths.yaml /ComfyUI/extra_model_paths.yaml
COPY dasiwa_i2v_api.json /dasiwa_i2v_api.json
RUN chmod +x /entrypoint.sh

CMD ["/entrypoint.sh"]