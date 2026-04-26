docker buildx create --name multiarch --use

# 2. 登录 DockerHub
docker login

# 3. 构建并推送多架构镜像
docker buildx build --platform linux/amd64,linux/arm64 -t chyengjason/ibkrweb:latest --push .