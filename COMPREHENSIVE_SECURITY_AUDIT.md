# COMPREHENSIVE SECURITY AUDIT REPORT

## Le Acupuncture PWA - Current State Analysis

**Date:** January 9, 2026  
**Status:** Pre-Deployment Security Review (No Changes Made)

---

## EXECUTIVE SUMMARY

**Risk Level: 🔴 CRITICAL**

Your application has **15+ significant security vulnerabilities** that must be fixed before any production deployment. The most critical issues involve hardcoded secrets that are publicly exposed in the source code repository.

**Key Findings:**

- ✗ Hardcoded credentials in multiple files
- ✗ Hardcoded API keys visible in version control
- ✗ Debug mode enabled for production
- ✗ Insecure inter-service communication
- ✗ Email credentials exposed
- ✗ CORS unrestricted
- ✗ Missing input validation
- ✗ Localhost APIs won't work on Azure
- ✗ SQLite inadequate for production
- ✓ Some good practices implemented (parameterized SQL, bcrypt passwords)

---

## 🔴 CRITICAL SEVERITY ISSUES

### 1. HARDCODED SECRET KEY IN main.py

**File:** `main.py`, Line 32  
**Severity:** 🔴 CRITICAL  
**Current Code:**

```python
app.secret_key = b"_53oi3uriq9pifpff;apl"
```

**Issues:**

- Secret key is hardcoded and visible in Git history forever
- Can be extracted from compiled bytecode
- Anyone with repo access can forge session cookies
- Same key for all deployments (dev, staging, prod)
- Not following Flask security best practices

**Impact:**

- Attackers can impersonate any user session
- Forge CSRF tokens
- Decrypt session data
- Elevate privileges

**Recommendation:** Use environment variable with strong random key per environment

---

### 2. HARDCODED API AUTHORIZATION KEY (Multiple Files)

**Files:**

- `main.py`, Line 33: `auth_key = "4L50v92nOgcDCYUM"`
- `api.py`, Line 12: `auth_key = "4L50v92nOgcDCYUM"`
- `methods.py`, Line 18: `app_header = {"Authorization": "4L50v92nOgcDCYUM"}`

**Severity:** 🔴 CRITICAL

**Issues:**

- Same key hardcoded in 3+ locations
- Key is publicly visible in repository
- No key rotation mechanism
- Used for all inter-service authentication
- No rate limiting per API key

**Impact:**

- Anyone can make unauthorized API calls
- Bypass all API authentication
- Modify blog content, about me, testimonials
- Delete all data

**Current Usage:**

```python
if request.headers.get("Authorization") == auth_key:  # Simple string comparison
    # Allow request
```

**Recommendation:** Use environment variables + implement proper API authentication (JWT tokens, API keys with rate limiting)

---

### 3. HARDCODED GMAIL CREDENTIALS IN twofa.py

**File:** `twofa.py`, Lines 20-21  
**Severity:** 🔴 CRITICAL

**Current Code:**

```python
server.login("leacupuncturetest@gmail.com", "pjpg wihe vhsc kkiw")
```

**Issues:**

- Gmail account credentials hardcoded in source code
- This appears to be an app-specific password (still exposed)
- Email and password visible in Git history
- Anyone with repo access has email access
- Used for 2FA codes - compromised = account takeover

**Impact:**

- Attackers can send arbitrary emails from your address
- Can reset admin passwords via email
- Can intercept 2FA codes
- Phishing attacks via your email

**Recommendation:**

- Immediately revoke this password in Google Account
- Use environment variables
- Consider Azure SendGrid instead
- Implement 2FA security questions as backup

---

### 4. DEBUG MODE ENABLED FOR PRODUCTION

**File:**

- `main.py`, Line 251: `app.run(debug=True, ...)`
- `api.py`, Line 113: `api.run(debug=True, ...)`

**Severity:** 🔴 CRITICAL

**Issues:**

```python
if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
```

- Debug mode enabled
- Full error stack traces exposed to users
- Interactive debugger accessible
- Code execution possible
- Sensitive environment info displayed
- On Azure, this runs as production

**Impact:**

