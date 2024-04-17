all: help

##@ General

# The help target prints out all targets with their descriptions organized
# beneath their categories. The categories are represented by '##@' and the
# target descriptions by '##'. The awk commands is responsible for reading the
# entire set of makefiles included in this invocation, looking for lines of the
# file as xyz: ## something, and then pretty-format the target and help. Then,
# if there's a line with ##@ something, that gets pretty-printed as a category.
# More info on the usage of ANSI control characters for terminal formatting:
# https://en.wikipedia.org/wiki/ANSI_escape_code#SGR_parameters
# More info on the awk command:
# http://linuxcommand.org/lc3_adv_awk.php

help: ## Display this help.
	@awk 'BEGIN {FS = ":.*##"; printf "\nUsage:\n  make \033[36m<target>\033[0m\n"} /^[a-zA-Z_0-9-]+:.*?##/ { printf "      \033[36m%-15s\033[0m %s\n", $$1, $$2 } /^##@/ { printf "\n\033[1m%s\033[0m\n", substr($$0, 5) } ' $(MAKEFILE_LIST)

##@ Development


##@ Build

BUILD_DATE ?= $(shell date +%Y%m%d%H%M)
SHORT_COMMIT ?= $(shell git rev-parse --short HEAD)
COMMIT ?= $(shell git rev-parse HEAD)
DIRTY_BUILD ?= $(shell git diff --quiet && echo 'false' || echo 'true')
BASE_IMAGE_REPO ?= 647854334008.dkr.ecr.us-east-1.amazonaws.com/promptgpt-base
RUNTIME_IMAGE_REPO ?= 647854334008.dkr.ecr.us-east-1.amazonaws.com/promptgpt
IMAGE_TAG ?= $(BUILD_DATE)-$(SHORT_COMMIT)

.PHONY: base
base: ## Build base image
	docker buildx build \
		-f deploy/base.Dockerfile \
		--output=type=docker \
		--build-arg BUILD_DATE=$(BUILD_DATE) \
		--build-arg COMMIT=$(COMMIT) \
		--tag $(BASE_IMAGE_REPO):$(IMAGE_TAG) .

.PHONY: build
build: ## Build runtime image
	echo "Build Runtime Image: ${RUNTIME_IMAGE_REPO}:${IMAGE_TAG}"
	docker buildx build \
		-f deploy/Dockerfile \
		--no-cache \
		--output=type=docker \
		--build-arg BUILD_DATE=$(BUILD_DATE) \
		--build-arg COMMIT=$(COMMIT) \
		--tag $(RUNTIME_IMAGE_REPO):$(IMAGE_TAG) .
