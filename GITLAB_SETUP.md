# 🚀 GitLab DevSecOps Setup Guide

## Quick Setup (5 Minutes)

### Step 1: Push Configuration to GitLab

```bash
cd /home/mathew/jobsathi

# Add all DevSecOps files
git add .gitlab-ci.yml .gitlab/ DEVSECOPS.md GITLAB_SETUP.md

# Commit
git commit -m "feat: Add GitLab DevSecOps pipeline with automated security scanning"

# Push to GitLab
git push origin main
```

### Step 2: Configure API Keys in GitLab

1. **Go to your GitLab project**: `https://gitlab.com/YOUR_USERNAME/jobsathi`

2. **Navigate to**: `Settings → CI/CD → Variables`

3. **Click "Add variable"** and add each of these:

| Key | Value | Type | Protected | Masked |
|-----|-------|------|-----------|--------|
| `GEMINI_API_KEY` | `AIzaSyDXNy1EXRlMnUYmoJYesy94SiDSc_rEYw8` | Variable | ✅ | ✅ |
| `ADZUNA_APP_ID` | `fe5df370` | Variable | ✅ | ✅ |
| `ADZUNA_APP_KEY` | `b5c45eed8f4fe54c6b5792413e5b40fb` | Variable | ✅ | ✅ |
| `JOOBLE_KEY` | `c17afd80-1164-4d6b-8a46-51d256a82728` | Variable | ✅ | ✅ |
| `SERPAPI_KEY` | `a3241c003b016f9044890f9f0fa870f3a58db4535e46692f64d7ff508665d9d8` | Variable | ✅ | ✅ |

**Important**: 
- ✅ Check **"Protected"** (only available in protected branches)
- ✅ Check **"Masked"** (hides value in job logs)
- ❌ Uncheck **"Expand variable reference"**

### Step 3: Enable Security Features

1. **Go to**: `Security & Compliance → Configuration`

2. **Enable these features**:
   - ✅ SAST (Static Application Security Testing)
   - ✅ Dependency Scanning
   - ✅ Secret Detection
   - ✅ Container Scanning
   - ✅ License Compliance

3. **Click "Configure" next to each** and accept defaults

### Step 4: Configure Merge Request Settings

1. **Go to**: `Settings → Merge Requests`

2. **Enable**:
   - ✅ Pipelines must succeed
   - ✅ All discussions must be resolved
   - ✅ Remove source branch after merge

3. **Set Merge checks**:
   - Approvals required: `1` (or `2` for critical projects)

### Step 5: Protect Main Branch

1. **Go to**: `Settings → Repository → Protected Branches`

2. **Find `main` branch** and set:
   - Allowed to merge: **Maintainers**
   - Allowed to push: **No one**
   - Allowed to force push: **Disabled** ❌

3. **Click "Protect"**

## 🧪 Test the Pipeline

### Create a Test Merge Request

```bash
# Create test branch
git checkout -b test/verify-devsecops

# Make a small change
echo "# Pipeline Test" >> README.md
git add README.md
git commit -m "test: Verify DevSecOps pipeline works"

# Push
git push origin test/verify-devsecops
```

### Watch Pipeline Run

1. **Go to GitLab**: Your project → Merge Requests
2. **Click "Create merge request"**
3. **Watch the pipeline run** (should take 5-10 minutes):
   - ✅ Secret Detection
   - ✅ SAST (Bandit + Safety)
   - ✅ Dependency Scanning
   - ✅ Container Scanning
   - ✅ License Scanning
   - ✅ Backend Tests
   - ✅ Frontend Tests

4. **Review results** in the MR interface
5. **Merge** if all checks pass

## 📊 View Security Dashboard

After the first pipeline runs:

1. **Go to**: `Security & Compliance → Vulnerability Report`
2. **View**:
   - Vulnerability severity distribution
   - Affected dependencies
   - Container image vulnerabilities
   - License compliance status

## 🎯 What Gets Scanned

| Scan Type | Tool | Runs On | Checks For |
|-----------|------|---------|------------|
| **Secret Detection** | GitLab Secrets | Every commit | API keys, passwords, tokens |
| **SAST** | Bandit + Safety | Every commit | Python code vulnerabilities |
| **Dependency Scan** | Safety + npm audit | Every commit | Vulnerable packages |
| **Container Scan** | Trivy | Main/MR only | Docker image vulnerabilities |
| **License Scan** | pip-licenses | Every commit | Open-source licenses |

## 🔔 Notifications

### Enable Email Notifications

1. **Go to**: `Settings → Notifications`
2. **Set notification level**: Custom
3. **Enable**:
   - ✅ Failed pipeline
   - ✅ Fixed pipeline
   - ✅ New issue
   - ✅ Merge request status

