from flask import Flask, request
import logging
import json
import random

app = Flask(__name__)

logging.basicConfig(level=logging.INFO)

# создаем словарь, в котором ключ — название города,
# а значение — массив, где перечислены id картинок,
# которые мы записали в прошлом пункте.

cities = {
    'москва': ['1030494/5a0caa7d6a1cae4efd5b',
               '1540737/9f695e569779055c1229'],
    'нью-йорк': ['1533899/e216c3fb2e6b0458e87f',
                 '1533899/143f08ed28549c84df0f'],
    'париж': ['1030494/0ffc36c53e49db9e2d70',
              '965417/92767891fbc01f798de4']
}

# создаем словарь, где для каждого пользователя
# мы будем хранить его имя
sessionStorage = {}
print('GLOBAL INIT!!!!!!!!!!!!!!!!!!!!!!!!!!!!!')


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
    # если пользователь новый, то просим его представиться.
    if req['session']['new']:
        res['response']['text'] = 'Привет! Назови свое имя!'
        # создаем словарь в который в будущем положим имя пользователя
        sessionStorage[user_id] = {
            'first_name': None,
            'game_over': False,
            'game_started': False,
            'right_city': None
        }
        return

    # если пользователь не новый, то попадаем сюда.
    # если поле имени пустое, то это говорит о том,
    # что пользователь еще не представился.
    if sessionStorage[user_id]['first_name'] is None:
        # в последнем его сообщение ищем имя.
        first_name = get_first_name(req)
        # если не нашли, то сообщаем пользователю что не расслышали.
        if first_name is None:
            res['response']['text'] = \
                'Не расслышала имя. Повтори, пожалуйста!'
        # если нашли, то приветствуем пользователя.
        # И спрашиваем какой город он хочет увидеть.
        else:
            sessionStorage[user_id]['first_name'] = first_name
            res['response'][
                'text'] = 'Приятно познакомиться, ' \
                          + first_name.title() \
                          + '. Я - Алиса. Отгадаешь город по фото?'

    else:
        if not sessionStorage[user_id]['game_over']:
            if not sessionStorage[user_id]['game_started']:
                if req['request']['original_utterance'].lower() in [
                    'да',
                    'отгадаю',
                    'ага',
                    'го',
                    'конечно',
                    'угу',
                ]:
                    sessionStorage[user_id]['right_city'] = random.choice([*cities])
                    res['response']['card'] = {}
                    res['response']['card']['type'] = 'BigImage'
                    res['response']['card']['title'] = ''
                    res['response']['card']['image_id'] = random.choice(cities[sessionStorage[user_id]['right_city']])
                    res['response']['text'] = 'Что это за город?'
                    sessionStorage[user_id]['game_started'] = True
                elif req['request']['original_utterance'].lower() in [
                    'нет',
                    'не',
                    'неа',
                    'не буду',
                    'не отгадаю',
                ]:
                    sessionStorage[user_id]['game_over'] = True
                    sessionStorage[user_id]['game_started'] = False
                else:
                    res['response']['text'] = 'Не расслышала ответ. Попробуй еще разок!'
            else:
                # ищем город в сообщение от пользователя
                city = get_city(req)
                # если этот город среди известных нам,
                # то показываем его (выбираем одну из двух картинок случайно)
                if city in cities:
                    res['response']['text'] = 'Угадал! Хочешь отгадывать дальше?'
                    sessionStorage[user_id]['game_started'] = False
                # если не нашел, то отвечает пользователю
                # 'Первый раз слышу об этом городе.'
                else:
                    res['response']['text'] = \
                        'Не угадал. Попробуй еще разок!'


def get_city(req):
    # перебираем именованные сущности
    for entity in req['request']['nlu']['entities']:
        # если тип YANDEX.GEO то пытаемся получить город(city),
        # если нет, то возвращаем None
        if entity['type'] == 'YANDEX.GEO':
            # возвращаем None, если не нашли сущности с типом YANDEX.GEO
            return entity['value'].get('city', None)


def get_first_name(req):
    # перебираем сущности
    for entity in req['request']['nlu']['entities']:
        # находим сущность с типом 'YANDEX.FIO'
        if entity['type'] == 'YANDEX.FIO':
            # Если есть сущность с ключом 'first_name',
            # то возвращаем ее значение.
            # Во всех остальных случаях возвращаем None.
            return entity['value'].get('first_name', None)


if __name__ == '__main__':
    app.run()
