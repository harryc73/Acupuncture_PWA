# Complete Azure Deployment Guide - Le Acupuncture PWA

**Current Status**: At Azure Create Web App page  
**Goal**: Deploy fully functional and secure website to the internet  
**Estimated Time**: 3-4 hours for first-time deployment

---

## PHASE 1: Complete Azure Web App Creation (You Are Here)

### Step 1: Fill out "Create Web App" form in Azure Portal

**Basics Tab:**

- [ ] **Subscription**: Select your Azure subscription
- [ ] **Resource Group**: Create new or select existing (e.g., "LeAcupuncture-RG")
- [ ] **Name**: Choose unique name (e.g., "leacupuncture" - becomes leacupuncture.azurewebsites.net)
- [ ] **Publish**: Select **Code**
- [ ] **Runtime stack**: Select **Python 3.11**
- [ ] **Operating System**: Select **Linux**
- [ ] **Region**: Select closest to your target audience (e.g., "West US 2", "UK South")
- [ ] **Pricing Plan**: Select **Basic B1** or higher (Free F1 won't work for production)

**Deployment Tab:**

- [ ] **Continuous deployment**: Enable (if you want auto-deploy from GitHub)
- [ ] **GitHub account**: Connect your GitHub account (harryc73/Acupuncture_PWA)
- [ ] **Organization**: harryc73
- [ ] **Repository**: Acupuncture_PWA
- [ ] **Branch**: Choose branch (main or Deployment)

**Networking Tab:**

- [ ] **Enable public access**: Yes
- [ ] **Enable network injection**: No (unless you need VNet)

**Monitoring Tab:**

- [ ] **Enable Application Insights**: Yes (highly recommended)
- [ ] **Region**: Same as web app

**Review + Create:**

- [ ] Click "Review + create"
- [ ] Wait for validation to pass
- [ ] Click "Create"
- [ ] **Wait 2-5 minutes** for deployment to complete
- [ ] Click "Go to resource" when ready

---

## PHASE 2: Critical Pre-Deployment Tasks (DO NOT SKIP)

### Step 2: Revoke Exposed Gmail Credentials (IMMEDIATE ACTION REQUIRED)

⚠️ **CRITICAL SECURITY ISSUE**: Your Gmail credentials are exposed in twofa.py

- [ ] Go to: https://myaccount.google.com/apppasswords
- [ ] Sign in as: leacupuncturetest@gmail.com
- [ ] Find app password: "pjpg wihe vhsc kkiw"
- [ ] Click "Remove" or "Revoke"
- [ ] Generate NEW app password (save securely - you'll need it in Step 8)

### Step 3: Decide on Two-App Architecture Strategy

Your app has TWO Flask applications that need to run simultaneously:

- **main.py** (port 5000) - Main website
- **api.py** (port 3000) - API endpoints

**Choose ONE approach:**

**Option A: Merge API into Main App (RECOMMENDED - Simplest)**

- [ ] I will merge api.py routes into main.py (single app)
- [ ] Advantages: Simplest deployment, one process, no CORS issues
- [ ] Time: 30 minutes to implement

**Option B: Use Background Process**

- [ ] I will run api.py as background process using threading
- [ ] Advantages: Minimal code changes
- [ ] Disadvantages: May not restart properly, harder to debug

**Option C: Deploy as Two Separate Azure Web Apps**

- [ ] I will create second Azure Web App for API
- [ ] Advantages: Proper separation, scalable
- [ ] Disadvantages: Costs 2x, requires updating methods.py URLs

**⚠️ Decision Required**: Choose option and note here: ****\_\_\_****

---

## PHASE 3: Prepare Your Local Codebase

### Step 4: Create Required Azure Configuration Files

#### A. Create requirements.txt (if not complete)

- [ ] Open `/workspaces/Acupuncture_PWA/requirements.txt`
- [ ] Verify it contains ALL dependencies:

```txt
Flask==2.3.0
Flask-CORS==4.0.0
Flask-Limiter==3.3.1
Flask-WTF==1.1.1
bcrypt==4.0.1
pyotp==2.8.0
bleach==6.0.0
jsonschema==4.17.3
Werkzeug==2.3.0
email-validator==2.0.0
gunicorn==21.2.0
```

- [ ] Save file

#### B. Create .deployment file (tells Azure how to deploy)

- [ ] Create file: `/workspaces/Acupuncture_PWA/.deployment`
- [ ] Add content:

```ini
[config]
SCM_DO_BUILD_DURING_DEPLOYMENT=true
```

#### C. Create startup.sh (tells Azure how to start your app)

**If you chose Option A (Merged App):**

- [ ] Create file: `/workspaces/Acupuncture_PWA/startup.sh`
- [ ] Add content:

```bash
#!/bin/bash
gunicorn --bind=0.0.0.0 --timeout 600 main:app
```

- [ ] Make executable: `chmod +x startup.sh`

**If you chose Option B (Background Process):**

- [ ] Create file: `/workspaces/Acupuncture_PWA/startup.sh`
- [ ] Add content:

```bash
#!/bin/bash
python api.py &
gunicorn --bind=0.0.0.0 --timeout 600 main:app
```

- [ ] Make executable: `chmod +x startup.sh`

### Step 5: Fix Security Vulnerabilities in Code

⚠️ **CRITICAL**: These changes MUST be done before deployment

#### A. Fix main.py (7 changes)

- [ ] **Line 19**: Remove hardcoded SECRET_KEY

```python
# BEFORE:
app.secret_key = b"_53oi3uriq9pifpff;apl"

# AFTER:
app.secret_key = os.environ.get('SECRET_KEY', 'dev-key-change-in-production')
```

- [ ] **Line 1**: Add import at top of file

```python
import os
```

- [ ] **Line 21**: Remove hardcoded AUTH_KEY

```python
# BEFORE:
AUTH_KEY = "4L50v92nOgcDCYUM"

# AFTER:
AUTH_KEY = os.environ.get('AUTH_KEY')
```

- [ ] **Line 24**: Change session configuration

```python
# BEFORE:
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=24)

# AFTER:
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=2)
app.config['SESSION_COOKIE_SECURE'] = True  # HTTPS only
app.config['SESSION_COOKIE_HTTPONLY'] = True  # Prevent XSS
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'  # CSRF protection
```

- [ ] **Line 176**: Add rate limiting to login route

```python
# BEFORE:
@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():

# AFTER:
from functools import wraps
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"]
)

@app.route('/admin/login', methods=['GET', 'POST'])
@limiter.limit("5 per minute")
def admin_login():
```

- [ ] **Line 251**: Disable debug mode

```python
# BEFORE:
app.run(port=5000, debug=True)

# AFTER:
if __name__ == '__main__':
    # Only run directly in development
    port = int(os.environ.get('PORT', 5000))
    app.run(port=port, debug=False)
```

- [ ] **Throughout**: Search for any print() statements and remove or replace with proper logging

#### B. Fix methods.py (5 changes)

- [ ] **Line 1**: Add import at top

```python
import os
```

- [ ] **Line 18**: Remove hardcoded auth header

```python
# BEFORE:
headers = {"Authorization": "4L50v92nOgcDCYUM"}

# AFTER:
AUTH_KEY = os.environ.get('AUTH_KEY')
headers = {"Authorization": AUTH_KEY}
```

- [ ] **Line 20, 30, 52**: Update all localhost URLs

```python
# BEFORE:
url = "http://127.0.0.1:3000/aboutme"

# AFTER:
API_BASE_URL = os.environ.get('API_BASE_URL', 'http://127.0.0.1:3000')
url = f"{API_BASE_URL}/aboutme"
```

- [ ] **Line 42**: Fix IP typo (127.0.1 → 127.0.0.1)

```python
# BEFORE:
url = f"http://127.0.1:3000/delete/blog/{blog_id}"

# AFTER:
url = f"{API_BASE_URL}/delete/blog/{blog_id}"
```

- [ ] **Throughout**: Update ALL API URLs to use API_BASE_URL environment variable

#### C. Fix twofa.py (3 changes)

- [ ] **Line 1**: Add import at top

```python
import os
```

- [ ] **Line 20-21**: Remove hardcoded Gmail credentials

```python
# BEFORE:
email_address = "leacupuncturetest@gmail.com"
email_password = "pjpg wihe vhsc kkiw"

# AFTER:
email_address = os.environ.get('EMAIL_ADDRESS')
email_password = os.environ.get('EMAIL_PASSWORD')
```

- [ ] **Line 25**: Add error handling

```python
# AFTER the environment variables:
if not email_address or not email_password:
    raise ValueError("EMAIL_ADDRESS and EMAIL_PASSWORD environment variables must be set")
```

#### D. Fix api.py (6 changes) - ONLY if using Option B or C

- [ ] **Line 1**: Add import at top

```python
import os
```

- [ ] **Line 12**: Remove hardcoded AUTH_KEY

```python
# BEFORE:
AUTH_KEY = "4L50v92nOgcDCYUM"

# AFTER:
AUTH_KEY = os.environ.get('AUTH_KEY')
```

- [ ] **Line 14**: Restrict CORS

```python
# BEFORE:
CORS(app)

# AFTER:
ALLOWED_ORIGINS = os.environ.get('ALLOWED_ORIGINS', 'http://127.0.0.1:5000').split(',')
CORS(app, resources={r"/*": {"origins": ALLOWED_ORIGINS}})
```

- [ ] **Line 40, 68**: Remove debug print() statements

```python
# Remove all print() statements or replace with:
import logging
logging.info(f"Message here")
```

- [ ] **Line 113**: Disable debug mode

```python
# BEFORE:
app.run(host='0.0.0.0', port=3000, debug=True)

# AFTER:
if __name__ == '__main__':
    port = int(os.environ.get('API_PORT', 3000))
    app.run(host='0.0.0.0', port=port, debug=False)
```

- [ ] **Throughout**: Search for any remaining print() statements and remove

### Step 6: Handle Database Strategy

**Choose ONE approach for SQLite database:**

**Option A: Keep SQLite, Upload Initial Database**

- [ ] Your database file: `/workspaces/Acupuncture_PWA/databaseFiles/database.db`
- [ ] Ensure it has initial admin user
- [ ] Will upload via FTP in Step 11
- [ ] ⚠️ Note: Changes won't persist across redeploys without external storage

**Option B: Use Azure Storage for SQLite (Better)**

- [ ] Will mount Azure File Share in Step 10
- [ ] Database persists across redeploys
- [ ] Recommended for production

**Option C: Migrate to PostgreSQL (Production-Grade)**

- [ ] Will require significant code changes (not covered in this guide)
- [ ] Use Azure Database for PostgreSQL
- [ ] Best for scalability and reliability

**⚠️ Decision Required**: Choose option and note here: ****\_\_\_****

### Step 7: Commit and Push All Changes to GitHub

- [ ] Open terminal in VS Code
- [ ] Check status: `git status`
- [ ] Add all changes: `git add .`
- [ ] Commit: `git commit -m "Security fixes and Azure deployment configuration"`
- [ ] Push to branch: `git push origin Deployment` (or your chosen branch)
- [ ] Verify on GitHub that changes are pushed

---

## PHASE 4: Configure Azure Web App Settings

### Step 8: Set Environment Variables in Azure

- [ ] In Azure Portal, go to your Web App resource
- [ ] Navigate to: **Configuration** (left sidebar under Settings)
- [ ] Click **+ New application setting** for each of the following:

#### Required Environment Variables:

1. **SECRET_KEY**

   - [ ] Name: `SECRET_KEY`
   - [ ] Value: Generate new key - Run in terminal: `python -c "import os; print(os.urandom(24).hex())"`
   - [ ] Copy the output (48-character string)
   - [ ] Click OK

2. **AUTH_KEY**

   - [ ] Name: `AUTH_KEY`
   - [ ] Value: Generate new key - Run: `python -c "import secrets; print(secrets.token_urlsafe(16))`
   - [ ] Copy the output
   - [ ] Click OK

3. **EMAIL_ADDRESS**

   - [ ] Name: `EMAIL_ADDRESS`
   - [ ] Value: `leacupuncturetest@gmail.com`
   - [ ] Click OK

4. **EMAIL_PASSWORD**

   - [ ] Name: `EMAIL_PASSWORD`
   - [ ] Value: Paste the NEW Gmail app password you generated in Step 2
   - [ ] Click OK

5. **API_BASE_URL** (if using two-app setup)

   - [ ] Name: `API_BASE_URL`
   - [ ] Value:
     - If Option A (merged): Not needed
     - If Option B (background): `http://127.0.0.1:3000`
     - If Option C (separate): `https://your-api-app.azurewebsites.net`
   - [ ] Click OK

6. **ALLOWED_ORIGINS** (if using separate API)

   - [ ] Name: `ALLOWED_ORIGINS`
   - [ ] Value: `https://leacupuncture.azurewebsites.net` (your main app URL)
   - [ ] Click OK

7. **FLASK_ENV**

   - [ ] Name: `FLASK_ENV`
   - [ ] Value: `production`
   - [ ] Click OK

8. **PYTHONUNBUFFERED**
   - [ ] Name: `PYTHONUNBUFFERED`
   - [ ] Value: `1`
   - [ ] Click OK

- [ ] Click **Save** at the top
- [ ] Click **Continue** when prompted about restart

### Step 9: Configure Startup Command

- [ ] Still in **Configuration** section
- [ ] Click on **General settings** tab
- [ ] Find **Startup Command** field
- [ ] Enter: `startup.sh`
- [ ] Click **Save**

### Step 10: Configure Azure File Storage (If Option B from Step 6)

Only if you chose Option B for database persistence:

- [ ] In Azure Portal, create new **Storage Account**
- [ ] Create **File Share** named "leacupuncture-data"
- [ ] Go back to your Web App
- [ ] Navigate to: **Configuration** > **Path mappings**
- [ ] Click **+ New Azure Storage Mount**
- [ ] Name: `database-storage`
- [ ] Configuration: Select your storage account and file share
- [ ] Mount path: `/home/site/wwwroot/databaseFiles`
- [ ] Click OK and Save

---

## PHASE 5: Deploy Application to Azure

### Step 11: Upload Database File (If Option A from Step 6)

- [ ] In Azure Portal, go to your Web App
- [ ] Navigate to: **Development Tools** > **Advanced Tools**
- [ ] Click **Go** (opens Kudu)
- [ ] Click **Debug console** > **CMD**
- [ ] Navigate to: `site/wwwroot/`
- [ ] Create folder: Click + icon, create `databaseFiles`
- [ ] Click on `databaseFiles` folder
- [ ] Drag and drop your local `database.db` file
- [ ] Wait for upload to complete

### Step 12: Trigger Deployment

**If you enabled continuous deployment (recommended):**

- [ ] Go to: **Deployment Center** in Azure Portal
- [ ] Click **Sync** to pull latest from GitHub
- [ ] Monitor deployment logs

**If manual deployment:**

- [ ] In VS Code, open terminal
- [ ] Install Azure CLI: Follow instructions at https://docs.microsoft.com/cli/azure/install-azure-cli
- [ ] Login: `az login`
- [ ] Deploy: `az webapp up --name leacupuncture --resource-group LeAcupuncture-RG`

### Step 13: Monitor Deployment

- [ ] In Azure Portal, go to **Deployment Center**
- [ ] Watch the deployment logs in real-time
- [ ] Wait for status to show **Success (Active)**
- [ ] If failed, check logs for errors

---

## PHASE 6: Initial Testing and Verification

### Step 14: Test Basic Application Access

- [ ] Open your Azure Web App URL: `https://leacupuncture.azurewebsites.net`
- [ ] Verify homepage loads correctly
- [ ] Check that images load (carousel, icons)
- [ ] Test navigation to all pages:
  - [ ] About
  - [ ] Blog
  - [ ] Booking
  - [ ] Privacy Policy
- [ ] Verify manifest.json is accessible: `https://leacupuncture.azurewebsites.net/static/manifest.json`

### Step 15: Test Admin Functionality

- [ ] Navigate to: `https://leacupuncture.azurewebsites.net/admin/login`
- [ ] Enter admin credentials
- [ ] Verify 2FA email is sent
- [ ] Check email and enter OTP code
- [ ] Verify successful login to admin panel
- [ ] Test each admin function:
  - [ ] Create new blog post
  - [ ] Edit blog post
  - [ ] Delete blog post
  - [ ] Update About Me content
  - [ ] View testimonials (if kept)
  - [ ] Change admin password
- [ ] Logout successfully

### Step 16: Test API Endpoints (If separate API)

Only if using Option B or C for architecture:

- [ ] Test About Me API: `curl https://leacupuncture.azurewebsites.net/api/aboutme`
- [ ] Test Blog API: `curl https://leacupuncture.azurewebsites.net/api/blog`
- [ ] Verify proper JSON responses
- [ ] Check CORS headers in browser console

### Step 17: Check Application Logs

- [ ] In Azure Portal, go to: **Monitoring** > **Log stream**
- [ ] Watch live logs for any errors
- [ ] Look for:
  - [ ] No import errors
  - [ ] No missing environment variable errors
  - [ ] No database connection errors
  - [ ] No 500 errors in requests

### Step 18: Check Application Insights (If enabled)

- [ ] In Azure Portal, go to your App Insights resource
- [ ] Navigate to: **Application Dashboard**
- [ ] Check metrics:
  - [ ] Server response time (should be < 2 seconds)
  - [ ] Failed requests (should be 0 or very low)
  - [ ] Server exceptions (should be 0)
- [ ] Navigate to: **Live Metrics** to see real-time data

---

## PHASE 7: Enable HTTPS and Custom Domain

### Step 19: Verify HTTPS is Working

- [ ] Your Azure URL should automatically have HTTPS: `https://leacupuncture.azurewebsites.net`
- [ ] Test in browser - look for padlock icon
- [ ] Verify certificate is valid (click padlock)

### Step 20: Add Custom Domain (Optional)

If you have a custom domain (e.g., www.leacupuncture.com):

- [ ] Purchase domain from registrar (GoDaddy, Namecheap, etc.)
- [ ] In Azure Portal, go to: **Custom domains**
- [ ] Click **+ Add custom domain**
- [ ] Enter your domain name
- [ ] Follow validation steps (add TXT or CNAME records)
- [ ] Wait for DNS propagation (15 minutes - 24 hours)
- [ ] Click **Validate** in Azure
- [ ] Click **Add custom domain**

### Step 21: Enable HTTPS for Custom Domain

- [ ] In **Custom domains** section, click on your domain
- [ ] Click **Add binding**
- [ ] Choose **SNI SSL**
- [ ] Select or create App Service Managed Certificate (FREE)
- [ ] Click **Add binding**
- [ ] Wait 5-10 minutes for certificate provisioning
- [ ] Verify HTTPS works: `https://www.yourdomain.com`

### Step 22: Force HTTPS Redirect

- [ ] In Azure Portal, go to: **Configuration** > **General settings**
- [ ] Set **HTTPS Only**: **On**
- [ ] Click **Save**
- [ ] Test: Try accessing `http://leacupuncture.azurewebsites.net` - should redirect to HTTPS

---

## PHASE 8: Security Hardening

### Step 23: Enable Azure Security Features

- [ ] Navigate to: **Security** in left sidebar
- [ ] Enable **Managed Identity**:

  - [ ] Go to **Identity**
  - [ ] Switch Status to **On**
  - [ ] Click **Save**

- [ ] Review **Security recommendations** (if any)

### Step 24: Configure IP Restrictions (Optional but Recommended for Admin)

To restrict admin access to specific IPs:

- [ ] Navigate to: **Networking** > **Access restriction**
- [ ] Click **+ Add rule**
- [ ] Name: "Admin Access Only"
- [ ] Action: Allow
- [ ] Priority: 100
- [ ] Type: IPv4
- [ ] IP Address Block: Your IP address/32 (get from whatismyip.com)
- [ ] Click **Add rule**

### Step 25: Enable Request Tracing

- [ ] Navigate to: **Diagnose and solve problems**
- [ ] Search for "Application Logs"
- [ ] Enable **Application Logging (Filesystem)**: On
- [ ] Level: **Error**
- [ ] Click **Save**

---

## PHASE 9: Performance Optimization

### Step 26: Enable Caching Headers

Add to main.py (after imports):

- [ ] Add caching headers for static files:

```python
@app.after_request
def add_cache_headers(response):
    if request.path.startswith('/static/'):
        response.cache_control.max_age = 31536000  # 1 year for static files
    return response
```

### Step 27: Configure Application Performance

- [ ] In Azure Portal, go to: **Configuration** > **General settings**
- [ ] **Always On**: Set to **On** (prevents cold starts)
- [ ] **ARR Affinity**: Set to **Off** (better for load balancing)
- [ ] Click **Save**

### Step 28: Test Performance

- [ ] Use GTmetrix: https://gtmetrix.com/
- [ ] Enter your Azure URL
- [ ] Analyze results
- [ ] Aim for:
  - [ ] Load time < 3 seconds
  - [ ] Performance score > 80%
- [ ] Use Google PageSpeed Insights: https://pagespeed.web.dev/
- [ ] Test both mobile and desktop

---

## PHASE 10: Backup and Monitoring Setup

### Step 29: Configure Automated Backups

- [ ] Navigate to: **Backups** in left sidebar
- [ ] Click **Configure**
- [ ] Create or select Storage Account
- [ ] Set backup schedule:
  - [ ] Frequency: Daily
  - [ ] Time: 2:00 AM (low traffic time)
  - [ ] Retention: 30 days
- [ ] Include database in backup: Yes (if using Azure SQL)
- [ ] Click **Save**

### Step 30: Set Up Alerts

- [ ] Navigate to: **Alerts** under Monitoring
- [ ] Click **+ Create** > **Alert rule**

Create alerts for:

**1. High Error Rate:**

- [ ] Condition: Failed requests > 10
- [ ] Severity: 2
- [ ] Action: Email you

**2. High Response Time:**

- [ ] Condition: Average response time > 5 seconds
- [ ] Severity: 3
- [ ] Action: Email you

**3. App Down:**

- [ ] Condition: App availability < 100%
- [ ] Severity: 0 (Critical)
- [ ] Action: Email and SMS

### Step 31: Configure Log Retention

- [ ] Navigate to: **App Service logs**
- [ ] **Application Logging (Filesystem)**: On
- [ ] **Web server logging**: On
- [ ] **Quota (MB)**: 50
- [ ] **Retention Period (Days)**: 7
- [ ] Click **Save**

---

## PHASE 11: Final Production Checklist

### Step 32: Security Final Checks

- [ ] Verify no hardcoded secrets in code (run: `git grep -i "password\|secret\|key" *.py`)
- [ ] Verify all secrets in Azure environment variables only
- [ ] Confirm debug=False in all Python files
- [ ] Verify HTTPS working on all pages
- [ ] Test that HTTP redirects to HTTPS
- [ ] Verify Gmail app password was revoked and new one is in use
- [ ] Check that admin login has rate limiting (try 6 failed attempts)
- [ ] Verify 2FA is working via email
- [ ] Check session timeout (wait 2 hours, should be logged out)

### Step 33: Functionality Final Checks

- [ ] Test all pages as anonymous user
- [ ] Test all pages as logged-in admin
- [ ] Verify booking iframe loads correctly
- [ ] Test form submissions (if any)
- [ ] Verify blog posts display correctly
- [ ] Test image loading on slow connection (Chrome DevTools > Network > Slow 3G)
- [ ] Verify PWA features (manifest, service worker)
- [ ] Test add to home screen on mobile device
- [ ] Verify robots.txt is accessible
- [ ] Test 404 page handling

### Step 34: Cross-Browser Testing

Test on all major browsers:

- [ ] Chrome (desktop and mobile)
- [ ] Firefox (desktop)
- [ ] Safari (desktop and iOS)
- [ ] Edge (desktop)
- [ ] Samsung Internet (Android)

Check:

- [ ] Layout renders correctly
- [ ] No console errors
- [ ] All interactive features work
- [ ] Images and fonts load

### Step 35: Mobile Responsiveness Testing

Test on different screen sizes:

- [ ] iPhone SE (375px width)
- [ ] iPhone 12/13 (390px width)
- [ ] Samsung Galaxy (360px width)
- [ ] iPad (768px width)
- [ ] Desktop (1920px width)

Verify:

- [ ] Navigation menu works (burger menu on mobile)
- [ ] Logo behaves correctly (hidden on mobile if intended)
- [ ] All content is readable
- [ ] No horizontal scrolling
- [ ] Touch targets are at least 44×44px
- [ ] Forms are easy to fill on mobile

### Step 36: SEO and Accessibility

- [ ] Verify all images have alt text
- [ ] Check meta descriptions are present
- [ ] Verify title tags are descriptive
- [ ] Test with screen reader (NVDA on Windows, VoiceOver on Mac)
- [ ] Check color contrast ratios (use Wave extension)
- [ ] Verify keyboard navigation works (Tab through all elements)
- [ ] Test heading hierarchy (H1 → H2 → H3)

---

## PHASE 12: Go Live

### Step 37: Update DNS (If using custom domain)

- [ ] Log into domain registrar
- [ ] Update DNS records:
  - [ ] A record: Point to Azure Web App IP
  - [ ] CNAME: www → leacupuncture.azurewebsites.net
- [ ] Wait for DNS propagation (use dnschecker.org to monitor)

### Step 38: Announce and Monitor

- [ ] Send test email to yourself using contact form (if applicable)
- [ ] Monitor logs for first 24 hours
- [ ] Check Azure costs in **Cost Management**
- [ ] Monitor Application Insights for errors
- [ ] Keep browser tab open with **Live Metrics** for first hour

### Step 39: Post-Launch Documentation

- [ ] Document your Azure resource names and locations
- [ ] Save all environment variable names (not values!) in a secure document
- [ ] Document your deployment process for future updates
- [ ] Create admin guide for non-technical users
- [ ] Set calendar reminders for:
  - [ ] SSL certificate renewal check (if manual)
  - [ ] Backup verification (weekly)
  - [ ] Security updates (monthly)

### Step 40: Celebrate! 🎉

- [ ] Your website is live on the internet!
- [ ] Test final URL: `https://leacupuncture.azurewebsites.net`
- [ ] Share with stakeholders
- [ ] Update GitHub README with live URL

---

## Emergency Rollback Plan

If something goes wrong after deployment:

1. **Immediate Rollback:**

   - Go to: **Deployment Center** in Azure Portal
   - Find previous successful deployment
   - Click **Redeploy**

2. **Stop the App:**

   - Click **Stop** at top of Web App overview
   - Investigate issues in logs
   - Click **Start** when ready

3. **Restore from Backup:**
   - Go to: **Backups**
   - Select recent backup
   - Click **Restore**

---

## Post-Deployment Maintenance Schedule

### Daily (First Week):

- [ ] Check Application Insights for errors
- [ ] Monitor response times
- [ ] Review logs for anomalies

### Weekly:

- [ ] Check backup completion status
- [ ] Review Azure costs
- [ ] Check for security advisories

### Monthly:

- [ ] Update Python dependencies (`pip list --outdated`)
- [ ] Review and rotate secrets (especially if any potential exposure)
- [ ] Check SSL certificate expiration
- [ ] Review Application Insights trends
- [ ] Update content (blog posts, testimonials)

### Quarterly:

- [ ] Full security audit
- [ ] Performance testing
- [ ] Backup restoration test
- [ ] Review and update documentation

---

## Quick Reference - Most Critical Steps

**Before you can deploy, you MUST:**

1. ✅ Revoke exposed Gmail password (Step 2)
2. ✅ Decide on two-app architecture (Step 3)
3. ✅ Fix all security issues in code (Step 5)
4. ✅ Commit and push to GitHub (Step 7)
5. ✅ Set all environment variables in Azure (Step 8)

**After deployment, immediately:**

1. ✅ Test admin login with 2FA (Step 15)
2. ✅ Verify HTTPS is working (Step 19)
3. ✅ Monitor logs for errors (Step 17)
4. ✅ Set up alerts (Step 30)

---

## Troubleshooting Common Issues

### "Application Error" on Azure URL

- Check logs in Azure Portal: Monitoring > Log stream
- Verify all environment variables are set correctly
- Check that requirements.txt has all dependencies
- Verify startup command is correct

### 2FA Email Not Sending

- Verify EMAIL_ADDRESS and EMAIL_PASSWORD are set in Azure
- Check that new Gmail app password is active
- Review logs for SMTP errors
- Test with a different email service if needed

### Database Not Found Errors

- Verify database.db was uploaded to correct location
- Check file permissions in Kudu
- Ensure path in code matches actual location
- Consider using Azure File Share for persistence

### Static Files Not Loading

- Verify static folder structure is correct
- Check that paths in HTML use {{ url_for('static', filename='...') }}
- Clear browser cache
- Check Azure logs for 404 errors

### API Endpoints Return 500 Errors

- If using two-app setup, verify API_BASE_URL is set correctly
- Check AUTH_KEY matches between main.py and api.py
- Verify api.py is running (check logs)
- Test API directly in browser

---

## Getting Help

- **Azure Support**: https://portal.azure.com → Support → New support request
- **Flask Documentation**: https://flask.palletsprojects.com/
- **Azure App Service Docs**: https://docs.microsoft.com/azure/app-service/
- **Application Insights**: https://docs.microsoft.com/azure/azure-monitor/app/app-insights-overview

---

**Total Checklist Items**: 150+  
**Estimated Completion Time**: 3-4 hours  
**Your Progress**: \_\_\_ / 150 items completed

**Good luck with your deployment! 🚀**
