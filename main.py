import datetime
import os
import time
import jdatetime
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
    
# تابع تبدیل تاریخ میلادی به شمسی
def gregorian_to_jalali(date_obj):
    """تبدیل تاریخ میلادی به شمسی"""
    if date_obj is None:
        return None
    return jdatetime.date.fromgregorian(date=date_obj.date())

# تابع تبدیل تاریخ و زمان میلادی به شمسی
def gregorian_to_jalali_datetime(datetime_obj):
    """تبدیل تاریخ و زمان میلادی به شمسی با تنظیم ساعت به وقت ایران"""
    if datetime_obj is None:
        return None
    # اضافه کردن 3.5 ساعت (210 دقیقه) به زمان UTC برای تبدیل به وقت ایران
    iran_time = datetime_obj + datetime.timedelta(minutes=210)
    return jdatetime.datetime.fromgregorian(datetime=iran_time)

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
    # به‌روزرسانی آمار مالی و بدهی‌ها
    update_financial_statistics()
    
    # دریافت اطلاعات دانشجو
    student = Student.query.filter_by(user_id=str(current_user.id)).first()
    if not student:
        flash('اطلاعات دانشجویی شما یافت نشد', 'danger')
        return redirect(url_for('index'))
    
    # دریافت رزروهای دانشجو
    reservations = Reservation.query.filter_by(student_id=student.id).all()
    
    # تبدیل تاریخ‌ها به شمسی
    jalali_dates = {}
    
    for reservation in reservations:
        jalali_dates[reservation.id] = gregorian_to_jalali_datetime(reservation.timestamp).strftime('%Y/%m/%d %H:%M:%S')
    
    # تاریخ فعلی به شمسی
    now_jalali = gregorian_to_jalali_datetime(datetime.datetime.now()).strftime('%Y/%m/%d')
    
    return render_template('dashboard.html', 
                           student=student, 
                           reservations=reservations, 
                           jalali_dates=jalali_dates,
                           now_jalali=now_jalali)

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
    food_price = request.form.get('food_price', 0)
    
    try:
        food_price = float(food_price)
    except (ValueError, TypeError):
        # تنظیم قیمت‌های ثابت بر اساس نوع وعده
        if meal == 'breakfast':
            food_price = 2000.0  # صبحانه
        elif meal == 'lunch':
            food_price = 3000.0  # ناهار
        elif meal == 'dinner':
            food_price = 5000.0  # شام
        else:
            food_price = 0.0
    
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
        food_price=food_price,
        delivered=0
    )
    db.session.add(new_reservation)
    db.session.commit()
    
    # به‌روزرسانی بدهی دانشجو و آمار مالی کل سیستم
    update_financial_statistics()
    
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
            food_item = meal_data[meal][0]
            food_name = food_item.get('name', food_item) if isinstance(food_item, dict) else food_item
            
            # تنظیم قیمت‌های ثابت بر اساس نوع وعده
            if meal == 'breakfast':
                food_price = 2000.0  # صبحانه
            elif meal == 'lunch':
                food_price = 3000.0  # ناهار
            elif meal == 'dinner':
                food_price = 5000.0  # شام
            else:
                food_price = 0.0
            
            # ایجاد رزرو جدید
            new_reservation = Reservation(
                student_id=student.id,
                day=day,
                meal=meal,
                food_name=food_name,
                food_price=food_price,
                delivered=0
            )
            db.session.add(new_reservation)
            success_count += 1
    
    if success_count > 0:
        db.session.commit()
        
        # به‌روزرسانی آمار مالی و بدهی‌ها
        update_financial_statistics()
        
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
    
    # بررسی دسترسی و وضعیت غذا
    if not student or reservation.student_id != student.id:
        flash('شما مجوز حذف این رزرو را ندارید', 'danger')
        return redirect(url_for('dashboard'))
    
    # بررسی وضعیت تحویل غذا
    if reservation.delivered == 1:
        flash('امکان لغو رزرو غذای تحویل شده وجود ندارد', 'danger')
        return redirect(url_for('dashboard'))
    
    try:
        # حذف رزرو
        db.session.delete(reservation)
        db.session.commit()
        
        # به‌روزرسانی آمار مالی و بدهی‌ها از طریق تابع مرکزی
        print("✓ فراخوانی تابع به‌روزرسانی آمار مالی پس از لغو رزرو انفرادی")
        update_financial_statistics()
        
        flash('رزرو با موفقیت لغو شد', 'success')
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error in cancel_reservation: {str(e)}")
        flash('خطا در لغو رزرو، لطفا دوباره تلاش کنید', 'danger')
    
    return redirect(url_for('dashboard'))

