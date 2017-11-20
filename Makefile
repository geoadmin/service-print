SHELL = /bin/bash

# Variables
GIT_BRANCH := $(shell if [ -f '.venv/deployed-git-branch' ]; then cat .venv/deployed-git-branch 2> /dev/null; else git rev-parse --symbolic-full-name --abbrev-ref HEAD; fi)
GIT_COMMIT_HASH ?= $(shell git rev-parse --verify HEAD)
GIT_COMMIT_DATE ?= $(shell git log -1  --date=iso --pretty=format:%cd)
APACHE_BASE_PATH ?= main
VERSION := $(shell if [ '$(KEEP_VERSION)' = 'true' ] && [ '$(LAST_VERSION)' != '-none-' ]; then echo $(LAST_VERSION); else python -c "print __import__('time').strftime('%s')"; fi)
BASEWAR ?= print-servlet-2.1.3-SNAPSHOT.war
PRINT_SERVER_URL ?= //service-print.dev.bgdi.ch
TOMCAT_SERVER_URL ?= //service-print.dev.bgdi.ch
TOMCAT_BASE_URL ?= ajp://localhost:8009
PRINT_INPUT :=  checker *.html *.yaml *.png WEB-INF
#PRINT_OUTPUT_BASE := /srv/tomcat/tomcat1/webapps/service-print-$(APACHE_BASE_PATH)
#PRINT_OUTPUT := $(PRINT_OUTPUT_BASE).war
PRINT_TEMP_DIR ?= /var/local/print
PYTHON_FILES := $(shell find print3/* -path print/static -prune -o -type f -name "*.py" -print)
USERNAME := $(shell whoami)
USER_SOURCE ?= rc_user
CURRENT_DIR := $(shell pwd)
INSTALL_DIR := $(CURRENT_DIR)/.venv

# Commands
AUTOPEP8_CMD := $(INSTALL_DIR)/bin/autopep8
FLAKE8_CMD := $(INSTALL_DIR)/bin/flake8
MAKO_CMD := $(INSTALL_DIR)/bin/mako-render
NOSE_CMD := $(INSTALL_DIR)/bin/nosetests
PIP_CMD := $(INSTALL_DIR)/bin/pip
PSERVE_CMD := $(INSTALL_DIR)/bin/pserve
PYTHON_CMD := $(INSTALL_DIR)/bin/python
COVERAGE_CMD := $(INSTALL_DIR)/bin/coverage

# Colors
RESET := $(shell tput sgr0)
RED := $(shell tput setaf 1)
GREEN := $(shell tput setaf 2)


.PHONY: help
help:
	@echo "Usage: make <target>"
	@echo
	@echo "Possible targets:"
	@echo
	@echo "--------------------------------------------------------------------------"
	@echo "|                          LOCAl DEVELOPMENT                             |"
	@echo "--------------------------------------------------------------------------"
	@echo "- user               Build the user specific version of the app"
	@echo "- serve              Serve using Flask internal server"
	@echo "- gunicornserve      Serve the application with gunicorn"
	@echo "- test               Launch the tests (no e2e tests)"
	@echo "- lint               Run the linter"
	@echo "- autolint           Run the autolinter"
	@echo "- printwar           Creates the .war print file"
	@echo "- clean              Remove generated files"
	@echo "- cleanall           Remove all the build artefacts"
	@echo
	@echo "--------------------------------------------------------------------------"
	@echo "|                         DOCKER DEVELOPMENT                             |"
	@echo "--------------------------------------------------------------------------"
	@echo "- dockerbuild        Builds a docker image using the current directory"
	@echo "- dockerrun          Creates and runs all the containers (in the background)"
	@echo
	@echo "--------------------------------------------------------------------------"
	@echo "|                       RANCHER DEPLOYMENT                               |"
	@echo "--------------------------------------------------------------------------"
	@echo "- rancherdeploy{dev|int|prod}       Deploys the images pushed in dockerhub"
	@echo
	@echo "Variables:"
	@echo 
	@echo "PRINT_ENV:           ${PRINT_ENV}"
	@echo "RANCHER_LABEL:       ${RANCHER_LABEL}"
	@echo "IMAGE_TAG:           ${IMAGE_TAG}"
	@echo "API_URL:             ${API_URL}"
	@echo "PRINT_SERVER_URL:    ${PRINT_SERVER_URL}"
	@echo "PRINT_TEMP_DIR:      ${PRINT_TEMP_DIR}"
	@echo "TOMCAT_SERVER_URL    ${TOMCAT_SERVER_URL}"
	@echo "NGINX_PORT:          ${NGINX_PORT}"
	@echo "WSGI_PORT:           ${WSGI_PORT}"
	@echo "TOMCAT_PORT:         ${TOMCAT_PORT}"
	@echo "BASEWAR:             ${BASEWAR}"
	@echo "INSTALL_DIR:         ${INSTALL_DIR}"
	@echo


.PHONY: all
all: setup   fixrights templates

setup: .venv

templates: tomcat/WEB-INF/web.xml print3/static/index.html

.PHONY: user
user:
	source $(USER_SOURCE) && make all

.PHONY: serve
serve:
	source rc_user && ${PYTHON_CMD} print3/main.py

.PHONY: gunicornserve
gunicornserve:
		source rc_user && ${PYTHON_CMD} print3/wsgi.py

.PHONY: test                                                                                                                                                                             
test:
		source rc_user && ${COVERAGE_CMD} run --source=print3 --omit=print3/wsgi.py setup.py test
		${COVERAGE_CMD} report -m


.PHONY: lint
lint:
	@echo "${GREEN}Linting python files...${RESET}";
	${FLAKE8_CMD}  $(PYTHON_FILES) && echo ${RED}

.PHONY: autolint
autolint:
	@echo "${GREEN}Auto correction of python files...${RESET}";
	${AUTOPEP8_CMD} --in-place --aggressive --aggressive --verbose --ignore=${PEP8_IGNORE} $(PYTHON_FILES)


.PHONY: printwar
printwar: tomcat/WEB-INF/web.xml
	echo "${GREEN}Updating print war...${RESET}" && \
	cd tomcat && \
	rm -f service-print-$(APACHE_BASE_PATH).war && \
	mkdir temp_$(VERSION) && \
	cp -f ${BASEWAR} temp_$(VERSION)/service-print-$(APACHE_BASE_PATH).war && \
	cp -fr ${PRINT_INPUT} temp_$(VERSION)/ && \
	cd temp_$(VERSION) && \
	jar cuf service-print-$(APACHE_BASE_PATH).war ${PRINT_INPUT} && \
	cp -r  service-print-$(APACHE_BASE_PATH).war .. && \
	echo "${GREEN}Print war creation was successful.${RESET}" &&  cd .. && \
	echo "${GREEN}Removing temp directory${RESET}" && \
	rm -rf temp_$(VERSION) 



tomcat/WEB-INF/web.xml.in:
	@echo "${GREEN}Template file tomcat/WEB-INF/web.xml has changed${RESET}"

tomcat/WEB-INF/web.xml: tomcat/WEB-INF/web.xml.in
	@echo "${GREEN}Creating print/WEB-INF/web.xml...${RESET}"
	${MAKO_CMD} \
		--var "print_temp_dir=$(PRINT_TEMP_DIR)" $< > $@

print3/static/index.html.in:
	@echo "${GREEN}Template file print3/static/index.html.in has changed${RESET}";

print3/static/index.html: print3/static/index.html.in
	@echo "${GREEN}Creating print3/static/index.html..${RESET}";
	${MAKO_CMD} \
		--var "print_war=$(PRINT_WAR)" \
		--var "apache_base_path=$(APACHE_BASE_PATH)" \
		--var "tomcat_base_url=$(TOMCAT_BASE_URL)" \
		--var "git_branch=$(GIT_BRANCH)" \
		--var "git_commit_hash=$(GIT_COMMIT_HASH)" \
		--var "git_commit_date=$(GIT_COMMIT_DATE)" \
		--var "print_temp_dir=$(PRINT_TEMP_DIR)" $< > $@

.venv:
	@echo "${GREEN}Setting up virtual environement...${RESET}";
	@if [ ! -d $(INSTALL_DIR) ]; \
	then \
		virtualenv $(INSTALL_DIR); \
		${PIP_CMD} install ${CURRENT_DIRECTORY}/pip-8.1.2.tar.gz; \
		${PIP_CMD} install pyopenssl ndg-httpsclient pyasn1; \
		${PIP_CMD} install -U pip wheel distribute; \
		${PIP_CMD} install setuptools==33.1.1;  \
		$(PIP_CMD) install -r requirements.txt; \
		$(PIP_CMD) install -r dev-requirements.txt; \
	fi
	${PIP_CMD} install -e .

.PHONY: dockerbuild
dockerbuild: composetemplateuser
		docker-compose build

.PHONY: composetemplateuser
composetemplateuser:
		source rc_user && envsubst < rancher-compose.yml.in > rancher-compose.yml && \
				envsubst "$(printf '${%s} ' $(bash -c "compgen -A variable"))" < nginx/nginx.conf.in > nginx/nginx.conf
				source rc_user && export RANCHER_DEPLOY=false && make docker-compose.yml

.PHONY: dockerrun
dockerrun: composetemplateuser
		docker-compose up -d

.PHONY: composetemplatedev
composetemplatedev:
		$(eval RANCHER_DEPLOY=$(call get_rancher_deploy_val,$(RANCHER_DEPLOY)))
		$(call build_templates,dev,$(RANCHER_DEPLOY))

.PHONY: composetemplateint
composetemplateint:
		$(eval RANCHER_DEPLOY=$(call get_rancher_deploy_val,$(RANCHER_DEPLOY)))
		$(call build_templates,int,$(RANCHER_DEPLOY))

.PHONY: composetemplateprod
composetemplateprod:
		$(eval RANCHER_DEPLOY=$(call get_rancher_deploy_val,$(RANCHER_DEPLOY)))
		$(call build_templates,prod,$(RANCHER_DEPLOY))

.PHONY: rancherdeploydev
rancherdeploydev: guard-RANCHER_ACCESS_KEY \
                  guard-RANCHER_SECRET_KEY \
                  guard-RANCHER_URL
	export RANCHER_DEPLOY=true && make composetemplatedev
	$(call start_service,$(RANCHER_ACCESS_KEY),$(RANCHER_SECRET_KEY),$(RANCHER_URL),dev)

.PHONY: rancherdeployint
rancherdeployint: guard-RANCHER_ACCESS_KEY \
                  guard-RANCHER_SECRET_KEY \
                  guard-RANCHER_URL
	export RANCHER_DEPLOY=true && make composetemplateint
	$(call start_service,$(RANCHER_ACCESS_KEY),$(RANCHER_SECRET_KEY),$(RANCHER_URL),int)

.PHONY: rancherdeployprod
rancherdeployprod: guard-RANCHER_ACCESS_KEY \
                  guard-RANCHER_SECRET_KEY \
                  guard-RANCHER_URL
	export RANCHER_DEPLOY=true && make composetemplateprod
	$(call start_service,$(RANCHER_ACCESS_KEY),$(RANCHER_SECRET_KEY),$(RANCHER_URL),prod)

# for nginx, we only replace variables that actually exist
define build_templates
		export $(shell cat $1.env) && export RANCHER_DEPLOY=$2 && \
		envsubst "$(printf '${%s} ' $(bash -c "compgen -A variable"))" < nginx/nginx.conf.in > nginx/nginx.conf
		envsubst < rancher-compose.yml.in > rancher-compose.yml && make docker-compose.yml
endef

define start_service
	rancher --access-key $1 --secret-key $2 --url $3 up --stack service-print-$4 --pull --force-upgrade --confirm-upgrade -d
endef

define get_rancher_deploy_val
		$(shell if [ '$1' == 'true'  ]; then echo 'true'; else echo 'false'; fi)
endef

docker-compose.yml::
	${MAKO_CMD} --var "rancher_deploy=$(RANCHER_DEPLOY)" \
		--var "image_tag=$(IMAGE_TAG)" \
		--var "nginx_port=$(NGINX_PORT)" \
		--var "wsgi_port=$(WSGI_PORT)" \
		--var "tomcat_port=$(TOMCAT_PORT)" \
		--var "rancher_label=$(RANCHER_LABEL)" \
		--var "print_env=$(PRINT_ENV)" docker-compose.yml.in > docker-compose.yml

fixrights:
	@echo "${GREEN}Fixing rights...${RESET}";
	chgrp -f -R geodata . || :
	chmod -f -R g+srwX . || :
	chmod -f -R o+sr . || :

.PHONY: cleancache
cleancache:
	rm -rf /var/local/print/*.pdf
	rm -rf /var/local/print/*.json
	rm -rf /var/local/print/mapfish*

.PHONY: clean
clean:
	rm -rf tomcat/WEB-INF/web.xml
	rm -rf tomcat/temp_*
	rm -f nginx/nginx.conf
	rm -f rancher-compose.yml
	rm -f docker-compose.yml

.PHONY: cleanall
cleanall: clean
	rm -rf .venv
	rm -rf print3.egg-info

guard-%:
		@ if test "${${*}}" = ""; then \
				echo "Environment variable $* not set. Add it to your command."; \
				exit 1; \
		fi
