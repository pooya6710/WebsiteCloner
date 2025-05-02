from app import app, db
from models import User
from werkzeug.security import generate_password_hash

def create_admin_user():
    """ایجاد کاربر مدیر در صورت عدم وجود"""
    
    with app.app_context():
        # بررسی وجود کاربر مدیر
        admin_exists = User.query.filter_by(username='admin').first()
        
        if admin_exists:
            print('کاربر مدیر از قبل وجود دارد:')
            print(f'نام کاربری: admin')
            print(f'رمز عبور: admin123')
            print(f'is_admin: {admin_exists.is_admin}')
            
            # اطمینان از دسترسی مدیریت
            if not admin_exists.is_admin:
                admin_exists.is_admin = True
                db.session.commit()
                print('دسترسی مدیریت به کاربر admin اعطا شد')
                
        else:
            # ایجاد کاربر مدیر جدید
            new_admin = User(
                username='admin',
                email='admin@example.com',
                password_hash=generate_password_hash('admin123'),
                is_admin=True
            )
            db.session.add(new_admin)
            db.session.commit()
            print('کاربر مدیر با موفقیت ایجاد شد:')
            print(f'نام کاربری: admin')
            print(f'رمز عبور: admin123')

if __name__ == '__main__':
    create_admin_user()