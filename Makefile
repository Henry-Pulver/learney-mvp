pretty: black pre-commit

pc:
	pre-commit run --all

black:
	black .

build:
	docker build . -t learney-backend

run:
	docker build . -t learney-backend
	docker run -p 8000:8000 -v `pwd`:/app -e PYTHONUNBUFFERED=1 learney-backend

test:
	docker build . -t learney-backend
	docker build . -f ./docker/Dockerfile.test -t learney-test
	docker run -p 8000:8000 -v `pwd`:/app -e PYTHONUNBUFFERED=1 learney-test

staging: test
	eb deploy Staging-Learneybackend-env

prod: test
	eb deploy Learneyapp-env
