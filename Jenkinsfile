#!/usr/bin/env groovy

final IMAGE_BASE_NAME = 'swisstopo/service-print'
final IMAGE_BASE_NAME_NGINX = 'swisstopo/service-print-nginx'
final IMAGE_BASE_NAME_TOMCAT = 'swisstopo/service-print-tomcat'
final IMAGE_TAG = 'staging'

node(label: "jenkins-slave") {
  try {
    stage("Checkout") {
      sh 'echo Checking out code from github'
      checkout scm
    }
    stage("Build") {
      sh '''
        echo Starting the build...
        make cleanall all dockerbuild
        echo Build successfull
      '''
    }
    stage("Run") {
      sh '''
        echo Starting the containers...
        make dockerrun
      '''
    }
    stage("Test") {
      sh '''
        echo Starting the tests...
        DOCKER_CONTAINER_ID="$(docker ps | grep "python print3" | awk '{ print $1  }')"
        docker exec -i "$DOCKER_CONTAINER_ID" coverage run --source=print3 --omit=print3/wsgi.py setup.py test
        echo All tests are successful

      '''
    }
    stage("Publish") {
      if (deployGitBranch == 'master') {
        sh 'echo Publishing images to dev'
      } else {
        sh 'echo Skipping publishing to dev'
      }
    }
  catch (e) {
    throw e
  }
  finally {
    sh 'docker-compose down & sleep 5'
    sh 'docker ps --all | grep swisstopo/service-print-tomcat | awk \'{print($1)}\' | xargs --no-run-if-empty docker rm --force'
    sh 'docker ps --all | grep "python print3" | awk \'{print($1)}\' | xargs --no-run-if-empty docker rm --force'
    sh 'docker ps --all | grep swisstopo/service-print-nginx | awk \'{print($1)}\' | xargs --no-run-if-empty docker rm --force'
    sh 'docker image rm swisstopo/service-print-tomcat:staging'
    sh 'docker image rm swisstopo/service-print:staging'
    sh 'docker image rm swisstopo/service-print-nginx:staging'
    sh 'git clean -dx --force'
    sh 'echo All dockers have been purged'
  }
}
