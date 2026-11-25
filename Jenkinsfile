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

        stage('Detect Docker') {
            steps {
                script {
                    // Docker stages are optional so the pipeline also runs on
                    // agents (e.g. a local Windows install) without Docker.
                    env.DOCKER_AVAILABLE = (runStatus('docker --version') == 0) ? 'true' : 'false'
                    echo "Docker available: ${env.DOCKER_AVAILABLE}"
                }
            }
        }

        stage('Set up Python') {
            steps {
                script {
                    if (isUnix()) {
                        sh '''
                            python3 -m venv ${VENV_DIR}
                            ${VENV_DIR}/bin/python -m pip install --upgrade pip
                            ${VENV_DIR}/bin/pip install -r requirements.txt -r requirements-dev.txt
                        '''
                    } else {
                        bat '''
                            python -m venv %VENV_DIR%
                            %VENV_DIR%\\Scripts\\python -m pip install --upgrade pip
                            %VENV_DIR%\\Scripts\\pip install -r requirements.txt -r requirements-dev.txt
                        '''
                    }
                }
            }
        }

        stage('Lint') {
            steps {
                script {
                    if (isUnix()) {
                        sh '${VENV_DIR}/bin/flake8 aceest_fitness wsgi.py --count --select=E9,F63,F7,F82 --show-source --statistics'
                    } else {
                        bat '%VENV_DIR%\\Scripts\\flake8 aceest_fitness wsgi.py --count --select=E9,F63,F7,F82 --show-source --statistics'
                    }
                }
            }
        }

        stage('Test') {
            steps {
                script {
                    if (isUnix()) {
                        sh '${VENV_DIR}/bin/python -m pytest'
                    } else {
                        bat '%VENV_DIR%\\Scripts\\python -m pytest'
                    }
                }
            }
        }

        stage('Build Docker Image') {
            when { environment name: 'DOCKER_AVAILABLE', value: 'true' }
            steps {
                script {
                    def cmd = "docker build -t ${IMAGE_NAME}:${IMAGE_TAG} -t ${IMAGE_NAME}:latest ."
                    if (isUnix()) { sh cmd } else { bat cmd }
                }
            }
        }

        stage('Verify Image') {
            when { environment name: 'DOCKER_AVAILABLE', value: 'true' }
            steps {
                script {
                    if (isUnix()) {
                        sh '''
                            docker run -d --name aceest_ci -p 5000:5000 ${IMAGE_NAME}:${IMAGE_TAG}
                            sleep 5
                            curl -fsS http://localhost:5000/health | grep "ok"
                        '''
                    } else {
                        bat '''
                            docker run -d --name aceest_ci -p 5000:5000 %IMAGE_NAME%:%IMAGE_TAG%
                            ping -n 6 127.0.0.1 > nul
                            curl -fsS http://localhost:5000/health
                        '''
                    }
                }
            }
        }
    }

    post {
        always {
            script {
                if (env.DOCKER_AVAILABLE == 'true') {
                    if (isUnix()) {
                        sh 'docker rm -f aceest_ci || true'
                    } else {
                        bat 'docker rm -f aceest_ci || exit 0'
                    }
                }
            }
        }
        success {
            echo 'BUILD SUCCESS: ACEest Fitness environment built, linted and tested.'
        }
        failure {
            echo 'BUILD FAILED: check the stage logs above.'
        }
    }
}

// Returns the exit status of a shell command without failing the build.
def runStatus(String cmd) {
    if (isUnix()) {
        return sh(script: cmd, returnStatus: true)
    }
    return bat(script: cmd, returnStatus: true)
}
