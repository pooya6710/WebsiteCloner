import datetime
import os
import time
from collections import OrderedDict
from flask import request, jsonify, render_template, redirect, url_for, flash, session
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash

from app import app, db, login_manager, logger, security_logger, login_attempts, max_login_attempts, login_timeout
from zarinpal import ZarinPal

# حذف درگاه پرداخت زرین‌پال به درخواست کاربر
# zarinpal_gateway = ZarinPal(sandbox=True)  # استفاده از محیط تست

# Create all database tables
with app.app_context():
    # Import models to register them with SQLAlchemy
    from models import Student, Reservation, Menu, DatabaseBackup, User, Payment
    db.create_all()
    
    # بارگذاری منوی پیش‌فرض (اگر وجود نداشته باشد)
    from models import load_default_menu
    load_default_menu(db.session)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Routes
@app.route('/')
def index():
    # آمار واقعی برای صفحه اصلی
    now = datetime.datetime.now()
    
    # تعداد کل دانشجویان
    student_count = Student.query.count()
    
    # تعداد کل رزروها
    reservation_count = Reservation.query.count()
    
    # تعداد رزروهای تحویل شده
    delivered_count = Reservation.query.filter_by(delivered=1).count()
    
    # تعداد روزهای منو
    menu_days_count = Menu.query.count()
    
    # آمار وعده‌های غذایی
    breakfast_count = Reservation.query.filter_by(meal='breakfast').count()
    lunch_count = Reservation.query.filter_by(meal='lunch').count()
    dinner_count = Reservation.query.filter_by(meal='dinner').count()
    
    # آمار غذاهای محبوب
    popular_foods = db.session.query(
        Reservation.food_name, 
        db.func.count(Reservation.id).label('count')
    ).group_by(Reservation.food_name).order_by(db.func.count(Reservation.id).desc()).limit(3).all()
    
    return render_template('index.html', 
                           now=now,
                           student_count=student_count,
                           reservation_count=reservation_count,
                           delivered_count=delivered_count,
                           menu_days_count=menu_days_count,
                           breakfast_count=breakfast_count,
                           lunch_count=lunch_count,
                           dinner_count=dinner_count,
                           popular_foods=popular_foods)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        feeding_code = request.form.get('username')  # نام فیلد در فرم هنوز username است
        password = request.form.get('password')
        
        # بررسی قفل حساب کاربری
        client_ip = request.remote_addr
        user_agent = request.headers.get('User-Agent', 'Unknown')
        current_time = time.time()
        
        # لاگ تلاش ورود
        security_logger.info(f"Login attempt from IP: {client_ip}, Feeding Code: {feeding_code}, User-Agent: {user_agent}")
        
        # پاک کردن رکوردهای منقضی شده تلاش‌های ناموفق
        for ip in list(login_attempts.keys()):
            if current_time - login_attempts[ip]['timestamp'] > login_timeout:
                security_logger.info(f"Removing expired login attempts record for IP: {ip}")
                del login_attempts[ip]
        
        # بررسی وضعیت قفل حساب برای آدرس IP فعلی
        if client_ip in login_attempts and login_attempts[client_ip]['attempts'] >= max_login_attempts:
            # بررسی زمان قفل
            time_passed = current_time - login_attempts[client_ip]['timestamp']
            if time_passed < login_timeout:
                remaining_time = int((login_timeout - time_passed) / 60)
                security_logger.warning(f"Blocked login attempt from IP: {client_ip} - Account is locked. Attempts: {login_attempts[client_ip]['attempts']}")
                flash(f'حساب کاربری شما به دلیل تلاش‌های ناموفق قفل شده است. لطفاً {remaining_time} دقیقه دیگر امتحان کنید.', 'danger')
                return render_template('login.html')
            else:
                # زمان قفل به پایان رسیده است
                security_logger.info(f"Unlocking account for IP: {client_ip} - Lock timeout expired")
                del login_attempts[client_ip]
        
        user = User.query.filter_by(username=feeding_code).first()
        
        if user and check_password_hash(user.password, password):
            # ورود موفق - پاک کردن سابقه تلاش‌های ناموفق
            if client_ip in login_attempts:
                del login_attempts[client_ip]
                
            # ثبت ورود موفق در لاگ
            security_logger.info(f"Successful login for Feeding Code: {feeding_code} from IP: {client_ip}")
            
            login_user(user)
            flash('با موفقیت وارد شدید', 'success')
            return redirect(url_for('dashboard'))
        else:
            # ورود ناموفق - افزایش شمارنده تلاش‌های ناموفق
            if client_ip not in login_attempts:
                login_attempts[client_ip] = {'attempts': 1, 'timestamp': current_time}
                security_logger.warning(f"Failed login attempt for Feeding Code: {feeding_code} from IP: {client_ip} (Attempt 1/{max_login_attempts})")
            else:
                login_attempts[client_ip]['attempts'] += 1
                login_attempts[client_ip]['timestamp'] = current_time
                security_logger.warning(f"Failed login attempt for Feeding Code: {feeding_code} from IP: {client_ip} (Attempt {login_attempts[client_ip]['attempts']}/{max_login_attempts})")
            
            # اعلان تعداد تلاش‌های باقی‌مانده
            remaining_attempts = max_login_attempts - login_attempts[client_ip]['attempts']
            if remaining_attempts > 0:
                flash(f'کد تغذیه یا رمز عبور اشتباه است. {remaining_attempts} تلاش دیگر باقی مانده است.', 'danger')
            else:
                security_logger.warning(f"Account locked for IP: {client_ip} due to too many failed login attempts ({max_login_attempts})")
                flash(f'حساب کاربری شما به مدت {int(login_timeout/60)} دقیقه قفل شده است.', 'danger')
    
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        feeding_code = request.form.get('feeding_code')
        
        # بررسی تطابق رمز عبور
        if password != confirm_password:
            flash('رمز عبور و تکرار آن مطابقت ندارند', 'danger')
            return render_template('register.html')
        
        # بررسی اینکه کد تغذیه قبلاً ثبت نشده باشد
        existing_student = Student.query.filter_by(feeding_code=feeding_code).first()
        if existing_student:
            flash('این کد تغذیه قبلاً ثبت شده است', 'danger')
            return render_template('register.html')
        
        # بررسی اینکه کاربری با این نام کاربری قبلاً ثبت نشده باشد
        existing_user = User.query.filter_by(username=feeding_code).first()
        if existing_user:
            flash('کاربری با این کد تغذیه قبلاً ثبت شده است', 'danger')
            return render_template('register.html')
        
        # ایجاد کاربر جدید - از کد تغذیه به عنوان نام کاربری استفاده می‌کنیم
        new_user = User(username=feeding_code, password=generate_password_hash(password))
        db.session.add(new_user)
        db.session.flush()  # برای دریافت ID کاربر
        
        # ایجاد دانشجو
        new_student = Student(user_id=str(new_user.id), feeding_code=feeding_code)
        db.session.add(new_student)
        db.session.commit()
        
        # ثبت لاگ ایجاد حساب جدید
        client_ip = request.remote_addr
        user_agent = request.headers.get('User-Agent', 'Unknown')
        security_logger.info(f"New user registered: User ID: {new_user.id}, Feeding Code: {feeding_code}, IP: {client_ip}, User-Agent: {user_agent}")
        
        flash('ثبت نام شما با موفقیت انجام شد. اکنون می‌توانید وارد سیستم شوید', 'success')
        return redirect(url_for('login'))
    
    return render_template('register.html')

