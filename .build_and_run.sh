docker build . -t learney
docker run -p 8000:8000 -e PYTHONUNBUFFERED=1 -v C:/Users/shahf/PycharmProjects/learney:/app/src/volume learney
