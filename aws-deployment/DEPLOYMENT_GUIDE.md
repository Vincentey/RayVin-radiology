# AWS Deployment Guide - Radiology AI Assistant

## Overview

This guide walks you through deploying the Radiology AI Assistant on AWS. 

**No domain required** - we'll use AWS's provided DNS names.

---

## Architecture Options

### Option 1: EC2 with Docker (Simplest - Recommended for Quick Start)
- Single EC2 instance running Docker
- Elastic IP for stable address
- Self-signed HTTPS or AWS ACM with ALB

### Option 2: ECS Fargate (Production - Scalable)
- Serverless container hosting
- Application Load Balancer with HTTPS
- Auto-scaling capabilities

---

## Option 1: EC2 Deployment (Quick Start)

### Step 1: Launch EC2 Instance

1. **Go to EC2 Console** → Launch Instance
2. **Settings:**
   - Name: `radiology-ai-server`
   - AMI: Amazon Linux 2023 or Ubuntu 22.04
   - Instance type: `t3.large` (2 vCPU, 8GB RAM) minimum
   - Key pair: Create or select existing
   - Security Group: Create new with these rules:
     - SSH (22) - Your IP only
     - HTTP (80) - Anywhere (0.0.0.0/0)
     - HTTPS (443) - Anywhere (0.0.0.0/0)
     - Custom TCP (8000) - Anywhere (for API)

3. **Storage:** 30GB gp3

### Step 2: Allocate Elastic IP

1. Go to **EC2 → Elastic IPs**
2. Click **Allocate Elastic IP address**
3. **Associate** it with your EC2 instance
4. Note this IP: `XX.XX.XX.XX` - this is your permanent address

### Step 3: Connect and Install Docker

```bash
# Connect to your instance
ssh -i your-key.pem ec2-user@XX.XX.XX.XX

# Update system
sudo yum update -y  # Amazon Linux
# OR
sudo apt update && sudo apt upgrade -y  # Ubuntu

# Install Docker
sudo yum install -y docker  # Amazon Linux
# OR
sudo apt install -y docker.io docker-compose  # Ubuntu

# Start Docker
sudo systemctl start docker
sudo systemctl enable docker
sudo usermod -aG docker $USER

# Logout and reconnect for docker group to take effect
exit
ssh -i your-key.pem ec2-user@XX.XX.XX.XX
```

### Step 4: Deploy Application

```bash
# Clone your repository (or upload files)
git clone https://github.com/YOUR_REPO/rass.git
cd rass

# Create .env file
cat > .env << 'EOF'
OPENAI_API_KEY=sk-proj-YOUR_KEY_HERE
PINECONE_API_KEY=YOUR_PINECONE_KEY_HERE
JWT_SECRET_KEY=OiUdut1bM4sMdFz6TDex3umQqyAUj0U1gXNeRzfGIl9teobDfmC6Xp_lYgYw_geMpT0VieazBfVolJ4CK-ET6w
CORS_ORIGINS=http://XX.XX.XX.XX,https://XX.XX.XX.XX
API_PORT=8000
FRONTEND_PORT=80
EOF

# Build and run with Docker Compose
docker-compose up --build -d

# Check status
docker-compose ps
docker-compose logs -f
```

### Step 5: Access Your Application

- **Frontend:** `http://XX.XX.XX.XX`
- **API Docs:** `http://XX.XX.XX.XX:8000/docs`
- **Health Check:** `http://XX.XX.XX.XX:8000/health`

---

## Setting Up HTTPS (Without Domain)

### Option A: Self-Signed Certificate (Quick)

Good for development/testing. Browsers will show warning but still works.

```bash
# Generate self-signed certificate
sudo mkdir -p /etc/nginx/ssl
sudo openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout /etc/nginx/ssl/nginx.key \
  -out /etc/nginx/ssl/nginx.crt \
  -subj "/C=US/ST=State/L=City/O=Hospital/CN=XX.XX.XX.XX"

# Update nginx.conf to use SSL
# (see nginx-ssl.conf in this folder)
```

### Option B: AWS Application Load Balancer + ACM (Production)

This provides **FREE** valid HTTPS certificate from AWS, but requires ALB.

1. **Create Application Load Balancer:**
   - Go to EC2 → Load Balancers → Create
   - Type: Application Load Balancer
   - Scheme: Internet-facing
   - Listeners: HTTP (80), HTTPS (443)
   - Security Group: Allow 80, 443 from anywhere

