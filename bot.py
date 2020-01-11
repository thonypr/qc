import os
import re

import telebot
import requests
import json

from telebot import types

import api

from sqlalchemy import inspect

from db_controller import db_controller


def object_as_dict(obj):
    return {c.key: getattr(obj, c.key)
            for c in inspect(obj).mapper.column_attrs}


# token = os.environ['TELEGRAM_TOKEN']
token = "688913128:AAFzLAOp9RaSZ3o2hMgZd0pYgrU0k6702fU"

bot = telebot.TeleBot(token)
# If you use redis, install this add-on https://elements.heroku.com/addons/heroku-redis
# r = redis.from_url(os.environ.get("REDIS_URL"))

states = {}


def refresh_states():
    states_db = db_controller.get_all_states()
    for row in states_db:
        # states[u'{}'.format(object_as_dict(row)['id'])] = object_as_dict(row)['name']
        states[object_as_dict(row)['id']] = object_as_dict(row)['name']


# states = {int(k):int(v) for k,v in states.items()}
#       Your bot code below

def makeAdminKeyboard():
    markup = types.InlineKeyboardMarkup()

    list = ["add_task"]
    if list:
        for item in list:
            markup.add(types.InlineKeyboardButton(text=item,
                                                  callback_data="a_{code}".format(code=item)))

    return markup


def makeKeyboard(list):
    markup = types.InlineKeyboardMarkup()

    if list:
        for item in list:
            markup.add(types.InlineKeyboardButton(text=item.name,
                                                  callback_data="t{id}".format(id=item.id)))

    return markup


def makeRatingKeyboard(task_id):
    markup = types.InlineKeyboardMarkup()

    list = [1, 2, 3, 4, 5, "?"]

    for item in list:
        markup.add(types.InlineKeyboardButton(text=item,
                                              callback_data="r{id}_{task_id}".format(id=item, task_id=task_id)))

    return markup

task_data = {
    "name" : None,
    "regexp": "no",
    "congrats": "no",
    "text": "no",
    "resources": [],
    "finished": False
}

countert = 1

add_task_state = 1

@bot.message_handler(func=lambda msg: msg.from_user.id == 235486635)
def add_task(message):
    to = message.from_user.id
    if not task_data["name"]:
        bot.send_message(chat_id=to,
                         text="Введи название задания",
                         parse_mode='HTML')
        task_data["name"] = "yes"
    else:


    if task_data["name"] == "yes":
        task_data["name"] = u'{}'.format(message.text)
        return

    if task_data["regexp"] == "no":
        bot.send_message(chat_id=to,
                         text="Введи формат ответа",
                         parse_mode='HTML')
        return
    if task_data["regexp"] == "no":
        task_data["regexp"] = u'{}'.format(message.text)
        return

    if task_data["congrats"] == "no":
        bot.send_message(chat_id=to,
                         text="Введи поздравление",
                         parse_mode='HTML')
        return
    if task_data["congrats"] == "no":
        task_data["congrats"] = u'{}'.format(message.text)
        return

    if task_data["text"] == "no":
        bot.send_message(chat_id=to,
                         text="Введи текст задания",
                         parse_mode='HTML')
        return
    if task_data["text"] == "no":
        task_data["text"] = u'{}'.format(message.text)
        return

    if not task_data["finished"]:
        bot.send_message(chat_id=to,
                         text="Скинь медиа или введи no",
                         parse_mode='HTML')
        return
    if message.text is not "no":
        res_id = ""
        if message.content_type == "photo":
            res_id = message.photo[0].file_id
            #todo: add captions hamdling
        elif message.content_type == "audio":
            res_id = message.audio[0].file_id
        elif message.content_type == "document":
            res_id = message.document[0].file_id
        task_data["resources"].append(res_id)
        return
    else:
        task_data["finished"] = True
        return
    if task_data["finished"]:
        # all data is preset
        # now we can create a task
        task_in_db = db_controller.add_task(task_data["text"], task_data["regexp"], True, task_data["name"], task_data["congrats"])
        # and then add resources to it when we will knew it's id
        i = 0


