ifndef VERBOSE
MAKEFLAGS += --no-print-directory
endif

define runtests
	python -m unittest discover -s $(1) -p $(2)
endef

SHELL  := /bin/bash
PYTHON := /usr/bin/env python3.9
PYTHON_VERSION := 3.9
PIPENV := pipenv
SRC_DIRS := platform_play tests

DOCKER_ACC := 'medopadrtd'

PPSERVER_GIT_SHA := $(shell git rev-parse --short HEAD)
PPSERVER_GIT_TAG := $(shell git describe --tags --abbrev=0)
PPSERVER_GIT_BRANCH := $(shell git rev-parse --abbrev-ref HEAD)

how:
	@echo "+ Getting docker mounted volume"
	@echo "docker inspect -f '{{ .Mounts }}' <container_id>"

run/deps:
	@echo "+ Running depedencies through docker..."
	@docker-compose up start_dependencies
	@sleep 10

stop/deps:
	@echo "+ Stopping depedencies through docker..."
	@docker-compose down
	@sleep 1

##### ppserver run #####
ppserver/run:
	@echo "+ Running ppserver"
	@cd apps/ppserver && $(PIPENV) run python ./ppserver.py

ppserver/run/local-dev:
	@echo "+ Running ppserver"
	@docker-compose -f docker-compose.yaml -f docker-compose.localdev.yaml up

ppserver/run/local-dev-ngrok: export Port=3911
ppserver/run/local-dev-ngrok: export Subdomain=iippserver
ppserver/run/local-dev-ngrok:
	@echo "+ Running ppserver"
	@echo "+ NOTE: this command won't work if you didn't setup ngrok on your PC. Have a look common section on this make file"
	@docker-compose -f docker-compose.yaml -f docker-compose.localdev.yaml build
	@docker-compose -f docker-compose.yaml -f docker-compose.localdev.yaml up -d
	@${HOME}/bin/ngrok http ${Port} --subdomain=${Subdomain}

##### ppserver tests #####
ppserver/tests/local: ## this needs run deps
	@echo "+ Running tests in local development computer"
	set -o allexport && source apps/ppserver/dev.env && set +o allexport && $(PIPENV) run all-tests

ppserver/tests/run-full-test-suit-in-docker-compose: ## DON'T USE THIS ONE DIRECTLY FORM CLI. INTENDED FOR USE INSIDE DOCKER
	@echo "+ Running ppserver full suit of tests in docker-compose"
	@sleep 25
	@mkdir -p testresults
	@pytest --durations=15 --disable-pytest-warnings -c .pytest.ini ./sdk/tests ./extensions/tests ./apps/ppserver/tests \
		--cov=sdk --cov=extensions \
		--junitxml=testresults/junitresult.xml 2>&1 | tee testresults/pytest.log

ppserver/tests/run-unit-tests-in-docker-compose: ## DON'T USE THIS ONE DIRECTLY FORM CLI. INTENDED FOR USE INSIDE DOCKER
	@echo "+ Running ppserver unit tests in docker-compose"
	@sleep 25
	@mkdir -p testresults
	@pytest --durations=15 --disable-pytest-warnings -c .pytest.ini ./sdk/tests/*/UnitTests ./extensions/tests/*/UnitTests ./apps/ppserver/tests/*/UnitTests \
		--cov=sdk --cov=extensions \
		--junitxml=testresults/unit-junitresult.xml 2>&1 | tee testresults/unit-pytest.log

ppserver/tests/run-integration-tests-in-docker-compose: ## DON'T USE THIS ONE DIRECTLY FORM CLI. INTENDED FOR USE INSIDE DOCKER
	@echo "+ Running ppserver integration tests in docker-compose"
	@sleep 25
	@mkdir -p testresults
	@pytest --durations=15 --disable-pytest-warnings -c .pytest.ini ./sdk/tests/*/IntegrationTests ./extensions/tests/*/IntegrationTests ./apps/ppserver/tests/*/IntegrationTests \
		--cov=sdk --cov=extensions \
		--junitxml=testresults/integration-junitresult.xml 2>&1 | tee testresults/integration-pytest.log

##### ppserver full test suit by docker #####
ppserver/tests/docker-compose:
	@echo "+ Running ppserver full test suit"
	@mkdir -p testresults
	@docker-compose -f docker-compose.yaml -f docker-compose.test.yaml up --build run-tests
	@if grep -q 'FAILED' './testresults/pytest.log'; then echo "FAILED"; exit 1; fi
	@if grep -q 'ERROR' './testresults/pytest.log'; then echo "FAILED"; exit 1; fi
	@echo "DONE"