@app.route('/admin')
@login_required
def admin():
    if not current_user.is_admin:
        flash('شما دسترسی به پنل مدیریت را ندارید', 'danger')
        return redirect(url_for('dashboard'))
    
    # به‌روزرسانی بدهی همه دانشجویان و آمار مالی قبل از نمایش داشبورد مدیریت
    update_financial_statistics()
    
    # دریافت آمار برای پنل مدیریت
    student_count = Student.query.count()
    reservation_count = Reservation.query.count()
    delivered_count = Reservation.query.filter_by(delivered=1).count()
    pending_count = Reservation.query.filter_by(delivered=0).count()
    
    # محاسبه کل هزینه غذاهای تحویل شده
    total_delivered_price = db.session.query(db.func.sum(Reservation.food_price)).filter_by(delivered=1).scalar() or 0
    
    # محاسبه کل هزینه غذاهای منتظر تحویل
    total_pending_price = db.session.query(db.func.sum(Reservation.food_price)).filter_by(delivered=0).scalar() or 0
    
    # آمار وعده‌های غذایی
    breakfast_count = Reservation.query.filter_by(meal='breakfast').count()
    lunch_count = Reservation.query.filter_by(meal='lunch').count()
    dinner_count = Reservation.query.filter_by(meal='dinner').count()
    total_count = breakfast_count + lunch_count + dinner_count
    
    # ساخت آمار
    stats = {
        'breakfast': breakfast_count,
        'lunch': lunch_count,
        'dinner': dinner_count,
        'total': total_count
    }
    
    return render_template('admin.html', 
                           student_count=student_count,
                           reservation_count=reservation_count,
                           delivered_count=delivered_count,
                           pending_count=pending_count,
                           total_delivered_price=total_delivered_price,
                           total_pending_price=total_pending_price,
                           stats=stats)

@app.route('/admin/students')
@login_required
def admin_students():
    if not current_user.is_admin:
        flash('شما دسترسی به این بخش را ندارید', 'danger')
        return redirect(url_for('dashboard'))
    
    # به‌روزرسانی بدهی همه دانشجویان قبل از نمایش لیست با استفاده از تابع مرکزی
    update_financial_statistics()
    
    # بازخوانی لیست دانشجویان پس از به‌روزرسانی
    students = Student.query.all()
    return render_template('admin_students.html', students=students)

@app.route('/admin/reservations')
@login_required
def admin_reservations():
    if not current_user.is_admin:
        flash('شما دسترسی به این بخش را ندارید', 'danger')
        return redirect(url_for('dashboard'))
    
    # به‌روزرسانی بدهی همه دانشجویان و آمار مالی قبل از نمایش
    update_financial_statistics()  # به‌روزرسانی آمار مالی دانشجویان
    update_reservation_prices()    # به‌روزرسانی قیمت‌های غذاها
    
    # دریافت پارامترهای فیلتر
    feeding_code = request.args.get('feeding_code')
    day_filter = request.args.get('day')
    meal_filter = request.args.get('meal')
    
    # پایه کوئری رزروها
    query = db.session.query(Reservation).join(Student)
    
    # اعمال فیلترها
    if feeding_code:
        query = query.filter(Student.feeding_code == feeding_code)
    
    if day_filter:
        query = query.filter(Reservation.day == day_filter)
        
    if meal_filter:
        query = query.filter(Reservation.meal == meal_filter)
    
    # مرتب‌سازی نتایج رزروها
    reservations = query.order_by(Reservation.day, Reservation.meal).all()
    
    # دریافت لیست تمام دانشجویان برای نمایش بدهی‌ها
    students = Student.query.all()
    
    # اطمینان از به‌روز بودن مقادیر بدهی دانشجویان
    for student in students:
        # چاپ لاگ برای اطمینان از به‌روزرسانی
        print(f"→ تأیید به‌روزرسانی: دانشجو {student.feeding_code} با بدهی {student.debt} تومان")
    
    # ترجمه نام روزها و وعده‌ها
    day_mapping = {
        "saturday": "شنبه",
        "sunday": "یکشنبه",
        "monday": "دوشنبه",
        "tuesday": "سه‌شنبه",
        "wednesday": "چهارشنبه",
        "thursday": "پنج‌شنبه",
        "friday": "جمعه"
    }
    
    meal_mapping = {
        "breakfast": "صبحانه",
        "lunch": "ناهار",
        "dinner": "شام"
    }
    
    # گروه‌بندی رزروها بر اساس روز
    days = ["saturday", "sunday", "monday", "tuesday", "wednesday", "thursday", "friday"]
    
    # ارسال تمام داده‌های مورد نیاز به قالب
    return render_template('admin_reservations.html', 
                          reservations=reservations,
                          students=students,  # اضافه کردن لیست دانشجویان برای نمایش بدهی
                          days=days,
                          day_mapping=day_mapping,
                          meal_mapping=meal_mapping,
                          feeding_code=feeding_code,
                          day_filter=day_filter,
                          meal_filter=meal_filter,
                          gregorian_to_jalali_datetime=gregorian_to_jalali_datetime)

