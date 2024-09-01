#N7y 

from flask import Flask,jsonify, render_template, request, redirect, url_for, session, send_from_directory
import sqlite3
import os
from werkzeug.utils import secure_filename
from datetime import datetime
import hashlib
from os import urandom



app = Flask(__name__)
app.secret_key = hashlib.md5(datetime.now().strftime("%Y%m%d%H%M%S").encode()).hexdigest() + hashlib.md5(urandom(64)).hexdigest() 

UPLOAD_FOLDER = 'static/uploads/'
valid_ = {'png', 'jpg', 'jpeg', 'gif', 'txt', 'pdf', 'zip'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def onlydem(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in valid_

def dbcon():
    conn = sqlite3.connect('datap.db')
    conn.row_factory = sqlite3.Row
    return conn




@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        conn = dbcon()
        user = conn.execute('SELECT * FROM users WHERE username = ? AND password = ?', (username, password)).fetchone()
        conn.close()

        if user:
            session['username'] = username
            return redirect(url_for('chat'))
        else:
            rmsg = "Invalid username or password"
            return render_template("login.html",rmsg=rmsg)
            

    return render_template('login.html')





@app.route('/chat', methods=['GET', 'POST'])
def chat():
    if 'username' not in session:
        return redirect(url_for('login'))

    conn = dbcon()

    if request.method == 'POST':
        message = request.form.get('message')
        file = request.files.get('file')
        filename = None

        if file and onlydem(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

        conn.execute('INSERT INTO messages (username, message, filename) VALUES (?, ?, ?)',
                     (session['username'], message, filename))
        conn.commit()

    messages = conn.execute('SELECT * FROM messages ORDER BY timestamp ASC').fetchall()
    conn.close()

    return render_template('chat.html', messages=messages)

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    if 'username' not in session:
        return redirect(url_for('login'))
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)


@app.route('/loadmsg')
def loadmsg():
    if 'username' not in session:
        return redirect(url_for('login'))
    conn = dbcon()
    messages = conn.execute('SELECT * FROM messages ORDER BY timestamp ASC').fetchall()
    conn.close()

    messages_list = []
    for message in messages:
        messages_list.append({
            'username': message['username'],
            'message': message['message'],
            'filename': message['filename'],
            'timestamp': message['timestamp'] 
        })

    return jsonify(messages_list)

# let there be admin
@app.route('/admin', methods=['GET', 'POST'])
def admin_login():
    conn = dbcon()
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        # Check if the user is the admin
        user = conn.execute('SELECT * FROM admin WHERE username = ? AND password = ? AND is_admin = 1', (username, password)).fetchone()
        print(user)
        if user:
            session['admin'] = True
            return redirect(url_for('admin_panel'))
        else:
            rmsg = "Invalid password"
            return render_template("admin_login.html",rmsg=rmsg)
            
    
    return render_template('admin_login.html')

@app.route('/admin_panel')
def admin_panel():
    conn = dbcon()
    if not session.get('admin'):
        return redirect(url_for('admin_login'))

    users = conn.execute('SELECT * FROM users').fetchall()  
    return render_template('admin_panel.html', users=users)

# let there be user
@app.route('/create_user', methods=['POST'])
def create_user():
    conn = dbcon()
    if not session.get('admin'):
        return redirect(url_for('admin_login'))

    username = request.form['username']
    password = request.form['password']


    conn.execute('INSERT INTO users (username, password) VALUES (?, ?)', (username, password))
    conn.commit()

    return redirect(url_for('admin_panel'))

## nuke user
@app.route('/delu/<int:uid>')
def delu(uid):
    conn = dbcon()
    if not session.get('admin'):
        return redirect(url_for('admin_login'))


    
    conn.execute('DELETE FROM users WHERE id = ?', (uid,))
    conn.commit()

    return redirect(url_for('admin_panel'))


# nuke da tracks
@app.route('/nukemesg')
def nukemesg():
    conn = dbcon()
    if not session.get('admin'):
        return redirect(url_for('admin_login'))

    conn.execute('DELETE FROM messages')
    conn.commit()

    return redirect(url_for('admin_panel'))

@app.route('/logout_admin')
def logout_admin():
    session.pop('admin', None)
    return redirect(url_for('admin_login'))








@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('login'))





if __name__ == '__main__':
    app.run(debug=True,host="0.0.0.0",port=7002)