@bot.message_handler(content_types=["sticker", "pinned_message", "photo", "audio"])
def insert_resource(message):
    to = message.from_user.id
    if to == 235486635:
        res_id = ""
        if message.content_type == "photo":
            res_id = message.photo[0].file_id
        elif message.content_type == "audio":
            res_id = message.audio[0].file_id
        elif message.content_type == "document":
            res_id = message.document[0].file_id
        bot.send_message(chat_id=to, text=res_id)


@bot.message_handler(commands=['start'])
def handle_start(message):
    to = message.from_user.id
    first_name = message.from_user.first_name
    last_name = message.from_user.last_name
    username = message.from_user.username
    text = u'{}'.format(message.text)
    # check if we have a user
    user = db_controller.get_user_by_tgid(to)
    if user:
        print("we got him!")
    else:
        # add this user to database
        # todo: smh get id of the init state
        db_controller.add_user(to, first_name, last_name, username, 1)
    # prepare set of available tasks
    available_tasks = db_controller.get_all_available_tasks_for_user(to)
    if available_tasks:
        keys = makeKeyboard(available_tasks)
        bot.send_message(chat_id=to,
                         text="Доступные для решения задания",
                         reply_markup=keys,
                         parse_mode='HTML')
    else:
        bot.send_message(chat_id=to,
                         text="Ого! У меня нет больше для тебя задач!",
                         parse_mode='HTML')


@bot.message_handler(content_types=[u"text"])
def handle_text(message):
    refresh_states()
    to = message.from_user.id
    first_name = message.from_user.first_name
    last_name = message.from_user.last_name
    username = message.from_user.username
    text = u'{}'.format(message.text)
    # firstly check if it's admin
    if to == 235486635:
        keys = makeAdminKeyboard()
        bot.send_message(chat_id=to,
                         reply_markup=keys)
    # check if we have a user
    user = db_controller.get_user_by_tgid(to)
    if user:
        print("we got him!")
        # now we have to get his state to see what we should do
        # if it has _ - then it's not WELCOME
        # state_id = user.state_id
        # get state by it's id
        # state = states[state_id]
        state = user.state.name
        if state == "WELCOME":
            # it's WELCOME
            # so let's just show all the available tasks
            available_tasks = db_controller.get_all_available_tasks_for_user(to)
            if available_tasks:
                keys = makeKeyboard(available_tasks)
                bot.send_message(chat_id=to,
                                 text="Доступные для решения задания",
                                 reply_markup=keys,
                                 parse_mode='HTML')
            else:
                bot.send_message(chat_id=to,
                                 text="Ого! У меня нет больше для тебя задач!",
                                 parse_mode='HTML')
        elif state.split("_")[0] == "VIEW":
            # it's a VIEW arch, so we gotta display corresponding task
            task_id = state.split("_")[1]
            # now, find it in database
            task = db_controller.get_task_by_id(task_id)

            # we gotta check the input with validation rules

            validation = task.answer_pattern
            # todo: need to check if there is a custom rules
            if validation == "custom":
                print("it's a custom task - always true!")
            else:
                pattern = re.compile(validation.lower())
                matches = pattern.match(text.lower())
                if matches:
                    print("CORRECT!")
                    bot.send_message(chat_id=to,
                                     text=task.congrat,
                                     parse_mode='HTML')
                    # mark task as SOLVED for that specific user
                    db_controller.mark_task_as_solved_for_user(to, task_id)
                    # user can rate currently solved task
                    # show rating keyboard for currently solved task
                    rates = makeRatingKeyboard(task_id)
                    bot.send_message(chat_id=to,
                                     text="Как тебе вопрос (оцени по возрастающей шкале)?\n"
                                          "1 - Так себе, фу\n"
                                          "5 - Супер! Побольше бы таких!\n"
                                          "? - Затрудняюсь ответить",
                                     parse_mode='HTML',
                                     reply_markup=rates)
                    # todo: change exactly to WELCOME state
                    db_controller.update_user_state_by_id(to, 1)

                    # prepare set of available tasks
                    # todo: FOR USER and that are NOT SOLVED by him!
                    available_tasks = db_controller.get_all_available_tasks_for_user(to)
                    if available_tasks:
                        keys = makeKeyboard(available_tasks)
                        bot.send_message(chat_id=to,
                                         text="Доступные для решения задания",
                                         reply_markup=keys,
                                         parse_mode='HTML')
                    else:
                        bot.send_message(chat_id=to,
                                         text="Ого! У меня нет больше для тебя задач!",
                                         parse_mode='HTML')
                else:
                    print("WRONG!")
                    # display the same task
                    resources = db_controller.get_resources_for_task_id(task_id)
                    for resource in resources:
                        if resource.type == "photo":
                            bot.send_photo(chat_id=to,
                                           photo=resource.tg_id,
                                           caption=resource.caption)
                        elif resource.type == "audio":
                            bot.send_audio(chat_id=to,
                                           audio=resource.tg_id,
                                           caption=resource.caption)
                        elif resource.type == "document":
                            bot.send_document(chat_id=to,
                                              data=resource.tg_id,
                                              caption=resource.caption)
                    bot.send_message(chat_id=to,
                                     text=task.task,
                                     parse_mode='HTML')



    else:
        # add this user to database
        # todo: smh get id of the init state
        db_controller.add_user(to, first_name, last_name, username, 1)
        # prepare set of available tasks
        available_tasks = db_controller.get_all_available_tasks_for_user(to)
        keys = makeKeyboard(available_tasks)
        bot.send_message(chat_id=to,
                         text="Доступные для решения задания",
                         reply_markup=keys,
                         parse_mode='HTML')
        i = 0


