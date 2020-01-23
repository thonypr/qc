import os
import re

import telebot

from telebot import types

from sqlalchemy import inspect

from bot_debugger import debug
from db_controller import db_controller


def object_as_dict(obj):
    return {c.key: getattr(obj, c.key)
            for c in inspect(obj).mapper.column_attrs}


token = os.environ['TELEGRAM_TOKEN']
bot = telebot.TeleBot(token)
# If you use redis, install this add-on https://elements.heroku.com/addons/heroku-redis
# r = redis.from_url(os.environ.get("REDIS_URL"))

bot.send_message(chat_id=235486635,
                 text="Перезапуск...",
                 parse_mode='HTML')
states = {}


def refresh_states():
    states_db = db_controller.get_all_states()
    for row in states_db:
        # states[u'{}'.format(object_as_dict(row)['id'])] = object_as_dict(row)['name']
        states[object_as_dict(row)['id']] = object_as_dict(row)['name']


# states = {int(k):int(v) for k,v in states.items()}
#       Your bot code below

def makeTaskKeyboard():
    markup = types.InlineKeyboardMarkup()

    list = ["Узнать ответ"]
    if list:
        for item in list:
            markup.add(types.InlineKeyboardButton(text=item,
                                                  callback_data="answer"))

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

    list = [{"code": 1, "text": "1"},
            {"code": 2, "text": "2"},
            {"code": 3, "text": "3"},
            {"code": 4, "text": "4"},
            {"code": 5, "text": "5"},
            {"code": 0, "text": "Затрудняюсь оценить"}]

    for item in list:
        markup.add(types.InlineKeyboardButton(text=item["text"],
                                              callback_data="r{id}_{task_id}".format(id=item["code"], task_id=task_id)))

    return markup


task_name = ""
task_descr = ""
task_reg = ""
task_congrat = ""
task_res = []
answ_res = []
task_finished = False
new_task_id = 0

add_task_state = 1

editors_ids = [
    235486635,
    78364174,
    231430952,
    105645437
]


@bot.message_handler(func=lambda msg: msg.from_user.id in editors_ids and msg.text == "clear")
def clear(message):
    to = message.from_user.id
    global task_name
    global task_descr
    global task_reg
    global task_congrat
    global task_res
    global answ_res
    global task_finished
    global new_task_id
    task_name = ""
    task_descr = ""
    task_reg = ""
    task_congrat = ""
    task_res = []
    answ_res = []
    task_finished = False
    new_task_id = 0
    bot.send_message(to, "Очищено!")


@bot.message_handler(func=lambda msg: msg.from_user.id in editors_ids and msg.text == "show")
def show(message):
    to = message.from_user.id
    available_tasks = db_controller.get_all_tasks()
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


@bot.message_handler(func=lambda msg: msg.from_user.id in editors_ids and msg.text == "add")
def add_task(message):
    to = message.from_user.id
    bot.send_message(to, "Введи название таски")
    bot.register_next_step_handler(message, get_name)


def get_name(message):
    if message.text != "clear":
        global task_name
        task_name = message.text
        bot.send_message(message.from_user.id, 'Укажи текст задания')
        bot.register_next_step_handler(message, get_descr)
    else:
        bot.register_next_step_handler(message, clear)


def get_descr(message):
    if message.text != "clear":
        global task_descr
        task_descr = message.text
        bot.send_message(message.from_user.id, 'Укажи регулярку под ответ \n'
                                               '(обычно просто слово или фраза, являющаяся ответом)')
        bot.register_next_step_handler(message, get_regex)
    else:
        bot.register_next_step_handler(message, clear)


def get_regex(message):
    if message.text != "clear":
        global task_reg
        task_reg = message.text
        bot.send_message(message.from_user.id, 'Укажи комментарий для задания')
        bot.register_next_step_handler(message, get_congrat)
    else:
        bot.register_next_step_handler(message, clear)


def get_congrat(message):
    if message.text != "clear":
        global task_congrat
        task_congrat = message.text
        bot.send_message(message.from_user.id, 'Скинь ресурсы под задание или напиши no')
        bot.register_next_step_handler(message, get_resource)
    else:
        bot.register_next_step_handler(message, clear)