@app.route('/logout')
@login_required
def logout():
    # ثبت لاگ خروج از سیستم
    client_ip = request.remote_addr
    user_agent = request.headers.get('User-Agent', 'Unknown')
    try:
        user_id = current_user.id
        username = current_user.username
        security_logger.info(f"User logged out: User ID: {user_id}, Username: {username}, IP: {client_ip}, User-Agent: {user_agent}")
    except Exception as e:
        security_logger.warning(f"Error logging logout: {str(e)}")
    
    logout_user()
    flash('با موفقیت خارج شدید', 'success')
    return redirect(url_for('index'))

@app.route('/dashboard')
@login_required
def dashboard():
    # دریافت اطلاعات دانشجو
    student = Student.query.filter_by(user_id=str(current_user.id)).first()
    if not student:
        flash('اطلاعات دانشجویی شما یافت نشد', 'danger')
        return redirect(url_for('index'))
    
    # دریافت رزروهای دانشجو
    reservations = Reservation.query.filter_by(student_id=student.id).all()
    
    return render_template('dashboard.html', student=student, reservations=reservations)

@app.route('/menu')
@login_required
def menu():
    # دریافت منوی هفتگی
    weekly_menu = Menu.query.all()
    # استفاده از OrderedDict برای حفظ ترتیب روزها (شنبه در ابتدا)
    days = OrderedDict([
        ("saturday", "شنبه"),
        ("sunday", "یکشنبه"),
        ("monday", "دوشنبه"),
        ("tuesday", "سه‌شنبه"),
        ("wednesday", "چهارشنبه"),
        ("thursday", "پنج‌شنبه"),
        ("friday", "جمعه")
    ])
    meals = {
        "breakfast": "صبحانه",
        "lunch": "ناهار",
        "dinner": "شام"
    }
    
    return render_template('menu.html', weekly_menu=weekly_menu, days=days, meals=meals)

