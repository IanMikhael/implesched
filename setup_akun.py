from app import app, db, User
from werkzeug.security import generate_password_hash

with app.app_context():
    db.create_all()
    akun_baru = [
        {'username': 'superadmin', 'password': 'impleschedule@123', 'role': 'superadmin'},
        {'username': 'admin_wp', 'password': 'SBU@123', 'role': 'admin'},
        {'username': 'admin_im', 'password': 'SBU@123', 'role': 'admin'}
    ]
    for akun in akun_baru:
        if not User.query.filter_by(username=akun['username'].lower()).first():
            pw_hash = generate_password_hash(akun['password'], method='pbkdf2:sha256')
            user = User(username=akun['username'].lower(), password=pw_hash, role=akun['role'])
            db.session.add(user)
            print(f"Akun {akun['username']} berhasil disiapkan.")
        else:
            print(f"Akun {akun['username']} sudah ada di database.")
    db.session.commit()
    print("Semua akun berhasil ditambahkan!")