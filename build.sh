docker buildx create --name multiarch --use --force 2>/dev/null || docker buildx use multiarch

docker login

docker buildx build --platform linux/amd64 -t chyengjason/ibkrweb:latest --push .