def get_resource(message):
    if message.text != "clear":
        global task_res
        global new_task_id
        res_id = ""
        res_type = ""
        res_caption = ""
        if message.content_type == "text" and message.text == "no":
            # we need to actually add task now to database
            task_in_db = db_controller.add_task(task_descr, task_reg, True, task_name, task_congrat)
            new_task_id = task_in_db.id
            db_controller.add_state("VIEW_{id}".format(id=task_in_db.id))
            # add resources
            for res in task_res:
                resource_in_db = db_controller.add_resource(res["res_id"], res["res_type"], task_in_db.id,
                                                            res["res_caption"])
                bot.send_message(message.from_user.id, 'Ресурс {id} добавлен!'.format(id=res["res_id"]))
            bot.send_message(message.from_user.id, 'Скинь ресурсы ответа на задание или напиши no')
            task_res = []
            bot.register_next_step_handler(message, get_answer_resources)
        else:
            if message.content_type == "photo":
                res_id = message.photo[0].file_id
                res_type = "photo"
                res_caption = message.caption
            elif message.content_type == "audio":
                res_id = message.audio[0].file_id
                res_type = "audio"
                res_caption = message.caption
            elif message.content_type == "document":
                res_id = message.document.file_id
                res_type = "document"
                res_caption = message.caption
            res_item = {"res_id": res_id, "res_type": res_type, "res_caption": res_caption}

            task_res.append(res_item)
            bot.send_message(message.from_user.id, 'Скинь ресурсы под задание или напиши no')
            bot.register_next_step_handler(message, get_resource)
    else:
        bot.register_next_step_handler(message, clear)


