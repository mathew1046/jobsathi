# GitLab DevSecOps Integration Guide

This document explains how JobSathi uses GitLab's DevSecOps features for automated security, testing, and deployment.

## 🛡️ Security Features Enabled

### 1. **Secret Detection**
- Scans code for exposed API keys, passwords, tokens
- Runs on every commit and merge request
- **Action Required**: Never commit `.env` files (already in `.gitignore`)

### 2. **SAST (Static Application Security Testing)**
- **Bandit**: Python code security scanner
- **Safety**: Checks Python dependencies for known vulnerabilities
- Runs on every push to detect security issues early

### 3. **Dependency Scanning**
- Scans `requirements.txt` (Python) and `package.json` (Node.js)
- Alerts on outdated or vulnerable dependencies
- **Recommendation**: Update dependencies monthly

### 4. **Container Scanning**
- Uses Trivy to scan Docker images for vulnerabilities
- Runs before deploying to staging/production
- Blocks deployment if critical vulnerabilities found

### 5. **License Scanning**
- Identifies all open-source licenses used
- Helps maintain compliance with license requirements

## 🚀 CI/CD Pipeline Stages

```
┌─────────────┐   ┌──────────┐   ┌─────────┐   ┌──────────┐
│  Security   │ → │   Test   │ → │  Build  │ → │  Deploy  │
└─────────────┘   └──────────┘   └─────────┘   └──────────┘
     5 scans         2 tests       2 images      staging/prod
```

### Stage 1: Security (Parallel)
- Secret Detection
- SAST (Bandit + Safety)
- Dependency Scanning (Python + Node.js)
- Container Scanning (Trivy)
- License Scanning

### Stage 2: Test
- Backend: pytest with coverage reporting
- Frontend: npm test + lint

### Stage 3: Build
- Build Docker images for backend and frontend
- Push to GitLab Container Registry
- Tag with commit SHA and `latest`

### Stage 4: Deploy
- **Staging**: Manual deploy from `main` branch
- **Production**: Manual approval required (tags only)

## 📊 Security Dashboard

View security findings at:
```
https://gitlab.com/YOUR_USERNAME/jobsathi/-/security/dashboard
```

### Key Metrics:
- Vulnerability severity distribution
- Dependency health score
- Container image vulnerabilities
- Secret detection alerts

## 🔧 Setup Instructions

### 1. Push Configuration to GitLab

```bash
# Add all DevSecOps files
git add .gitlab-ci.yml .gitlab/ DEVSECOPS.md

# Commit the changes
git commit -m "feat: Add GitLab DevSecOps pipeline with security scanning"

# Push to GitLab
git push origin main
```

### 2. Configure GitLab Variables

Go to: **Settings → CI/CD → Variables**

Add these **protected** and **masked** variables:

| Variable | Value | Protected | Masked | Description |
|----------|-------|-----------|--------|-------------|
| `GEMINI_API_KEY` | `your_key` | ✅ | ✅ | Google Gemini API |
| `ADZUNA_APP_ID` | `your_id` | ✅ | ✅ | Adzuna job search |
| `ADZUNA_APP_KEY` | `your_key` | ✅ | ✅ | Adzuna API key |
| `JOOBLE_KEY` | `your_key` | ✅ | ✅ | Jooble API key |
| `SERPAPI_KEY` | `your_key` | ✅ | ✅ | SerpAPI key |

**Note**: `CI_REGISTRY`, `CI_REGISTRY_USER`, `CI_REGISTRY_PASSWORD` are automatically provided by GitLab.

### 3. Enable Security Features

Go to: **Security & Compliance → Configuration**

Enable:
- ✅ SAST (Static Application Security Testing)
- ✅ Dependency Scanning
- ✅ Secret Detection
- ✅ Container Scanning
- ✅ License Compliance

### 4. Configure Merge Request Settings

Go to: **Settings → Merge Requests**

- ✅ Enable "Pipelines must succeed"
- ✅ Enable "All discussions must be resolved"
- Set **Merge checks**: Require 1-2 approvals
- ✅ Enable "Remove source branch" after merge

### 5. Protect Main Branch

Go to: **Settings → Repository → Protected Branches**

For `main` branch:
- **Allowed to merge**: Maintainers only
- **Allowed to push**: No one
- **Allowed to force push**: Disabled
- ✅ Require approval from code owners

### 6. Test the Pipeline

```bash
# Create a test branch
git checkout -b test/devsecops-pipeline

# Make a small change
echo "# DevSecOps Pipeline Test" >> README.md
git add README.md
git commit -m "test: Verify DevSecOps pipeline"

# Push and create merge request
git push origin test/devsecops-pipeline

# Go to GitLab UI:
# 1. Create Merge Request
# 2. Watch pipeline run (5 security scans, 2 tests)
# 3. Review security scan results
# 4. Merge if all checks pass
```

## 🚨 Security Alerts & Response

### Critical Vulnerability Found

1. **Check Security Dashboard** for details
2. **Identify** affected dependency or code
3. **Update** dependency: `pip install --upgrade package` or `npm update`
4. **Verify** fix by re-running pipeline
5. **Document** in commit message

### Secret Detected

⚠️ **IMMEDIATE ACTION REQUIRED**:

1. **Revoke** the exposed secret immediately
2. **Generate** new secret/API key
3. **Update** GitLab CI/CD variables
4. **Update** local `.env` file
5. **Verify** `.gitignore` includes `.env`
6. **Re-run** pipeline to confirm

### Dependency with Known Vulnerability

