import os
from app import app, db, User
from werkzeug.security import generate_password_hash

# 1. Pastikan folder instance ada agar SQLite tidak error
basedir = os.path.abspath(os.path.dirname(__file__))
instance_folder = os.path.join(basedir, 'instance')
if not os.path.exists(instance_folder):
    os.makedirs(instance_folder)

with app.app_context():
    # 2. Inisialisasi database
    db.create_all()
    
    akun_baru = [
        {'username': 'superadmin', 'password': 'impleschedule@123', 'role': 'superadmin'},
        {'username': 'admin_wp', 'password': 'SBU@123', 'role': 'admin'},
        {'username': 'admin_im', 'password': 'SBU@123', 'role': 'admin'}
    ]
    
    for akun in akun_baru:
        # Gunakan .lower() untuk memastikan konsistensi username
        username_lower = akun['username'].lower()
        if not User.query.filter_by(username=username_lower).first():
            # Method pbkdf2:sha256 adalah standar yang aman
            pw_hash = generate_password_hash(akun['password'], method='pbkdf2:sha256')
            user = User(username=username_lower, password=pw_hash, role=akun['role'])
            db.session.add(user)
            print(f"Akun {username_lower} berhasil disiapkan.")
        else:
            print(f"Akun {username_lower} sudah ada di database.")
            
    db.session.commit()
    print("Semua proses setup akun selesai!")