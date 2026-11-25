pipeline {
    agent any
    
    environment {
        DOCKER_REGISTRY = 'docker.io'
        DOCKER_USERNAME = credentials('docker_username')
        DOCKER_PASSWORD = credentials('docker_password')
        IMAGE_NAME = 'aceest-fitness'
        REGISTRY_URL = "${DOCKER_USERNAME}/${IMAGE_NAME}"
        SONARQUBE_HOST = credentials('sonarqube_host')
        SONARQUBE_TOKEN = credentials('sonarqube_token')
        KUBECONFIG = credentials('kubeconfig')
    }
    
    options {
        timestamps()
        timeout(time: 1, unit: 'HOURS')
        buildDiscarder(logRotator(numToKeepStr: '10'))
    }
    
    stages {
        stage('Checkout') {
            steps {
                script {
                    echo "Checking out source code..."
                    checkout scm
                    sh 'git log -1 --pretty=%B'
                }
            }
        }
        
        stage('Build') {
            steps {
                script {
                    echo "Building Python application..."
                    sh '''
                        python --version
                        pip install -r requirements.txt
                    '''
                }
            }
        }
        
        stage('Code Quality Analysis') {
            steps {
                script {
                    echo "Running SonarQube analysis..."
                    sh '''
                        pip install sonar-scanner
                        sonar-scanner \
                            -Dsonar.projectKey=aceest-fitness \
                            -Dsonar.sources=. \
                            -Dsonar.host.url=${SONARQUBE_HOST} \
                            -Dsonar.login=${SONARQUBE_TOKEN} \
                            -Dsonar.exclusions=**/*.pyc,**/tests/**,**/venv/** \
                            -Dsonar.python.coverage.reportPaths=coverage.xml
                    '''
                }
            }
        }
        
        stage('Unit Tests') {
            steps {
                script {
                    echo "Running pytest test suite..."
                    sh '''
                        pip install pytest pytest-cov
                        pytest test_ACEest_Fitness.py -v --cov=. --cov-report=xml --cov-report=html --junitxml=test-results.xml
                    '''
                }
            }
            post {
                always {
                    junit 'test-results.xml'
                    publishHTML([
                        allowMissing: false,
                        alwaysLinkToLastBuild: true,
                        keepAll: true,
                        reportDir: 'htmlcov',
                        reportFiles: 'index.html',
                        reportName: 'Coverage Report'
                    ])
                }
            }
        }
        
        stage('Build Docker Image') {
            steps {
                script {
                    echo "Building Docker image..."
                    sh '''
                        VERSION=$(cat VERSION 2>/dev/null || echo "3.2.4")
                        docker build -t ${REGISTRY_URL}:${VERSION} \
                                     -t ${REGISTRY_URL}:latest \
                                     -t ${REGISTRY_URL}:${BUILD_NUMBER} .
                    '''
                }
            }
        }
        
        stage('Push to Registry') {
            steps {
                script {
                    echo "Pushing Docker image to registry..."
                    sh '''
                        echo ${DOCKER_PASSWORD} | docker login -u ${DOCKER_USERNAME} --password-stdin ${DOCKER_REGISTRY}
                        VERSION=$(cat VERSION 2>/dev/null || echo "3.2.4")
                        docker push ${REGISTRY_URL}:${VERSION}
                        docker push ${REGISTRY_URL}:latest
                        docker push ${REGISTRY_URL}:${BUILD_NUMBER}
                    '''
                }
            }
        }
        
        stage('Security Scan') {
            steps {
                script {
                    echo "Running security scan on Docker image..."
                    sh '''
                        VERSION=$(cat VERSION 2>/dev/null || echo "3.2.4")
                        docker run --rm -v /var/run/docker.sock:/var/run/docker.sock \
                            aquasec/trivy image --severity HIGH,CRITICAL \
                            ${REGISTRY_URL}:${VERSION} || true
                    '''
                }
            }
        }
        
        stage('Deploy to Staging') {
            steps {
                script {
                    echo "Deploying to Kubernetes staging environment..."
                    sh '''
                        VERSION=$(cat VERSION 2>/dev/null || echo "3.2.4")
                        kubectl set image deployment/aceest-fitness-staging \
                                 aceest-fitness=${REGISTRY_URL}:${VERSION} \
                                 --namespace=staging || \
                        kubectl apply -f k8s/deployment-staging.yaml -n staging
                        kubectl rollout status deployment/aceest-fitness-staging -n staging --timeout=5m
                    '''
                }
            }
        }
        
        stage('Integration Tests') {
            steps {
                script {
                    echo "Running integration tests..."
                    sh '''
                        sleep 30
                        STAGING_URL=$(kubectl get svc aceest-fitness-staging -n staging -o jsonpath='{.status.loadBalancer.ingress[0].ip}' 2>/dev/null || echo "localhost")
                        curl -f http://${STAGING_URL}:5000/health || exit 1
                        pytest test_integration.py -v || true
                    '''
                }
            }
        }
        
        stage('Deploy to Production') {
            when {
                branch 'main'
            }
            steps {
                script {
                    echo "Deploying to Kubernetes production environment..."
                    sh '''
                        VERSION=$(cat VERSION 2>/dev/null || echo "3.2.4")
                        kubectl set image deployment/aceest-fitness \
                                 aceest-fitness=${REGISTRY_URL}:${VERSION} \
                                 --namespace=production || \
                        kubectl apply -f k8s/deployment-production.yaml -n production
                        kubectl rollout status deployment/aceest-fitness -n production --timeout=5m
                    '''
                }
            }
        }
        
        stage('Smoke Tests') {
            when {
                branch 'main'
            }
            steps {
                script {
                    echo "Running smoke tests on production..."
                    sh '''
                        PROD_URL=$(kubectl get svc aceest-fitness -n production -o jsonpath='{.status.loadBalancer.ingress[0].ip}' 2>/dev/null || echo "localhost")
                        curl -f http://${PROD_URL}:5000/health || exit 1
                        curl -f http://${PROD_URL}:5000/ready || exit 1
                    '''
                }
            }
        }
    }
    
    post {
        always {
            script {
                echo "Cleaning up workspace..."
                sh '''
                    docker logout ${DOCKER_REGISTRY} || true
                    rm -rf venv/ __pycache__/ .pytest_cache/ htmlcov/
                '''
            }
            cleanWs()
        }
        success {
            echo "Pipeline succeeded!"
        }
        failure {
            echo "Pipeline failed!"
        }
    }
}
