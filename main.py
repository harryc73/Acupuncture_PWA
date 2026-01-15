from flask import Flask
from flask import redirect
from flask import render_template
from flask import request
from flask import jsonify
from flask import session
import requests
from flask_wtf import CSRFProtect
from flask_csp.csp import csp_header
import logging
import userManagement as dbHandler
import twofa
import testimonial_admin as admin_t
import blog_admin as admin_b
from flask import send_file
from datetime import timedelta
import methods as method

# Code snippet for logging a message
# app.logger.critical("message")

app_log = logging.getLogger(__name__)
logging.basicConfig(
    filename="security_log.log",
    encoding="utf-8",
    level=logging.DEBUG, 
    format="%(asctime)s %(message)s",
)

# Generate a unique basic 16 key: https://acte.ltd/utils/randomkeygen
app = Flask(__name__)
app.secret_key = b"_53oi3uriq9pifpff;apl"
auth_key = "4L50v92nOgcDCYUM"
csrf = CSRFProtect(app)

app_header = {"Authorization": "4L50v92nOgcDCYUM"}

# Set session lifetime to 24 hours
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(minutes=1440)

# Context processor to inject base_url into all templates
@app.context_processor
def inject_base_url():
    return {
        'base_url': request.host_url.rstrip('/'),
        'site_name': 'Le Acupuncture',
        'default_description': 'Professional acupuncture services'
    }

# Checks if the user is logged in, particularly when trying to access a page which requires authentication
# Redirects to the login page if not authenticated
@app.before_request
def require_login():
    public_routes = [
        '/', '/admin_login.html', '/static', '/about.html', '/booking.html', '/privacy.html', '/blog.html', '/index.html'
    ]
    if request.path.startswith('/static'):
        return
    if request.path in public_routes:
        return
    if session.get('username') is None:
        session.clear()
        return redirect("/index.html", 302)

@app.after_request
def add_header(response):
    response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, post-check=0, pre-check=0, max-age=0"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    return response



# Redirect index.html to domain root for consistent UX
@app.route("/index", methods=["GET"])
@app.route("/index.htm", methods=["GET"])
@app.route("/index.asp", methods=["GET"])
@app.route("/index.php", methods=["GET"])
@app.route("/index.html", methods=["GET"])
def root():
    return redirect("/", 302)


@app.route("/", methods=["POST", "GET"])
@csp_header(
    {
        "base-uri": "'self'",
        "default-src": "'self'",
        "style-src": "'self' 'unsafe-inline' www.instagram.com",
        "script-src": "'self' www.instagram.com https://cdn.tiny.cloud",
        "img-src": "'self' data: cdninstagram.com",
        "media-src": "'self'",
        "font-src": "'self'",
        "object-src": "'self'",
        "child-src": "'self'",
        "connect-src": "'self'",
        "worker-src": "'self'",
        "report-uri": "/csp_report",
        "frame-ancestors": "'none'",
        "form-action": "'self'",
        "frame-src": "'self' www.instagram.com le-acupuncture.au2.cliniko.com www.google.com https://cdn.tiny.cloud",
    }
)
def index():
    return render_template("/index.html")