@app.route('/reserve', methods=['POST'])
@login_required
def reserve():
    day = request.form.get('day')
    meal = request.form.get('meal')
    food_name = request.form.get('food_name')
    
    if not all([day, meal, food_name]):
        flash('لطفاً تمام فیلدها را پر کنید', 'danger')
        return redirect(url_for('menu'))
    
    # دریافت اطلاعات دانشجو
    student = Student.query.filter_by(user_id=str(current_user.id)).first()
    if not student:
        flash('اطلاعات دانشجویی شما یافت نشد', 'danger')
        return redirect(url_for('menu'))
    
    # بررسی اینکه رزرو قبلاً انجام نشده باشد
    existing_reservation = Reservation.query.filter_by(
        student_id=student.id, day=day, meal=meal
    ).first()
    
    if existing_reservation:
        flash(f'شما قبلاً برای {day} وعده {meal} رزرو کرده‌اید', 'warning')
        return redirect(url_for('menu'))
    
    # ایجاد رزرو جدید
    new_reservation = Reservation(
        student_id=student.id,
        day=day,
        meal=meal,
        food_name=food_name,
        delivered=0
    )
    db.session.add(new_reservation)
    db.session.commit()
    
    flash(f'رزرو شما برای {day} وعده {meal} با موفقیت ثبت شد', 'success')
    return redirect(url_for('dashboard'))