- Users see full source code on errors
- Attackers can read error messages for vulnerability info
- Interactive debugger port exposed
- Arbitrary code execution possible

**Recommendation:** Check FLASK_ENV environment variable to disable debug in production

---

### 5. EXPOSED GMAIL CREDENTIALS (Second Instance)

**File:** `twofa.py`, Line 21  
**Additional Detail:**

The password `"pjpg wihe vhsc kkiw"` appears to be a Google App Password (16 characters, spaces).

**Current Attack Vector:**

1. Clone your repo from GitHub
2. Read `twofa.py`
3. Use credentials to login to `leacupuncturetest@gmail.com`
4. Reset admin password via password reset emails
5. Takeover admin account
6. Access all admin panels

---

### 6. LOCALHOST API CALLS ON AZURE (Will Break)

**File:** `methods.py`, Lines 20, 30, 42, 52

**Current Code:**

```python
url = "http://127.0.0.1:3000/update_aboutme"      # Line 20 - WRONG IP
url = "http://127.0.0.1:3000/post_blog"           # Line 30 - WRONG IP
delete_url = f"http://127.0.1:3000/delete_blog/{blog_id}"   # Line 42 - TYPO!
url = f"http://127.0.0.1:3000/{endpoint}"         # Line 52 - WRONG IP
```

**Severity:** 🔴 CRITICAL  
**Additional Typo Found:** Line 42 uses `127.0.1` instead of `127.0.0.1`

**Issues:**

- These URLs work only on your local machine
- Azure Web Apps are serverless - no localhost
- API calls will fail with connection refused
- Application won't function on Azure

**Impact:**

- Blog feature won't work on production
- About me updates won't work
- Admin testimonials won't work
- Users see 500 errors on these features

**Production Fix:**

```python
# Should be:
API_BASE_URL = os.environ.get("API_BASE_URL", "http://localhost:3000")
url = f"{API_BASE_URL}/endpoint"
```

**Note on Azure:** Both apps (port 5000 and 3000) must run on same instance, accessible via `http://localhost:3000`

---

### 7. INSECURE INTER-SERVICE COMMUNICATION (HTTP)

**File:** `methods.py` - All API calls

**Severity:** 🔴 CRITICAL

**Current Code:**

```python
url = "http://127.0.0.1:3000/update_aboutme"  # ❌ HTTP (unencrypted)
response = requests.post(url, json=data, headers=app_header)  # ❌ No SSL verification
```

**Issues:**

- Data sent over HTTP (unencrypted)
- No SSL certificate verification
- Man-in-the-middle attacks possible
- Authorization headers sent in plaintext
- Blog content, about me exposed in transit

**Impact:**

- Attacker can intercept API calls
- Steal admin authorization key
- Modify blog content in transit
- Redirect API calls

**Recommendation:**

- Use HTTPS between services
- Explicit SSL verification: `verify=True`
- On Azure, use internal service communication via private endpoints

---

## 🟠 HIGH SEVERITY ISSUES

### 8. NO RATE LIMITING ON ADMIN LOGIN

**File:** `main.py`, Line 176  
**Severity:** 🟠 HIGH

**Current Code:**

```python
@app.route("/admin_login.html", methods=["GET", "POST"])
def admin_login():
    # NO RATE LIMITING
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        if dbHandler.checkAdmin(username, password):
```

**Issues:**

- Unlimited login attempts per IP
- Brute force attacks possible
- No account lockout
- No login attempt logging
- 2FA protects against brute force, but should add rate limit anyway

**Impact:**

- Attacker can try 1000s of passwords
- Even with bcrypt, weak passwords vulnerable
- 2FA codes can be intercepted/guessed

**Recommendation:** Rate limit to 5 attempts per hour per IP

---

### 9. MISSING INPUT VALIDATION ON API ENDPOINTS

**File:** `api.py` - Multiple endpoints  
**Severity:** 🟠 HIGH

**Current Code:**

```python
@api.route("/post_blog", methods=["POST"])
def post_blog():
    if request.headers.get("Authorization") == auth_key:
        data = request.get_json()  # ❌ NO VALIDATION
        response = admin_b.post_blog(data)
        return response, 200
```

