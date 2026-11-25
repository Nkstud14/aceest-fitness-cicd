# ACEest Fitness & Performance - CI/CD Pipeline

A comprehensive DevOps implementation of a fitness management application with a fully automated CI/CD pipeline using industry-standard tools and practices.

## Project Overview

ACEest Fitness is a Flask-based web application designed to manage fitness clients, track their progress, and provide comprehensive reporting. This project demonstrates modern DevOps practices including:

- **Containerization**: Docker with multi-stage builds
- **Orchestration**: Kubernetes with rolling, canary, and blue-green deployments
- **CI/CD**: Jenkins pipeline with automated testing and quality checks
- **Code Quality**: SonarQube integration for static analysis
- **Testing**: Comprehensive pytest test suite with code coverage
- **Registry**: Docker Hub integration for image management

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                      GitHub Repository                      │
│                    (Source Code Management)                 │
└────────────────────┬────────────────────────────────────────┘
                     │ Webhook / Poll
┌────────────────────▼────────────────────────────────────────┐
│                   Jenkins Pipeline                          │
├─────────────────────────────────────────────────────────────┤
│ 1. Checkout      2. Build     3. Quality Analysis           │
│ 4. Unit Tests    5. Docker    6. Push Registry              │
│ 7. Staging Dep   8. Smoke     9. Production Deployment      │
└────────────────────┬────────────────────────────────────────┘
                     │
      ┌──────────────┼──────────────┐
      │              │              │
      ▼              ▼              ▼
   SonarQube    Docker Hub    Kubernetes Cluster
                              (Minikube/Cloud)