@app.route('/reserve_all_day', methods=['POST'])
@login_required
def reserve_all_day():
    day = request.form.get('day')
    
    if not day:
        flash('روز مورد نظر مشخص نشده است', 'danger')
        return redirect(url_for('menu'))
    
    # دریافت اطلاعات دانشجو
    student = Student.query.filter_by(user_id=str(current_user.id)).first()
    if not student:
        flash('اطلاعات دانشجویی شما یافت نشد', 'danger')
        return redirect(url_for('menu'))
    
    # دریافت منوی روز مورد نظر
    day_menu = Menu.query.filter_by(day=day).first()
    if not day_menu:
        flash(f'منوی روز {day} یافت نشد', 'danger')
        return redirect(url_for('menu'))
    
    meal_data = day_menu.meal_data
    success_count = 0
    already_reserved = 0
    
    # وعده‌های غذایی
    meals = ['breakfast', 'lunch', 'dinner']
    
    for meal in meals:
        # بررسی اینکه این وعده در منو وجود داشته باشد و حداقل یک غذا داشته باشد
        if meal in meal_data and meal_data[meal] and len(meal_data[meal]) > 0:
            # بررسی رزرو قبلی
            existing_reservation = Reservation.query.filter_by(
                student_id=student.id, day=day, meal=meal
            ).first()
            
            if existing_reservation:
                already_reserved += 1
                continue
            
            # انتخاب اولین غذای هر وعده
            food_name = meal_data[meal][0]
            
            # ایجاد رزرو جدید
            new_reservation = Reservation(
                student_id=student.id,
                day=day,
                meal=meal,
                food_name=food_name,
                delivered=0
            )
            db.session.add(new_reservation)
            success_count += 1
    
    if success_count > 0:
        db.session.commit()
        meal_fa = 'وعده' if success_count == 1 else 'وعده'
        flash(f'{success_count} {meal_fa} غذا برای روز {day} با موفقیت رزرو شد', 'success')
    else:
        if already_reserved > 0:
            flash(f'شما قبلاً تمام وعده‌های روز {day} را رزرو کرده‌اید', 'warning')
        else:
            flash(f'هیچ وعده‌ای برای روز {day} رزرو نشد', 'warning')
    
    return redirect(url_for('dashboard'))

@app.route('/cancel_reservation/<int:reservation_id>', methods=['POST'])
@login_required
def cancel_reservation(reservation_id):
    reservation = Reservation.query.get_or_404(reservation_id)
    student = Student.query.filter_by(user_id=str(current_user.id)).first()
    
    if not student or reservation.student_id != student.id:
        flash('شما مجوز حذف این رزرو را ندارید', 'danger')
        return redirect(url_for('dashboard'))
    
    db.session.delete(reservation)
    db.session.commit()
    
    flash('رزرو با موفقیت لغو شد', 'success')
    return redirect(url_for('dashboard'))

@app.route('/admin')
@login_required
def admin():
    if not current_user.is_admin:
        flash('شما دسترسی به پنل مدیریت را ندارید', 'danger')
        return redirect(url_for('dashboard'))
    
    # دریافت آمار برای پنل مدیریت
    student_count = Student.query.count()
    reservation_count = Reservation.query.count()
    delivered_count = Reservation.query.filter_by(delivered=1).count()
    pending_count = Reservation.query.filter_by(delivered=0).count()
    
    return render_template('admin.html', 
                           student_count=student_count,
                           reservation_count=reservation_count,
                           delivered_count=delivered_count,
                           pending_count=pending_count)

@app.route('/admin/students')
@login_required
def admin_students():
    if not current_user.is_admin:
        flash('شما دسترسی به این بخش را ندارید', 'danger')
        return redirect(url_for('dashboard'))
    
    students = Student.query.all()
    return render_template('admin_students.html', students=students)

@app.route('/admin/reservations')
@login_required
def admin_reservations():
    if not current_user.is_admin:
        flash('شما دسترسی به این بخش را ندارید', 'danger')
        return redirect(url_for('dashboard'))
    
    reservations = Reservation.query.all()
    return render_template('admin_reservations.html', reservations=reservations)

@app.route('/admin/student/<int:student_id>/reservations')
@login_required
def admin_student_reservations(student_id):
    if not current_user.is_admin:
        flash('شما دسترسی به این بخش را ندارید', 'danger')
        return redirect(url_for('dashboard'))
    
    student = Student.query.get_or_404(student_id)
    reservations = Reservation.query.filter_by(student_id=student_id).all()
    
    return render_template('admin_student_reservations.html', 
                           student=student, 
                           reservations=reservations)