**Issues:**

- No validation of incoming JSON
- No schema enforcement
- No content type check
- Malformed data causes crashes
- SQL injection possible (though parameterized queries used)

**Impact:**

- Crashes from malformed requests
- Information disclosure via error messages
- Potential injection attacks

---

### 10. CORS ALLOWS ALL ORIGINS

**File:** `api.py`, Line 14  
**Severity:** 🟠 HIGH

**Current Code:**

```python
cors = CORS(api)  # ❌ Allows ANY origin
```

**Issues:**

- Any website can make API requests
- No origin validation
- Cross-site request forgery possible
- CORS preflight requests not restricted

**Impact:**

- Malicious website can call your API
- Users' browsers execute attacker's requests
- Blog content modified from any domain

**Recommendation:** Restrict to your domain only

```python
cors = CORS(api, resources={
    r"/*": {"origins": ["https://le-acupuncture.com.au", "http://localhost:5000"]}
})
```

---

### 11. MISSING SECURE COOKIE FLAGS

**File:** `main.py`, Lines 44-46  
**Severity:** 🟠 HIGH  
**Status:** ⚠️ Partially Implemented

**Current Code:**

```python
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(minutes=1440)
# SESSION_COOKIE_SECURE missing
# SESSION_COOKIE_HTTPONLY missing
# SESSION_COOKIE_SAMESITE missing
```

**Issues:**

- `SECURE` flag missing - cookies sent over HTTP
- `HTTPONLY` flag missing - JavaScript can access cookies
- `SAMESITE` missing - CSRF attacks possible
- Session timeout is 24 hours (too long for admin)

**Impact:**

- XSS attacks can steal cookies
- Session hijacking
- CSRF attacks possible

**Recommendation:**

```python
app.config['SESSION_COOKIE_SECURE'] = True
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Strict'
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(minutes=60)  # 1 hour
```

---

### 12. SQLite DATABASE NOT SUITABLE FOR PRODUCTION

**File:** All files using `sqlite3`  
**Severity:** 🟠 HIGH

**Issues:**

- SQLite locks entire database on writes
- No concurrent user support
- No encryption at rest
- No backup capabilities
- File-based, can be accidentally deleted
- No access control
- Not suitable for web applications

**Impact:**

- One admin update locks database
- Slow application
- Data loss if file deleted
- No audit trail

**Recommendation:** Migrate to Azure SQL Database (PostgreSQL/MySQL)

---

### 13. LOGGING SENSITIVE DATA

**File:** `main.py`, Lines 24-27  
**Severity:** 🟠 HIGH

**Current Code:**

```python
logging.basicConfig(
    filename="security_log.log",
    level=logging.DEBUG,  # ❌ Debug level logs too much
)
```

**Issues:**

- `logging.DEBUG` logs too much information
- `security_log.log` in working directory
- Logs may contain passwords, OTP codes, user data
- Committed to Git (though likely in .gitignore)

**Impact:**

- Sensitive data in log files
- Attacker reads logs to find vulnerabilities
- Privacy violations

**Recommendation:** Use `logging.INFO` or `logging.WARNING` in production

---

### 14. PRINT STATEMENTS IN PRODUCTION CODE

**Files:**

- `api.py`, Line 40: `print(f"Received data: {data}")`
- `api.py`, Line 68: `print(response)`

**Severity:** 🟠 HIGH

**Issues:**

- Debug print statements left in code
- Printed to stdout on server
- May expose sensitive data
- Unprofessional logging

**Impact:**

- Data leakage via log aggregation
- Debugging information in production logs
- Performance impact

**Recommendation:** Replace all `print()` with `app.logger.debug()` or remove

---

### 15. NO INPUT SANITIZATION ON FILE UPLOADS

**File:** `blog_admin.py`, Lines 39-49  
**Severity:** 🟠 HIGH

**Current Code:**

```python
def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

# File saved directly:
image_path.save(file_path)
```

**Issues:**

- Only extension checked, not file content
- No file size limit
- No filename sanitization (could have path traversal)
- Files saved to predictable location
- No virus scanning

**Impact:**

- Malicious files uploaded
- Path traversal attacks
- Disk space exhaustion
- Arbitrary file read/write

