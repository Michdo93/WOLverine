from extensions import db
from datetime import datetime

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='user')

    def __repr__(self):
        return f"<User {self.username} ({self.role})>"

class Host(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    ip = db.Column(db.String(50), nullable=False)
    mac = db.Column(db.String(50), nullable=False)
    ssh_user = db.Column(db.String(50))
    ssh_password = db.Column(db.String(50))
    ssh_key_path = db.Column(db.String(100))

    schedules = db.relationship('Schedule', backref='device', lazy=True)
    stats = db.relationship('Stat', backref='device', lazy=True)

    def __repr__(self):
        return f"<Host {self.name}>"

class Schedule(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    device_id = db.Column(db.Integer, db.ForeignKey('host.id'), nullable=False)
    action = db.Column(db.String(50), nullable=False)  # for example 'wake', 'shutdown', 'reboot'
    datetime = db.Column(db.DateTime, nullable=False)

    def __repr__(self):
        return f"<Schedule {self.device_id} - {self.action} at {self.datetime}>"

class Stat(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    device_id = db.Column(db.Integer, db.ForeignKey('host.id'), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    cpu = db.Column(db.Float, nullable=True)  # in percent
    ram = db.Column(db.Float, nullable=True)  # in percent
    ping = db.Column(db.Float, nullable=True) # in ms

    def __repr__(self):
        return f"<Stat {self.device_id} - CPU: {self.cpu}%, RAM: {self.ram}%, Ping: {self.ping}ms>"