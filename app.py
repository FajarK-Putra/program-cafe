import time
from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from pymongo import MongoClient
from flask_socketio import SocketIO, emit
import os
from werkzeug.utils import secure_filename
from bson.objectid import ObjectId
from datetime import datetime
import logging

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'static/images/'
app.secret_key = 'super_secret_key'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
socketio = SocketIO(app)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

client = MongoClient("mongodb+srv://fjrkurnia1112:dU8AIK8XmZB5mQpp@cluster0.hzdsmnv.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0")
user_collection = client.user.datapelanggan
menu = client.menu.minuman
pesanan_collection = client.menu.pesanan

# Tambahkan enumerate ke Jinja2 environment
app.jinja_env.globals.update(enumerate=enumerate)

@app.route('/')
def login_page():
    current_queue_number = pesanan_collection.count_documents({})  # Mendapatkan jumlah total pesanan sebagai nomor antrian saat ini
    return render_template('login.html', current_queue_number=current_queue_number)

@app.route('/login', methods=['POST'])
def login():
    username_or_email_or_phone = request.form['username_or_email_or_phone']
    password = request.form['password']

    user = user_collection.find_one({
        "$or": [{"username": username_or_email_or_phone}, {"email": username_or_email_or_phone}, {"phone": username_or_email_or_phone}],
        "password": password
    })

    if user:
        session['username'] = user['username']
        session['user_id'] = str(user['_id'])
        if user["username"] == 'admin':
            return redirect(url_for('admin'))
        else:
            return redirect(url_for('member'))
    else:
        return render_template('login.html', error="Username, email, nomor HP, atau password salah")

@app.route('/signup', methods=['POST'])
def signup():
    username = request.form['username']
    email = request.form['email']
    password = request.form['password']
    phone = request.form['phone']

    existing_user = user_collection.find_one({"$or": [{"username": username}, {"email": email}]})

    if existing_user:
        return render_template('signup.html', error="Username atau email sudah digunakan")

    user_collection.insert_one({
        "username": username,
        "email": email,
        "password": password,
        "phone": phone,
        "join_date": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    })
    return render_template('signup.html', success="Sign up berhasil. Silahkan login.")

@app.route('/signup_page')
def signup_page():
    return render_template('signup.html')

