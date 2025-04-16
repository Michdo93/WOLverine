import eventlet
eventlet.monkey_patch()

import bcrypt
import hmac
import time
import secrets
from flask import Flask, render_template, request, redirect, session, jsonify, Response, url_for, flash
from flask_socketio import SocketIO
from flask_cors import CORS
from functools import wraps
from extensions import db
from utils.host_client import HostClient
from datetime import datetime
import pytz
from uuid import uuid4
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.date import DateTrigger
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore

app = Flask(__name__)
app.secret_key = secrets.token_hex(32)

CORS(app, origins=["http://localhost:5000"]) 

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///wolverine.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

scheduler = BackgroundScheduler(
    jobstores={
        'default': SQLAlchemyJobStore(url='sqlite:///jobs.db')  # oder dieselbe wie deine Haupt-DB, aber getrennt ist manchmal besser
    },
    timezone='UTC'  # oder deine Standard-TZ, aber du setzt ja eh lokalisiert
)
scheduler.start()

socketio = SocketIO(app, cors_allowed_origins='*', async_mode='eventlet')
#socketio = SocketIO(app, cors_allowed_origins='*', async_mode='eventlet', logger=True, engineio_logger=True)

from models import User, Host, Schedule, Stat

# -------------------
# Basic Auth Helpers
# -------------------

def verify_password(username, password):
    user = User.query.filter_by(username=username).first()
    if not user:
        return False

    if user.password.startswith('$2b$'):
        return bcrypt.checkpw(password.encode('utf-8'), user.password.encode('utf-8'))
    else:
        return hmac.compare_digest(user.password, password)

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

def current_user():
    return User.query.filter_by(username=session.get('user')).first()

