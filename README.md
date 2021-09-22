# Learney
MVP for Learney (now live here: https://app.learney.me) - the personalised learning platform that lets you take your own path.

Read about it here: https://henry-pulver.medium.com/the-future-of-online-learning-for-knowledge-work-cb9608f9bc1a.

Sign up to be an early-access user here: https://learney.me.

## Development

Use Python 3.7 or later.

```commandline
python --version
```

Before committing changes, make sure to install pre-commit as follows:

```commandline
pip install pre-commit
pre-commit install
```

### Running Learney locally

#### Requirements

1. Have a working installation of `docker`. This means you are able to run `docker` containers. To test this is the case, try running:

```commandline
docker run hello-world
```
(if that doesn't work, try `sudo docker run hello-world`)

2. Have access to the locally-stored secret files (ask Henry for these if you don't have them already).

#### Running

From the root of this repo, simply run (add `sudo` at the start if necessary):

```commandline
./.build_and_run.sh
```

Now try visiting `http://0.0.0.0:8000/` (or try `http://localhost:8000/` if `0.0.0.0` isn't working!) and if you see a Learney map there, you're done!

#### Running tests

It's easiest to run tests in the Docker container.
To do this, go to `Dockerfile`, comment out the last uncommented line, starting with `CMD` and uncomment
the very bottom commented line which also starts with `CMD`.

Then, assuming you've set up Docker and have the secrets correctly (see `Requirements` section above if not), simply run:
```commandline
./.build_and_run.sh
```
