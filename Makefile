pretty: black pre-commit

pc:
	pre-commit run --all

black:
	black .

build:
	docker build . -t learney-backend

run-local:
	cd src && PATH=`pwd`/src:${PATH} python manage.py migrate && python manage.py runserver 0.0.0.0:8000

run:
	docker build . -t learney-backend
	docker run -p 8000:8000 -v `pwd`:/app -e PYTHONUNBUFFERED=1 -e USE_STAGING_DB=1 learney-backend

test:
	docker build . -t learney-backend
	docker build . -f ./docker/Dockerfile.test -t learney-test
	docker run -p 8000:8000 -v `pwd`:/app -e PYTHONUNBUFFERED=1 learney-test

staging: test
	eb deploy Staging-Learneybackend-env

prod: test
	eb deploy Learneyapp-env
