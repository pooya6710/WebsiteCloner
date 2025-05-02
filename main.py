import datetime
from flask import request, jsonify, render_template, redirect, url_for, flash, session
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash

from app import app, db, login_manager, logger

# Create all database tables
with app.app_context():
    # Import models to register them with SQLAlchemy
    from models import Student, Reservation, Menu, DatabaseBackup, User
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
    # افزودن متغیر now برای فوتر تا سال جاری را نمایش دهد
    now = datetime.datetime.now()
    return render_template('index.html', now=now)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()
        
        if user and check_password_hash(user.password_hash, password):
            login_user(user)
            flash('با موفقیت وارد شدید', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('نام کاربری یا رمز عبور اشتباه است', 'danger')
    
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
        new_user = User(username=feeding_code, email=f"{feeding_code}@example.com", password_hash=generate_password_hash(password))
        db.session.add(new_user)
        db.session.flush()  # برای دریافت ID کاربر
        
        # ایجاد دانشجو
        new_student = Student(user_id=str(new_user.id), feeding_code=feeding_code)
        db.session.add(new_student)
        db.session.commit()
        
        flash('ثبت نام شما با موفقیت انجام شد. اکنون می‌توانید وارد سیستم شوید', 'success')
        return redirect(url_for('login'))
    
    return render_template('register.html')

@app.route('/logout')
@login_required
def logout():
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
    days = {
        "saturday": "شنبه",
        "sunday": "یکشنبه",
        "monday": "دوشنبه",
        "tuesday": "سه‌شنبه",
        "wednesday": "چهارشنبه",
        "thursday": "پنج‌شنبه",
        "friday": "جمعه"
    }
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

@app.route('/admin/menu')
@login_required
def admin_menu():
    if not current_user.is_admin:
        flash('شما دسترسی به این بخش را ندارید', 'danger')
        return redirect(url_for('dashboard'))
    
    weekly_menu = Menu.query.all()
    days = {
        "saturday": "شنبه",
        "sunday": "یکشنبه",
        "monday": "دوشنبه",
        "tuesday": "سه‌شنبه",
        "wednesday": "چهارشنبه",
        "thursday": "پنج‌شنبه",
        "friday": "جمعه"
    }
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
    
    day = request.form.get('day')
    meal = request.form.get('meal')
    food_items = request.form.get('food_items').split('\n')
    food_items = [item.strip() for item in food_items if item.strip()]
    
    # دریافت منوی روز مورد نظر
    day_menu = Menu.query.filter_by(day=day).first()
    if not day_menu:
        flash(f'منوی روز {day} یافت نشد', 'danger')
        return redirect(url_for('admin_menu'))
    
    # به‌روزرسانی منو
    meal_data = day_menu.meal_data
    meal_data[meal] = food_items
    day_menu.meal_data = meal_data
    db.session.commit()
    
    flash(f'منوی {meal} روز {day} با موفقیت به‌روزرسانی شد', 'success')
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
        if not check_password_hash(user.password_hash, current_password):
            flash('رمز عبور فعلی نادرست است', 'danger')
            return redirect(url_for('settings'))
        
        # به‌روزرسانی رمز عبور
        user.password_hash = generate_password_hash(new_password)
        db.session.commit()
        
        flash('رمز عبور شما با موفقیت تغییر یافت', 'success')
        return redirect(url_for('dashboard'))
    
    return render_template('settings.html')

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
    days = {
        "saturday": "شنبه",
        "sunday": "یکشنبه",
        "monday": "دوشنبه",
        "tuesday": "سه‌شنبه",
        "wednesday": "چهارشنبه",
        "thursday": "پنج‌شنبه",
        "friday": "جمعه"
    }
    
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
    day_order = {"saturday": 0, "sunday": 1, "monday": 2, "tuesday": 3, "wednesday": 4, "thursday": 5, "friday": 6}
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
                           meal_stats=meal_stats)

if __name__ == '__main__':
    # شروع برنامه فلسک
    app.run(host='0.0.0.0', port=5000, debug=True)