### Enable Slack/Discord Notifications (Optional)

1. **Go to**: `Settings → Integrations`
2. **Choose**: Slack or Discord
3. **Configure** webhook URL
4. **Enable** pipeline notifications

## 🚨 Common Issues & Solutions

### Issue 1: "GEMINI_API_KEY not found"

**Solution**: 
```bash
# Verify variables are set
# Go to: Settings → CI/CD → Variables
# Check that GEMINI_API_KEY exists and is marked as Protected + Masked
```

### Issue 2: Pipeline Fails on Secret Detection

**Cause**: `.env` file was accidentally committed

**Solution**:
```bash
# Check if .env is in git history
git log --all --full-history -- "*/.env"

# Remove from git but keep local file
git rm --cached backend/.env frontend/.env
git commit -m "fix: Remove .env files from git"
git push

# Verify .gitignore includes .env
grep "\.env" .gitignore
```

### Issue 3: Container Scanning Takes Too Long

**Solution**: Cache Docker layers
```yaml
# In .gitlab-ci.yml, add:
container_scanning:
  cache:
    key: docker-layers
    paths:
      - docker-cache/
```

### Issue 4: Build Stage Fails (No Registry Access)

**Note**: Build stage only runs on `main` branch or tags. The registry variables are automatically provided by GitLab.

**To skip builds initially**:
```bash
# Push to main without triggering builds
git push -o ci.skip origin main
```

## 📈 Pipeline Stages Explained

```
┌───────────────────────────────────────────────────────┐
│                    SECURITY (5 scans)                  │
├──────────┬──────────┬──────────┬──────────┬───────────┤
│ Secret   │  SAST    │ Dependency│Container │ License   │
│ Detection│ (Bandit) │ Scanning  │ Scanning │ Scanning  │
└──────────┴──────────┴──────────┴──────────┴───────────┘
                           ↓
┌───────────────────────────────────────────────────────┐
│                    TESTING (2 jobs)                    │
├──────────────────────────┬────────────────────────────┤
│    Backend Tests         │    Frontend Tests          │
│    (pytest + coverage)   │    (npm test + lint)       │
└──────────────────────────┴────────────────────────────┘
                           ↓
┌───────────────────────────────────────────────────────┐
│                    BUILD (2 images)                    │
├──────────────────────────┬────────────────────────────┤
│    Build Backend Image   │    Build Frontend Image    │
│    (Docker + Push)       │    (Docker + Push)         │
└──────────────────────────┴────────────────────────────┘
                           ↓
┌───────────────────────────────────────────────────────┐
│                    DEPLOY (Manual)                     │
├──────────────────────────┬────────────────────────────┤
│    Deploy Staging        │    Deploy Production       │
│    (main branch)         │    (tags only)             │
└──────────────────────────┴────────────────────────────┘
```

## 🎓 Best Practices

### 1. Never Commit Secrets
```bash
# Always use .env files
# Never hardcode API keys in code
# Use GitLab CI/CD Variables for secrets
```

### 2. Review Security Dashboard Weekly
```bash
# Check for new vulnerabilities
# Update dependencies promptly
# Review license compliance
```

### 3. Keep Dependencies Updated
```bash
# Check monthly
pip list --outdated
npm outdated

# Update
pip install --upgrade -r backend/app/requirements.txt
cd frontend && npm update
```

### 4. Use Feature Branches
```bash
# Always work in feature branches
git checkout -b feature/new-feature

# Never push directly to main
# Use merge requests for code review
```

## 📚 Additional Resources

- **DEVSECOPS.md** - Complete DevSecOps documentation
- **README.md** - Project overview and setup
- **DOCKER.md** - Docker setup and deployment
- **[GitLab Security Docs](https://docs.gitlab.com/ee/user/application_security/)**

## ✅ Verification Checklist

After setup, verify:

- [ ] `.gitlab-ci.yml` pushed to repository
- [ ] All CI/CD variables configured (5 API keys)
- [ ] Security features enabled in GitLab
- [ ] Main branch is protected
- [ ] Merge request settings configured
- [ ] Test pipeline ran successfully
- [ ] Security Dashboard shows scan results
- [ ] No secrets detected in repository

## 🎉 Success!

Your project now has:
- ✅ Automated security scanning
- ✅ Container vulnerability detection
- ✅ Secret detection
- ✅ Dependency monitoring
- ✅ License compliance tracking
- ✅ Quality gates for code merges
- ✅ Enterprise-grade DevSecOps

**Total setup time: ~5 minutes** ⚡

For detailed information, see **DEVSECOPS.md**

---

**Questions?** Check DEVSECOPS.md or open an issue on GitLab.
