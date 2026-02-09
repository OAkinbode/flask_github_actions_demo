# Flask App with CI/CD to Azure

A sample Flask application with automated CI/CD pipeline using GitHub Actions to deploy to Azure Container Instances.

## Features

- ✅ Flask web application
- ✅ Automated testing with pytest
- ✅ Docker containerization
- ✅ CI/CD pipeline with GitHub Actions
- ✅ Deployment to Azure Container Instances
- ✅ Health checks and monitoring

## Project Structure

```
my-flask-app/
├── .github/
│   └── workflows/
│       └── deploy.yml          # GitHub Actions workflow
├── app/
│   ├── __init__.py
│   └── routes.py               # Application routes
├── tests/
│   ├── __init__.py
│   └── test_app.py             # Unit tests
├── Dockerfile                   # Docker configuration
├── requirements.txt             # Python dependencies
├── app.py                       # Application entry point
└── README.md                    # This file
```

## Local Development

### Prerequisites

- Python 3.11+
- Docker (optional, for local container testing)

### Setup

1. Clone the repository:
```bash
git clone <your-repo-url>
cd my-flask-app
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Run the application:
```bash
python app.py
```

The app will be available at `http://localhost:5000`

### Available Endpoints

- `GET /` - Welcome message
- `GET /health` - Health check endpoint
- `GET /api/info` - Application information

### Running Tests

```bash
pytest
```

With coverage:
```bash
pytest --cov=app --cov-report=term-missing
```

## Docker

### Build the image:
```bash
docker build -t flask-app .
```

### Run the container:
```bash
docker run -p 5000:5000 flask-app
```

## Azure Setup

### Prerequisites

1. Azure account with active subscription
2. Azure CLI installed

### Setup Steps

1. **Create Resource Group:**
```bash
az group create --name flask-app-rg --location eastus
```

2. **Create Azure Container Registry:**
```bash
az acr create \
  --resource-group flask-app-rg \
  --name myflaskapp \
  --sku Basic \
  --admin-enabled true
```

3. **Get ACR credentials:**
```bash
az acr credential show --name myflaskapp
```

4. **Create Service Principal for GitHub Actions:**
```bash
az ad sp create-for-rbac \
  --name "github-actions-flask-app" \
  --role contributor \
  --scopes /subscriptions/{subscription-id}/resourceGroups/flask-app-rg \
  --sdk-auth
```

### GitHub Secrets

Add these secrets to your GitHub repository (Settings → Secrets and variables → Actions):

- `AZURE_CREDENTIALS` - Output from the service principal creation (JSON format)
- `AZURE_ACR_USERNAME` - Azure Container Registry username
- `AZURE_ACR_PASSWORD` - Azure Container Registry password
- `SLACK_WEBHOOK` (Optional) - Slack webhook URL for notifications

## CI/CD Pipeline

The GitHub Actions workflow (`.github/workflows/deploy.yml`) automatically:

1. **Test** - Runs unit tests with coverage on every push/PR
2. **Build** - Builds Docker image and pushes to Azure Container Registry (on main branch)
3. **Deploy** - Deploys to Azure Container Instances (on main branch)
4. **Notify** - Sends deployment status to Slack (optional)

### Workflow Triggers

- Push to `main` branch
- Pull requests to `main` branch
- Manual trigger via workflow_dispatch

### Customization

Update these environment variables in `.github/workflows/deploy.yml`:

```yaml
env:
  AZURE_CONTAINER_REGISTRY: myflaskapp  # Your ACR name
  AZURE_RESOURCE_GROUP: flask-app-rg    # Your resource group
  CONTAINER_NAME: flask-app             # Your container name
  IMAGE_NAME: flask-web-app             # Your image name
```

## Deployment

Once configured, simply push to the `main` branch:

```bash
git add .
git commit -m "Deploy new version"
git push origin main
```

The GitHub Actions workflow will automatically:
- Run tests
- Build and push Docker image
- Deploy to Azure Container Instances
- Perform health checks

## Monitoring

After deployment, access your application at:
```
http://{CONTAINER_NAME}-{github-sha}.eastus.azurecontainer.io:5000
```

Check application health:
```bash
curl http://your-app-url/health
```

## License

MIT License

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request