@bot.callback_query_handler(func=lambda call: True)
def handle_query(call):
    refresh_states()
    if call.data.startswith("t"):
        # clicked on one of the tasks, gotta find out which one
        task_id = call.data[1:]
        # now, find it in database
        task = db_controller.get_task_by_id(task_id)
        # bot.answer_callback_query(callback_query_id=call.id,
        #                           show_alert=True,
        #                           text="Let' go!")
        # todo: in loop show all the resources for the task
        resources = db_controller.get_resources_for_task_id(task_id)
        for resource in resources:
            if resource.type == "photo":
                bot.send_photo(chat_id=call.from_user.id,
                               photo=resource.tg_id,
                               caption=resource.caption)
            elif resource.type == "audio":
                bot.send_audio(chat_id=call.from_user.id,
                               audio=resource.tg_id,
                               caption=resource.caption)
            elif resource.type == "document":
                bot.send_document(chat_id=call.from_user.id,
                                  data=resource.tg_id,
                                  caption=resource.caption)
        bot.send_message(chat_id=call.from_user.id,
                         text=task.task,
                         parse_mode='HTML')
        # and switch state for a user
        state_id = list(states.keys())[list(states.values()).index("VIEW_{id}".format(id=task_id))]
        db_controller.update_user_state_by_id(call.from_user.id, state_id)
    elif call.data.startswith("r"):
        rate_value = call.data.split("_")[0][1:]
        task_id = call.data.split("_")[1]
        # now set it to a corresponding table that user marked task
        if rate_value == "?":
            rate_value = 0
        db_controller.add_rating_for_task_from_user(rate_value, call.from_user.id, task_id)
        bot.answer_callback_query(callback_query_id=call.id,
                                  show_alert=True,
                                  text="Спасибо!")
    # process admin commands
    elif call.data.startswith("a_"):
        # get command type
        command = call.data.split("a_")[1]
        if command == "add_task":
            bot.send_message(chat_id=call.from_user.id,
                             text="Введи имя задания",
                             parse_mode='HTML')


bot.polling(none_stop=True, interval=0)
