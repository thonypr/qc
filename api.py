#!flask/bin/python

from flask import Flask, jsonify
from flask import abort
from flask import make_response
from flask import request
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import create_engine
from datetime import datetime

from db_controller import db_controller
from flask_marshmallow import Marshmallow

from db_controller.db_controller import Task, State, TGUser, Resource, get_all_available_tasks_for_user

app = Flask(__name__)
ma = Marshmallow(app)


# get_all_available_tasks_for_user(1)

class StateSchema(ma.ModelSchema):
    class Meta:
        model = State


class UserSchema(ma.ModelSchema):
    class Meta:
        model = TGUser


class TaskSchema(ma.ModelSchema):
    class Meta:
        model = Task


class ResourceSchema(ma.ModelSchema):
    class Meta:
        model = Resource


# db_controller.get_all_tasks()


@app.route('/api/tasks', methods=['GET'])
def get_tasks():
    # get it from database
    tasks_db = db_controller.get_all_tasks()
    tasks_schema = TaskSchema(many=True)
    output = tasks_schema.dump(tasks_db)
    return jsonify({'tasks': output})


@app.route('/api/tasks/<int:task_id>', methods=['GET'])
def get_task(task_id):
    result = db_controller.get_task_by_id(task_id)
    task_schema = TaskSchema()
    output = task_schema.dump(result)
    if not result:
        abort(404)
    return jsonify({'result': output})


@app.errorhandler(404)
def not_found(error):
    return make_response(jsonify({'error': 'Not found'}), 404)


@app.route('/api/tasks', methods=['POST'])
def create_task():
    if not request.json or not 'task' in request.json:
        abort(400)
    # todo: check that author of response is a valid person
    # add it to database
    # conn = db_connect.connect()
    # todo: add obfuscation and checking for vulnerabilities
    task = request.json['task']
    answer_pattern = request.json.get('answer_pattern', "")
    congrat = request.json.get('congrat', "")
    active = request.json.get('active', True)
    name = request.json.get('name', "")
    # start_time = datetime.now()
    task_in_db = db_controller.add_task(task, answer_pattern, active, name, congrat)

    # todo check that it was added successfully in db
    # now we can add it to runtime
    # todo: consider using runtime collection in order to get tasks immediately without connecting to database?
    # tasks.append(task)

    task_schema = TaskSchema()
    output = task_schema.dump(task_in_db)
    # add also creation of the states for the new task
    db_controller.add_state("VIEW_{id}".format(id=output['id']))
    # and creating a rating-state for that task
    db_controller.add_state("RATE_{id}".format(id=output['id']))
    # db_controller.add_state("FINISH_{id}".format(id=output['id']))

    return jsonify({'result': output}), 201


@app.route('/api/tasks/switch/on/<int:task_id>', methods=['PUT'])
def switch_task_on(task_id):
    task = db_controller.get_from_db_by_id(task_id)
    if not task:
        abort(404)
    upd_task = db_controller.update_task_state_by_id(task_id, True)
    task_schema = TaskSchema()
    output = task_schema.dump(upd_task)
    return jsonify({'result': output}), 201


@app.route('/api/tasks/switch/off/<int:task_id>', methods=['PUT'])
def switch_task_off(task_id):
    task = db_controller.get_from_db_by_id(task_id)
    if not task:
        abort(404)
    upd_task = db_controller.update_task_state_by_id(task_id, False)
    task_schema = TaskSchema()
    output = task_schema.dump(upd_task)
    return jsonify({'result': output}), 201


@app.route('/api/tasks/<int:task_id>', methods=['PUT'])
# def update_task(task_id):
#     task_in_list = list(filter(lambda t: t['id'] == task_id, tasks))
#     if len(task_in_list) == 0:
#         abort(404)
#     if not request.json:
#         abort(400)
#     from pip._vendor.appdirs import unicode
#     if 'task' in request.json and type(request.json['task']) != unicode:
#         abort(400)
#     if 'answer_pattern' in request.json and type(request.json['answer_pattern']) is not unicode:
#         abort(400)
#     if 'done' in request.json and type(request.json['done']) is not bool:
#         abort(400)
#     upd_task_info = request.json
#     # todo: check that author of response is a valid person
#     # add it to database
#     conn = 0
#     # todo: add obfuscation and checking for vulnerabilities
#     task = upd_task_info['task']
#     answer_pattern = upd_task_info['answer_pattern']
#     done = upd_task_info['done']
#     start_time = upd_task_info['start_time']
#     query = conn.execute(
#             "update tasks set task = '{task}' and answer_pattern = '{answer_pattern}' "
#             "and done = '{done}' and start_time = '{start_time}' "
#             "where id = {id}".format(
#                 task=task,
#                 answer_pattern=answer_pattern,
#                 done=done,
#                 start_time=start_time,
#                 id=task_id
#             ))
#     # todo: check that we inserted it in db
#     task_in_list[0]['task'] = request.json.get('task', task[0]['task'])
#     task_in_list[0]['answer_pattern'] = request.json.get('answer_pattern', task[0]['answer_pattern'])
#     task_in_list[0]['done'] = request.json.get('done', task[0]['done'])
#     return jsonify({'task': task_in_list[0]})

