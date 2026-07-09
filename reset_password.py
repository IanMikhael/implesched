from app import app, db, User
from werkzeug.security import generate_password_hash

with app.app_context():
    user = User.query.filter_by(username="superadmin").first()

    if user:
        user.password = generate_password_hash(
            "impleschedule@123",
            method="pbkdf2:sha256"
        )
        db.session.commit()
        print("Password superadmin berhasil direset.")
    else:
        print("User superadmin tidak ditemukan.")