##### ppserver tests by docker #####
ppserver/tests/docker-compose-unit-tests:
	@echo "+ Running ppserver unit tests"
	@mkdir -p testresults
	@docker-compose -f docker-compose.unit-tests.yaml up --build run-tests
	@if grep -q 'FAILED' './testresults/unit-pytest.log'; then echo "FAILED"; exit 1; fi
	@if grep -q 'ERROR' './testresults/unit-pytest.log'; then echo "FAILED"; exit 1; fi
	@echo "DONE"

ppserver/tests/docker-compose-integration-tests:
	@echo "+ Running ppserver integration tests"
	@mkdir -p testresults
	@docker-compose -f docker-compose.yaml -f docker-compose.integration-tests.yaml up --build run-tests
	@if grep -q 'FAILED' './testresults/integration-pytest.log'; then echo "FAILED"; exit 1; fi
	@if grep -q 'ERROR' './testresults/integration-pytest.log'; then echo "FAILED"; exit 1; fi
	@echo "DONE"

##### ppserver docker build & push #####
ppserver/push/docker/ghcr: export DOCKER_ACC = 'ghcr.io/huma-engineering'
ppserver/push/docker/ghcr:
	@echo "+ Pushing py-ppserver service to docker package registry at $(DOCKER_ACC)"
	@echo "> Note: make sure you have login in terminal already $ docker login ghcr.io -u <username>"
	-docker pull ${DOCKER_ACC}/py-ppserver:latest
ifneq  ("","$(findstring release-,$(PPSERVER_GIT_BRANCH))")
	docker build . --cache-from $(DOCKER_ACC)/py-ppserver:latest \
		-f docker/ppserver/Dockerfile \
		-t $(DOCKER_ACC)/py-ppserver:${PPSERVER_GIT_SHA}-${PPSERVER_GIT_BRANCH} \
		--build-arg=GIT_COMMIT=$(PPSERVER_GIT_SHA) \
		--build-arg=GIT_BRANCH=$(PPSERVER_GIT_BRANCH) \
		--label commit=$(PPSERVER_GIT_SHA) \
		--label org.opencontainers.image.source=https://github.com/huma-engineering/py-phoenix-server
	docker push ${DOCKER_ACC}/py-ppserver:${PPSERVER_GIT_SHA}-${PPSERVER_GIT_BRANCH}
	docker push ${DOCKER_ACC}/py-ppserver:latest
	echo "+ Image id ${PPSERVER_GIT_SHA}-${PPSERVER_GIT_BRANCH}"
else
	docker build . --cache-from $(DOCKER_ACC)/py-ppserver:latest \
		-f docker/ppserver/Dockerfile \
		-t $(DOCKER_ACC)/py-ppserver:${PPSERVER_GIT_SHA} \
		--build-arg=GIT_COMMIT=$(PPSERVER_GIT_SHA) \
		--label commit=$(PPSERVER_GIT_SHA) \
		--label org.opencontainers.image.source=https://github.com/huma-engineering/py-phoenix-server
	docker push ${DOCKER_ACC}/py-ppserver:${PPSERVER_GIT_SHA}
	docker push ${DOCKER_ACC}/py-ppserver:latest
	echo "+ Image id ${PPSERVER_GIT_SHA}"
endif

##### extensions #####
ppserver/tests/extensions: ## this needs run deps
	@echo "+ Running extensions tests in local development computer"
	set -o allexport && source apps/ppserver/dev.env && set +o allexport && $(PIPENV) run extensions-tests

##### sdk ######
sdk/linter:
	@echo "+ Running linter for sdk"
	@$(PIPENV) run sdk-lint

##### common #####
pipenv/setup: ## Set virtual env for pipenv
	@echo "+ Setting up pipenv environment"
	@$(PIPENV) --python $(PYTHON_VERSION) sync && $(PIPENV) --python $(PYTHON_VERSION) sync --dev && $(PIPENV) --python $(PYTHON_VERSION) update && $(PIPENV) --python $(PYTHON_VERSION) update --dev && pre-commit install

common/install-ngrok:
	@echo "+ Installing ngrok in ${HOME}"
	@mkdir -p ${HOME}/bin && \
		wget https://bin.equinox.io/c/4VmDzA7iaHb/ngrok-stable-linux-amd64.zip -O /${HOME}/bin/ngrok.zip && \
		cd ${HOME}/bin && \
		unzip ngrok.zip && \
		rm -rf ngrok.zip && \
		chmod u+x ngrok

common/save-authtoken-ngrok:
	@echo '+ Saving auth token'
	@echo '+ Command Sytle > AuthToken=<token_from_ngrok_account> make save-authtoken-ngrok'
	@ngrok authtoken ${AuthToken}

common/run-ngrok: export Port=3901
common/run-ngrok:
	@${HOME}/bin/ngrok http ${Port}