# @app.route('/api/tasks/<int:task_id>', methods=['DELETE'])
# def delete_task(task_id):
#     task = list(filter(lambda t: t['id'] == task_id, tasks))
#     if len(task) == 0:
#         abort(404)
#     tasks.remove(task[0])
#     return jsonify({'result': True})

@app.route('/api/states', methods=['GET'])
def get_states():
    # get it from database
    states = db_controller.get_all_states()
    states_schema = StateSchema(many=True)
    output = states_schema.dump(states)
    return jsonify({'states': output})


@app.route('/api/states', methods=['POST'])
def create_state():
    if not request.json or not 'name' in request.json:
        abort(400)
    # todo: check that author of response is a valid person
    # add it to database
    # conn = db_connect.connect()
    # todo: add obfuscation and checking for vulnerabilities
    name = request.json['name']
    state = db_controller.add_state(name)

    # todo check that it was added successfully in db
    # now we can add it to runtime
    # todo: consider using runtime collection in order to get tasks immediately without connecting to database?
    # tasks.append(task)

    state_schema = StateSchema()
    output = state_schema.dump(state)
    return jsonify({'result': output}), 201


@app.route('/api/users', methods=['GET'])
def get_users():
    # get it from database
    users = db_controller.get_all_users()
    users_schema = UserSchema(many=True)
    output = users_schema.dump(users)
    return jsonify({'users': output})


@app.route('/api/users/<int:user_id>', methods=['GET'])
def get_user_by_id(user_id):
    # get it from database
    user = db_controller.get_user_by_id(user_id)
    user_schema = UserSchema()
    output = user_schema.dump(user)
    return jsonify({'user': output})


@app.route('/api/users', methods=['POST'])
def add_user():
    if not request.json or not 'tg_id' in request.json or not 'tg_first_name' or not 'state':
        abort(400)
    # todo: check that author of response is a valid person
    # add it to database
    # conn = db_connect.connect()
    # todo: add obfuscation and checking for vulnerabilities
    tg_id = request.json['tg_id']
    tg_first_name = request.json['tg_first_name']
    tg_last_name = request.json.get('tg_last_name', "")
    tg_user_name = request.json.get('tg_user_name', "")
    # todo: get WELCOME or other state
    state = request.json['state']

    user = db_controller.add_user(tg_id, tg_first_name, tg_last_name, tg_user_name, state)

    # todo check that it was added successfully in db
    # now we can add it to runtime
    # todo: consider using runtime collection in order to get tasks immediately without connecting to database?
    # tasks.append(task)

    user_schema = UserSchema()
    output = user_schema.dump(user)
    return jsonify({'result': output}), 201


@app.route('/api/resources', methods=['POST'])
def create_resource():
    if not request.json or not 'tg_id' in request.json or not 'type' in request.json or not 'task_id' in request.json:
        abort(400)
    # todo: check that author of response is a valid person
    # add it to database
    # conn = db_connect.connect()
    # todo: add obfuscation and checking for vulnerabilities
    tg_id = request.json['tg_id']
    type = request.json['type']
    task_id = request.json['task_id']
    caption = request.json.get('caption', "")
    resource_in_db = db_controller.add_resource(tg_id, type, task_id, caption)

    # todo check that it was added successfully in db
    # now we can add it to runtime
    # todo: consider using runtime collection in order to get tasks immediately without connecting to database?
    # tasks.append(task)

    resource_schema = ResourceSchema()
    output = resource_schema.dump(resource_in_db)
    return jsonify({'result': output}), 201


if __name__ == '__main__':
    app.run(debug=True)