**Recommendation:**

- Validate file magic bytes
- Generate random filenames
- Set file size limits
- Scan with antivirus

---

## 🟡 MEDIUM SEVERITY ISSUES

### 16. WEAK API AUTHENTICATION MECHANISM

**File:** `api.py` - All endpoints  
**Severity:** 🟡 MEDIUM

**Current Code:**

```python
if request.headers.get("Authorization") == auth_key:  # Simple string comparison
    # Allow request
```

**Issues:**

- Simple string comparison
- No timing attack protection
- No API key expiration
- No per-request signature verification
- No audit trail of API calls
- No rate limiting per API key

**Better Approach:** JWT tokens or API keys with expiration

---

### 17. ADMIN PAGE URL IS PREDICTABLE

**File:** `main.py`, Line 164  
**Severity:** 🟡 MEDIUM

**Current Code:**

```python
@app.route("/admin_login.html", methods=["GET", "POST"])
@app.route("/admin.html", methods=["GET"])
```

**Issues:**

- Admin URL is public (`/admin.html`, `/admin_login.html`)
- Easy to discover
- Enables reconnaissance attacks

**Better Approach:** Random UUID path: `/dashboard/a1b2c3d4e5f6/`

---

### 18. WEAK 2FA IMPLEMENTATION

**File:** `twofa.py`  
**Severity:** 🟡 MEDIUM

**Current Code:**

```python
def generate_otp():
    return str(random.randint(100000, 999999))  # 6-digit random

def verify_otp(user_input, otp_code):
    if user_input == otp_code:  # Simple comparison
        return True
```

**Issues:**

- 6-digit OTP = only 1 million possible values (weak)
- Random, not time-based (no TOTP)
- 1 minute expiry ❓ (not visible in code)
- No backup codes
- No rate limiting on OTP attempts
- Sent via email (unencrypted)

**Recommendation:**

- Increase to 8-digit or use TOTP
- Add 30-second timeout
- Rate limit OTP attempts
- Use encrypted email

---

### 19. NO HTTPS ENFORCEMENT

**File:** `main.py`  
**Severity:** 🟡 MEDIUM

**Issues:**

- No HTTPS redirect
- SESSION_COOKIE_SECURE = True (but HTTPS not enforced)
- Mixed content possible
- Credentials sent in plain HTTP

**Recommendation:**

```python
@app.before_request
def enforce_https():
    if not request.is_secure:
        return redirect(request.url.replace('http://', 'https://'), code=301)
```

---

### 20. NO CSRF PROTECTION ON API ENDPOINTS

**File:** `api.py`  
**Severity:** 🟡 MEDIUM

**Current Code:**

```python
@api.route("/post_blog", methods=["POST"])
def post_blog():
    # No CSRF token verification
```

**Status:** This is partially acceptable since API uses Authorization header (not vulnerable to simple CSRF), but should be documented.

---

## 🟢 GOOD PRACTICES IMPLEMENTED ✓

### ✓ 1. Parameterized SQL Queries

**Location:** All database queries  
**Status:** ✅ GOOD

Example from `userManagement.py`:

```python
cur.execute("SELECT * FROM admin_users WHERE admin_user=?", (username,))
```

Protection against SQL injection. Well done!

---

### ✓ 2. Password Hashing with Bcrypt

**Location:** `userManagement.py`, Lines 10-17  
**Status:** ✅ GOOD

```python
hashed = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt())
if bcrypt.checkpw(password.encode('utf-8'), stored_password):
```

Using bcrypt with salt. Industry standard. ✓

---

### ✓ 3. CSRF Protection with Flask-WTF

**Location:** `main.py`, Line 34  
**Status:** ✅ GOOD

```python
csrf = CSRFProtect(app)
```

CSRF protection enabled on main app.

---

### ✓ 4. Input Sanitization with Bleach

**Location:** `blog_admin.py`, Lines 15-16, 39-49  
**Status:** ✅ GOOD

```python
title = bleach.clean(title)
blog_content = bleach.clean(blog_content, tags=allowed_tags)
```

User input sanitized before storage. ✓

---

