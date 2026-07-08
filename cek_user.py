print("Program mulai")

from app import app, User
from werkzeug.security import check_password_hash

print("Import berhasil")

with app.app_context():
    print("Masuk app context")

    user = User.query.filter_by(username="superadmin").first()

    print("User:", user)

    if user:
        print("Username:", user.username)
        print("Password cocok:", check_password_hash(user.password, "impleschedule@123"))
    else:
        print("User tidak ditemukan")