@app.route('/info_akun')
def info_akun():
    if 'username' in session:
        user_id = session['user_id']
        user = user_collection.find_one({'_id': ObjectId(user_id)})
        if user:
            user['join_date'] = user.get('join_date', datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
            return render_template('info_akun.html', user=user)
        else:
            return redirect(url_for('login_page'))
    else:
        return redirect(url_for('login_page'))

@app.route('/admin')
def admin():
    return render_template('admin.html')

@app.route('/load_data_admin')
def load_data_admin():
    menu_items = list(menu.find())
    return render_template('/table/load_table_admin.html', menu_items=menu_items)

@app.route('/tambah_menu_form')
def tambah_menu_form():
    return render_template('tambah_menu.html')

@app.route('/load_data_index')
def load_data_index():
    menu_items = list(menu.find())
    return render_template('/table/load_table_index.html', menu_items=menu_items)

@app.route('/tambah_menu', methods=['POST'])
def tambah_menu():
    nama = request.form['nama']
    harga = request.form['harga']
    stok = request.form['stok']
    gambar = request.files['gambar']

    if gambar and allowed_file(gambar.filename):
        filename = secure_filename(gambar.filename)
        gambar_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        gambar.save(gambar_path)

        menu_item = {
            'nama': nama,
            'harga': harga,
            'stok': stok,
            'gambar': str(filename)
        }

        menu.insert_one(menu_item)
        socketio.emit('update_menu')  # Emit an update event to all clients
        return redirect(url_for('admin', success="ok"))
    else:
        return redirect(url_for('admin', success="not"))

@app.route('/edit_menu', methods=['POST'])
def edit_menu():
    item_id = request.form['id']
    menu_item = menu.find_one({'_id': ObjectId(item_id)})
    return render_template('edit_menu.html', menu_item=menu_item)

@app.route('/update_menu', methods=['POST'])
def update_menu():
    item_id = request.form['id']
    nama = request.form['nama']
    harga = int(request.form['harga'])
    stok = int(request.form['stok'])
    gambar = request.files['gambar']

    if gambar and allowed_file(gambar.filename):
        filename = secure_filename(gambar.filename)
        gambar_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        gambar.save(gambar_path)
        menu.update_one(
            {'_id': ObjectId(item_id)},
            {'$set': {
                'nama': nama,
                'harga': harga,
                'stok': stok,
                'gambar': str(filename)
            }}
        )
    else:
        menu.update_one(
            {'_id': ObjectId(item_id)},
            {'$set': {
                'nama': nama,
                'harga': harga,
                'stok': stok
            }}
        )
    socketio.emit('update_menu')  # Emit an update event to all clients
    return redirect(url_for('admin'))

@app.route('/delete_menu', methods=['POST'])
def delete_menu():
    item_id = request.form['id']
    menu.delete_one({'_id': ObjectId(item_id)})
    socketio.emit('update_menu')  # Emit an update event to all clients
    return redirect(url_for('admin'))

@app.route('/member')
def member():
    menu_items = list(menu.find())
    is_logged_in = 'username' in session
    if is_logged_in:
        check_status = list(pesanan_collection.find({"status": "menunggu", "username":session["username"]}))
        if len(check_status) > 0:
            return redirect(f"/pesanan_anda/{check_status[0]["_id"]}")
    return render_template('index.html', menu_items=menu_items, is_logged_in=is_logged_in)

@app.route('/edit_profile', methods=['POST'])
def edit_profile():
    if 'username' in session:
        user_id = session['user_id']
        new_email = request.form['email']
        new_phone = request.form['phone']
        new_password = request.form['password']
        user_collection.update_one(
            {'_id': ObjectId(user_id)},
            {'$set': {
                'email': new_email,
                'phone': new_phone,
                'password': new_password
            }}
        )
        return jsonify({'status': 'success'})
    else:
        return jsonify({'status': 'unauthorized'})

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login_page'))

@app.route('/pesan', methods=['POST'])
def pesan():
    data = request.get_json()
    username = session['username']
    items = data['items']
    total = data['total']
    payment_method = data['payment_method']
    tanggal = datetime.now()
    print(items)

    for data in items:
        stock_minuman = menu.find_one({"nama":data["name"]})
        if stock_minuman is not None and stock_minuman["stok"] < 0:
            return jsonify({"status": "fail", "pesanan_id": 0})

    # Insert order to the database
    pesanan_id = pesanan_collection.insert_one({
        "username": username,
        "items": items,
        "total": total,
        "payment_method": payment_method,  # Menyimpan metode pembayaran
        "tanggal": tanggal,
        "status_bayar": False,
        "status": "menunggu",
        "nomor_antrian":0
    }).inserted_id

    return jsonify({"status": "success", "pesanan_id": str(pesanan_id)})

@app.route('/get_pesanan/<pesanan_id>')
def get_pesanan(pesanan_id):
    pesanan = pesanan_collection.find_one({"_id": ObjectId(pesanan_id)})
    if pesanan:
        pesanan['_id'] = str(pesanan['_id'])
        pesanan['tanggal'] = pesanan['tanggal'].strftime('%Y-%m-%d %H:%M:%S')
        return jsonify({"status": "success", "pesanan": pesanan})
    return jsonify({"status": "error", "message": "Pesanan tidak ditemukan"})

@app.route('/riwayatpesanan')
def riwayatpesanan():
    pesanan_siap = list(pesanan_collection.find({"status": "siap", "username":session["username"]}))
    for pesanan in pesanan_siap:
        pesanan['_id'] = str(pesanan['_id'])
        pesanan['tanggal'] = pesanan['tanggal'].strftime('%Y-%m-%d %H:%M:%S')
    return render_template('riwayatpesanan.html', pesanan_siap=pesanan_siap)

@app.route('/pesanan_anda/<pesanan_id>')
def pesanan_anda(pesanan_id):
    if 'username' in session:
        pesanan = pesanan_collection.find_one({"_id": ObjectId(pesanan_id)})
        if pesanan:
            nomor_antrian = pesanan_collection.count_documents({"tanggal": {"$lt": pesanan["tanggal"]}}) + 1
            pesanan_collection.update_one({'_id': ObjectId(pesanan_id)}, {'$set': {'nomor_antrian': nomor_antrian}})
            return render_template('pesanan_anda.html', pesanan=pesanan, nomor_antrian=nomor_antrian)
        else:
            return render_template('pesanan_anda.html', pesanan="", nomor_antrian="", error="Tidak ada pesanan yang ditemukan.")
    else:
        return redirect(url_for('login_page'))

@app.route('/admin/antrian')
def antrian():
    return render_template('antrian.html')

@app.route('/load_data_antrian')
def load_data_antrian():
    antrian_items = list(pesanan_collection.find().sort("tanggal", 1))
    for pesanan in antrian_items:
        if isinstance(pesanan['tanggal'], str):
            pesanan['tanggal'] = datetime.strptime(pesanan['tanggal'], '%Y-%m-%d %H:%M:%S')
        pesanan['status_bayar'] = pesanan.get('status_bayar', False)
        pesanan['metode_pembayaran'] = pesanan.get('payment_method', 'Tidak Diketahui')
        
        # Tambahkan log untuk memeriksa data pesanan
        logging.debug(f"Pesanan: {pesanan}")
    return render_template('/table/load_table_antrian.html',  antrian_items=antrian_items)

@app.route('/mark_as_ready', methods=['POST'])
def mark_as_ready():
    pesanan_id = request.form.get('id')
    data_user = pesanan_collection.find_one({'_id': ObjectId(pesanan_id)})
    if data_user is not None:
        if data_user['status_bayar']:
            pesanan_collection.update_one({'_id': ObjectId(pesanan_id)}, {'$set': {'status_siap': True}})
            pesanan_collection.update_one({'_id': ObjectId(pesanan_id)}, {'$set': {'status': 'siap'}})
            return jsonify({'status': 'success'})
        else:
            return jsonify({'status': 'need payment'})
    else:
        return jsonify({'status': 'fail'})

@app.route('/admin/pesanan')
def pesanan():
    if 'username' in session and session['username'] == 'admin':
        pesanan_items = list(pesanan_collection.find())
        list_items = {}
        for pesanan in pesanan_items:
            if isinstance(pesanan.get('tanggal'), str):
                pesanan['tanggal'] = datetime.strptime(pesanan['tanggal'], '%Y-%m-%d %H:%M:%S').strftime('%Y-%m-%d %H:%M:%S')
            pesanan['status_bayar'] = pesanan.get('status_bayar', False)
            pesanan['metode_pembayaran'] = pesanan.get('payment_method', 'Tidak Diketahui')  # Pastikan pengambilan metode pembayaran
            list_items[str(pesanan['_id'])] = pesanan['items']
        return render_template('pesanan.html', pesanan_items=pesanan_items, list_items=list_items)
    else:
        return redirect(url_for('login_page'))

@app.route('/check_order_status/<pesanan_id>', methods=['GET'])
def check_order_status(pesanan_id):
    pesanan = pesanan_collection.find_one({'_id': ObjectId(pesanan_id)})
    if pesanan:
        return jsonify({'status': 'success', 'status_siap': pesanan.get('status_siap', False)})
    return jsonify({'status': 'error', 'message': 'Pesanan tidak ditemukan'})

@app.route('/fetch_lock_payment', methods=['POST'])
def fetch_lock_payment():
    if 'username' in session:
        check_status = list(pesanan_collection.find({"status": "menunggu", "username":session["username"]}))
        if len(check_status) > 0:
            return jsonify({'status': 'lock', 'id':str(check_status[0]["_id"])})         
        return jsonify({'status': 'unlock', 'id':0})
    return jsonify({'status': 'not authorize', 'id':0})

@app.route('/confirm_payment', methods=['POST'])
def confirm_payment():
    pesanan_id = request.form.get('id')
    data_user = pesanan_collection.find_one({'_id': ObjectId(pesanan_id)})
    if data_user is not None:
        for data in data_user["items"]:
            total_stock = menu.find_one({"nama":data["name"]})['stok']
            menu.update_one({'nama': data["name"]}, {'$set': {'stok': total_stock - data['quantity'] }})
            
        pesanan_collection.update_one({'_id': ObjectId(pesanan_id)}, {'$set': {'status_bayar': True}})
        return jsonify({'status': 'success'})
    return jsonify({'status': 'fail'})

@app.route('/delete_pesanan', methods=['POST'])
def delete_pesanan():
    if 'username' in session and session['username'] == 'admin':
        pesanan_ids = request.form.getlist('pesanan_ids')
        for pesanan_id in pesanan_ids:
            pesanan_collection.delete_one({'_id': ObjectId(pesanan_id)})
        return redirect(url_for('pesanan'))
    else:
        return redirect(url_for('login_page'))

@app.route('/admin/members')
def admin_members():
    if 'username' in session and session['username'] == 'admin':
        members = list(user_collection.find())
        return render_template('members.html', members=members)
    else:
        return redirect(url_for('login_page'))

if __name__ == '__main__':
    socketio.run(app, debug=True)
