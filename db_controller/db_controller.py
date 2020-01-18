import json
import os
from urllib.parse import urljoin, urlparse

from sqlalchemy import create_engine, ForeignKey, ForeignKeyConstraint
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship, backref
from sqlalchemy.interfaces import PoolListener
from settings import DATABASES


class ForeignKeysListener(PoolListener):
    def connect(self, dbapi_con, con_record):
        db_cursor = dbapi_con.execute('pragma foreign_keys=ON')

DATABASES = {}
url = os.environ['JAWSDB_URL']
print("TEST!" + url)
if 'JAWSDB_URL' in os.environ:
    url = urlparse(os.environ['JAWSDB_URL'])
    print(DATABASES)

    # Ensure default database exists.
    DATABASES['default'] = DATABASES.get('default', {})
    # Update with environment configuration.
    DATABASES['default'].update({
        'NAME': url.path[1:],
        'USER': url.username,
        'PASSWORD': url.password,
        'HOST': url.hostname,
        'PORT': url.port,
    })
# database_url = "sqlite:///data.db"
# engine = create_engine(database_url, listeners=[ForeignKeysListener()], echo=True)
password = DATABASES['default']['PASSWORD']
login = DATABASES['default']['PASSWORD']
name = DATABASES['default']['NAME']
name = "p29qne1tj1q5bjkw"
url = DATABASES['default']['HOST']
port = DATABASES['default']['PORT']
print(login)
engine = create_engine('pymysql://{login}:{password}@{url}:{port}/{name}'.format(
    login=login,
    password=password,
    name=name,
    url=url,
    port=port), echo=True)

Base = declarative_base()
from sqlalchemy import Table, Column, Integer, String, MetaData, DateTime, Boolean, BigInteger


class State(Base):
    __tablename__ = "state"
    id = Column(Integer, primary_key=True)
    name = Column(String(10))

    tgusers = relationship("TGUser", back_populates="state")

    def __init__(self, name):
        self.name = name

    def __repr__(self):
        return "<State('%s')>" % self.name

    def json_to_dict(self, data):
        return json.loads(data)


class TGUser(Base):
    __tablename__ = "tguser"
    # id = Column(Integer, primary_key=True)
    tg_id = Column(BigInteger, primary_key=True)
    tg_first_name = Column(String(50))
    tg_last_name = Column(String(50))
    tg_nick = Column(String(50))
    state_id = Column(Integer, ForeignKey('state.id'))
    state = relationship("State", back_populates="tgusers")
    ForeignKeyConstraint(['state'], ['state.id'])

    tasks = relationship("Task", secondary="ratings")

    def __init__(self, tg_id, tg_first_name, tg_last_name, tg_nick, state_id):
        self.tg_id = tg_id
        self.tg_first_name = tg_first_name
        self.tg_last_name = tg_last_name
        self.tg_nick = tg_nick
        self.state_id = state_id

    def __repr__(self):
        return "<TGUser('%s', '%s', '%s', '%s')>" % (self.tg_id, self.tg_first_name, self.tg_last_name, self.tg_nick)


class Task(Base):
    __tablename__ = "tasks"
    id = Column(Integer, primary_key=True)
    name = Column(String(50))
    task = Column(String(50))
    answer_pattern = Column(String(50))
    active = Column(Boolean)
    congrat = Column(String(50))

    users = relationship("TGUser", secondary="ratings")
    # start_time = Column(DateTime)

    def __init__(self, task, answer_pattern, active, name, congrat):
        self.task = task
        self.answer_pattern = answer_pattern
        self.active = active
        self.name = name
        self.congrat = congrat
        # self.start_time = start_time

    def __repr__(self):
        return "<Task('%s', '%s', '%s')>" % (self.task, self.answer_pattern, self.active)


class Resource(Base):
    __tablename__ = "resource"
    id = Column(Integer, primary_key=True)
    tg_id = Column(String(70))
    type = Column(String(20))
    caption = Column(String(100))
    task_id = Column(Integer, ForeignKey('tasks.id'))
    ForeignKeyConstraint(['task_id'], ['tasks.id'])

    def __init__(self, tg_id, type, task_id, caption):
        self.tg_id = tg_id
        self.type = type
        self.task_id = task_id,
        self.caption = caption

    def json_to_dict(self, data):
        return json.loads(data)


class ResourceAnswer(Base):
    __tablename__ = "resource_answer"
    id = Column(Integer, primary_key=True)
    tg_id = Column(String(70))
    type = Column(String(20))
    caption = Column(String(100))
    task_id = Column(Integer, ForeignKey('tasks.id'))
    ForeignKeyConstraint(['task_id'], ['tasks.id'])

    def __init__(self, tg_id, type, task_id, caption):
        self.tg_id = tg_id
        self.type = type
        self.task_id = task_id,
        self.caption = caption

    def json_to_dict(self, data):
        return json.loads(data)


