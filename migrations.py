import os
import sys
from app import app, db

def migrate_database():
    """اجرای مهاجرت دیتابیس برای اضافه کردن ستون‌های جدید"""
    with app.app_context():
        print("شروع مهاجرت پایگاه داده...")
        
        # بررسی و اضافه کردن ستون قیمت غذا به جدول رزروها
        try:
            db.session.execute(db.text("ALTER TABLE reservations ADD COLUMN IF NOT EXISTS food_price FLOAT DEFAULT 0.0"))
            db.session.commit()
            print("ستون food_price با موفقیت به جدول reservations اضافه شد.")
        except Exception as e:
            db.session.rollback()
            print(f"خطا در اضافه کردن ستون food_price: {str(e)}")
        
        # ایجاد جدول‌های جدید
        try:
            # اطمینان از به روز بودن ساختار پایگاه داده
            db.create_all()
            print("همه جدول‌های مورد نیاز ایجاد شدند.")
        except Exception as e:
            print(f"خطا در ایجاد جدول‌ها: {str(e)}")
        
        print("مهاجرت پایگاه داده با موفقیت انجام شد.")

if __name__ == "__main__":
    migrate_database()