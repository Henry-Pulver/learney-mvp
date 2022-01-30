pretty: black pre-commit

pc:
	pre-commit run --all

black:
	black .

build:
	docker build . -t learney-backend

run:
	./.build_and_run.sh

staging:
	eb deploy Staging-Learneybackend-env

prod:
	eb deploy Learneyapp-env
