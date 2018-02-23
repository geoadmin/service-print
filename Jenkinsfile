#!/usr/bin/env groovy

final IMAGE_BASE_NAME = 'swisstopo/service-print'
final IMAGE_BASE_NAME_NGINX = 'swisstopo/service-print-nginx'
final IMAGE_BASE_NAME_TOMCAT = 'swisstopo/service-print-tomcat'
final DOCKER_REGISTRY_URL  = 'https://registry.hub.docker.com'

node(label: "jenkins-slave") {
  final deployGitBranch = env.BRANCH_NAME
  def IMAGE_TAG = "staging"

  final scmVars = checkout scm
  if (deployGitBranch != 'master') {
    IMAGE_TAG = scmVars.GIT_COMMIT
  }
  def COMPOSE_PROJECT_NAME = IMAGE_TAG

  try {
    withEnv(["IMAGE_TAG=${IMAGE_TAG}", "COMPOSE_PROJECT_NAME=${COMPOSE_PROJECT_NAME}"]) {
      stage("Build") {
        sh 'echo Starting the build...'
        sh 'docker --version'
        sh 'docker-compose --version'
        sh 'echo "export IMAGE_TAG=${IMAGE_TAG}" >> rc_user'
        sh 'make dockerbuild'
      }
      stage("Run") {
        sh 'echo Starting the containers...'
        sh 'docker-compose -p "${COMPOSE_PROJECT_NAME}" up -d'
        sh 'docker ps -a'
      }
      stage("Sanity") {
        sh 'NGINX_OK=$(docker ps -aq --filter status="running" --filter name="${COMPOSE_PROJECT_NAME}_nginx") && if [ -z "$NGINX_OK" ]; then exit 1; fi'
        sh 'WSGI_OK=$(docker ps -aq --filter status="running" --filter name="${COMPOSE_PROJECT_NAME}_wsgi") && if [ -z "$WSGI_OK" ]; then exit 1; fi'
        sh 'TOMCAT_OK=$(docker ps -aq --filter status="running" --filter name="${COMPOSE_PROJECT_NAME}_tomcat") && if [ -z "$TOMCAT_OK" ]; then exit 1; fi'
      }
      stage("Lint") {
        sh '''
          echo Starting linting...
          DOCKER_CONTAINER_ID="$(docker ps | grep "${COMPOSE_PROJECT_NAME}_wsgi" | awk '{ print $1 }')"
          docker exec -i "$DOCKER_CONTAINER_ID" flake8 -v $(find tests/* print3/* -path print/static -prune -o -type f -name "*.py" -print)
          echo All tests are successful
        '''
      }
      stage("Test") {
        sh '''
          echo Starting the tests...
          DOCKER_CONTAINER_ID="$(docker ps | grep "${COMPOSE_PROJECT_NAME}_wsgi" | awk '{ print $1 }')"
          docker exec -i "$DOCKER_CONTAINER_ID" coverage run --source=print3 --omit=print3/wsgi.py setup.py test
          docker exec -i "$DOCKER_CONTAINER_ID" coverage report -m
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
  }
  catch (e) {
    throw e
  }
  finally {
    withEnv(["IMAGE_TAG=${IMAGE_TAG}", "COMPOSE_PROJECT_NAME=${COMPOSE_PROJECT_NAME}"]) {
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
}