@app.route('/admin/student/<int:student_id>/reservations')
@login_required
def admin_student_reservations(student_id):
    if not current_user.is_admin:
        flash('شما دسترسی به این بخش را ندارید', 'danger')
        return redirect(url_for('dashboard'))
    
    # به‌روزرسانی آمار مالی و بدهی‌ها
    update_financial_statistics()
    
    student = Student.query.get_or_404(student_id)
    reservations = Reservation.query.filter_by(student_id=student_id).all()
    
    return render_template('admin_student_reservations.html', 
                           student=student, 
                           reservations=reservations,
                           gregorian_to_jalali_datetime=gregorian_to_jalali_datetime)

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
    
    try:
        # پردازش لیست غذاها با اضافه کردن قیمت ثابت بر اساس نوع وعده
        food_items = []
        for item in food_items_text.split('\n'):
            if item.strip():
                # تعیین قیمت بر اساس نوع وعده غذایی
                if meal == 'breakfast':
                    price = 2000  # صبحانه 2 هزار تومان
                elif meal == 'lunch':
                    price = 3000  # ناهار 3 هزار تومان
                elif meal == 'dinner':
                    price = 5000  # شام 5 هزار تومان
                else:
                    price = 0
                
                # افزودن به صورت دیکشنری با قیمت
                food_items.append({"name": item.strip(), "price": price})
        
        # محدود کردن به یک غذا برای هر وعده
        if len(food_items) > 1:
            food_items = [food_items[0]]
            
        # لاگ اطلاعات ورودی برای دیباگ
        print(f"Updating menu - Day: {day}, Meal: {meal}")
        print(f"Food items with prices: {food_items}")
        
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
        
        # استفاده از مقدار جدید برای بروزرسانی
        import copy
        import json
        
        # ایجاد یک کپی عمیق از داده‌ها برای اطمینان از تغییر واقعی
        new_menu_data = copy.deepcopy(current_data)
        
        # تلاش مستقیم برای ذخیره تغییرات به صورت خام SQL به‌جای ORM
        try:
            import json
            # تبدیل دیکشنری به JSON string
            meal_data_json = json.dumps(new_menu_data)
            print(f"Converting to JSON string: {meal_data_json}")
            
            # به‌روزرسانی مستقیم از طریق SQL برای اطمینان از اعمال تغییرات
            from sqlalchemy import text
            sql = text("UPDATE menu SET meal_data = :meal_data WHERE id = :id")
            db.session.execute(sql, {"meal_data": meal_data_json, "id": day_menu.id})
            db.session.commit()
            print(f"Successfully committed changes directly using SQL")
        except Exception as e:
            print(f"Error in direct SQL update: {str(e)}")
            # روش جایگزین - استفاده از ORM استاندارد
            day_menu.meal_data = new_menu_data
            db.session.add(day_menu)
            db.session.commit()
            print(f"Fallback: Successfully committed changes using ORM")
        
        # تخلیه کش SQLAlchemy
        db.session.expire_all()
        
        # تایید نهایی تغییرات با دریافت مجدد از دیتابیس
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

