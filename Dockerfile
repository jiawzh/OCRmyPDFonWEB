FROM jbarlow83/ocrmypdf-alpine:latest

# 添加镜像元数据
LABEL maintainer="Your Name <your.email@example.com>"
LABEL version="1.0"
LABEL description="OCRmyPDF Web Interface based on Alpine Linux"
LABEL org.opencontainers.image.title="OCRmyPDF Web"

# 设置环境变量
ENV PYTHONUNBUFFERED=1

# 安装基本系统依赖
RUN apk add --no-cache --update \
    python3 \
    py3-pip \
    python3-dev \
    build-base \
    libffi-dev \
    cmake \
    git \
    g++ \
    jpeg-dev \
    zlib-dev

# 创建应用目录
RUN mkdir -p /app
WORKDIR /app

# 创建并激活虚拟环境安装依赖
RUN python3 -m venv /app/venv
ENV PATH="/app/venv/bin:$PATH"
ENV VIRTUAL_ENV="/app/venv"

# 安装更轻量级的替代库，而不是使用streamlit
RUN /app/venv/bin/pip install --no-cache-dir flask flask-bootstrap pillow watchdog

# Copy language files
ENV TESSDATA_PREFIX=/usr/share/tessdata
COPY ./traineddata/chi_sim_vert.traineddata /usr/share/tessdata/chi_sim_vert.traineddata
COPY ./traineddata/chi_sim.traineddata /usr/share/tessdata/chi_sim.traineddata
COPY ./traineddata/eng.traineddata /usr/share/tessdata/eng.traineddata

# Copy application code
COPY server.py /app/

# Expose the port
EXPOSE 5000

# Set entry point
ENTRYPOINT ["/app/venv/bin/python", "server.py"]


