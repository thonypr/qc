import requests
import json
import urllib.parse

bot_token = "1047244780:AAHzWh6dK8N2vB977Yk1TLgXcs9yjv6LX2k"


def debug(tg_id, name, last_name, nickname, text):
    import requests

    url = "https://api.telegram.org/bot{token}/sendMessage".format(token=bot_token)

    message = u'id={id}\nname={name}\nlast_name={last_name}\nnickname={nickname}\n\n' \
              u'says - {text}'.format(id=tg_id, name=name, last_name=last_name, nickname=nickname, text=text)

    message_encoded = urllib.parse.quote(message)

    payload = 'chat_id={chat_id}&text={message}'.format(chat_id=tg_id, message=message_encoded)
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded'
    }

    response = requests.request("POST", url, headers=headers, data=payload)

    print(response.text.encode('utf8'))
