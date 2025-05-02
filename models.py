import json
import os
import datetime
from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, JSON, Text, Boolean
from sqlalchemy.orm import relationship
from flask_login import UserMixin
from app import db, logger

class User(UserMixin, db.Model):
    """مدل کاربر برای احراز هویت و مدیریت دسترسی‌ها"""
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True)
    username = Column(String(64), unique=True, nullable=False)
    email = Column(String(120), unique=True, nullable=False)
    password_hash = Column(String(256), nullable=False)
    is_admin = Column(Boolean, default=False)  # آیا کاربر مدیر سیستم است؟
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    
    def __repr__(self):
        return f"<User(username='{self.username}', email='{self.email}')>"

class Student(db.Model):
    """مدل دانشجو برای ذخیره‌سازی اطلاعات کاربران"""
    __tablename__ = 'students'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(String(50), unique=True, nullable=False)  # ارتباط با کاربر
    feeding_code = Column(String(20), unique=True, nullable=False)  # کد تغذیه دانشجویی
    
    # ارتباط با رزروها
    reservations = relationship("Reservation", back_populates="student", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Student(user_id='{self.user_id}', feeding_code='{self.feeding_code}')>"

class Reservation(db.Model):
    """مدل رزرو برای ذخیره‌سازی رزروهای غذا"""
    __tablename__ = 'reservations'
    
    id = Column(Integer, primary_key=True)
    student_id = Column(Integer, ForeignKey('students.id'), nullable=False)
    day = Column(String(20), nullable=False)  # روز هفته
    meal = Column(String(20), nullable=False)  # وعده غذایی
    food_name = Column(String(100), nullable=False)  # نام غذا
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)
    delivered = Column(Integer, default=0)  # وضعیت تحویل: 0=تحویل نشده، 1=تحویل شده
    
    # ارتباط با دانشجو
    student = relationship("Student", back_populates="reservations")
    
    def __repr__(self):
        return f"<Reservation(student_id={self.student_id}, day='{self.day}', meal='{self.meal}', food_name='{self.food_name}')>"

class Menu(db.Model):
    """مدل منو برای ذخیره‌سازی منوی غذایی هفتگی"""
    __tablename__ = 'menu'
    
    id = Column(Integer, primary_key=True)
    day = Column(String(20), unique=True, nullable=False)  # روز هفته
    meal_data = Column(JSON, nullable=False)  # دیکشنری وعده‌های غذایی
    
    def __repr__(self):
        return f"<Menu(day='{self.day}')>"

class DatabaseBackup(db.Model):
    """مدل پشتیبان‌گیری از دیتابیس"""
    __tablename__ = 'backups'
    
    id = Column(Integer, primary_key=True)
    filename = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)
    
    def __repr__(self):
        return f"<DatabaseBackup(filename='{self.filename}', timestamp='{self.timestamp}')>"

def init_db():
    """تابع راه‌اندازی اولیه دیتابیس"""
    return db.session