```

## Application Features

### Core Functionality
- **Client Management**: Create, update, delete fitness clients
- **Workout Tracking**: Log workouts with details (type, duration, notes)
- **Progress Monitoring**: Track weekly adherence and performance metrics
- **Metrics Recording**: Record weight, waist circumference, body fat percentage
- **Program Generation**: AI-style program recommendations
- **Report Generation**: PDF reports for clients

### Technology Stack
- **Backend**: Flask 3.0.0 with SQLAlchemy ORM
- **Database**: SQLite (development) / PostgreSQL (production)
- **API**: RESTful API with JSON responses
- **Testing**: Pytest with code coverage reporting
- **Containerization**: Docker with multi-stage builds
- **Orchestration**: Kubernetes with Helm charts
- **CI/CD**: Jenkins with declarative pipeline

## Deployment Strategies

### 1. Rolling Update (Default)
- Gradually replaces old pods with new ones
- Zero-downtime deployment
- Configuration: maxSurge=1, maxUnavailable=0

### 2. Blue-Green Deployment
- Maintains two identical production environments
- Complete version switch in one operation
- Allows instant rollback
- Files: `k8s/blue-green-deployment.yaml`

### 3. Canary Deployment
- Routes small percentage of traffic to new version
- Monitors metrics and error rates
- Automatically rolls back if issues detected
- Files: `k8s/canary-deployment.yaml`

## Project Structure

```
aceest-fitness/
├── ACEest_Fitness.py              # Main Flask application
├── test_ACEest_Fitness.py         # Pytest test suite
├── requirements.txt               # Python dependencies
├── Dockerfile                     # Multi-stage Docker build
├── Jenkinsfile                    # Jenkins pipeline configuration
├── sonar-project.properties       # SonarQube configuration
├── .gitignore                     # Git ignore patterns
├── k8s/                           # Kubernetes manifests
│   ├── deployment-production.yaml # Production deployment
│   ├── deployment-staging.yaml    # Staging deployment
│   ├── blue-green-deployment.yaml # Blue-green strategy
│   └── canary-deployment.yaml     # Canary deployment strategy
├── docs/
│   └── DEPLOYMENT_GUIDE.md        # Detailed deployment guide
└── VERSION                        # Application version
```

## Getting Started

### Prerequisites
- Docker & Docker Compose
- Kubernetes (Minikube for local, AWS/Azure/GCP for cloud)
- Jenkins with Docker plugin
- SonarQube server
- Git

### Local Development

1. **Clone the Repository**
   ```bash
   git clone https://github.com/yourusername/aceest-fitness.git
   cd aceest-fitness
   ```

2. **Set up Python Environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. **Run Application Locally**
   ```bash
   python ACEest_Fitness.py
   # Access at http://localhost:5000
   # Default credentials: admin/admin123
   ```

4. **Run Tests**
   ```bash
   pytest test_ACEest_Fitness.py -v --cov=. --cov-report=html
   # Coverage report: htmlcov/index.html
   ```

### Docker Build

1. **Build Docker Image**
   ```bash
   docker build -t aceest-fitness:3.2.4 .
   ```

2. **Run Docker Container**
   ```bash
   docker run -d -p 5000:5000 \
     -e FLASK_ENV=development \
     -e FLASK_DEBUG=false \
     aceest-fitness:3.2.4
   ```

3. **Push to Docker Hub**
   ```bash
   docker tag aceest-fitness:3.2.4 yourusername/aceest-fitness:3.2.4
   docker push yourusername/aceest-fitness:3.2.4
   ```

### Kubernetes Deployment

1. **Deploy to Minikube**
   ```bash
   minikube start
   kubectl apply -f k8s/deployment-staging.yaml
   kubectl apply -f k8s/deployment-production.yaml
   ```

2. **Verify Deployment**
   ```bash
   kubectl get deployments -n production
   kubectl get pods -n production
   kubectl get svc -n production
   ```

3. **Access Application**
   ```bash
   # Get LoadBalancer IP
   kubectl get svc aceest-fitness -n production
   # Access: http://<LOAD_BALANCER_IP>:80
   ```

## CI/CD Pipeline

### Jenkins Pipeline Stages

1. **Checkout**: Clone source code from GitHub
2. **Build**: Install dependencies and build Python application
3. **Code Quality Analysis**: Run SonarQube analysis
4. **Unit Tests**: Execute pytest suite with coverage reporting
5. **Build Docker Image**: Create Docker image with version tags
6. **Push to Registry**: Push images to Docker Hub
7. **Security Scan**: Scan Docker image for vulnerabilities (Trivy)
8. **Deploy to Staging**: Deploy to Kubernetes staging namespace
9. **Integration Tests**: Run smoke tests on staging environment
10. **Deploy to Production**: Deploy to Kubernetes production namespace (main branch only)
11. **Smoke Tests**: Verify production deployment health

### Environment Variables

**Jenkins Credentials:**
- `docker_username`: Docker Hub username
- `docker_password`: Docker Hub password
- `sonarqube_host`: SonarQube server URL
- `sonarqube_token`: SonarQube authentication token
- `kubeconfig`: Kubernetes configuration file

### Jenkins Job Configuration

**Trigger:**
- GitHub webhook on push
- Poll SCM: `H/5 * * * *` (every 5 minutes)

**Parameters:**
- DOCKER_REGISTRY: docker.io
- ENVIRONMENT: staging/production

## API Endpoints

### Authentication
- `POST /login` - User login
- `POST /logout` - User logout

### Health Checks
- `GET /health` - Health check
- `GET /ready` - Readiness check

### Clients
- `GET /api/clients` - List all clients
- `POST /api/clients` - Create new client
- `GET /api/clients/<id>` - Get client details
- `PUT /api/clients/<id>` - Update client
- `DELETE /api/clients/<id>` - Delete client

### Workouts
- `GET /api/workouts` - List workouts
- `POST /api/workouts` - Create workout
- `GET /api/workouts?client_id=<id>` - Get client workouts

### Progress
- `GET /api/progress` - List progress records
- `POST /api/progress` - Create progress record

### Metrics
- `GET /api/metrics` - List metrics
- `POST /api/metrics` - Create metric

## Testing

### Unit Tests
```bash
pytest test_ACEest_Fitness.py -v
```

### Coverage Report
```bash
pytest --cov=. --cov-report=html
```

### Test Categories
- Health Endpoints
- Authentication
- Client API Operations
- Workout Management
- Progress Tracking
- Metrics Recording
- Error Handling

## SonarQube Integration

### Configuration File
- **Location**: `sonar-project.properties`
- **Metrics Analyzed**:
  - Code coverage
  - Duplication
  - Complexity
  - Bugs and vulnerabilities
  - Code smells

### View Results
1. Navigate to SonarQube dashboard
2. Project: aceest-fitness
3. Review code quality metrics
4. Track improvements over time

## Challenges & Solutions

### Challenge 1: Database Persistence in Kubernetes
**Problem**: SQLite database lost on pod restart
**Solution**: Implement persistent volumes for production, use PostgreSQL

### Challenge 2: Zero-Downtime Deployments
**Problem**: Existing connections interrupted during updates
**Solution**: Use rolling updates with graceful shutdown period

### Challenge 3: Configuration Management
**Problem**: Different configs for staging and production
**Solution**: Use ConfigMaps and Secrets for environment-specific configuration

### Challenge 4: Image Tag Management
**Problem**: Tracking multiple versions in registry
**Solution**: Use semantic versioning with git tags and pipeline build numbers

## Deployment Strategies Comparison

| Strategy | Downtime | Rollback | Traffic | Use Case |
|----------|----------|----------|---------|----------|
| Rolling | None | Slow | Gradual | Standard updates |
| Blue-Green | None | Instant | Complete | Critical updates |
| Canary | None | Automatic | % Based | High-risk changes |

## Monitoring & Logging

### Kubernetes Monitoring
```bash
# View pod logs
kubectl logs -f deployment/aceest-fitness -n production