### ✓ 5. Session Timeout

**Location:** `main.py`, Line 42  
**Status:** ✅ GOOD (but timeout too long)

```python
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(minutes=1440)
```

Session timeout implemented (24 hours), though should be reduced to 60 minutes.

---

### ✓ 6. CSP Headers Configured

**Location:** `main.py`, Line 111-129  
**Status:** ✅ GOOD

Content Security Policy headers implemented to prevent XSS attacks.

---

### ✓ 7. Rate Limiting Configured

**Location:** `api.py`, Lines 15-19  
**Status:** ✅ GOOD (but incomplete)

```python
limiter = Limiter(
    get_remote_address,
    default_limits=["200 per day", "50 per hour"]
)
```

API rate limiting implemented, but login endpoint needs it.

---

## 📊 VULNERABILITY SUMMARY TABLE

| #   | Issue                     | Severity    | File                        | Line        | Impact                  |
| --- | ------------------------- | ----------- | --------------------------- | ----------- | ----------------------- |
| 1   | Hardcoded Secret Key      | 🔴 CRITICAL | main.py                     | 32          | Session forgery         |
| 2   | Hardcoded API Key         | 🔴 CRITICAL | main.py, api.py, methods.py | 33, 12, 18  | Unauthorized API access |
| 3   | Exposed Gmail Credentials | 🔴 CRITICAL | twofa.py                    | 20-21       | Account takeover        |
| 4   | Debug Mode Enabled        | 🔴 CRITICAL | main.py, api.py             | 251, 113    | Code execution          |
| 5   | Localhost APIs on Azure   | 🔴 CRITICAL | methods.py                  | 20,30,42,52 | App won't work          |
| 6   | HTTP Inter-Service Comm   | 🔴 CRITICAL | methods.py                  | all         | Man-in-the-middle       |
| 7   | IP Typo (127.0.1)         | 🔴 CRITICAL | methods.py                  | 42          | API calls fail          |
| 8   | No Login Rate Limiting    | 🟠 HIGH     | main.py                     | 176         | Brute force             |
| 9   | Missing Input Validation  | 🟠 HIGH     | api.py                      | all         | Injection attacks       |
| 10  | CORS Unrestricted         | 🟠 HIGH     | api.py                      | 14          | CSRF attacks            |
| 11  | Missing Cookie Flags      | 🟠 HIGH     | main.py                     | 44-46       | XSS/CSRF                |
| 12  | SQLite for Production     | 🟠 HIGH     | all                         | -           | Scalability             |
| 13  | Debug Logging             | 🟠 HIGH     | main.py                     | 26          | Data leakage            |
| 14  | Print Statements          | 🟠 HIGH     | api.py                      | 40,68       | Data exposure           |
| 15  | Weak File Upload          | 🟠 HIGH     | blog_admin.py               | 39-49       | Malicious files         |
| 16  | Weak API Auth             | 🟡 MEDIUM   | api.py                      | all         | Timing attacks          |
| 17  | Predictable Admin URL     | 🟡 MEDIUM   | main.py                     | 164         | Reconnaissance          |
| 18  | Weak 2FA                  | 🟡 MEDIUM   | twofa.py                    | all         | Brute force OTP         |
| 19  | No HTTPS Enforcement      | 🟡 MEDIUM   | main.py                     | -           | Man-in-the-middle       |
| 20  | No API CSRF Token         | 🟡 MEDIUM   | api.py                      | all         | CSRF (partial)          |

---

## 🚨 IMMEDIATE ACTION REQUIRED

### Before ANY deployment, you MUST:

1. **Revoke Gmail Password** - Immediately disable `leacupuncturetest@gmail.com` app password

   - Go to https://myaccount.google.com/apppasswords
   - Remove the exposed password
   - If repo is public, this account is compromised

2. **Rotate All Secrets**

   - Generate new SECRET_KEY using `secrets.token_hex(32)`
   - Generate new AUTH_KEY using `secrets.token_hex(16)`
   - Do NOT store in code

3. **Move to Environment Variables**

   - Create `.env` file (add to .gitignore)
   - Remove hardcoded values from code
   - Use `os.environ.get()`

