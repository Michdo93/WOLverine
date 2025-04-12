import eventlet
eventlet.monkey_patch()

import bcrypt
import hmac
import time
import secrets
from flask import Flask, render_template, request, redirect, session, jsonify, Response
from flask_socketio import SocketIO
from functools import wraps
from config import USERS, HOSTS
from utils.host import Host
import base64

app = Flask(__name__)
app.secret_key = secrets.token_hex(32)

socketio = SocketIO(app, async_mode='eventlet')

host_objects = [Host(**h) for h in HOSTS]
host_status = [None] * len(host_objects)


# -------------------
# Basic Auth Helpers
# -------------------
def verify_password(username, password):
    stored = USERS.get(username)
    if not stored:
        return False

    if stored.startswith('$2b$'):
        return bcrypt.checkpw(password.encode('utf-8'), stored.encode('utf-8'))
    else:
        return hmac.compare_digest(stored, password)


def require_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.authorization
        if not auth or not verify_password(auth.username, auth.password):
            return Response(
                "Authentication required.",
                401,
                {'WWW-Authenticate': 'Basic realm="Login Required"'}
            )
        return f(*args, **kwargs)
    return decorated


# -------------------
# Web Routes
# -------------------
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user = request.form['username']
        pwd = request.form['password']

        if verify_password(user, pwd):
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
            "has_ssh": bool(host.ssh_user and (host.ssh_key_path or host.ssh_password)),
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
    action_type = request.json.get("action")

    if action_type == "wake":
        if not host.is_online():
            host.wake()
            return jsonify({'action': 'wake'})
        return jsonify({'error': 'Host already online'}), 409

    if action_type == "shutdown":
        if host.is_online():
            host.shutdown()
            return jsonify({'action': 'shutdown'})
        return jsonify({'error': 'Host offline'}), 409

    if action_type == "reboot":
        if host.is_online():
            host.reboot()
            return jsonify({'action': 'reboot'})
        return jsonify({'error': 'Host offline'}), 409

    return jsonify({'error': 'Invalid action'}), 400


# -------------------
# REST API Endpoints
# -------------------

@app.route('/rest/computer', methods=['GET'])
@require_auth
def rest_get_all_computers():
    return jsonify([
        {
            "name": host.name,
            "ip": host.ip,
            "mac": host.mac,
            "ssh_user": host.ssh_user,
            "has_ssh": bool(host.ssh_user and (host.ssh_key_path or host.ssh_password))
        }
        for host in host_objects
    ])


def get_host_by_name(name):
    for host in host_objects:
        if host.name == name:
            return host
    return None


@app.route('/rest/computer/<name>', methods=['GET'])
@require_auth
def rest_get_computer(name):
    host = get_host_by_name(name)
    if not host:
        return jsonify({'error': 'Host not found'}), 404

    return jsonify({
        "name": host.name,
        "ip": host.ip,
        "mac": host.mac,
        "ssh_user": host.ssh_user,
        "has_ssh": bool(host.ssh_user and (host.ssh_key_path or host.ssh_password))
    })


@app.route('/rest/computer/<name>/ip', methods=['GET'])
@require_auth
def rest_get_ip(name):
    host = get_host_by_name(name)
    if not host:
        return jsonify({'error': 'Host not found'}), 404
    return jsonify({'ip': host.ip})


@app.route('/rest/computer/<name>/mac', methods=['GET'])
@require_auth
def rest_get_mac(name):
    host = get_host_by_name(name)
    if not host:
        return jsonify({'error': 'Host not found'}), 404
    return jsonify({'mac': host.mac})


@app.route('/rest/computer/<name>/status', methods=['GET'])
@require_auth
def rest_get_status(name):
    host = get_host_by_name(name)
    if not host:
        return jsonify({'error': 'Host not found'}), 404
    return jsonify({'status': 'online' if host.is_online() else 'offline'})


@app.route('/rest/computer/<name>/systeminfo', methods=['GET'])
@require_auth
def rest_get_info(name):
    host = get_host_by_name(name)
    if not host:
        return jsonify({'error': 'Host not found'}), 404
    if not host.is_online():
        return jsonify({'error': 'Host is offline'}), 409
    return jsonify({'info': host.get_info()})


@app.route('/rest/computer/<name>/wake', methods=['POST'])
@require_auth
def rest_wake(name):
    host = get_host_by_name(name)
    if not host:
        return jsonify({'error': 'Host not found'}), 404
    if host.is_online():
        return jsonify({'error': 'Host already online'}), 409
    host.wake()
    return jsonify({'status': 'wake sent'}), 200


@app.route('/rest/computer/<name>/shutdown', methods=['POST'])
@require_auth
def rest_shutdown(name):
    host = get_host_by_name(name)
    if not host:
        return jsonify({'error': 'Host not found'}), 404
    if not host.is_online():
        return jsonify({'error': 'Host is offline'}), 409
    host.shutdown()
    return jsonify({'status': 'shutdown sent'}), 200


@app.route('/rest/computer/<name>/reboot', methods=['POST'])
@require_auth
def rest_reboot(name):
    host = get_host_by_name(name)
    if not host:
        return jsonify({'error': 'Host not found'}), 404
    if not host.is_online():
        return jsonify({'error': 'Host is offline'}), 409
    host.reboot()
    return jsonify({'status': 'reboot sent'}), 200


# -------------------
# Host Monitoring
# -------------------

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


socketio.start_background_task(target=monitor_hosts)


if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000)
