import os
import pymysql
basedir = os.path.abspath(os.path.dirname(__file__))


class Config(object):
    # ...
    # LOGIN = os.environ.get('MYSQL_LOGIN') or 'root'
    # PASSWORD = os.environ.get('MYSQL_PASSWORD') or 'ozizibbz'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'mysql+pymysql://root:ozizibbz@localhost:3306/questions'
    SQLALCHEMY_TRACK_MODIFICATIONS = False