4. **Check Git History**

   - Run: `git log -p --all -- twofa.py` to see if credentials were in public history
   - If repo is public on GitHub, credentials are compromised
   - Use `git-filter-repo` to remove from history if needed

5. **Disable Debug Mode**

   - Check FLASK_ENV environment variable
   - Set `debug = False` for production

6. **Fix API URLs**
   - Use environment variable for API base URL
   - Fix typo: `127.0.1` → `127.0.0.1`

---

## 🏗️ ARCHITECTURE ISSUES

### Running Two Flask Apps (ports 5000 and 3000)

**Issue:** How will these run on Azure?

**Current Setup:**

- `main.py` runs on port 5000 (main web app)
- `api.py` runs on port 3000 (API server)
- They communicate via `http://127.0.0.1:3000`

**Azure Web App Problem:**

- Azure Web App is single-process
- Both can't run simultaneously
- How is this currently deployed?

**Solutions:**

1. **Merge into single Flask app** - Recommended
2. **Run as background job + main app** - Complex
3. **Use Azure Container - Run two separate services**
4. **Azure Service Fabric** - Enterprise solution

**Recommendation:** Merge `api.py` endpoints into `main.py` to avoid inter-service communication complexity.

---

## 📋 DEPLOYMENT CHECKLIST

### Before Going to Azure:

- [ ] Fix hardcoded secrets
- [ ] Move to environment variables
- [ ] Disable debug mode
- [ ] Fix localhost URLs
- [ ] Add rate limiting to login
- [ ] Restrict CORS
- [ ] Enable HTTPS enforcement
- [ ] Add input validation
- [ ] Improve logging
- [ ] Remove print statements
- [ ] Reduce session timeout
- [ ] Add secure cookie flags
- [ ] Rotate all credentials
- [ ] Check Git history for exposed secrets

### After Deploying to Azure:

- [ ] Set environment variables in Azure Portal
- [ ] Use Azure Key Vault for secrets
- [ ] Set up Application Insights
- [ ] Configure SSL certificate
- [ ] Test all functionality
- [ ] Monitor error logs
- [ ] Set up alerts

---

## 📞 QUESTIONS FOR YOU

Before proceeding with fixes, please clarify:

1. **Is your GitHub repository public or private?**

   - If public, those Gmail credentials are compromised

2. **How are you currently running both API (port 3000) and main app (port 5000)?**

   - Locally? Docker? Separate servers?

3. **Do you have an Azure SQL Database ready?**

   - Or should we keep SQLite for now?

4. **Should admin panel have a custom hidden URL?**

   - Instead of `/admin.html`

5. **Is `security_log.log` in `.gitignore`?**
   - It should be to prevent logging secrets in version control

---

## 🎯 RISK ASSESSMENT

**Overall Risk Level: 🔴 CRITICAL**

| Category           | Risk        | Notes                                  |
| ------------------ | ----------- | -------------------------------------- |
| Secrets Exposure   | 🔴 CRITICAL | Hardcoded in source code               |
| Authentication     | 🔴 CRITICAL | Simple string comparison, exposed keys |
| API Security       | 🔴 CRITICAL | Localhost URLs break on cloud          |
| Data Protection    | 🟠 HIGH     | SQLite, no encryption                  |
| Infrastructure     | 🔴 CRITICAL | Won't run on Azure as-is               |
| Email Security     | 🔴 CRITICAL | Gmail credentials exposed              |
| Session Management | 🟡 MEDIUM   | Some flags missing                     |
| Input Validation   | 🟠 HIGH     | Missing on API endpoints               |

**Recommendation:** 🚫 **DO NOT DEPLOY** until critical issues are fixed.

---

## NEXT STEPS

This audit identifies the vulnerabilities without making changes.

**When ready, ask me to:**

1. "Fix the security issues" - I'll apply all recommended fixes
2. "Fix [specific issue]" - I'll address individual vulnerabilities
3. "Create migration plan" - I'll outline step-by-step fixes

**Total estimated time to fix:** 2-3 hours for all critical and high severity issues.

---

**Report Complete**  
_This is a comprehensive analysis of current security state._  
_No files have been modified._
