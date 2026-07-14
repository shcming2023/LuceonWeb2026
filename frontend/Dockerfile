FROM node:20-alpine@sha256:fb4cd12c85ee03686f6af5362a0b0d56d50c58a04632e6c0fb8363f609372293 AS builder
WORKDIR /app

# 先安装依赖后再复制源码可利用缓存
COPY package*.json ./
RUN npm ci --no-audit --no-fund

# 复制项目源码并构建静态资源
COPY . .
RUN npm run build

FROM nginx:alpine@sha256:54f2a904c251d5a34adf545a72d32515a15e08418dae0266e23be2e18c66fefa

ARG VERSION=dev
ARG VCS_REF=unknown
ARG SOURCE_URL=https://github.com/shcming2023/LuceonWeb2026
LABEL org.opencontainers.image.title="LuceonWeb2026 frontend" \
      org.opencontainers.image.version=$VERSION \
      org.opencontainers.image.revision=$VCS_REF \
      org.opencontainers.image.source=$SOURCE_URL

# 复制构建产物
COPY --from=builder /app/dist /usr/share/nginx/html

# 复制 nginx 配置
COPY nginx.conf /etc/nginx/nginx.conf

EXPOSE 80

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=5 \
    CMD wget -q -O /dev/null http://127.0.0.1/

CMD ["nginx", "-g", "daemon off;"]
