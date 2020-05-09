from flask import Flask, request
import logging
import json
import re
import requests

app = Flask(__name__)

logging.basicConfig(level=logging.INFO)


YA_TRANSLATE_API_KEY = "trnsl.1.1.20200412T174232Z.82b140a82ba53672.c1410c1fe31826712984fbd80ebca505df79f428"

sessionStorage = {}


@app.route('/post', methods=['POST'])
def main():
    logging.info(f'Request: {request.json!r}')
    response = {
        'session': request.json['session'],
        'version': request.json['version'],
        'response': {
            'end_session': False
        }
    }
    handle_dialog(response, request.json)
    logging.info(f'Response: {response!r}')
    return json.dumps(response)


def handle_dialog(res, req):
    user_id = req['session']['user_id']
    if req['session']['new']:
        res['response']['text'] = 'Привет! Я могу переводить русские слова в английские!'
        sessionStorage[user_id] = {}
        return

    if re.match(r"переведи(те)? слово:? *", req['request']['original_utterance'].lower()):
        word = re.sub(r"переведи(те)? слово:? *", "", req['request']['original_utterance'].lower())
        if not word:
            res['response']['text'] = 'Не указано слово, которое нужно перевести!'
        else:
            TRANSLATE_SERVER = "https://translate.yandex.net/api/v1.5/tr.json/translate"
            translate_options = {"key": YA_TRANSLATE_API_KEY,
                                 "text": word,
                                 "lang": "ru-en"}
            try:
                result = requests.get(TRANSLATE_SERVER, params=translate_options).json()
            except BaseException as e:
                res['response']['text'] = f"Не удалось перевести по причине: {e}"
                return
            res['response']['text'] = result["text"][0]
    else:
        res['response']['text'] = 'Неправильный формат ввода, пишите «Переведите (переведи) слово: *слово*»'


if __name__ == '__main__':
    app.run()