@app.route('/admin/menu')
@login_required
def admin_menu():
    if not current_user.is_admin:
        flash('شما دسترسی به این بخش را ندارید', 'danger')
        return redirect(url_for('dashboard'))
    
    weekly_menu = Menu.query.all()
    # استفاده از OrderedDict برای حفظ ترتیب روزها (شنبه در ابتدا)
    days = OrderedDict([
        ("saturday", "شنبه"),
        ("sunday", "یکشنبه"),
        ("monday", "دوشنبه"),
        ("tuesday", "سه‌شنبه"),
        ("wednesday", "چهارشنبه"),
        ("thursday", "پنج‌شنبه"),
        ("friday", "جمعه")
    ])
    meals = {
        "breakfast": "صبحانه",
        "lunch": "ناهار",
        "dinner": "شام"
    }
    
    return render_template('admin_menu.html', weekly_menu=weekly_menu, days=days, meals=meals)

@app.route('/admin/update_menu', methods=['POST'])
@login_required
def admin_update_menu():
    if not current_user.is_admin:
        flash('شما دسترسی به این بخش را ندارید', 'danger')
        return redirect(url_for('dashboard'))
    
    # دریافت و بررسی داده‌های فرم
    day = request.form.get('day')
    meal = request.form.get('meal')
    food_items_text = request.form.get('food_items')
    
    # بررسی اعتبار داده‌های ورودی
    if not day or not meal:
        flash('روز و وعده غذایی باید مشخص شوند', 'danger')
        return redirect(url_for('admin_menu'))
    
    # پردازش لیست غذاها
    food_items = [item.strip() for item in food_items_text.split('\n') if item.strip()]
    
    try:
        # لاگ اطلاعات ورودی برای دیباگ
        print(f"Updating menu - Day: {day}, Meal: {meal}")
        print(f"Food items: {food_items}")
        
        # دریافت منوی روز مورد نظر
        day_menu = Menu.query.filter_by(day=day).first()
        if not day_menu:
            print(f"Creating new menu for day: {day}")
            flash(f'منوی روز {day} یافت نشد - در حال ایجاد منوی جدید', 'warning')
            # ایجاد یک منوی جدید برای این روز
            day_menu = Menu(day=day, meal_data={
                "breakfast": [],
                "lunch": [],
                "dinner": []
            })
            db.session.add(day_menu)
            db.session.flush()  # برای دریافت ID جدید
            print(f"Created new menu with ID: {day_menu.id}")
        else:
            print(f"Found existing menu for day: {day}, ID: {day_menu.id}")
            print(f"Current meal_data: {day_menu.meal_data}")
        
        # تضمین اینکه meal_data یک دیکشنری معتبر است
        current_data = {}
        if day_menu.meal_data:
            if isinstance(day_menu.meal_data, dict):
                current_data = day_menu.meal_data
                print(f"meal_data is valid dictionary")
            elif isinstance(day_menu.meal_data, str):
                import json
                try:
                    current_data = json.loads(day_menu.meal_data)
                    print(f"Converted string meal_data to dictionary")
                except json.JSONDecodeError as e:
                    print(f"JSON decode error: {str(e)}")
                    current_data = {}
            else:
                print(f"Unknown meal_data type: {type(day_menu.meal_data)}")
                current_data = {}
        else:
            print("meal_data is None or empty, initializing new dictionary")
        
        # وعده‌های غذایی پیش‌فرض را اضافه می‌کنیم اگر وجود نداشته باشند
        for meal_name in ['breakfast', 'lunch', 'dinner']:
            if meal_name not in current_data:
                current_data[meal_name] = []
                print(f"Added missing meal type: {meal_name}")
        
        # به‌روزرسانی منو برای وعده مورد نظر
        print(f"Updating menu for meal: {meal} with items: {food_items}")
        current_data[meal] = food_items.copy()
        
        # بررسی و لاگ داده‌های جدید
        print(f"New meal_data structure: {current_data}")
        day_menu.meal_data = current_data
        
        # کامیت کردن تغییرات به دیتابیس
        db.session.commit()
        print(f"Successfully committed changes to database")
        
        # تایید نهایی تغییرات
        updated_menu = Menu.query.get(day_menu.id)
        print(f"Verification - Updated menu data: {updated_menu.meal_data}")
        
        flash(f'منوی {meal} روز {day} با موفقیت به‌روزرسانی شد', 'success')
    except Exception as e:
        db.session.rollback()
        # لاگ خطا با جزئیات بیشتر
        import traceback
        error_details = traceback.format_exc()
        print(f"ERROR updating menu: {str(e)}")
        print(f"Traceback: {error_details}")
        flash(f'خطا در به‌روزرسانی منو: {str(e)}', 'danger')
    
    return redirect(url_for('admin_menu'))

