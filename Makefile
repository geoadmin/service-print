SHELL = /bin/bash
# Variables
APACHE_ENTRY_PATH := $(shell if [ '$(APACHE_BASE_PATH)' = 'main' ]; then echo ''; else echo /$(APACHE_BASE_PATH); fi)
APP_VERSION := $(shell python -c "print __import__('time').strftime('%s')")
BASEWAR ?= print-servlet-2.1.3-SNAPSHOT.war
VERSION := $(shell if [ '$(KEEP_VERSION)' = 'true' ] && [ '$(LAST_VERSION)' != '-none-' ]; then echo $(LAST_VERSION); else python -c "print __import__('time').strftime('%s')"; fi)
BRANCH_STAGING := $(shell if [ '$(DEPLOY_TARGET)' = 'dev' ]; then echo 'test'; else echo 'integration'; fi)
BRANCH_TO_DELETE :=
CURRENT_DIRECTORY := $(shell pwd)
DEPLOYCONFIG ?=
DEPLOY_TARGET ?=
GIT_BRANCH := $(shell if [ -f '.venv/deployed-git-branch' ]; then cat .venv/deployed-git-branch 2> /dev/null; else git rev-parse --symbolic-full-name --abbrev-ref HEAD; fi)
GIT_COMMIT_HASH ?= $(shell git rev-parse --verify HEAD)
GIT_COMMIT_DATE ?= $(shell git log -1  --date=iso --pretty=format:%cd)
INSTALL_DIRECTORY := .venv
MODWSGI_USER := www-data
NO_TESTS ?= withtests
PRINT_PROXY_URL ?= //service-print.dev.bgdi.ch
TOMCAT_BASE_URL ?= ajp://localhost:8009
PRINT_INPUT :=  *.html *.yaml *.png WEB-INF
PRINT_OUTPUT_BASE := /srv/tomcat/tomcat1/webapps/service-print-$(APACHE_BASE_PATH)
PRINT_OUTPUT := $(PRINT_OUTPUT_BASE).war
PRINT_TEMP_DIR := /var/local/print
PYTHON_FILES := $(shell find print3/* -path print/static -prune -o -type f -name "*.py" -print)
TEMPLATE_FILES := $(shell find -type f -name "*.in" -print)
USERNAME := $(shell whoami)
USER_SOURCE ?= rc_user
WSGI_APP := $(CURRENT_DIRECTORY)/apache/application.wsgi
SERVER_PORT ?= 9000

# Commands
AUTOPEP8_CMD := $(INSTALL_DIRECTORY)/bin/autopep8
FLAKE8_CMD := $(INSTALL_DIRECTORY)/bin/flake8
MAKO_CMD := $(INSTALL_DIRECTORY)/bin/mako-render
NOSE_CMD := $(INSTALL_DIRECTORY)/bin/nosetests
PIP_CMD := $(INSTALL_DIRECTORY)/bin/pip
PSERVE_CMD := $(INSTALL_DIRECTORY)/bin/pserve
PYTHON_CMD := $(INSTALL_DIRECTORY)/bin/python

# Linting rules
PEP8_IGNORE := "E128,E221,E241,E251,E272,E501,E711,E731"

# E128: continuation line under-indented for visual indent
# E221: multiple spaces before operator
# E241: multiple spaces after ':'
# E251: multiple spaces around keyword/parameter equals
# E272: multiple spaces before keyword
# E501: line length 79 per default
# E711: comparison to None should be 'if cond is None:' (SQLAlchemy's filter syntax requires this ignore!)
# E731: do not assign a lambda expression, use a def

# Colors
RESET := $(shell tput sgr0)
RED := $(shell tput setaf 1)
GREEN := $(shell tput setaf 2)

# Versions
# We need GDAL which is hard to install in a venv, modify PYTHONPATH to use the
# system wide version.
PYTHON_VERSION := $(shell python --version 2>&1 | cut -d ' ' -f 2 | cut -d '.' -f 1,2)
PYTHONPATH ?= .venv/lib/python${PYTHON_VERSION}/site-packages:/usr/lib64/python${PYTHON_VERSION}/site-packages
SERVER_ID := $(shell ${PYTHON_CMD}  -c 'import uuid; print uuid.uuid1()')

.PHONY: help
help:
	@echo "Usage: make <target>"
	@echo
	@echo "Possible targets:"
	@echo "- all                Build the app"
	@echo "- user               Build the user specific version of the app"
	@echo "- serve              Serve the application with pserve"
	@echo "- test               Launch the tests (no e2e tests)"
	@echo "- lint               Run the linter"
	@echo "- autolint           Run the autolinter"
	@echo "- deploybranch       Deploy current branch to dev (must be pushed before hand)"
	@echo "- deploybranchint    Deploy current branch to dev and int (must be pushed before hand)"
	@echo "- deletebranch       List deployed branches or delete a deployed branch (BRANCH_TO_DELETE=...)"
	@echo "- printconfig        Set tomcat print env variables"
	@echo "- printwar           Creates the .jar print file (only one per env per default)"
	@echo "- deploydev          Deploys master to dev (SNAPSHOT=true to also create a snapshot)"
	@echo "- deployint          Deploys a snapshot to integration (SNAPSHOT=201512021146)"
	@echo "- deployprod         Deploys a snapshot to production (SNAPSHOT=201512021146)"
	@echo "- cleancache         Remove print cache"
	@echo "- clean              Remove generated files"
	@echo "- cleanall           Remove all the build artefacts"
	@echo
	@echo "Variables:"
	@echo "APACHE_ENTRY_PATH:   ${APACHE_ENTRY_PATH}"
	@echo "API_URL:             ${API_URL}"
	@echo "PRINT_PROXY_URL:     ${PRINT_PROXY_URL}"
	@echo "BRANCH_STAGING:      ${BRANCH_STAGING}"
	@echo "GIT_BRANCH:          ${GIT_BRANCH}"
	@echo "TOMCAT_BASE_URL      ${TOMCAT_BASE_URL}"
	@echo "SERVER_PORT:         ${SERVER_PORT}"
	@echo

.PHONY: all
all: setup  templates printconfig printwar fixrights

setup: .venv

templates: apache/wsgi.conf apache/tomcat-print.conf tomcat/WEB-INF/web.xml development.ini production.ini print3/static/index.html

.PHONY: user
user:
	source $(USER_SOURCE) && make all

.PHONY: dev
dev:
	source rc_dev && make all

.PHONY: int
int:
	source rc_int && make all

.PHONY: prod
prod:
	source rc_prod && make all

.PHONY: serve
serve:
	PYTHONPATH=${PYTHONPATH} ${PSERVE_CMD} development.ini --reload

.PHONY: test
test:
	PYTHONPATH=${PYTHONPATH} ${NOSE_CMD} print3/tests/

.PHONY: lint
lint:
	@echo "${GREEN}Linting python files...${RESET}";
	${FLAKE8_CMD} --ignore=${PEP8_IGNORE} $(PYTHON_FILES) && echo ${RED}

.PHONY: autolint
autolint:
	@echo "${GREEN}Auto correction of python files...${RESET}";
	${AUTOPEP8_CMD} --in-place --aggressive --aggressive --verbose --ignore=${PEP8_IGNORE} $(PYTHON_FILES)


.PHONY: deploybranch
deploybranch:
	@echo "${GREEN}Deploying branch $(GIT_BRANCH) to dev...${RESET}";
	./scripts/deploybranch.sh

.PHONY: deletebranch
deletebranch:
	./scripts/delete_branch.sh $(BRANCH_TO_DELETE)

.PHONY: deploybranchint
deploybranchint:
	@echo "${GREEN}Deploying branch $(GIT_BRANCH) to dev and int...${RESET}";
	./scripts/deploybranch.sh int

print/WEB-INF/web.xml.in:
	@echo "${GREEN}Template file print/WEB-INF/web.xml has changed${RESET}"
print/WEB-INF/web.xml: print/WEB-INF/web.xml.in
	@echo "${GREEN}Creating print/WEB-INF/web.xml...${RESET}"
	${MAKO_CMD} \
		--var "print_temp_dir=$(PRINT_TEMP_DIR)" $< > $@
.PHONY: printconfig
printconfig:
	@echo '# File managed by Makefile service-print'  > /srv/tomcat/tomcat1/bin/setenv-local.sh
	@echo 'export JAVA_XMX="2G"'  >> /srv/tomcat/tomcat1/bin/setenv-local.sh

.PHONY: printwar
printwar: printconfig print/WEB-INF/web.xml.in
	cd tomcat && \
	mkdir temp_$(VERSION) && \
	echo "${GREEN}Updating print war...${RESET}" && \
	cp -f ${BASEWAR} temp_$(VERSION)/service-print-$(APACHE_BASE_PATH).war && \
	cp -fr ${PRINT_INPUT} temp_$(VERSION)/ && \
	cd temp_$(VERSION) && \
	jar uf service-print-$(APACHE_BASE_PATH).war ${PRINT_INPUT} && \
	echo "${GREEN}Print war creation was successful.${RESET}" && \
	rm -rf $(PRINT_OUTPUT) $(PRINT_OUTPUT_BASE) && \
	cp -f service-print-$(APACHE_BASE_PATH).war $(PRINT_OUTPUT) && chmod 666 $(PRINT_OUTPUT) && cd .. && \
	echo "${GREEN}Removing temp directory${RESET}" && \
	rm -rf temp_$(VERSION) && \
	echo "${GREEN}Restarting tomcat...${RESET}" && \
	sudo /etc/init.d/tomcat-tomcat1 restart && \
	echo "${GREEN}It may take a few seconds for $(PRINT_OUTPUT_BASE) directory to appear...${RESET}";

# Remove when ready to be merged
.PHONY: deploydev
deploydev:
	@if test "$(SNAPSHOT)" = "true"; \
	then \
		scripts/deploydev.sh -s; \
	else \
		scripts/deploydev.sh; \
	fi

.PHONY: deployint
deployint:
	scripts/deploysnapshot.sh $(SNAPSHOT) int $(NO_TESTS) $(DEPLOYCONFIG)

.PHONY: deployprod
deployprod:
	scripts/deploysnapshot.sh $(SNAPSHOT) prod $(NO_TESTS) $(DEPLOYCONFIG)


rc_branch.mako:
	@echo "${GREEN}Branch has changed${RESET}";
rc_branch: rc_branch.mako
	@echo "${GREEN}Creating branch template...${RESET}"
	${MAKO_CMD} \
		--var "git_branch=$(GIT_BRANCH)" \
		--var "deploy_target=$(DEPLOY_TARGET)" \
		--var "branch_staging=$(BRANCH_STAGING)" $< > $@

deploy/deploy-branch.cfg.in:
	@echo "${GREEN]}Template file deploy/deploy-branch.cfg.in has changed${RESET}";
deploy/deploy-branch.cfg: deploy/deploy-branch.cfg.in
	@echo "${GREEN}Creating deploy/deploy-branch.cfg...${RESET}";
	${MAKO_CMD} --var "git_branch=$(GIT_BRANCH)" $< > $@

deploy/conf/00-branch.conf.in:
	@echo "${GREEN}Templat file deploy/conf/00-branch.conf.in has changed${RESET}";
deploy/conf/00-branch.conf: deploy/conf/00-branch.conf.in
	@echo "${GREEN}Creating deploy/conf/00-branch.conf...${RESET}"
	${MAKO_CMD} --var "git_branch=$(GIT_BRANCH)" $< > $@

apache/tomcat-print.conf.in:
	@echo "${GREEN}Template file apache/tomcat-print.conf.in has changed${RESET}";
apache/tomcat-print.conf: apache/tomcat-print.conf.in
	@echo "${GREEN}Creating apache/tomcat-print.conf...${RESET}";
	${MAKO_CMD} \
		--var "print_war=$(PRINT_WAR)" \
		--var "apache_entry_path=$(APACHE_ENTRY_PATH)" \
		--var "apache_base_path=$(APACHE_BASE_PATH)" \
		--var "tomcat_base_url=$(TOMCAT_BASE_URL)" \
		--var "print_temp_dir=$(PRINT_TEMP_DIR)" $< > $@

tomcat/WEB-INF/web.xml.in:
	@echo "${GREEN}Template file tomcat/WEB-INF/web.xml has changed${RESET}"
tomcat/WEB-INF/web.xml: tomcat/WEB-INF/web.xml.in
	@echo "${GREEN}Creating print/WEB-INF/web.xml...${RESET}"
	${MAKO_CMD} \
		--var "print_temp_dir=$(PRINT_TEMP_DIR)" $< > $@

apache/application.wsgi.mako:
	@echo "${GREEN}Template file apache/application.wsgi.mako has changed${RESET}";
apache/application.wsgi: apache/application.wsgi.mako
	@echo "${GREEN}Creating apache/application.wsgi...${RESET}";
	${MAKO_CMD} \
		--var "current_directory=$(CURRENT_DIRECTORY)" \
		--var "apache_base_path=$(APACHE_BASE_PATH)" \
		--var "modwsgi_config=$(MODWSGI_CONFIG)" $< > $@

apache/wsgi.conf.in:
	@echo "${GREEN}Template file apache/wsgi.conf.in has changed${RESET}";
apache/wsgi.conf: apache/wsgi.conf.in apache/application.wsgi
	@echo "${GREEN}Creating apache/wsgi.conf...${RESET}";
	${MAKO_CMD} \
		--var "app_version=$(APP_VERSION)" \
		--var "apache_entry_path=$(APACHE_ENTRY_PATH)" \
		--var "apache_base_path=$(APACHE_BASE_PATH)" \
		--var "robots_file=$(ROBOTS_FILE)" \
		--var "branch_staging=$(BRANCH_STAGING)" \
		--var "git_branch=$(GIT_BRANCH)" \
		--var "current_directory=$(CURRENT_DIRECTORY)" \
		--var "modwsgi_user=$(MODWSGI_USER)" \
		--var "wsgi_threads=$(WSGI_THREADS)" \
		--var "wsgi_app=$(WSGI_APP)" \
		--var "print_temp_dir=$(PRINT_TEMP_DIR)" $< > $@

development.ini.in:
	@echo "${GREEN}Template file development.ini.in has changed${RESET}";
development.ini: development.ini.in
	@echo "${GREEN}Creating development.ini....${RESET}";
	${MAKO_CMD} \
		--var "app_version=$(APP_VERSION)" \
		--var "server_port=$(SERVER_PORT)" $< > $@

production.ini.in:
	@echo "${GREEN}Template file production.ini.in has changed${RESET}";
production.ini: production.ini.in
	@echo "${GREEN}Creating production.ini...${RESET}";
	${MAKO_CMD} \
		--var "app_version=$(APP_VERSION)" \
		--var "server_id=$(SERVER_ID)" \
		--var "server_port=$(SERVER_PORT)" \
		--var "apache_entry_path=$(APACHE_ENTRY_PATH)" \
		--var "apache_base_path=$(APACHE_BASE_PATH)" \
		--var "current_directory=$(CURRENT_DIRECTORY)" \
		--var "api_url=$(API_URL)" \
		--var "print_proxy_url=$(PRINT_PROXY_URL)" \
		--var "host=$(HOST)" \
		--var "print_temp_dir=$(PRINT_TEMP_DIR)" $< > $@

print3/static/index.html.in:
	@echo "${GREEN}Template file print3/static/index.html.in has changed${RESET}";

print3/static/index.html: print3/static/index.html.in
	@echo "${GREEN}Creating print3/static/index.html..${RESET}";
	${MAKO_CMD} \
		--var "print_war=$(PRINT_WAR)" \
		--var "apache_entry_path=$(APACHE_ENTRY_PATH)" \
		--var "apache_base_path=$(APACHE_BASE_PATH)" \
		--var "tomcat_base_url=$(TOMCAT_BASE_URL)" \
		--var "git_branch=$(GIT_BRANCH)" \
		--var "git_commit_hash=$(GIT_COMMIT_HASH)" \
		--var "git_commit_date=$(GIT_COMMIT_DATE)" \
		--var "print_temp_dir=$(PRINT_TEMP_DIR)" $< > $@

requirements.txt:
	@echo "${GREEN}File requirements.txt has changed${RESET}";
.venv: requirements.txt
	@echo "${GREEN}Setting up virtual environement...${RESET}";
	@if [ ! -d $(INSTALL_DIRECTORY) ]; \
	then \
		virtualenv $(INSTALL_DIRECTORY); \
		${PIP_CMD} install ${CURRENT_DIRECTORY}/pip-8.1.2.tar.gz; \
		${PIP_CMD} install pyopenssl ndg-httpsclient pyasn1; \
		${PIP_CMD} install -U pip wheel distribute; \
		${PIP_CMD} install setuptools==33.1.1;  \
	fi
	${PIP_CMD} install -e .


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
	rm -rf production.ini
	rm -rf development.ini
	rm -rf apache/wsgi.conf
	rm -rf apache/tomcat-print.conf
	rm -rf tomcat/WEB-INF/web.xml
	rm -rf apache/application.wsgi
	rm -rf rc_branch
	rm -rf deploy/deploy-branch.cfg
	rm -rf deploy/conf/00-branch.conf
	rm -rf tomcat/temp_*

.PHONY: cleanall
cleanall: clean
	rm -rf .venv
	rm -rf print3.egg-info