# تابع به‌روزرسانی قیمت‌های غذا در رزروهای موجود
def update_reservation_prices():
    """
    به‌روزرسانی قیمت‌های غذا در تمام رزروهای موجود بر اساس نوع وعده
    """
    print("✓ فراخوانی تابع به‌روزرسانی قیمت‌های غذا")
    try:
        # دریافت تمام رزروها
        reservations = Reservation.query.all()
        updated_count = 0
        
        for res in reservations:
            old_price = res.food_price
            
            # تنظیم قیمت‌های ثابت بر اساس نوع وعده
            if res.meal == 'breakfast':
                res.food_price = 2000.0  # صبحانه
            elif res.meal == 'lunch':
                res.food_price = 3000.0  # ناهار
            elif res.meal == 'dinner':
                res.food_price = 5000.0  # شام
            
            if old_price != res.food_price:
                updated_count += 1
                print(f"   ✓ به‌روزرسانی رزرو {res.id}: {res.day}, {res.meal} - قیمت قدیم: {old_price} تومان، قیمت جدید: {res.food_price} تومان")
        
        # ذخیره تغییرات
        db.session.commit()
        print(f"✓ تعداد {updated_count} رزرو با موفقیت به‌روزرسانی شد")
        return True
    except Exception as e:
        db.session.rollback()
        print(f"✗ خطا در به‌روزرسانی قیمت‌های غذا: {e}")
        import traceback
        print(f"✗ جزئیات خطا: {traceback.format_exc()}")
        logger.error(f"خطا در به‌روزرسانی قیمت‌های غذا: {e}")
        return False

# تابع بروزرسانی کامل آمار مالی و بدهی
def update_financial_statistics():
    """
    بروزرسانی کامل آمار مالی و بدهی‌های تمام دانشجویان
    این تابع در نقاط کلیدی سیستم فراخوانی می‌شود:
    - ثبت رزرو جدید
    - لغو رزرو
    - تایید تحویل غذا
    - بازدید از پنل‌های مدیریت و گزارش‌ها
    """
    print("✓ فراخوانی تابع به‌روزرسانی آمار مالی و بدهی دانشجویان")
    
    # ابتدا قیمت‌های رزروها را به‌روز می‌کنیم
    update_reservation_prices()
    
    try:
        # محاسبه بدهی همه دانشجویان
        students = Student.query.all()
        print(f"✓ تعداد دانشجویان برای به‌روزرسانی: {len(students)}")
        
        # ریست کردن بدهی همه دانشجویان برای اطمینان از به‌روزرسانی صحیح
        for student in students:
            # ریست مقدار بدهی
            student.debt = 0
            # اعتبار حساب همچنان حفظ می‌شود
            # student.credit = 0
        db.session.flush()
        
        for student in students:
            # محاسبه بدهی کل برای هر دانشجو - فقط غذاهای تحویل شده
            student_debt = 0
            # غذاهای تحویل شده برای محاسبه بدهی
            delivered_reservations = Reservation.query.filter_by(student_id=student.id, delivered=1).all()
            
            for res in delivered_reservations:
                student_debt += res.food_price
            
            # محاسبه بدهی برای غذاهای تحویل نشده (به منظور نمایش در داشبورد)
            pending_debt = 0
            pending_reservations = Reservation.query.filter_by(student_id=student.id, delivered=0).all()
            
            print(f"✓ دانشجو: {student.feeding_code}, تعداد رزروهای تحویل نشده: {len(pending_reservations)}")
            
            for res in pending_reservations:
                pending_debt += res.food_price
                print(f"   - رزرو: {res.day}, {res.meal}, قیمت: {res.food_price} تومان")
            
            # ذخیره‌سازی بدهی در فیلد debt 
            student.debt = student_debt
            print(f"✓ بدهی نهایی دانشجو {student.feeding_code} برای غذاهای تحویل شده: {student.debt} تومان")
            print(f"✓ هزینه‌های آتی دانشجو {student.feeding_code} برای غذاهای رزرو شده: {pending_debt} تومان")
            
            # نمایش کل بدهی و هزینه‌های پیش‌رو در داشبورد به صورت جداگانه
        
        # ذخیره تغییرات و اطمینان از commit شدن آنها
        db.session.commit()
        print("✓ تمام بدهی‌ها با موفقیت به‌روزرسانی شدند")
        
        # تأیید به‌روزرسانی موفق
        updated_students = Student.query.all()
        for student in updated_students:
            if student.debt > 0:
                print(f"→ تأیید به‌روزرسانی: دانشجو {student.feeding_code} با بدهی {student.debt} تومان")
        
        return True
    except Exception as e:
        db.session.rollback()
        print(f"✗ خطا در به‌روزرسانی آمار مالی: {e}")
        import traceback
        print(f"✗ جزئیات خطا: {traceback.format_exc()}")
        logger.error(f"خطا در بروزرسانی آمار مالی: {e}")
        return False


