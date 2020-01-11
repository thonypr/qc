from app import db


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True, index=True, unique=True)
    login = db.Column(db.String(255), index=True, unique=True)
    password = db.Column(db.String(255))
    role = db.Column(db.String(45))

    def __repr__(self):
        return '<User {}>'.format(self.username)


class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True, index=True, unique=True)
    title = db.Column(db.String(20), index=True)
    question = db.Column(db.String(1000))
    info = db.Column(db.String(255))
    answer = db.Column(db.String(255))

    def __repr__(self):
        return '<Task {}>'.format(self.title)
