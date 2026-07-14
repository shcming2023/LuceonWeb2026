FROM python:3.12.13-slim@sha256:64695412729fbe8cf054511723820c82bbe5a077d4a6b4070cd4a7225d3422ce

ARG VERSION=dev
ARG VCS_REF=unknown
ARG SOURCE_URL=https://github.com/shcming2023/LuceonWeb2026
LABEL org.opencontainers.image.title="LuceonWeb2026 backend and Worker" \
      org.opencontainers.image.version=$VERSION \
      org.opencontainers.image.revision=$VCS_REF \
      org.opencontainers.image.source=$SOURCE_URL

# Install libgl for opencv support & Noto fonts for Chinese characters
RUN apt-get update && \
    apt-get install -y \
        fonts-noto-core \
        fonts-noto-cjk \
        fontconfig \
        chromium \
        docker.io \
        qpdf \
        tesseract-ocr \
        libgl1 \
        libglib2.0-0 && \
    fc-cache -fv && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

# 复制依赖文件
COPY requirements.txt .

# 安装 Python 依赖
RUN python3 -m pip install -U -r requirements.txt && \
    python3 -m pip freeze --all > /app/pip-freeze.txt && \
    python3 -m pip cache purge

# 复制应用代码和启动脚本
COPY . .
RUN chmod +x /app/entrypoint.sh

# 设置入口点
ENTRYPOINT ["/app/entrypoint.sh"]

HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=5 \
    CMD python3 -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/api/system/health', timeout=3)"

# 启动命令
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"] 
