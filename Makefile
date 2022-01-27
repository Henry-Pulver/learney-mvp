pretty: black pre-commit

pc:
	pre-commit run --all

black:
	black .

build:
	docker build . -t learney-backend

staging:
	eb deploy Staging-Learneybackend-env

prod:
	eb deploy Learneyapp-env