def require_admin(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        user = current_user()
        if not user or user.role != 'admin':
            return "Access denied", 403
        return f(*args, **kwargs)
    return decorated

# -------------------
# Web Routes
# -------------------

# Dashboard

# Login
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        user = User.query.filter_by(username=username).first()
        if user and verify_password(user.username, password):
            session['user'] = user.username
            session['role'] = user.role
            return redirect('/')
        return 'Login failed'
    return render_template('login.html')

# Logout
@app.route('/logout')
def logout():
    session.clear()
    return redirect('/login')

# Dashboard/Index
@app.route('/')
def index():
    if 'user' not in session:
        return redirect('/login')

    hosts = Host.query.all()
    
    return render_template('index.html', hosts=hosts, session=session)

# Update Host-Card
@app.route('/status/<int:idx>')
def status(idx):
    host = db.session.get(Host, idx)

    if not host:
        return jsonify({'error': 'Host not found'}), 404
    
    client = HostClient(
        name=host.name,
        ip=host.ip,
        mac=host.mac,
        ssh_user=host.ssh_user,
        ssh_password=host.ssh_password,
        ssh_key_path=host.ssh_key_path
    )

    return jsonify({
        'online': client.is_online(),
        'info': client.get_info() if client.is_online() else ''
    })

# Perform Action
@app.route('/action/<int:idx>', methods=['POST'])
def action(idx):
    host = db.session.get(Host, idx)
    if not host:
        return jsonify({'error': 'Host not found'}), 404

    client = HostClient(
        name=host.name,
        ip=host.ip,
        mac=host.mac,
        ssh_user=host.ssh_user,
        ssh_password=host.ssh_password,
        ssh_key_path=host.ssh_key_path
    )

    action_type = request.json.get("action")

    if action_type == "wake":
        if not client.is_online():
            client.wake()
            return jsonify({'action': 'wake'})
        return jsonify({'error': 'Host already online'}), 409

    if action_type == "shutdown":
        if client.is_online():
            client.shutdown()
            return jsonify({'action': 'shutdown'})
        return jsonify({'error': 'Host offline'}), 409

    if action_type == "reboot":
        if client.is_online():
            client.reboot()
            return jsonify({'action': 'reboot'})
        return jsonify({'error': 'Host offline'}), 409

    return jsonify({'error': 'Invalid action'}), 400

# User management

# Users view
@app.route('/users')
def user_list():
    if 'user' not in session:
        return redirect('/login')

    user = current_user()
    if not user or user.role != 'admin':
        return "Access denied", 403

    users = User.query.all()
    return render_template('users.html', users=users)

# Add user
@app.route("/users/create", methods=["GET", "POST"])
def add_user():
    if request.method == "POST":
        pw_raw = request.form["password"].encode("utf-8")
        hashed_pw = bcrypt.hashpw(pw_raw, bcrypt.gensalt()).decode("utf-8")

        user = User(username=request.form["username"], role=request.form["role"], password=hashed_pw)
        db.session.add(user)
        db.session.commit()
        flash("User added successfully.")
        return redirect(url_for("user_list"))
    return render_template("user_form.html", action="Add", user=None)

# Edit user
@app.route("/users/edit/<int:user_id>", methods=["GET", "POST"])
def edit_user(user_id):
    user = User.query.get_or_404(user_id)
    if request.method == "POST":
        user.username = request.form["username"]
        user.role = request.form["role"]
        if request.form["password"]:
            pw_raw = request.form["password"].encode("utf-8")
            user.password = bcrypt.hashpw(pw_raw, bcrypt.gensalt()).decode("utf-8")
        db.session.commit()
        flash("User updated successfully.")
        return redirect(url_for("user_list"))
    return render_template("user_form.html", action="Edit", user=user)

# Delete user
@app.route("/users/delete/<int:user_id>")
def delete_user(user_id):
    user = User.query.get_or_404(user_id)
    db.session.delete(user)
    db.session.commit()
    flash("User deleted.")
    return redirect(url_for("user_list"))

# Host Configuration

# Create host
@app.route("/hosts/create", methods=["GET", "POST"])
@require_admin
def add_host():
    if request.method == "POST":
        host = Host(
            name=request.form["name"],
            ip=request.form["ip"],
            mac=request.form["mac"],
            ssh_user=request.form.get("ssh_user"),
            ssh_password=request.form.get("ssh_password") or None,
            ssh_key_path=request.form.get("ssh_key_path") or None
        )
        db.session.add(host)
        db.session.commit()
        flash("Host added successfully.")
        return redirect(url_for("index"))
    return render_template("host_form.html", action="Add", host=None)

# Edit host
@app.route("/hosts/edit/<int:host_id>", methods=["GET", "POST"])
@require_admin
def edit_host(host_id):
    host = db.session.get(Host, host_id)
    if not host:
        return jsonify({'error': 'Host not found'}), 404

    if request.method == "POST":
        host.name = request.form["name"]
        host.ip = request.form["ip"]
        host.mac = request.form["mac"]
        host.ssh_user = request.form.get("ssh_user")
        host.ssh_password = request.form.get("ssh_password") or None
        host.ssh_key_path = request.form.get("ssh_key_path") or None
        db.session.commit()
        flash("Host updated.")
        return redirect(url_for("index"))
    return render_template("host_form.html", action="Edit", host=host)

# delete host
@app.route("/hosts/delete/<int:host_id>", methods=["POST"])
@require_admin
def delete_host(host_id):
    host = db.session.get(Host, host_id)
    if not host:
        return jsonify({'error': 'Host not found'}), 404

    db.session.delete(host)
    db.session.commit()
    flash("Host deleted.")
    return redirect(url_for("index"))

# Scheduled tasks/actions

# List scheduled tasks/actions
@app.route('/schedules/<int:host_id>')
def get_schedules_for_host(host_id):
    schedules = Schedule.query.filter_by(device_id=host_id).order_by(Schedule.datetime).all()
    return jsonify([{
        'id': s.id,
        'action': s.action,
        'datetime': s.datetime.isoformat()
    } for s in schedules])

# Create Schedule
@app.route('/schedules', methods=['POST'])
def create_schedule():
    data = request.get_json()
    user_tz = pytz.timezone(data.get("timezone", "UTC"))

    naive_local_dt = datetime.fromisoformat(data['datetime'])
    localized = user_tz.localize(naive_local_dt)

    new_schedule = Schedule(
        device_id=data['device_id'],
        action=data['action'],
        datetime=localized
    )
    db.session.add(new_schedule)
    db.session.commit()

    scheduler.add_job(
        func=execute_scheduled_action,
        trigger=DateTrigger(run_date=localized.astimezone(pytz.utc)),
        args=[new_schedule.id],
        id=str(uuid4()),  # optional schedule.id als str()
        replace_existing=True
    )

    return jsonify({'status': 'created'}), 201

# Edit Schedule
@app.route('/schedules/<int:schedule_id>', methods=['PUT'])
def edit_schedule(schedule_id):
    data = request.get_json()
    schedule = Schedule.query.get_or_404(schedule_id)
    user_tz = pytz.timezone(data.get("timezone", "UTC"))

    naive_local_dt = datetime.fromisoformat(data['datetime'])
    localized = user_tz.localize(naive_local_dt)

    schedule.device_id = data['device_id']
    schedule.action = data['action']
    schedule.datetime = localized

    db.session.commit()

    job_id = f"schedule_{schedule.id}"
    scheduler.remove_job(job_id=job_id)  # alten Job löschen
    scheduler.add_job(
        func=execute_scheduled_action,
        trigger=DateTrigger(run_date=localized.astimezone(pytz.utc)),
        args=[schedule.id],
        id=job_id,
        replace_existing=True
    )

    return jsonify({'status': 'updated'})

# Delete Schedule
@app.route('/schedules/<int:schedule_id>', methods=['DELETE'])
def delete_schedule(schedule_id):
    schedule = Schedule.query.get(schedule_id)
    if not schedule:
        return jsonify({'error': 'Schedule not found'}), 404
    
    job_id = f"schedule_{schedule.id}"
    try:
        scheduler.remove_job(job_id=job_id)
    except Exception as e:
        print(f"Warning: Job {job_id} not found or already removed – {e}")

    db.session.delete(schedule)
    db.session.commit()

    return jsonify({'status': 'deleted'}), 200

# -------------------
# REST API Endpoints
# -------------------

@app.route('/rest/computer', methods=['GET'])
@require_auth
def rest_get_all_computers():
    hosts = Host.query.all()
    return jsonify([
        {
            "name": host.name,
            "ip": host.ip,
            "mac": host.mac,
            "ssh_user": host.ssh_user,
            "has_ssh": bool(host.ssh_user and (host.ssh_key_path or host.ssh_password))
        }
        for host in hosts
    ])


def get_host_by_name(name):
    return Host.query.filter_by(name=name).first()

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

    client = HostClient(
        name=host.name,
        ip=host.ip,
        mac=host.mac,
        ssh_user=host.ssh_user,
        ssh_password=host.ssh_password,
        ssh_key_path=host.ssh_key_path
    )

    return jsonify({'status': 'online' if client.is_online() else 'offline'})

@app.route('/rest/computer/<name>/systeminfo', methods=['GET'])
@require_auth
def rest_get_info(name):
    host = get_host_by_name(name)
    if not host:
        return jsonify({'error': 'Host not found'}), 404

    client = HostClient(
        name=host.name,
        ip=host.ip,
        mac=host.mac,
        ssh_user=host.ssh_user,
        ssh_password=host.ssh_password,
        ssh_key_path=host.ssh_key_path
    )

    if not client.is_online():
        return jsonify({'error': 'Host is offline'}), 409
    return jsonify({'info': client.get_info()})

@app.route('/rest/computer/<name>/wake', methods=['POST'])
@require_auth
def rest_wake(name):
    host = get_host_by_name(name)
    if not host:
        return jsonify({'error': 'Host not found'}), 404

    client = HostClient(
        name=host.name,
        ip=host.ip,
        mac=host.mac,
        ssh_user=host.ssh_user,
        ssh_password=host.ssh_password,
        ssh_key_path=host.ssh_key_path
    )

    if client.is_online():
        return jsonify({'error': 'Host already online'}), 409

    client.wake()
    return jsonify({'status': 'wake sent'}), 200

@app.route('/rest/computer/<name>/shutdown', methods=['POST'])
@require_auth
def rest_shutdown(name):
    host = get_host_by_name(name)
    if not host:
        return jsonify({'error': 'Host not found'}), 404

    client = HostClient(
        name=host.name,
        ip=host.ip,
        mac=host.mac,
        ssh_user=host.ssh_user,
        ssh_password=host.ssh_password,
        ssh_key_path=host.ssh_key_path
    )

    if not client.is_online():
        return jsonify({'error': 'Host is offline'}), 409

    client.shutdown()
    return jsonify({'status': 'shutdown sent'}), 200

@app.route('/rest/computer/<name>/reboot', methods=['POST'])
@require_auth
def rest_reboot(name):
    host = get_host_by_name(name)
    if not host:
        return jsonify({'error': 'Host not found'}), 404

    client = HostClient(
        name=host.name,
        ip=host.ip,
        mac=host.mac,
        ssh_user=host.ssh_user,
        ssh_password=host.ssh_password,
        ssh_key_path=host.ssh_key_path
    )

    if not client.is_online():
        return jsonify({'error': 'Host is offline'}), 409

    client.reboot()
    return jsonify({'status': 'reboot sent'}), 200

# -------------------
# Scheduler
# -------------------

def execute_scheduled_action(schedule_id):
    with app.app_context():
        schedule = Schedule.query.get(schedule_id)
        if not schedule:
            print(f"Schedule ID {schedule_id} not found.")
            return

        host = Host.query.get(schedule.device_id)
        if not host:
            print(f"Host ID {schedule.device_id} not found.")
            return

        client = HostClient(
            name=host.name,
            ip=host.ip,
            mac=host.mac,
            ssh_user=host.ssh_user,
            ssh_password=host.ssh_password,
            ssh_key_path=host.ssh_key_path
        )

        action = schedule.action
        print(f"Executing scheduled action: {action} for host {host.name}")

        try:
            if action == "wake":
                if not client.is_online():
                    client.wake()
            elif action == "shutdown":
                if client.is_online():
                    client.shutdown()
            elif action == "reboot":
                if client.is_online():
                    client.reboot()
        except Exception as e:
            print(f"Error executing {action} on {host.name}: {e}")

def load_scheduled_jobs():
    with app.app_context():
        schedules = Schedule.query.all()
        for schedule in schedules:
            if schedule.datetime > datetime.utcnow():  # nur zukünftige Jobs
                scheduler.add_job(
                    func=execute_scheduled_action,
                    trigger=DateTrigger(run_date=schedule.datetime),
                    args=[schedule.id],
                    id=f"schedule_{schedule.id}",
                    replace_existing=True
                )

# -------------------
# Host Monitoring
# -------------------

def monitor_hosts():
    with app.app_context():
        host_status = {}

        while True:
            hosts = Host.query.all()
            for host in hosts:
                client = HostClient(
                    name=host.name,
                    ip=host.ip,
                    mac=host.mac,
                    ssh_user=host.ssh_user,
                    ssh_password=host.ssh_password,
                    ssh_key_path=host.ssh_key_path
                )

                try:
                    current = client.is_online()
                    last_status = host_status.get(host.id)

                    if last_status != current:
                        host_status[host.id] = current
                        socketio.emit('status_update', {
                            'idx': host.id,
                            'online': current,
                            'info': client.get_info() if current else ''
                        })
                except Exception as e:
                    print(f"Error checking host {host.name}: {e}")
            time.sleep(5)

socketio.start_background_task(target=monitor_hosts)
load_scheduled_jobs()

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000)
