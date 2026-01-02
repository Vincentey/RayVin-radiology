# Radiology AI - Production Deployment Checklist

## Pre-Launch (Complete Before Going Live)

### ☐ Environment Setup
- [ ] AWS account created with MFA
- [ ] IAM admin user created (not using root)
- [ ] EC2 instance launched (t3.large recommended)
- [ ] Elastic IP allocated and associated
- [ ] Security group configured (SSH restricted to your IP)
- [ ] Key pair downloaded and secured

### ☐ Secrets Generated
- [ ] JWT Secret Key generated: `python -c "import secrets; print(secrets.token_urlsafe(64))"`
- [ ] OpenAI API key obtained
- [ ] Pinecone API key obtained
- [ ] All secrets stored in .env (NOT in git)

### ☐ Code Deployment
- [ ] Code transferred to server (git clone or scp)
- [ ] .env file created with production values
- [ ] Docker and Docker Compose installed
- [ ] Containers built: `docker-compose build`
- [ ] Services started: `docker-compose up -d`
- [ ] Health check passes: `curl http://localhost:8000/health`

### ☐ Security Hardening
- [ ] Default passwords changed in auth.py
- [ ] CORS_ORIGINS set to actual domain
- [ ] HTTPS enabled (self-signed or ACM)
- [ ] Rate limiting added (optional but recommended)
- [ ] Input validation confirmed

### ☐ Testing
- [ ] Login works
- [ ] Signup works
- [ ] File upload works
- [ ] X-ray analysis returns findings
- [ ] RAG recommendations generate
- [ ] All API endpoints respond

---

## Go-Live Day

### Morning
- [ ] Final backup of any existing data
- [ ] Verify all services running: `docker-compose ps`
- [ ] Test login from external network
- [ ] Test file upload from external network

### Afternoon
- [ ] Announce soft launch to test users
- [ ] Monitor logs: `docker-compose logs -f`
- [ ] Check for errors every hour
- [ ] Document any issues

### Evening
- [ ] Review day's activity
- [ ] Fix any critical issues
- [ ] Plan next day's work

---

## Post-Launch (First Week)

### Daily
- [ ] Check health endpoint
- [ ] Review error logs
- [ ] Monitor disk space: `df -h`
- [ ] Check API costs (OpenAI dashboard)

### End of Week
- [ ] Collect user feedback
- [ ] Prioritize bug fixes
- [ ] Plan improvements
- [ ] Security review

---

## Contact Info

| Role | Name | Contact |
|------|------|---------|
| Admin | _______ | _______ |
| DevOps | _______ | _______ |
| Support | _______ | _______ |

---

## Emergency Procedures

### Service Down
```bash
ssh -i "key.pem" ubuntu@XX.XX.XX.XX
docker-compose logs --tail 100
docker-compose restart
```

### Rollback
```bash
docker-compose down
git checkout <previous-commit>
docker-compose build
docker-compose up -d
```

### Contact Support
- AWS Support: aws.amazon.com/support
- OpenAI: platform.openai.com/help