@app.route('/admin/delivery/<int:reservation_id>', methods=['POST'])
@login_required
def admin_delivery(reservation_id):
    if not current_user.is_admin:
        flash('شما دسترسی به این بخش را ندارید', 'danger')
        return redirect(url_for('dashboard'))
    
    reservation = Reservation.query.get_or_404(reservation_id)
    reservation.delivered = 1  # تنظیم وضعیت تحویل به "تحویل شده"
    db.session.commit()
    
    flash('وضعیت تحویل غذا با موفقیت به‌روزرسانی شد', 'success')
    return redirect(url_for('admin_reservations'))

@app.route('/reserve_all_week', methods=['POST'])
@login_required
def reserve_all_week():
    # دریافت اطلاعات دانشجو
    student = Student.query.filter_by(user_id=str(current_user.id)).first()
    if not student:
        flash('اطلاعات دانشجویی شما یافت نشد', 'danger')
        return redirect(url_for('menu'))
    
    # دریافت منوی هفتگی
    weekly_menu = Menu.query.all()
    if not weekly_menu:
        flash('منوی هفتگی یافت نشد', 'danger')
        return redirect(url_for('menu'))
    
    success_count = 0
    already_reserved = 0
    
    # وعده‌های غذایی
    meals = ['breakfast', 'lunch', 'dinner']
    
    for day_menu in weekly_menu:
        for meal in meals:
            # بررسی اینکه این وعده در منو وجود داشته باشد و حداقل یک غذا داشته باشد
            if meal in day_menu.meal_data and day_menu.meal_data[meal] and len(day_menu.meal_data[meal]) > 0:
                # بررسی رزرو قبلی
                existing_reservation = Reservation.query.filter_by(
                    student_id=student.id, day=day_menu.day, meal=meal
                ).first()
                
                if existing_reservation:
                    already_reserved += 1
                    continue
                
                # انتخاب اولین غذای هر وعده
                food_name = day_menu.meal_data[meal][0]
                
                # ایجاد رزرو جدید
                new_reservation = Reservation(
                    student_id=student.id,
                    day=day_menu.day,
                    meal=meal,
                    food_name=food_name,
                    delivered=0
                )
                db.session.add(new_reservation)
                success_count += 1
    
    if success_count > 0:
        db.session.commit()
        meal_fa = 'وعده' if success_count == 1 else 'وعده'
        flash(f'{success_count} {meal_fa} غذا برای کل هفته با موفقیت رزرو شد', 'success')
    else:
        if already_reserved > 0:
            flash('شما قبلاً تمام وعده‌های هفته را رزرو کرده‌اید', 'warning')
        else:
            flash('هیچ وعده‌ای برای هفته رزرو نشد', 'warning')
    
    return redirect(url_for('dashboard'))

@app.route('/settings', methods=['GET', 'POST'])
@login_required
def settings():
    if request.method == 'POST':
        current_password = request.form.get('current_password')
        new_password = request.form.get('new_password')
        confirm_password = request.form.get('confirm_password')
        
        # بررسی تطابق رمز عبور جدید
        if new_password != confirm_password:
            flash('رمز عبور جدید و تکرار آن مطابقت ندارند', 'danger')
            return redirect(url_for('settings'))
        
        # بررسی رمز عبور فعلی
        user = User.query.get(current_user.id)
        if not check_password_hash(user.password, current_password):
            flash('رمز عبور فعلی نادرست است', 'danger')
            return redirect(url_for('settings'))
        
        # به‌روزرسانی رمز عبور
        user.password = generate_password_hash(new_password)
        db.session.commit()
        
        flash('رمز عبور شما با موفقیت تغییر یافت', 'success')
        return redirect(url_for('dashboard'))
    
    return render_template('settings.html')

