# این فایل برای رفع مشکل دور circular import بین main.py و models.py ایجاد شده است
import os
import logging
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from sqlalchemy.orm import DeclarativeBase
from werkzeug.middleware.proxy_fix import ProxyFix

# Initialize logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                   level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Create base class for SQLAlchemy models
class Base(DeclarativeBase):
    pass

# Initialize SQLAlchemy
db = SQLAlchemy(model_class=Base)

# Create Flask app
app = Flask(__name__)

# تنظیمات امنیتی کلید جلسه - استفاده از کلید تصادفی طولانی و پیچیده
secret_key = os.environ.get("SESSION_SECRET")
if not secret_key or secret_key == "default_secret_key":
    import secrets
    secret_key = secrets.token_hex(32)  # 256 بیت کلید تصادفی
    logger.warning('از کلید امنیتی پیش‌فرض استفاده می‌شود. برای محیط تولید، متغیر محیطی SESSION_SECRET را تنظیم کنید.')

app.secret_key = secret_key

# تنظیمات امنیتی کوکی‌ها
app.config["SESSION_COOKIE_SECURE"] = True  # فقط در HTTPS ارسال شود
app.config["SESSION_COOKIE_HTTPONLY"] = True  # غیرقابل دسترس با JavaScript
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"  # محافظت در برابر حملات CSRF
app.config["PERMANENT_SESSION_LIFETIME"] = 3600  # منقضی شدن جلسه بعد از 1 ساعت

# تنظیمات Content Security Policy (CSP)
app.config["CSP"] = {
    'default-src': "'self'",
    'script-src': "'self' https://cdn.jsdelivr.net",
    'style-src': "'self' https://cdn.jsdelivr.net https://cdn.replit.com",
    'font-src': "'self' https://cdn.jsdelivr.net",
    'img-src': "'self' data:"
}

app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

# Configure database
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL", "sqlite:///university_food.db")
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# Initialize database with app
db.init_app(app)

# Initialize Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = 'لطفاً برای دسترسی به این صفحه وارد سیستم شوید.'

# تعریف میدلور امنیتی برای افزودن هدرهای HTTP امنیتی
@app.after_request
def add_security_headers(response):
    # غیرفعال کردن MIME sniffing
    response.headers['X-Content-Type-Options'] = 'nosniff'
    
    # جلوگیری از قرار گرفتن در iframe در سایت‌های دیگر (محافظت در برابر Clickjacking)
    response.headers['X-Frame-Options'] = 'SAMEORIGIN'
    
    # محافظت در برابر حملات XSS
    response.headers['X-XSS-Protection'] = '1; mode=block'
    
    # تنظیم سیاست امنیتی محتوا (CSP)
    if app.config.get('CSP'):
        csp = ''
        for directive, sources in app.config['CSP'].items():
            csp += f"{directive} {sources}; "
        response.headers['Content-Security-Policy'] = csp
    
    # مدیریت اطلاعات ارجاع‌دهنده (Referrer)
    response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
    
    return response

# تنظیمات کوکی‌های جلسه
# در حالت توسعه (development) تنظیمات امنیتی را به صورت موقت غیرفعال می‌کنیم
# فقط برای محیط توسعه - در محیط تولید این تنظیمات باید فعال باشند
app.config["SESSION_COOKIE_SECURE"] = False  # در محیط تولید به True تغییر دهید

# قفل کردن حساب بعد از تعداد مشخصی تلاش ناموفق
# دیکشنری برای نگهداری تعداد تلاش‌های ناموفق لاگین
login_attempts = {}
max_login_attempts = 5
login_timeout = 900  # در ثانیه (15 دقیقه)