common/git-info:
	@echo $(PPSERVER_GIT_SHA)
	@echo $(PPSERVER_GIT_TAG)
	@echo $(PPSERVER_GIT_BRANCH)

common/git-unit-tests-code-cov-pr-comment:
	@echo "+ unit PR comment creation"
	@echo -n "**Unit Test** Coverage: " > pr-unit-test-coverage.txt && \
		cat testresults/unit-pytest.log | grep TOTAL | tail -c 4 >> pr-unit-test-coverage.txt

common/git-integration-tests-code-cov-pr-comment:
	@echo "+ integration PR comment creation"
	@echo -n "**Integration Test** Coverage: " > pr-integration-test-coverage.txt && \
		cat testresults/integration-pytest.log | grep TOTAL | tail -c 4 >> pr-integration-test-coverage.txt

common/git-tests-code-cov-pr-comment:
	@echo "+ PR comment creation"
	@cat pr-integration-test-coverage.txt >> pr-unit-test-coverage.txt && \
		echo "#### Links" >> pr-unit-test-coverage.txt && \
		echo "- [Github Actions](https://github.com/${GITHUB_REPOSITORY}/actions/runs/${GITHUB_RUN_ID})" >> pr-unit-test-coverage.txt

.PHONY: help all
help:
	@grep -hE '^[a-zA-Z0-9\._/-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-40s\033[0m %s\n", $$1, $$2}'

.DEFAULT_GOAL := help

###################
### Helm Charts ###
###################

CHARTS:=huma-server-sdk ## charts list
CHARTS_FOLDER=deploy/charts
GHCR_BASE?=ghcr.io/huma-engineering/helm-charts

define extract_chart_version
	ret=`grep -A0 'version:' $(2)/Chart.yaml | tail -n1 | cut -c 10-`
	$(1) := $$(ret)
endef

.PHONY: charts/help charts/helm
charts/help: ## Print the instruction for Helm Charts usage
	@echo "TL;DR If your setup is right you just call one command:"
	@echo "> make charts/upload"
	@echo ""
	@echo "Note 1"
	@echo "Should install the latest Helm v3 (version needed is >=3.7) with command"
	@echo "> make charts/helm"
	@echo ""
	@echo "Note 2"
	@echo "1. Generate the Github PAT token following [Github Docs](https://docs.github.com/en/packages/working-with-a-github-packages-registry/working-with-the-container-registry)"
	@echo "2. Set $GITHUB_USER and $GITHUB_TOKEN (PAT token) in your environment."
	@echo "   Test your login with > make charts/login"
	@echo "3. > make charts/upload"
	@echo "4. Find the packages in github packages:"
	@echo "  1. First connect to helm-charts repository"
	@echo "  2. Go to the Package settings and then helm-charts repository as 'Actions repository access' accessor"
	@echo "  3. Optionally on Package settings, any team can be added as read or write actor"

charts/helm: ## Download Helm v3 locally if necessary.
ifeq (,$(shell which helm 2>/dev/null))
	@{ \
	set -e ;\
	bash <(curl -fsSL https://raw.githubusercontent.com/helm/helm/master/scripts/get-helm-3);\
	}
endif

.PHONY: charts/login
charts/login: charts/helm ## Login to ghcr.io. You may need to copy this on your CI
	@echo "+ Login to GHCR"
	@echo ${GITHUB_TOKEN} | helm registry login -u ${GITHUB_USER} --password-stdin ghcr.io

.PHONY: charts/package-%
charts/package-%: ## Package ( means creating .tgz) the helm chart
	$(eval $(call extract_chart_version,version,${CHARTS_FOLDER}/$*))
	@echo "+ Package $* charts"
	@export HELM_EXPERIMENTAL_OCI=1 && \
		mkdir -p ./.bin && \
		helm package ${CHARTS_FOLDER}/$* -d ./.bin

.PHONY: charts/upload-%
charts/upload-%: charts/package-% ## Upload $* chart to ghcr.io registry
	$(eval $(call extract_chart_version,version,${CHARTS_FOLDER}/$*))
	@echo "+ Upload $* charts"
	@export HELM_EXPERIMENTAL_OCI=1 && \
		helm push ./.bin/$*-${version}.tgz oci://${GHCR_BASE}

CHARTS_UPLOAD:=$(addprefix charts/upload-,$(CHARTS))
CHARTS_PACKAGE:=$(addprefix charts/package-,$(CHARTS))

.PHONY: charts/upload
charts/upload: charts/login $(CHARTS_UPLOAD) ## Upload the charts in charts folder
	@echo "+ Uploaded charts:"
	@echo "  ${CHARTS}"

.PHONY: charts/package
charts/package: $(CHARTS_PACKAGE) ## Package the charts in chart folder
	@echo "+ Packaged charts:"
	@echo "  ${CHARTS}"