```bash
# Check which package is vulnerable
safety check -r backend/app/requirements.txt

# Update specific package
pip install --upgrade vulnerable-package

# Update all packages (careful!)
pip install --upgrade -r backend/app/requirements.txt

# Test locally
pytest

# Commit and push
git add backend/app/requirements.txt
git commit -m "fix: Update vulnerable dependency"
git push
```

## 📈 Best Practices

### 1. **Branch Protection**
- Always work in feature branches
- Never push directly to `main`
- Require CI pipeline to pass before merge
- Require code review approval

### 2. **Regular Dependency Updates**

**Weekly**:
```bash
# Check for outdated packages
pip list --outdated
npm outdated
```

**Monthly**:
```bash
# Update Python dependencies
pip install --upgrade -r backend/app/requirements.txt
pip freeze > backend/app/requirements.txt

# Update Node.js dependencies
cd frontend && npm update
```

### 3. **Local Security Scanning**

Before committing:
```bash
# Run Bandit (Python security)
pip install bandit
bandit -r backend/app/

# Check for secrets
pip install detect-secrets
detect-secrets scan

# Audit npm packages
cd frontend && npm audit

# Fix automatically
npm audit fix
```

### 4. **Docker Image Security**

```bash
# Scan local images before pushing
docker run --rm -v /var/run/docker.sock:/var/run/docker.sock \
  aquasec/trivy image jobsathi-backend:latest

# Use security-hardened Dockerfile
docker build -f .gitlab/Dockerfile.security -t jobsathi-backend:secure .
```

## 🎯 Compliance & Reporting

### Generate Security Report

From GitLab UI:
1. Go to **Security & Compliance → Vulnerability Report**
2. Filter by severity: Critical, High, Medium, Low
3. Click **Export** → Download CSV or PDF

### Audit Log

View all security events:
- Go to **Settings → Audit Events**
- Filter by date, user, or action type

### License Compliance

View all dependencies and licenses:
- Go to **Security & Compliance → License Compliance**
- Export license report

## 🔄 Continuous Improvement

### Daily Tasks (Automated)
- ✅ Secret detection on every commit
- ✅ SAST on every push
- ✅ Dependency scanning on every MR

### Weekly Tasks
- [ ] Review Security Dashboard
- [ ] Check for new vulnerabilities
- [ ] Review failed pipelines

### Monthly Tasks
- [ ] Full dependency audit and updates
- [ ] Review and update security policies
- [ ] Container image security scan
- [ ] License compliance review

### Quarterly Tasks
- [ ] Penetration testing (if applicable)
- [ ] Security training for team
- [ ] Review access controls
- [ ] Update security documentation

## 📊 Pipeline Success Metrics

After successful setup, you should see:

- ✅ Green pipeline badge on merge requests
- ✅ Security Dashboard populated with scan results
- ✅ No exposed secrets detected
- ✅ Container images scanned before deployment
- ✅ Merge requests blocked if critical vulnerabilities found
- ✅ All tests passing
- ✅ Code coverage reports available

## 📚 Resources

- [GitLab Security Documentation](https://docs.gitlab.com/ee/user/application_security/)
- [GitLab CI/CD Variables](https://docs.gitlab.com/ee/ci/variables/)
- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [Container Security Best Practices](https://docs.docker.com/develop/security-best-practices/)
- [Bandit Documentation](https://bandit.readthedocs.io/)
- [Trivy Documentation](https://aquasecurity.github.io/trivy/)

## 🆘 Troubleshooting

### Pipeline Fails: Secret Detection

**Problem**: Secret detected in code

**Solution**:
```bash
# Check what was detected
git log --all --full-history -- "**/.env"

# Remove from history (if accidentally committed)
git filter-branch --force --index-filter \
  "git rm --cached --ignore-unmatch backend/.env" \
  --prune-empty --tag-name-filter cat -- --all

# Force push (⚠️ coordinate with team)
git push origin --force --all
```

### Pipeline Fails: SAST

**Problem**: Bandit reports false positives

**Solution**: Add exceptions in `.gitlab-ci.yml`:
```yaml
sast:
  script:
    - bandit -r backend/app/ -f json -o bandit-report.json \
      --skip B101,B601  # Skip assert_used, subprocess_popen
```

### Pipeline Fails: Dependency Scanning

**Problem**: Vulnerable dependency detected

**Solution**:
```bash
# Identify vulnerable package
safety check -r backend/app/requirements.txt

# Update to safe version
pip install --upgrade package-name==safe-version

# Or update all
pip install --upgrade -r backend/app/requirements.txt

# Test
pytest

# Commit
git add backend/app/requirements.txt
git commit -m "fix(deps): Update vulnerable dependencies"
```

### Pipeline Fails: Container Scanning

**Problem**: Base image has vulnerabilities

**Solution**: Use security-hardened Dockerfile:
```bash
# Build with security-hardened file
docker build -f .gitlab/Dockerfile.security -t jobsathi-backend:latest .

# Or update base image
# In Dockerfile: python:3.12-slim → python:3.12-slim-bookworm
```

### Build Fails: Missing Environment Variables

**Problem**: `GEMINI_API_KEY not found`

**Solution**:
1. Go to **Settings → CI/CD → Variables**
2. Add `GEMINI_API_KEY` with **Protected** and **Masked** checked
3. Re-run pipeline

## 🎉 Success!

Your project now has:
- ✅ **Automated security scanning** on every commit
- ✅ **Container vulnerability detection**
- ✅ **Secret detection** to prevent API key leaks
- ✅ **Dependency monitoring** for vulnerable packages
- ✅ **License compliance** tracking
- ✅ **Quality gates** to block insecure code
- ✅ **Enterprise-grade security**

**Never commit security fixes that expose vulnerabilities in commit messages or code comments.**

For critical security issues, contact your security team immediately.