# Check pod status
kubectl describe pod <pod-name> -n production

# Monitor resource usage
kubectl top pods -n production
```

### Health Endpoints
- `/health` - Service availability
- `/ready` - Ready to accept traffic

## Security Best Practices

1. **Container Security**
   - Non-root user execution
   - Read-only root filesystem
   - Capability dropping
   - Resource limits

2. **Network Security**
   - Service accounts with limited RBAC
   - Pod security policies
   - Network policies

3. **Secret Management**
   - Kubernetes Secrets for credentials
   - Environment variable injection
   - Credential rotation

4. **Code Security**
   - Dependency scanning
   - Vulnerability assessment
   - SAST with SonarQube

## Troubleshooting

### Pod CrashLoopBackOff
```bash
kubectl logs <pod-name> -n production
kubectl describe pod <pod-name> -n production
```

### Service Not Accessible
```bash
kubectl get svc -n production
kubectl port-forward svc/aceest-fitness 5000:80 -n production
```

### Image Pull Errors
```bash
kubectl create secret docker-registry regcred \
  --docker-server=docker.io \
  --docker-username=<username> \
  --docker-password=<password>
```

## Contributing

1. Create feature branch: `git checkout -b feature/new-feature`
2. Commit changes: `git commit -am 'Add new feature'`
3. Push to branch: `git push origin feature/new-feature`
4. Create Pull Request

## Version History

- **v3.2.4** - Current stable release with blue-green deployment support
- **v3.2.3** - Previous stable release
- **v3.1.2** - Earlier version
- **v3.0.1** - Major release
- **v2.2.4** - Legacy version

## License

MIT License - See LICENSE file for details

## Support & Contact

- **Issues**: GitHub Issues
- **Email**: support@aceest-fitness.com
- **Documentation**: See `/docs` directory

## References

- [Flask Documentation](https://flask.palletsprojects.com/)
- [Kubernetes Documentation](https://kubernetes.io/docs/)
- [Jenkins Pipeline](https://www.jenkins.io/doc/book/pipeline/)
- [SonarQube](https://docs.sonarqube.org/)
- [Docker Best Practices](https://docs.docker.com/develop/dev-best-practices/)