@app.route('/cancel_all_day', methods=['POST'])
@login_required
def cancel_all_day():
    day = request.form.get('day')
    
    if not day:
        flash('روز مورد نظر مشخص نشده است', 'danger')
        return redirect(url_for('dashboard'))
    
    # دریافت اطلاعات دانشجو
    student = Student.query.filter_by(user_id=str(current_user.id)).first()
    if not student:
        flash('اطلاعات دانشجویی شما یافت نشد', 'danger')
        return redirect(url_for('dashboard'))
    
    # دریافت رزروهای روز مورد نظر
    reservations = Reservation.query.filter_by(
        student_id=student.id, day=day, delivered=0
    ).all()
    
    if not reservations:
        # انتخاب نام فارسی روز
        # استفاده از OrderedDict برای حفظ ترتیب روزها (شنبه در ابتدا)
        days = OrderedDict([
            ("saturday", "شنبه"),
            ("sunday", "یکشنبه"),
            ("monday", "دوشنبه"),
            ("tuesday", "سه‌شنبه"),
            ("wednesday", "چهارشنبه"),
            ("thursday", "پنج‌شنبه"),
            ("friday", "جمعه")
        ])
        flash(f'شما رزرو قابل لغوی برای روز {days.get(day, day)} ندارید', 'warning')
        return redirect(url_for('dashboard'))
    
    # حذف رزروها
    count = 0
    for reservation in reservations:
        db.session.delete(reservation)
        count += 1
    
    db.session.commit()
    
    # انتخاب نام فارسی روز
    # استفاده از OrderedDict برای حفظ ترتیب روزها (شنبه در ابتدا)
    days = OrderedDict([
        ("saturday", "شنبه"),
        ("sunday", "یکشنبه"),
        ("monday", "دوشنبه"),
        ("tuesday", "سه‌شنبه"),
        ("wednesday", "چهارشنبه"),
        ("thursday", "پنج‌شنبه"),
        ("friday", "جمعه")
    ])
    flash(f'{count} رزرو برای روز {days.get(day, day)} با موفقیت لغو شد', 'success')
    return redirect(url_for('dashboard'))

@app.route('/cancel_all_week', methods=['POST'])
@login_required
def cancel_all_week():
    # دریافت اطلاعات دانشجو
    student = Student.query.filter_by(user_id=str(current_user.id)).first()
    if not student:
        flash('اطلاعات دانشجویی شما یافت نشد', 'danger')
        return redirect(url_for('dashboard'))
    
    # دریافت همه رزروهای قابل لغو
    reservations = Reservation.query.filter_by(
        student_id=student.id, delivered=0
    ).all()
    
    if not reservations:
        flash('شما هیچ رزرو قابل لغوی ندارید', 'warning')
        return redirect(url_for('dashboard'))
    
    # حذف رزروها
    count = 0
    for reservation in reservations:
        db.session.delete(reservation)
        count += 1
    
    db.session.commit()
    
    flash(f'{count} رزرو برای کل هفته با موفقیت لغو شد', 'success')
    return redirect(url_for('dashboard'))

