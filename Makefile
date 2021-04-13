MKFILE_PATH := $(abspath $(lastword $(MAKEFILE_LIST)))
CURRENT_DIR := $(notdir $(patsubst %/,%,$(dir $(MKFILE_PATH))))

DOCKER_IMAGE := ${CURRENT_DIR}
DOCKER_CONTAINER := ${CURRENT_DIR}

ADDITIONAL_OPTIONS := ""
DOCKER_RUN_CMD = \
	if [ $$(docker ps -q -f name=${DOCKER_CONTAINER}) ]; then \
                docker kill --signal SIGINT ${DOCKER_CONTAINER}; \
	fi; \
        if [ $$(docker ps --all -q -f name=${DOCKER_CONTAINER}) ]; then \
                docker rm -f ${DOCKER_CONTAINER}; \
        fi; \
	docker run \
		--init \
		--name ${DOCKER_CONTAINER} \
		-v ${PWD}/data:/app/data \
		--user $$(id -u):$$(id -g) \
		$${ADDITIONAL_OPTIONS} \
		${DOCKER_IMAGE}



.PHONY: list
vars:
	echo Docker image: ${DOCKER_IMAGE}

build:
	docker build . -t ${DOCKER_IMAGE}

run-it:
	export ADDITIONAL_OPTIONS="-it --rm"; \
	${DOCKER_RUN_CMD}

run-daemon:
	export ADDITIONAL_OPTIONS="-d --restart=always"; \
        ${DOCKER_RUN_CMD}

stop:
	if [ $$(docker ps -q -f name=${DOCKER_CONTAINER}) ]; then \
                docker kill --signal SIGINT ${DOCKER_CONTAINER}; \
        fi

