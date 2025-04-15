from extensions import db

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

    def __repr__(self):
        return f"<Host {self.name}>"