@app.route('/admin/reports')
@login_required
def admin_reports():
    if not current_user.is_admin:
        flash('شما دسترسی به این بخش را ندارید', 'danger')
        return redirect(url_for('dashboard'))
    
    # جمع‌آوری آمار برای غذاهای پرطرفدار
    food_stats = db.session.query(
        Reservation.food_name, 
        db.func.count(Reservation.id).label('count')
    ).group_by(Reservation.food_name).order_by(db.func.count(Reservation.id).desc()).limit(5).all()
    
    # محاسبه درصد برای هر غذا
    total_reservations = Reservation.query.count()
    popular_foods = []
    for food_name, count in food_stats:
        percentage = (count / total_reservations * 100) if total_reservations > 0 else 0
        popular_foods.append({
            'name': food_name,
            'count': count,
            'percentage': percentage
        })
    
    # آمار رزروها بر اساس روزهای هفته
    # استفاده از OrderedDict برای حفظ ترتیب روزها (شنبه در ابتدا)
    days = OrderedDict([
        ("saturday", "شنبه"),
        ("sunday", "یکشنبه"),
        ("monday", "دوشنبه"),
        ("tuesday", "سه‌شنبه"),
        ("wednesday", "چهارشنبه"),
        ("thursday", "پنج‌شنبه"),
        ("friday", "جمعه")
    ])
    
    # مرتب‌سازی ترتیب روزهای هفته (شنبه در ابتدا)
    day_order = OrderedDict([
        ("saturday", 0),
        ("sunday", 1),
        ("monday", 2),
        ("tuesday", 3),
        ("wednesday", 4),
        ("thursday", 5),
        ("friday", 6)
    ])
    
    # آمار ترکیبی روز و وعده‌های غذایی
    day_meal_stats = db.session.query(
        Reservation.day,
        Reservation.meal,
        db.func.count(Reservation.id).label('count')
    ).group_by(Reservation.day, Reservation.meal).all()
    
    # ساختار داده برای آمار روزانه به تفکیک وعده
    daily_meal_stats = {}
    for day_name in days.keys():
        daily_meal_stats[day_name] = {
            'day_name': days[day_name],
            'breakfast': 0,
            'lunch': 0,
            'dinner': 0,
            'total': 0
        }
    
    # پر کردن آمار روزانه به تفکیک وعده
    for day, meal, count in day_meal_stats:
        if day in daily_meal_stats:
            daily_meal_stats[day][meal] = count
            daily_meal_stats[day]['total'] += count
    
    # تبدیل دیکشنری به لیست برای استفاده در تمپلیت
    daily_stats_detail = []
    for day, stats in daily_meal_stats.items():
        daily_stats_detail.append(stats)
    
    # مرتب‌سازی بر اساس ترتیب روزهای هفته
    day_name_to_key = {value: key for key, value in days.items()}
    daily_stats_detail.sort(key=lambda x: day_order.get(day_name_to_key.get(x['day_name'], ''), 7))
    
    # آمار کلی روزهای هفته برای نمودار اصلی
    day_stats = db.session.query(
        Reservation.day, 
        db.func.count(Reservation.id).label('count')
    ).group_by(Reservation.day).all()
    
    daily_stats = []
    for day, count in day_stats:
        percentage = (count / total_reservations * 100) if total_reservations > 0 else 0
        daily_stats.append({
            'day': day,
            'day_name': days.get(day, day),  # نام فارسی روز
            'count': count,
            'percentage': percentage
        })
    
    # مرتب‌سازی بر اساس ترتیب روزهای هفته
    daily_stats.sort(key=lambda x: day_order.get(x['day'], 7))
    
    # آمار وعده‌های غذایی
    meal_stats_data = db.session.query(
        Reservation.meal, 
        db.func.count(Reservation.id).label('count')
    ).group_by(Reservation.meal).all()
    
    meal_stats = []
    for meal, count in meal_stats_data:
        percentage = (count / total_reservations * 100) if total_reservations > 0 else 0
        meal_stats.append({
            'meal': meal,
            'count': count,
            'percentage': percentage
        })
    
    return render_template('admin_reports.html', 
                           popular_foods=popular_foods,
                           daily_stats=daily_stats,
                           daily_stats_detail=daily_stats_detail,
                           meal_stats=meal_stats)

if __name__ == '__main__':
    # شروع برنامه فلسک
    app.run(host='0.0.0.0', port=5000, debug=True)
