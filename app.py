# Eventlet muss ganz oben importiert werden, bevor Flask und andere Module.
import eventlet
eventlet.monkey_patch()

import bcrypt
import time
from flask import Flask, render_template, request, redirect, session, jsonify
from flask_socketio import SocketIO
from config import USERS, HOSTS
from utils.host import Host
import secrets

app = Flask(__name__)
app.secret_key = secrets.token_hex(32)

# SocketIO für WebSockets
socketio = SocketIO(app, async_mode='eventlet')

# Erstelle Host-Objekte
host_objects = [Host(**h) for h in HOSTS]
host_status = [None] * len(host_objects)  # Status der Hosts initialisieren

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user = request.form['username']
        pwd = request.form['password']

        # Prüfen, ob der Benutzer existiert und das Passwort übereinstimmt
        if user in USERS:
            # Falls das Passwort gehasht ist
            stored_password = USERS[user]
            if stored_password.startswith('$2b$'):  # bcrypt hash check
                if bcrypt.checkpw(pwd.encode('utf-8'), stored_password.encode('utf-8')):
                    session['user'] = user
                    return redirect('/')
            else:
                # Wenn es kein Hash ist, das Passwort direkt vergleichen (für unverschlüsselte Passwörter)
                if stored_password == pwd:
                    session['user'] = user
                    return redirect('/')
        return 'Login failed'
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/login')

@app.route('/')
def index():
    if 'user' not in session:
        return redirect('/login')

    host_data = []
    for host in host_objects:
        host_info = {
            "name": host.name,
            "ip": host.ip,
            "mac": host.mac,
            "ssh_user": host.ssh_user,
            "ssh_password": host.ssh_password,
            "has_ssh": bool(host.ssh_user and (host.ssh_key_path or host.ssh_password)),  # Prüfen, ob SSH-Daten vorhanden
        }
        host_data.append(host_info)

    return render_template('index.html', hosts=host_data)

@app.route('/status/<int:idx>')
def status(idx):
    host = host_objects[idx]
    return jsonify({
        'online': host.is_online(),
        'info': host.get_info() if host.is_online() else ''
    })

@app.route('/action/<int:idx>', methods=['POST'])
def action(idx):
    host = host_objects[idx]
    if host.is_online():
        host.shutdown()
        return jsonify({'action': 'shutdown'})
    else:
        host.wake()
        return jsonify({'action': 'wake'})

# Überprüft die Hosts alle 5 Sekunden
def monitor_hosts():
    while True:
        for idx, host in enumerate(host_objects):
            try:
                current = host.is_online()
                if host_status[idx] != current:
                    host_status[idx] = current
                    socketio.emit('status_update', {
                        'idx': idx,
                        'online': current,
                        'info': host.get_info() if current else ''
                    })
            except Exception as e:
                print(f"Error checking host {host.name}: {e}")
        time.sleep(5)

# Startet den Monitor-Thread
socketio.start_background_task(target=monitor_hosts)

# Startet die Flask-Anwendung
if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000)