2. **Request ACM Certificate:**
   - Go to AWS Certificate Manager
   - Request public certificate
   - For "Domain name" use: `*.elb.amazonaws.com` (or your domain later)
   - Choose DNS validation

3. **Configure HTTPS Listener:**
   - Add HTTPS:443 listener
   - Select your ACM certificate
   - Forward to target group (your EC2)

4. **Access via ALB DNS:**
   - Find ALB DNS name (e.g., `radiology-alb-123456.us-east-1.elb.amazonaws.com`)
   - Access: `https://radiology-alb-123456.us-east-1.elb.amazonaws.com`

---

## Option 2: ECS Fargate Deployment (Advanced)

### Step 1: Create ECR Repository

```bash
# Create repository
aws ecr create-repository --repository-name radiology-ai

# Login to ECR
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin YOUR_ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com

# Build and push
docker build -t radiology-ai .
docker tag radiology-ai:latest YOUR_ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com/radiology-ai:latest
docker push YOUR_ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com/radiology-ai:latest
```

### Step 2: Store Secrets in Secrets Manager

```bash
# Create secrets
aws secretsmanager create-secret --name radiology/openai-key \
  --secret-string "sk-proj-YOUR_OPENAI_KEY"

aws secretsmanager create-secret --name radiology/pinecone-key \
  --secret-string "YOUR_PINECONE_KEY"

aws secretsmanager create-secret --name radiology/jwt-secret \
  --secret-string "OiUdut1bM4sMdFz6TDex3umQqyAUj0U1gXNeRzfGIl9teobDfmC6Xp_lYgYw_geMpT0VieazBfVolJ4CK-ET6w"
```

### Step 3: Create ECS Cluster

1. Go to **ECS Console → Clusters → Create Cluster**
2. Choose **Networking only (Fargate)**
3. Name: `radiology-cluster`

### Step 4: Create Task Definition

1. Use the `task-definition.json` in this folder
2. Replace `YOUR_ACCOUNT_ID` and `YOUR_REGION`
3. Register: `aws ecs register-task-definition --cli-input-json file://task-definition.json`

### Step 5: Create Service with ALB

1. Create service from task definition
2. Add Application Load Balancer
3. Configure health check path: `/health`

---

## Cost Estimates (Monthly)

| Component | EC2 Option | ECS Fargate Option |
|-----------|------------|-------------------|
| Compute | ~$60 (t3.large) | ~$100-200 |
| Load Balancer | $0 (optional) or ~$20 | ~$20 |
| Data Transfer | ~$10 | ~$10 |
| Secrets Manager | ~$1 | ~$1 |
| **Total** | **~$70-90** | **~$130-230** |

---

## Pinecone Free Tier Notes

Pinecone free tier includes:
- 1 project
- 1 index with 100K vectors
- Sufficient for this application (~18 pathologies)

No changes needed - the code works with free tier.

---

## Quick Reference

### Your JWT Secret Key
```
OiUdut1bM4sMdFz6TDex3umQqyAUj0U1gXNeRzfGIl9teobDfmC6Xp_lYgYw_geMpT0VieazBfVolJ4CK-ET6w
```

### Default Credentials
| Username | Password | Role |
|----------|----------|------|
| admin | admin123 | Admin |
| radiologist | rad123 | Radiologist |
| user | user123 | User |

### URLs (replace XX.XX.XX.XX with your Elastic IP)
- Frontend: `http://XX.XX.XX.XX`
- API: `http://XX.XX.XX.XX:8000`
- Swagger Docs: `http://XX.XX.XX.XX:8000/docs`
- Health Check: `http://XX.XX.XX.XX:8000/health`

---

## Troubleshooting

### Container won't start
```bash
docker-compose logs api
```

### API not responding
```bash
# Check if container is running
docker ps

# Check health
curl http://localhost:8000/health
```

### Out of memory
- Upgrade to larger instance (t3.xlarge = 16GB RAM)
- Or add swap space

### Model loading slow
First request loads the AI models (~500MB). This takes 30-60 seconds. Subsequent requests are fast.

---

## Getting a Domain Name Later

When you're ready for a custom domain:

1. **Register domain** at Route 53, Namecheap, GoDaddy, etc.
2. **Create hosted zone** in Route 53
3. **Point domain to your Elastic IP** or ALB
4. **Get free SSL certificate** from AWS ACM
5. **Update CORS_ORIGINS** in your .env file

---

## Support

If you encounter issues:
1. Check CloudWatch logs
2. Review container logs: `docker-compose logs`
3. Verify security group allows traffic
4. Ensure API keys are correctly set


