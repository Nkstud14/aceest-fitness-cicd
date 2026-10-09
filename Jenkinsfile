pipeline {
    agent any

    options {
        timestamps()
        disableConcurrentBuilds()
        buildDiscarder(logRotator(numToKeepStr: '10'))
    }

    environment {
        IMAGE_NAME = 'aceest-fitness'
        IMAGE_TAG  = "build-${env.BUILD_NUMBER}"
        VENV_DIR   = '.venv'
    }

    stages {
        stage('Checkout') {
            steps {
                checkout scm
            }
        }

        stage('Set up Python') {
            steps {
                sh '''
                    python3 -m venv ${VENV_DIR}
                    . ${VENV_DIR}/bin/activate
                    python -m pip install --upgrade pip
                    pip install -r requirements.txt -r requirements-dev.txt
                '''
            }
        }

        stage('Lint') {
            steps {
                sh '''
                    . ${VENV_DIR}/bin/activate
                    flake8 aceest_fitness wsgi.py --count --select=E9,F63,F7,F82 --show-source --statistics
                '''
            }
        }

        stage('Test') {
            steps {
                sh '''
                    . ${VENV_DIR}/bin/activate
                    pytest
                '''
            }
        }

        stage('Build Docker Image') {
            steps {
                sh 'docker build -t ${IMAGE_NAME}:${IMAGE_TAG} -t ${IMAGE_NAME}:latest .'
            }
        }

        stage('Verify Image') {
            steps {
                sh '''
                    docker run -d --name aceest_ci -p 5000:5000 ${IMAGE_NAME}:${IMAGE_TAG}
                    sleep 5
                    curl -fsS http://localhost:5000/health | grep "ok"
                '''
            }
        }
    }

    post {
        always {
            sh 'docker rm -f aceest_ci || true'
            sh 'rm -rf ${VENV_DIR} || true'
        }
        success {
            echo 'BUILD SUCCESS: ACEest Fitness image built and verified.'
        }
        failure {
            echo 'BUILD FAILED: check the stage logs above.'
        }
    }
}