@app.route('/admin/delivery/<int:reservation_id>', methods=['POST'])
@login_required
def admin_delivery(reservation_id):
    if not current_user.is_admin:
        flash('شما دسترسی به این بخش را ندارید', 'danger')
        return redirect(url_for('dashboard'))
    
    try:
        # استفاده از اجرای مستقیم SQL برای اطمینان از اجرای تغییرات
        try:
            from sqlalchemy import text
            sql = text("UPDATE reservations SET delivered = 1 WHERE id = :id")
            result = db.session.execute(sql, {"id": reservation_id})
            db.session.commit()
            print(f"Updated reservation directly with SQL: {result.rowcount} row(s) affected")
            
            # اگر هیچ رزروی به‌روز نشد، احتمالا ID نامعتبر است
            if result.rowcount == 0:
                flash('رزرو مورد نظر یافت نشد', 'danger')
                return redirect(request.referrer or url_for('admin_reservations'))
                
        except Exception as sql_error:
            print(f"SQL update error: {str(sql_error)}, falling back to ORM")
            # راه حل جایگزین در صورت خطا در SQL مستقیم
            reservation = Reservation.query.get_or_404(reservation_id)
            
            # بررسی وضعیت فعلی
            if reservation.delivered == 1:
                flash('این غذا قبلا تحویل داده شده است', 'warning')
                return redirect(request.referrer or url_for('admin_reservations'))
            
            # تنظیم وضعیت تحویل به "تحویل شده"
            reservation.delivered = 1
            db.session.commit()
        
        # بروزرسانی بدهی و آمار مالی کل سیستم
        if update_financial_statistics():
            flash('وضعیت تحویل غذا با موفقیت به‌روزرسانی شد', 'success')
        else:
            flash('وضعیت تحویل بروز شد، اما در بروزرسانی آمار مالی مشکلی پیش آمد', 'warning')
            
        # بازگشت به صفحه قبلی (اگر ممکن باشد)
        return redirect(request.referrer or url_for('admin_reservations'))
    
    except Exception as e:
        db.session.rollback()
        logger.error(f"خطا در تأیید تحویل غذا: {e}")
        flash('خطا در تأیید تحویل غذا، لطفا دوباره تلاش کنید', 'danger')
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
                food_item = day_menu.meal_data[meal][0]
                food_name = food_item.get('name', food_item) if isinstance(food_item, dict) else food_item
                
                # تنظیم قیمت‌های ثابت بر اساس نوع وعده
                if meal == 'breakfast':
                    food_price = 2000.0  # صبحانه
                elif meal == 'lunch':
                    food_price = 3000.0  # ناهار
                elif meal == 'dinner':
                    food_price = 5000.0  # شام
                else:
                    food_price = food_item.get('price', 0) if isinstance(food_item, dict) else 0
                
                # ایجاد رزرو جدید
                new_reservation = Reservation(
                    student_id=student.id,
                    day=day_menu.day,
                    meal=meal,
                    food_name=food_name,
                    food_price=food_price,
                    delivered=0
                )
                db.session.add(new_reservation)
                success_count += 1
    
    if success_count > 0:
        db.session.commit()
        
        # به‌روزرسانی آمار مالی و بدهی‌ها از طریق تابع مرکزی
        print("✓ فراخوانی تابع به‌روزرسانی آمار مالی پس از رزرو هفتگی")
        update_financial_statistics()
        
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
    try:
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
        
        # استفاده از try-except برای دیباگ
        return render_template('settings.html')
    except Exception as e:
        logger.error(f"Error in settings route: {str(e)}")
        flash('خطا در سیستم رخ داده است. لطفا دوباره تلاش کنید.', 'danger')
        return redirect(url_for('dashboard'))

# مسیرهای تعمیر و نگهداری به درخواست کاربر حذف شدند


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
    
    try:
        # دریافت رزروهای روز مورد نظر - فقط رزروهایی که تحویل نشده‌اند
        reservations = Reservation.query.filter_by(
            student_id=student.id, day=day, delivered=0
        ).all()
        
        if not reservations:
            flash(f'شما رزرو قابل لغوی برای روز {days.get(day, day)} ندارید', 'warning')
            return redirect(url_for('dashboard'))
        
        # حذف رزروها
        count = 0
        for reservation in reservations:
            db.session.delete(reservation)
            count += 1
        
        db.session.commit()
        
        # به‌روزرسانی آمار مالی و بدهی‌ها از طریق تابع مرکزی
        print("✓ فراخوانی تابع به‌روزرسانی آمار مالی پس از لغو رزرو روزانه")
        update_financial_statistics()
        
        flash(f'{count} رزرو برای روز {days.get(day, day)} با موفقیت لغو شد', 'success')
        return redirect(url_for('dashboard'))
    
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error in cancel_all_day: {str(e)}")
        flash('خطا در لغو رزروها، لطفا دوباره تلاش کنید', 'danger')
        return redirect(url_for('dashboard'))