def load_default_menu(db_session):
    """بارگذاری منوی پیش‌فرض به دیتابیس"""
    # بررسی اینکه آیا منو قبلاً بارگذاری شده است
    if db_session.query(Menu).count() == 0:
        # منوی پیش‌فرض
        default_menu = {
            "saturday": {
                "breakfast": ["نان و پنیر و گردو", "املت", "نیمرو"],
                "lunch": ["چلو کباب کوبیده", "قیمه", "قورمه سبزی"],
                "dinner": ["ماکارونی", "عدس پلو", "کتلت"]
            },
            "sunday": {
                "breakfast": ["نان و پنیر و خرما", "تخم مرغ آبپز", "حلیم"],
                "lunch": ["زرشک پلو با مرغ", "خورشت بادمجان", "کوکو سبزی"],
                "dinner": ["چلو کباب جوجه", "خوراک لوبیا", "استانبولی پلو"]
            },
            "monday": {
                "breakfast": ["نان و کره و مربا", "نان و تخم مرغ", "شیر و غلات"],
                "lunch": ["چلو خورشت قیمه", "کوبیده", "فسنجان"],
                "dinner": ["خوراک مرغ", "کشک و بادمجان", "کوفته تبریزی"]
            },
            "tuesday": {
                "breakfast": ["نان و پنیر و سبزی", "املت", "عدسی"],
                "lunch": ["چلو کباب بختیاری", "چلو خورشت سبزی", "کوکو سیب زمینی"],
                "dinner": ["الویه", "میرزا قاسمی", "حلیم بادمجان"]
            },
            "wednesday": {
                "breakfast": ["نان و پنیر و گردو", "تخم مرغ نیمرو", "آش"],
                "lunch": ["چلو جوجه کباب", "چلو قورمه سبزی", "دلمه برگ مو"],
                "dinner": ["کتلت", "عدس پلو", "ماکارونی"]
            },
            "thursday": {
                "breakfast": ["نان و مربا و کره", "نیمرو", "آش رشته"],
                "lunch": ["چلو کباب کوبیده", "چلو خورشت قیمه", "کباب تابه ای"],
                "dinner": ["خوراک مرغ", "کوکو سبزی", "خوراک لوبیا"]
            },
            "friday": {
                "breakfast": ["نان و کره و مربا", "نان و پنیر", "آش"],
                "lunch": ["استانبولی پلو", "عدس پلو", "کباب تابه ای"],
                "dinner": ["چلو کباب", "املت", "سالاد الویه"]
            }
        }
        
        # افزودن منوی پیش‌فرض به دیتابیس
        for day, meals in default_menu.items():
            menu_item = Menu(day=day, meal_data=meals)
            db_session.add(menu_item)
        
        db_session.commit()
        logger.info("منوی پیش‌فرض با موفقیت بارگذاری شد.")
        
        # ایجاد یک کاربر مدیر پیش‌فرض
        from werkzeug.security import generate_password_hash
        admin_exists = db_session.query(User).filter_by(username='admin').first()
        if not admin_exists:
            admin_user = User(
                username='admin',
                email='admin@example.com',
                password_hash=generate_password_hash('admin123'),
                is_admin=True
            )
            db_session.add(admin_user)
            db_session.commit()
            logger.info("کاربر مدیر با موفقیت ایجاد شد.")

def migrate_from_json_to_db(json_file, db_session):
    """مهاجرت داده‌ها از فایل JSON به دیتابیس"""
    if os.path.exists(json_file):
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            for user_id, user_data in data.items():
                # بررسی وجود دانشجو در دیتابیس
                student = db_session.query(Student).filter_by(user_id=user_id).first()
                if not student:
                    # ایجاد دانشجوی جدید
                    student = Student(user_id=user_id, feeding_code=user_data.get('feeding_code', ''))
                    db_session.add(student)
                    db_session.flush()  # دریافت شناسه دانشجوی جدید
                
                # افزودن رزروها
                if 'reservations' in user_data:
                    for reservation_data in user_data['reservations']:
                        # بررسی وجود رزرو مشابه
                        existing_reservation = db_session.query(Reservation).filter_by(
                            student_id=student.id,
                            day=reservation_data['day'],
                            meal=reservation_data['meal']
                        ).first()
                        
                        if not existing_reservation:
                            reservation = Reservation(
                                student_id=student.id,
                                day=reservation_data['day'],
                                meal=reservation_data['meal'],
                                food_name=reservation_data['food_name'],
                                delivered=reservation_data.get('delivered', 0)
                            )
                            db_session.add(reservation)
            
            db_session.commit()
            logger.info(f"داده‌ها از فایل {json_file} با موفقیت به دیتابیس منتقل شدند.")
            
            # تغییر نام فایل JSON پس از مهاجرت موفق
            os.rename(json_file, f"{json_file}.migrated_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}")
            
        except Exception as e:
            db_session.rollback()
            logger.error(f"خطا در مهاجرت داده‌ها: {str(e)}")
