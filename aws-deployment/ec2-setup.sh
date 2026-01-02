#!/bin/bash
# Radiology AI Assistant - EC2 Quick Setup Script
# Run this on a fresh Amazon Linux 2023 or Ubuntu 22.04 EC2 instance

set -e

echo "=============================================="
echo "  Radiology AI Assistant - EC2 Setup"
echo "=============================================="

# Detect OS
if [ -f /etc/os-release ]; then
    . /etc/os-release
    OS=$ID
else
    echo "Cannot detect OS"
    exit 1
fi

echo "Detected OS: $OS"

# Install Docker
echo "Installing Docker..."
if [ "$OS" = "amzn" ]; then
    sudo yum update -y
    sudo yum install -y docker git
    sudo systemctl start docker
    sudo systemctl enable docker
elif [ "$OS" = "ubuntu" ]; then
    sudo apt update
    sudo apt install -y docker.io docker-compose git
    sudo systemctl start docker
    sudo systemctl enable docker
else
    echo "Unsupported OS: $OS"
    exit 1
fi

# Add user to docker group
sudo usermod -aG docker $USER

# Install docker-compose if not present
if ! command -v docker-compose &> /dev/null; then
    echo "Installing docker-compose..."
    sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    sudo chmod +x /usr/local/bin/docker-compose
fi

echo ""
echo "=============================================="
echo "  Docker installed successfully!"
echo "=============================================="
echo ""
echo "NEXT STEPS:"
echo ""
echo "1. Log out and log back in (for docker group)"
echo "   exit"
echo ""
echo "2. Clone or upload your project files"
echo "   git clone YOUR_REPO_URL"
echo "   cd rass"
echo ""
echo "3. Create your .env file"
echo "   nano .env"
echo ""
echo "4. Add these values to .env:"
echo "   OPENAI_API_KEY=sk-proj-YOUR_KEY"
echo "   PINECONE_API_KEY=YOUR_KEY"
echo "   JWT_SECRET_KEY=OiUdut1bM4sMdFz6TDex3umQqyAUj0U1gXNeRzfGIl9teobDfmC6Xp_lYgYw_geMpT0VieazBfVolJ4CK-ET6w"
echo "   CORS_ORIGINS=http://YOUR_ELASTIC_IP"
echo ""
echo "5. Start the application"
echo "   docker-compose up --build -d"
echo ""
echo "6. Check status"
echo "   docker-compose ps"
echo "   docker-compose logs -f"
echo ""