@app.route('/cancel_all_week', methods=['POST'])
@login_required
def cancel_all_week():
    # دریافت اطلاعات دانشجو
    student = Student.query.filter_by(user_id=str(current_user.id)).first()
    if not student:
        flash('اطلاعات دانشجویی شما یافت نشد', 'danger')
        return redirect(url_for('dashboard'))
    
    try:
        # دریافت فقط رزروهایی که تحویل نشده‌اند
        reservations = Reservation.query.filter_by(
            student_id=student.id, delivered=0
        ).all()
        
        if not reservations:
            flash('شما هیچ رزروی قابل لغو ندارید', 'warning')
            return redirect(url_for('dashboard'))
        
        # حذف رزروها
        count = 0
        for reservation in reservations:
            db.session.delete(reservation)
            count += 1
        
        db.session.commit()
        
        # به‌روزرسانی بدهی دانشجو پس از حذف رزرو
        update_financial_statistics()
        
        flash(f'{count} رزرو برای کل هفته با موفقیت لغو شد', 'success')
        return redirect(url_for('dashboard'))
    
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error in cancel_all_week: {str(e)}")
        flash('خطا در لغو رزروها، لطفا دوباره تلاش کنید', 'danger')
        return redirect(url_for('dashboard'))

@app.route('/admin/reports')
@login_required
def admin_reports():
    if not current_user.is_admin:
        flash('شما دسترسی به این بخش را ندارید', 'danger')
        return redirect(url_for('dashboard'))
    
    # به‌روزرسانی بدهی همه دانشجویان و آمار مالی قبل از نمایش گزارش‌ها
    update_financial_statistics()
    
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
    
    # آمار مالی - محاسبه هزینه‌ها
    delivered_price = db.session.query(db.func.sum(Reservation.food_price)).filter_by(delivered=1).scalar() or 0
    pending_price = db.session.query(db.func.sum(Reservation.food_price)).filter_by(delivered=0).scalar() or 0
    total_price = delivered_price + pending_price
    
    # اطلاعات آماری مالی
    financial_stats = {
        'delivered_price': delivered_price,
        'pending_price': pending_price,
        'total_price': total_price,
        'delivered_percentage': (delivered_price / total_price * 100) if total_price > 0 else 0,
        'pending_percentage': (pending_price / total_price * 100) if total_price > 0 else 0,
    }
    
    # آمار مالی به تفکیک وعده‌های غذایی
    financial_meal_stats_data = db.session.query(
        Reservation.meal,
        db.func.sum(Reservation.food_price).label('price')
    ).group_by(Reservation.meal).all()
    
    financial_meal_stats = []
    for meal, price in financial_meal_stats_data:
        percentage = (price / total_price * 100) if total_price > 0 else 0
        financial_meal_stats.append({
            'meal': meal,
            'price': price,
            'percentage': percentage
        })
    
    # آمار مالی به تفکیک روز هفته
    financial_day_stats_data = db.session.query(
        Reservation.day,
        db.func.sum(Reservation.food_price).label('price')
    ).group_by(Reservation.day).all()
    
    financial_day_stats = []
    for day, price in financial_day_stats_data:
        percentage = (price / total_price * 100) if total_price > 0 else 0
        financial_day_stats.append({
            'day': day,
            'day_name': days.get(day, day),  # نام فارسی روز
            'price': price,
            'percentage': percentage
        })
    
    # مرتب‌سازی بر اساس ترتیب روزهای هفته
    financial_day_stats.sort(key=lambda x: day_order.get(x['day'], 7))
    
    return render_template('admin_reports.html', 
                           popular_foods=popular_foods,
                           daily_stats=daily_stats,
                           daily_stats_detail=daily_stats_detail,
                           meal_stats=meal_stats,
                           financial_stats=financial_stats,
                           financial_meal_stats=financial_meal_stats,
                           financial_day_stats=financial_day_stats)

if __name__ == '__main__':
    # به‌روزرسانی اولیه قیمت‌ها و آمار مالی
    with app.app_context():
        print("✓ به‌روزرسانی اولیه قیمت‌ها و آمار مالی قبل از شروع اپلیکیشن")
        update_financial_statistics()
    
    # شروع برنامه فلسک
    app.run(host='0.0.0.0', port=5000, debug=True)
