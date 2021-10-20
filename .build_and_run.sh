docker build . -t learney-backend
docker run -p 8000:8000 -v `pwd`:/app -e PYTHONUNBUFFERED=1 learney-backend
