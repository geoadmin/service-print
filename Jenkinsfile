#!/usr/bin/env groovy

final IMAGE_BASE_NAME = 'swisstopo/service-print'
final IMAGE_BASE_NAME_NGINX = 'swisstopo/service-print-nginx'
final IMAGE_BASE_NAME_TOMCAT = 'swisstopo/service-print-tomcat'
final DOCKER_REGISTRY_URL  = 'https://registry.hub.docker.com'

node(label: "jenkins-slave") {
  final deployGitBranch = env.BRANCH_NAME
  env.COMPOSE_PROJECT_NAME = "${env.JOB_NAME}-${env.BUILD_ID}"
  def IMAGE_TAG = "staging"
  env.IMAGE_TAG = IMAGE_TAG

  try {
    stage("Checkout") {
      sh 'echo Checking out code from github'
      final scmVars = checkout scm
      sh 'docker --version'
      sh 'docker-compose --version'
      if (deployGitBranch == 'master') {
        IMAGE_TAG = 'staging'
      } else {
        IMAGE_TAG = scmVars.GIT_COMMIT
      }
      sh "echo Setting IMAGE_TAG to ${IMAGE_TAG}"
      env.IMAGE_TAG = "${IMAGE_TAG}"
    }
    stage("Build") {
      sh 'echo Starting the build...'
      sh 'echo "export IMAGE_TAG=${IMAGE_TAG}" >> rc_user'
      sh 'make dockerbuild'
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
    if (deployGitBranch == 'master') {
       stage("Publish") {
         sh 'echo Publishing images to Dockerhub'
         withCredentials(
           [[$class: 'UsernamePasswordMultiBinding',
             credentialsId: 'iwibot-admin-user-dockerhub',
             usernameVariable: 'USERNAME',
             passwordVariable: 'PASSWORD']]
         ){
           sh 'docker login -u "$USERNAME" -p "$PASSWORD"'
           docker.image("${IMAGE_BASE_NAME}:${IMAGE_TAG}").push()
           docker.image("${IMAGE_BASE_NAME_NGINX}:${IMAGE_TAG}").push()
           docker.image("${IMAGE_BASE_NAME_TOMCAT}:${IMAGE_TAG}").push()
         }
       }
    }
    if (deployGitBranch == 'master') {
       stage("Deploy") {
         sh 'echo Deploying to dev'
         sh 'make rancherdeploydev'
         sh 'echo Deployed to dev'
       }
    }
  }
  catch (e) {
    throw e
  }
  finally {
    sh 'docker-compose down -v || echo Skipping'
    sh "docker rmi ${IMAGE_BASE_NAME}:${IMAGE_TAG} || echo Skipping"
    sh "docker rmi ${IMAGE_BASE_NAME_NGINX}:${IMAGE_TAG} || echo Skipping"
    sh "docker rmi ${IMAGE_BASE_NAME_TOMCAT}:${IMAGE_TAG}  || echo Skipping"
    sh 'git clean -dx --force'
    sh 'docker ps'
    sh 'docker ps --all --filter status=exited'
    sh 'echo All dockers have been purged'
  }
}