def get_answer_resources(message):
    if message.text != "clear":
        global answ_res
        global new_task_id

        res_id = ""
        res_type = ""
        res_caption = ""
        if message.content_type == "text" and message.text == "no":
            # add resources to answers
            for res in answ_res:
                resource_in_db = db_controller.add_answer_resource(res["res_id"], res["res_type"], new_task_id,
                                                                   res["res_caption"])
                bot.send_message(message.from_user.id, 'Ресурс {id} добавлен!'.format(id=res["res_id"]))
            answ_res = []
            bot.send_message(message.from_user.id, 'Задание добавлено!')
            users_to_notify = db_controller.get_all_users()
            for useritem in users_to_notify:
                bot.send_message(useritem.tg_id, 'Добавлено новое задание!')

            return
        else:
            if message.content_type == "photo":
                res_id = message.photo[0].file_id
                res_type = "photo"
                res_caption = message.caption
            elif message.content_type == "audio":
                res_id = message.audio[0].file_id
                res_type = "audio"
                res_caption = message.caption
            elif message.content_type == "document":
                res_id = message.document.file_id
                res_type = "document"
                res_caption = message.caption
            res_item = {"res_id": res_id, "res_type": res_type, "res_caption": res_caption}

            answ_res.append(res_item)
            bot.send_message(message.from_user.id, 'Скинь ресурсы ответа под задание или напиши no')
            bot.register_next_step_handler(message, get_answer_resources)
    else:
        bot.register_next_step_handler(message, clear)


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
        debug(to, first_name, last_name, username, "Started!")
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

            debug(to, first_name, last_name,
                  username, "@{login} says {text} for a {task_name}"
                  .format(login=username, text=message.text, task_name=task.name))
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
                    resources_answer = db_controller.get_resources_answer_for_task_id(task_id)
                    for resource in resources_answer:
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
                    # mark task as SOLVED for that specific user
                    db_controller.mark_task_as_solved_for_user(to, task_id)
                    debug(to, first_name, last_name, username,
                          "@{login} solved {task_name}".format(login=username, task_name=task.name))
                    # user can rate currently solved task
                    # show rating keyboard for currently solved task
                    rates = makeRatingKeyboard(task_id)
                    bot.send_message(chat_id=to,
                                     text="Как тебе вопрос (оцени по возрастающей шкале)?",
                                     parse_mode='HTML',
                                     reply_markup=rates)
                    # todo: change exactly to WELCOME state
                    db_controller.update_user_state_by_id(to, 1)

                    # prepare set of available tasks
                    # todo: FOR USER and that are NOT SOLVED by him!
                    available_tasks = db_controller.get_all_available_tasks_for_user(to)
                    if available_tasks:
                        # keys = makeKeyboard(available_tasks)
                        bot.send_message(chat_id=to,
                                         text="Для просмотра доступных заданий жми /start",
                                         # reply_markup=keys,
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
                                     reply_markup=makeTaskKeyboard(),
                                     parse_mode='HTML')
                    bot.send_message(chat_id=to,
                                     text="Для просмотра доступных заданий жми /start",
                                     # reply_markup=keys,
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
                         reply_markup=makeTaskKeyboard(),
                         parse_mode='HTML')
        bot.send_message(chat_id=call.from_user.id,
                         text="Для просмотра доступных заданий жми /start",
                         # reply_markup=keys,
                         parse_mode='HTML')
        # and switch state for a user
        state_id = list(states.keys())[list(states.values()).index("VIEW_{id}".format(id=task_id))]
        db_controller.update_user_state_by_id(call.from_user.id, state_id)
        # change it's text to avoid double clicking
        bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,
                              text="Для возврата к списку заданий жми /start")
    elif call.data.startswith("r"):
        rate_value = call.data.split("_")[0][1:]
        task_id = call.data.split("_")[1]
        # now set it to a corresponding table that user marked task
        # if rate_value == "?":
        #     rate_value = 0
        db_controller.add_rating_for_task_from_user(rate_value, call.from_user.id, task_id)
        # bot.answer_callback_query(callback_query_id=call.id,
        #                           show_alert=True,
        #                           text="Спасибо!")
        bot.answer_callback_query(callback_query_id=call.id, show_alert=False, text="Спасибо!")
        bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,
                              text="Оценено задание {task} в {rate}".format(
                                  task=task_id,
                                  rate=rate_value
                              ))
    # process admin commands
    elif call.data.startswith("a_"):
        # get command type
        command = call.data.split("a_")[1]
        if command == "add_task":
            bot.send_message(chat_id=call.from_user.id,
                             text="Введи имя задания",
                             parse_mode='HTML')
    elif call.data == "answer":
        state_id = db_controller.get_user_by_tgid(call.from_user.id).state_id
        state = db_controller.get_state_by_id(state_id).name
        task_id = state.split("_")[1]
        task = db_controller.get_task_by_id(task_id)

        to = call.from_user.id
        first_name = call.from_user.first_name
        last_name = call.from_user.last_name
        username = call.from_user.username
        debug(to, first_name, last_name,
              username, "@{login} cheated on {task_name}"
              .format(login=call.from_user.username, task_name=task.name))
        print("CORRECT!")
        bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,
                              text="Ответ:")
        bot.send_message(chat_id=call.from_user.id,
                         text=task.congrat,
                         parse_mode='HTML')
        resources_answer = db_controller.get_resources_answer_for_task_id(task_id)
        for resource in resources_answer:
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
        # mark task as SOLVED for that specific user
        db_controller.mark_task_as_solved_for_user(call.from_user.id, task_id)
        # user can rate currently solved task
        # show rating keyboard for currently solved task
        rates = makeRatingKeyboard(task_id)
        bot.send_message(chat_id=call.from_user.id,
                         text="Как тебе вопрос?",
                         parse_mode='HTML',
                         reply_markup=rates)
        # todo: change exactly to WELCOME state
        db_controller.update_user_state_by_id(call.from_user.id, 1)

        # prepare set of available tasks
        # todo: FOR USER and that are NOT SOLVED by him!
        available_tasks = db_controller.get_all_available_tasks_for_user(call.from_user.id)
        if available_tasks:
            # keys = makeKeyboard(available_tasks)
            bot.send_message(chat_id=call.from_user.id,
                             text="Для просмотра доступных заданий жми /start",
                             # reply_markup=keys,
                             parse_mode='HTML')
        else:
            bot.send_message(chat_id=call.from_user.id,
                             text="Ого! У меня нет больше для тебя задач!",
                             parse_mode='HTML')


bot.polling(none_stop=True, interval=0)
