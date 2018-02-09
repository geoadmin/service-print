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
      '''
    }
    stage("Run") {
      sh '''
        echo Starting the containers...
      '''
    }
    stage("Test") {
      sh '''
        echo Starting the tests...
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
    sh 'echo All dockers have been purged'
  }
}