@app.route("/admin_login.html", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        if dbHandler.checkAdmin(username, password):
            admin_email = dbHandler.getAdminEmail(username)
            otp_code = twofa.generate_otp()
            session["username"] = username
            session["admin_email"] = admin_email
            print(f"OTP code: {otp_code}")
            print(f"Admin email: {admin_email}")
            session["otp_code"] = otp_code
            twofa.send_otp_via_email(admin_email, otp_code)
            return render_template("2fa.html", session=username)
        else:
            app.logger.critical("Failed login attempt")
            return render_template("admin_login.html", error=True)
    return render_template("admin_login.html")



@app.route("/admin.html", methods=["GET"])
def admin_page():
    return render_template("/admin.html")

@app.route("/admin_testimonials.html", methods=["GET", "POST"])
def add_testiominals():
    if request.method == "POST":
        delete_id = request.form.get("id")
        if delete_id:
            delete = method.delete_testimonial(delete_id)
            data = method.get_api_data("get_testimonials")
            return render_template("admin_testimonials.html", data=data, delete=delete)
        else:
            form_data = admin_t.sanitize_testimonial(request.form)
            success = method.add_testimonial(form_data)
            data = method.get_api_data("get_testimonials")
            return render_template("admin_testimonials.html", data=data, success=success)
    data = method.get_api_data("get_testimonials")
    return render_template("admin_testimonials.html", data=data)

@app.route("/2fa.html", methods=["POST"])
def twofa_page():
    if request.method == "POST":
        # Generate OTP and send it via email
        user_input = request.form["otp_code"]
        otp_code = session.get("otp_code")
        if twofa.verify_otp(user_input, otp_code):
            app.logger.critical("Successful 2FA attempt")
            return redirect("/admin.html")
        else:
            app.logger.critical("Failed 2FA attempt")
            return render_template("2fa.html", error=True)
    return render_template("2fa.html")

@app.route("/booking.html", methods=["GET"])
def booking():
    data = method.get_api_data("get_testimonials")
    return render_template("/booking.html", data=data)

@app.route("/admin_blog.html", methods=["GET", "POST"])
def admin_blog():
    if request.method == "POST":
        delete_id = request.form.get("id")
        if delete_id:
            print(f"Delete ID: {delete_id}")
            delete = method.delete_blog(delete_id)
            data = method.get_api_data("get_blog")
            return render_template("admin_blog.html", data=data, delete=delete)
        else:
            blog_data = admin_b.sanatize_blog(request)
            print(blog_data)
            success = method.post_blog(blog_data)
            data = method.get_api_data("get_blog")
        return render_template("/admin_blog.html", success=success, data=data)
    data = method.get_api_data("get_blog")
    return render_template("/admin_blog.html", data=data)

@app.route("/admin_about.html", methods=["GET", "POST"])
def admin_about():
    if request.method == "POST":
        form_data = admin_b.sanatize_aboutme(request)
        print(form_data)
        success = method.update_aboutme(form_data)
        data = method.get_api_data("get_aboutme")
        return render_template("/admin_about.html", success=success, data=data)
    data = method.get_api_data("get_aboutme")
    return render_template("/admin_about.html", data=data)

@app.route("/admin_change_password.html", methods=["GET", "POST"])
def admin_change_password():
    admin_email = session.get("admin_email")
    username = session.get("username")
    if request.method == "GET":
        otp_code = twofa.generate_otp()
        print(f"Change OTP Code: {otp_code}")
        print(f"Change Admin email: {admin_email}")
        session["otp_code"] = otp_code
        twofa.send_otp_via_email(admin_email, otp_code)
        return render_template("/admin_change_password.html")
    if request.method == "POST":
        input_code = request.form["input_code"]
        otp_code = session.get("otp_code")
        current_password = request.form["current_password"]
        new_password = request.form["new_password"]
        if twofa.verify_otp(input_code, otp_code) and dbHandler.checkAdmin(username, current_password):
            print("Passed verification check")
            errors = dbHandler.validate_password(new_password)
            if not errors or not any(errors.values()):
                dbHandler.changePassword(username, new_password)
                return render_template("/admin_change_password.html", success=True, errors=None)
            else:
                return render_template("/admin_change_password.html", errors=errors)
        else:
            return render_template("/admin_change_password.html", error="Invalid 2FA code or current password", errors=None)

@app.route("/privacy.html", methods=["GET"])
def privacy():
    return render_template("/privacy.html")

@app.route("/about.html", methods=["GET"])
def about():
    data = {}
    data = method.get_api_data("get_aboutme")
    return render_template("/about.html", data=data)

@app.route("/blog.html", methods=["GET"])
def blog():
    data = {}
    data = method.get_api_data("get_blog")
    return render_template("/blog.html", data=data)

@app.route("/download_logs", methods=["GET"])
def download_logs():
    return send_file("security_log.log", as_attachment=True)

@app.route("/logout", methods=["POST", "GET"])
def logout():
    username = session.pop('username', None)
    if username:
        app_log.info("User '%s' logged out successfully", username)
    session.clear()
    return redirect("admin_login.html")

# Endpoint for logging CSP violations
@app.route("/csp_report", methods=["POST"])
@csrf.exempt
def csp_report():
    app.logger.critical(request.data.decode())
    return "done"

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
