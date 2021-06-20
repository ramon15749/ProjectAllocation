# Project Allocation

## Quickstart

Clone the repository, cd into it and run

```bash
sudo docker-compose build
sudo docker-compose up -d
```

The front-end GUI can be accessed via localhost:8080 while API endpoints is accessible via localhost:5050

## Docker containers

For each component of this project a separate docker container is afforded, controlled ("orchestrated") by docker-compose.

For the sake of simplicity, the same image is used for the separate containers. The image stems from [python:3.6-stretch](https://hub.docker.com/_/python), which contains a debian 9 linux. Instead of debian a more lightweight image like alpine could also be used.

The are four containers in this project at work.

- web: where are Flask web application runs
- worker: where the RQ worker process runs
- dashboard: where the rq-dashboard monitoring web application runs
- redis: containing the redis server

The image is build from `app/Dockerfile`. This one Dockerfile includes all the necessary python components and their dependencies from `app/requirements.txt`. Because we're using the same image for multiple purposes like the flask application, the rqworker and the rq-dashboard it has to contain all of these components. In an advanced use case you want to build different images which are tailored to their individual purposes.

For the redis server container the out-of-the-box [redis](https://hub.docker.com/_/redis) image is used - not much use building a image for redis by ourself.

## docker-compose in development and production

To give an example of a development workflow with docker-compose two configuration files are used. A feature of docker-compose is to have multiple configuration files layered on top of each other where later files override settings from previous ones.

In this project the default `docker-compose.yml` runs the application in a production like manner while the additional `docker-compose-development.yml` runs the application in a way more suitable for development. "Production like" does not actual mean to run it like this on the internet, you would at least need something like a nginx thrown in, but it should give ideas on how to manage different environments with docker-compose.

To run the application in a production like manner:

```
sudo docker-compose up -d
```

This will start the docker containers defined in docker-compose.yml. It is equivalent to running `docker-compose -f docker-compose.yml up -d`

To start the application in a development manner:

```
docker-compose -f docker-compose.yml -f docker-compose-development.yml up -d
```

This will read the configuration from docker-compose.yml and include the changes stated in docker-compose-development.yml before running the containers. By this way we alter the configuration given in the first file by the configuration from the second.

## docker-compose.yml

docker-compose.yml defines a service made up of four containers. A service is a group of containers and additional settings that make up an docker-compose application.

```yaml
services:
  web:
    build: ./app
    image: master-image
    command: /usr/local/bin/gunicorn -b :5000 main:app
    …
  worker:
    image: master-image
    command: rqworker --name worker --url redis://redis:6379/0
    …
  dashboard:
    image: master-image
    command: rq-dashboard --port 5555 --redis-url redis://redis:6379/0
    …
  redis:
    image: redis
```

### Reuse of images

In order to use the same image on multiple containers we have one container build it, name it, store it, and then reuse it on the other containers. `build: :/app` tells docker-compose to build an image from the Dockerfile it finds under the ./app directory. The subsequent `image: master-image` tells it to store that image under the name _master-image_. The `image: master-image` lines on the other containers refer to that image by its name. The choice of building the image in the context of the _web_ container is arbitrary, you could to this on anyone of the other containers.

Instead of reusing the same image we could have said `build: ./app` on all of the three containers and leave out the `image: master-image` lines. This would result in three individual but identical images being build.

However, we do specify a different _command:_ on each container. As we set up the image in the Dockerfile to be universaly usable, no specific command is run from there. Which means that if you would run the image outside of docker-compose on its own it would do nothing and just exit.

#### web container

On the _web_ container `command: /usr/local/bin/gunicorn -b :5000 main:app` tells docker-compose to run (in the container) the gunicorn web server. _-b :5000_ tells gunicorn to bind to (listen to) port 5000 on whatever IPs the container has. _main:app_ points gunicorn to the place where the flask application is. It in effect tells gunicorn to look for the python module _main_ in its working directory (which we set to _/app_ in the Dockerfile) and look for the variable _app_ which must be a valid flask application instance. Gunicorn with its dependencies and all the files that make up our web application have been copied into the image during the Dockerfile build process.

#### worker container

On the _worker_ container `command: rqworker --name worker --url redis://redis:6379/0` tells docker-compose to run a _rqworker_ process. _--url redis://redis:6379/0_ tells the worker where it finds the redis server from where it fetches the jobs to execute and sends back the results. As the same image is used, the working directory of the worker is also /app, which again contains a copy of the web application files placed into the image. The rqworker needs access to the _jobs.py_ file where it find the code to excecute jobs. After all rqworker is a python program that needs to have the python modules in reach which it is supposed to execute.

#### dashboard container

On the _dashboard_ container `command: rq-dashboard --port 5555 --redis-url redis://redis:6379/0` tells docker to run the rq-dashboard application. The application gets told were to open the web server port and where to find the redis server it should monitor. In the same way as with the web and worker container the working directory of the rq-dashboard app is set to /app where a copy of the web application files resides. But in this case it does not actually matter, rq-dashboard does not need access to flask or tasks.py files and would run just as fine in a different working directory.

#### redis container

For the _redis_ container we specify that we want to use a prebuild image from [Docker Hub](https://hub.docker.com/_/redis) rather than a self made one, for which a simple `image: redis` is sufficient. The default configuration of redis pretty much suits us, so we don't need to set any options.

### Networking

docker-compose automatically sets up local network for our service where the containers can talk to each other; usually in the 172.x.x.x range. It also ensures that containers can address each other by their names. That's why we can write redis://redis:6379 without knowing the actual IP of the redis container.

## docker-compose-development.yml

docker-compose-development.yml is the overlay configuration file with works in conjunction with docker-compose.yml, so it only states the changes to it.

```yaml
services:
  web:
    container_name: web
    environment:
      - FLASK_APP=main.py
      - FLASK_DEBUG=1
    volumes:
      - ./app:/app
    command: flask run --host=0.0.0.0

  worker:
     container_name: worker
     volumes:
      - ./app:/app
  …
```

One thing it does is to override _command:_ on the web container to use a different web server. Instead of gunicorn in docker-compose.yml it uses the web server bundled with flask:

```yaml
    command: flask run --host=0.0.0.0:
```

For the flask web server to work we also need to set some environment variables:

```
    environment:
      - FLASK_APP=main.py
      - FLASK_DEBUG=1
```

This tells flask where to find the application instance and activates debug mode.

Using the bundled flask web server is not recommended for production use, but has some advantages during development. It comes with a build in debugger and it will automatically reload when you make changes to the source files – a feature we utilize in our workflow.

### Container names

We also set _container_name:_ when in development. This allows for easy reference to a container in docker commands executed from the shell. In the docker command line arguments containers can either be referenced by their _container id_ or by their _container name_. Both of them have to be unique over all docker containers on a host and that's not just the ones from our project. Even though we specified web:, worker:, dashboard: and redis: in docker-compose.yml this will only be local to our service and for e.g. network name resolution, but they are not the final container names. Without the _container_name:_ option docker-compose will auto generate a name for every container and make sure it's unique.

For example

```
  web:
    container_name: web
```

assigns the name 'web' to the web container. Now we can e.g. inspect the logs by `docker-compose logs web` rather than `docker-compose logs myproject_web_1` or whatever name the container got auto assigned.

Explicitly naming containers however is not a good thing for production, as you might happen to have more than one called 'web' or 'redis' on the same host.

### Automatic reload on source file changes

The bundled flask development web server has the ability to auto reload itself when it detects a change to a source file. This comes in handy during development because you don't have manually restart the server to see the effect of the changes you've made. But as we are running the web server inside a container changes to files on the host file system e.g. in the _app/_ directory must affect files in the container. This is done by mounting the the _app/_ directory on the host to the _/app_ in the container.

```
  volumes: ./app:/app
```

Note that you can mount to a directory inside a container even when that directory is not empty. The mounted directory will shadow the contents of the target directory. In our case the /app directory already contains files that have been copied during the image build, but these files will be shadowed by the mounted directory.

Auto reload does not only work for the flask web server inside the web container. The rqworker will also use the latest version of a source files when it starts to execute a job. Because it will reload itself everytime it executes a job anyway (see the section about worker performance in the RQ documentation for details).

## Working with containers

Following the log of a specific container

```bash
sudo docker-compose logs -f web
```

Getting a shell in a container

```bash
sudo docker-compose exec -i -t web /bin/bash
```

Stopping containers and cleaning up

```bash
sudo docker-compose down --volumes
```