class Ratings(Base):
    __tablename__ = 'ratings'
    # id = Column(Integer, primary_key=True)
    tguser_id = Column(BigInteger, ForeignKey('tguser.tg_id'), primary_key=True)
    task_id = Column(Integer, ForeignKey('tasks.id'), primary_key=True)
    rating = Column(Integer, default=0)
    is_solved = Column(Boolean, default=False)

    tguser = relationship(TGUser, backref=backref("ratings"), cascade="all")
    task = relationship(Task, backref=backref("ratings"), cascade="all")

    def __init__(self, tguser_id, task_id):
        self.tguser_id = tguser_id
        self.task_id = task_id

    def json_to_dict(self, data):
        return json.loads(data)


# Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)


def get_all_tasks():
    session = Session()
    return session.query(Task).all()


def get_all_available_tasks():
    session = Session()
    return session.query(Task).filter_by(active=True).all()


def get_all_available_tasks_for_user(user_id):
    all_tasks = get_all_available_tasks()
    session = Session()
    #todo: find a way to use many-to-many relationship
    user = session.query(TGUser).filter_by(tg_id=user_id).first()
    user_solved = [obj.task_id for obj in list(filter(lambda x: x.is_solved is True, list(user.ratings)))]
    return [item for item in all_tasks if item.id not in user_solved]


def add_task(task, answer_pattern, active, name, congrat):
    session = Session()
    new_task = Task(task, answer_pattern, active, name, congrat)
    session.add(new_task)
    session.commit()
    return session.query(Task).order_by(Task.id.desc()).first()


def get_task_by_id(task_id):
    session = Session()
    return session.query(Task).filter_by(id=task_id).first()


def update_task_state_by_id(task_id, state):
    session = Session()
    session.query(Task).filter_by(id=task_id).update({Task.done: state})
    session.commit()
    return session.query(Task).filter_by(id=task_id).first()


def get_all_states():
    session = Session()
    return session.query(State).all()


def get_state_by_id(id):
    session = Session()
    return session.query(State).filter_by(id=id).first()


def add_state(name):
    session = Session()
    state = State(name)
    session.add(state)
    session.commit()
    return session.query(State).order_by(State.id.desc()).first()


def get_all_users():
    session = Session()
    return session.query(TGUser).all()


def get_user_by_tgid(tg_id):
    session = Session()
    return session.query(TGUser).filter_by(tg_id=tg_id).first()


def get_user_by_id(state_id):
    session = Session()
    return session.query(TGUser).filter_by(id=state_id).first()


def get_user_by_tgid(tgid):
    session = Session()
    return session.query(TGUser).filter_by(tg_id=tgid).first()


def add_user(tg_id, tg_first_name, tg_last_name, tg_nick, state):
    session = Session()
    user = TGUser(tg_id, tg_first_name, tg_last_name, tg_nick, state)
    session.add(user)
    session.commit()
    return user


def get_resources_for_task_id(task_id):
    session = Session()
    return session.query(Resource).filter_by(task_id=task_id)


def get_resources_answer_for_task_id(task_id):
    session = Session()
    return session.query(ResourceAnswer).filter_by(task_id=task_id)


def add_resource(tg_id, type, task_id, caption):
    session = Session()
    new_resource = Resource(tg_id, type, task_id, caption)
    session.add(new_resource)
    session.commit()
    return session.query(Resource).order_by(Resource.id.desc()).first()


def add_answer_resource(tg_id, type, task_id, caption):
    session = Session()
    new_resource = ResourceAnswer(tg_id, type, task_id, caption)
    session.add(new_resource)
    session.commit()
    return session.query(ResourceAnswer).order_by(ResourceAnswer.id.desc()).first()


def update_user_state_by_id(tg_id, state_id):
    session = Session()
    session.query(TGUser).filter_by(tg_id=tg_id).update({TGUser.state_id: state_id})
    session.commit()
    return session.query(TGUser).filter_by(tg_id=tg_id).first()


def add_rating_for_task_from_user(rating, tguser_id, task_id):
    session = Session()

    task = session.query(Ratings).filter_by(tguser_id=tguser_id, task_id=task_id)
    if task:
        task.update({Ratings.rating: rating})
    else:
        task.update({Ratings.rating: 0})

    session.commit()
    return session.query(Ratings).filter_by(tguser_id=tguser_id, task_id=task_id).first()


def mark_task_as_solved_for_user(tguser_id, task_id):
    session = Session()
    new_rating = Ratings(tguser_id=tguser_id, task_id=task_id)
    new_rating.is_solved = True

    session.add(new_rating)
    session.commit()
    return new_rating


