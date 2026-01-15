# Product Backlog

---

## Pre-Deployment Tasks

### 🔴 CRITICAL Security Fixes (MUST DO BEFORE AZURE DEPLOYMENT)

- [ ] Remove hardcoded SECRET_KEY from main.py (line 32) - move to environment variables
- [ ] Remove hardcoded AUTH_KEY from main.py, api.py, methods.py - move to environment variables
- [ ] Revoke/remove Gmail credentials from twofa.py immediately
- [ ] Disable debug mode in main.py and api.py (check FLASK_ENV variable)
- [ ] Fix localhost API URLs in methods.py - use environment variable (127.0.0.1:3000)
- [ ] Fix IP typo in methods.py line 42 (127.0.1 → 127.0.0.1)
- [ ] Create .env.example file with required environment variables
- [ ] Create/update .gitignore to exclude .env and security_log.log

### 🟠 HIGH Priority Security Fixes

- [ ] Add rate limiting to admin login endpoint (max 5 attempts/hour)
- [ ] Restrict CORS to only your domain
- [ ] Add input validation to all API endpoints
- [ ] Add secure cookie flags (SECURE, HTTPONLY, SAMESITE)
- [ ] Reduce session timeout from 24 hours to 1 hour
- [ ] Replace print() statements with logging calls
- [ ] Change debug logging level from DEBUG to INFO
- [ ] Improve file upload validation (check file content, not just extension)
- [ ] Add HTTPS enforcement redirect

### 🟡 MEDIUM Priority Improvements

- [ ] Change admin URL from /admin.html to random UUID path
- [ ] Improve 2FA implementation (longer OTP, TOTP, backup codes)
- [ ] Consider merging api.py into main.py to simplify architecture
- [ ] Migrate from SQLite to Azure SQL Database

### Post-Deployment

- [ ] Set up Azure Key Vault for secrets
- [ ] Configure Application Insights for logging
- [ ] Set up SSL/TLS certificate
- [ ] Test all functionality end-to-end
- [ ] Configure monitoring and alerts

---

## Sprint Tasks

- Implement mum changes
- Fix menu issue on phone size
- Figure out how to get rid of admin changes if needed, so its not accessible
- Deploy (after security fixes completed)
