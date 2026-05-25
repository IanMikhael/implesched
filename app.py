from flask import Flask, render_template, redirect, url_for, request, flash, make_response
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from weasyprint import HTML
import pandas as pd
from io import BytesIO

app = Flask(__name__)
app.config['SECRET_KEY'] = 'kunci_rahasia_imple_terakorp_2026'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# ================= MODEL DATABASE =================
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(20), nullable=False)

class Jadwal(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nama_klinik = db.Column(db.String(100), nullable=False)
    nama_pic = db.Column(db.String(100), nullable=False)
    no_hp = db.Column(db.String(20), nullable=False)
    alamat = db.Column(db.Text, nullable=False)
    tipe_training = db.Column(db.String(50), nullable=False)
    paket = db.Column(db.String(20), nullable=False, default='Basic') # Kolom paket ditambahkan
    tanggal_training = db.Column(db.DateTime, nullable=False)
    status_selesai = db.Column(db.Boolean, default=False)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# ================= ROUTING & LOGIC =================
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user = User.query.filter_by(username=request.form['username'].strip().lower()).first()
        if user and check_password_hash(user.password, request.form['password']):
            login_user(user)
            return redirect(url_for('dashboard'))
        flash('Username atau password salah!', 'danger')
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/')
@login_required
def dashboard():
    semua_jadwal = Jadwal.query.order_by(Jadwal.tanggal_training.asc()).all()
    hari_ini = datetime.now().date()
    notif = [j for j in semua_jadwal if j.tanggal_training.date() == hari_ini and not j.status_selesai]
    return render_template('dashboard.html', semua_jadwal=semua_jadwal, notif=notif)

@app.route('/jadwal/tambah', methods=['GET', 'POST'])
@login_required
def tambah_jadwal():
    if request.method == 'POST':
        tgl_jam = datetime.fromisoformat(request.form['tanggal_training'])
        baru = Jadwal(
            nama_klinik=request.form['nama_klinik'],
            nama_pic=request.form['nama_pic'],
            no_hp=request.form['no_hp'],
            alamat=request.form['alamat'],
            tipe_training=request.form['tipe_training'],
            paket=request.form.get('paket', 'Basic'), # Menangkap data paket
            tanggal_training=tgl_jam
        )
        db.session.add(baru)
        db.session.commit()
        flash('Jadwal berhasil ditambahkan!', 'success')
        return redirect(url_for('dashboard'))
    return render_template('form_jadwal.html')

@app.route('/jadwal/edit/<int:id>', methods=['POST'])
@login_required
def edit_jadwal(id):
    jadwal = Jadwal.query.get_or_404(id)
    jadwal.nama_klinik = request.form['nama_klinik']
    jadwal.nama_pic = request.form['nama_pic']
    jadwal.no_hp = request.form['no_hp']
    jadwal.alamat = request.form['alamat']
    jadwal.tipe_training = request.form['tipe_training']
    jadwal.paket = request.form.get('paket', jadwal.paket) # Mengupdate data paket
    jadwal.tanggal_training = datetime.fromisoformat(request.form['tanggal_training'])
    db.session.commit()
    flash(f'Jadwal klinik {jadwal.nama_klinik} berhasil diupdate!', 'success')
    return redirect(url_for('dashboard'))

@app.route('/jadwal/toggle/<int:id>')
@login_required
def toggle_status(id):
    jadwal = Jadwal.query.get_or_404(id)
    jadwal.status_selesai = not jadwal.status_selesai
    db.session.commit()
    return redirect(url_for('dashboard'))

@app.route('/jadwal/delete/<int:id>')
@login_required
def hapus_jadwal(id):
    jadwal = Jadwal.query.get_or_404(id)
    db.session.delete(jadwal)
    db.session.commit()
    flash('Jadwal berhasil dihapus!', 'warning')
    return redirect(url_for('dashboard'))

# ================= EXPORT DATA (STABIL) =================
@app.route('/export_data', methods=['GET'])
@login_required
def export_data():
    format_file = request.args.get('format')
    status_filter = request.args.get('status')
    dari_str = request.args.get('dari_tanggal')
    sampai_str = request.args.get('sampai_tanggal')

    query = Jadwal.query
    if status_filter == 'terjadwal': query = query.filter_by(status_selesai=False)
    elif status_filter == 'selesai': query = query.filter_by(status_selesai=True)

    if dari_str: query = query.filter(Jadwal.tanggal_training >= datetime.fromisoformat(dari_str))
    if sampai_str: query = query.filter(Jadwal.tanggal_training <= datetime.fromisoformat(sampai_str))

    jadwals = query.all()

    # Siapkan data untuk Pandas (Excel & CSV), tambahkan Paket
    data = [{"Klinik": j.nama_klinik, "Paket": j.paket, "PIC": j.nama_pic, "Waktu": j.tanggal_training.strftime('%Y-%m-%d %H:%M'), "Status": "Selesai" if j.status_selesai else "Terjadwal"} for j in jadwals]
    df = pd.DataFrame(data)

    if format_file == 'pdf':
        html_string = render_template('export_pdf.html', jadwals=jadwals, now=datetime.now())
        pdf = HTML(string=html_string).write_pdf()
        response = make_response(pdf)
        response.headers['Content-Type'] = 'application/pdf'
        response.headers['Content-Disposition'] = 'attachment; filename=laporan_training.pdf'
        return response
    elif format_file == 'excel':
        output = BytesIO()
        df.to_excel(output, index=False)
        output.seek(0)
        response = make_response(output.getvalue())
        response.headers['Content-Type'] = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        response.headers['Content-Disposition'] = 'attachment; filename=laporan_training.xlsx'
        return response
    elif format_file == 'csv':
        response = make_response(df.to_csv(index=False))
        response.headers['Content-Type'] = 'text/csv'
        response.headers['Content-Disposition'] = 'attachment; filename=laporan_training.csv'
        return response

    return "Format tidak valid"

# ================= MANAGEMENT USER =================
@app.route('/users', methods=['GET', 'POST'])
@login_required
def kelola_users():
    if current_user.role != 'superadmin':
        flash('Akses ditolak!', 'danger')
        return redirect(url_for('dashboard'))
    if request.method == 'POST':
        user_baru = User(
            username=request.form['username'].strip().lower(),
            password=generate_password_hash(request.form['password'], method='pbkdf2:sha256'),
            role=request.form['role']
        )
        db.session.add(user_baru)
        db.session.commit()
        flash('User ditambahkan!', 'success')
    return render_template('users.html', users=User.query.all())

@app.route('/users/edit/<int:id>', methods=['POST'])
@login_required
def edit_user(id):
    if current_user.role != 'superadmin':
        flash('Akses ditolak!', 'danger')
        return redirect(url_for('dashboard'))
    user = User.query.get_or_404(id)
    user.username = request.form['username'].strip().lower()
    user.role = request.form['role']
    password_baru = request.form['password']
    if password_baru:
        user.password = generate_password_hash(password_baru, method='pbkdf2:sha256')
    db.session.commit()
    flash(f'Akun {user.username} berhasil diupdate!', 'success')
    return redirect(url_for('kelola_users'))

@app.route('/users/delete/<int:id>')
@login_required
def hapus_user(id):
    if current_user.role == 'superadmin':
        user = User.query.get_or_404(id)
        if user.id != current_user.id:
            db.session.delete(user)
            db.session.commit()
            flash('Akun berhasil dihapus!', 'warning')
    return redirect(url_for('kelola_users'))

def init_db():
    with app.app_context():
        db.create_all()
        if not User.query.filter_by(username='superadmin').first():
            pw = generate_password_hash('admin123', method='pbkdf2:sha256')
            admin = User(username='superadmin', password=pw, role='superadmin')
            db.session.add(admin)
            db.session.commit()

if __name__ == '__main__':
    init_db()
    app.run(debug=True)