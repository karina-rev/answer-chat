import re
import eli5
import random
import config
import utils

from eli5 import formatters
from pymystem3 import Mystem
from nltk.corpus import stopwords

ADVICES_FOR_NORM_TARGET = ['добавить вежливое приветствие - доброе утро/день/вечер!',
                           'добавить слова с позитивным окрасом - хороший, добрый, замечательный, прекрасный',
                           'поговорить про внутренний мир человека',
                           'ответить с философской точки зрения - про человека, душу, жизнь',
                           'поговорить про любовь, надежду и чувства',
                           'посмотреть на ситуацию с физиологической точки зрения. Как, по-вашему мнению, работает в '
                           'данном случае мозг и тело?',
                           'рассказать про Ваш опыт и обстоятельства',
                           'дать совет. Что нужно/необходимо/важно/обязательно сделать в данном случае?',
                           'если это уместно, рассказать про долг и правила. Что правильно сделать в данном случае?']

HREF_WORDS = ['href', 'nofollow', 'rel', '_blank', 'target', 'https', 'www', 'http', 'com', 'youtube', 'youtu', 'be']
IMG_WORDS = ['img', 'src', 'imgsmail', 'data', 'gif', 'big', 'jpg', 'download', 'otvet']
VIDEO_WORDS = ['amp', 'video']
ALL_STOPWORDS = stopwords.words('russian') + [
    'это', 'наш', 'тыс', 'млн', 'млрд', 'также', 'т', 'д',
    'который', 'прошлый', 'сей', 'свой', 'наш', 'мочь', 'такой', 'очень'
]

NUM_ADVICES_FOR_NORM = 5
RU_WORDS = re.compile("[А-Яа-я]+")
WORDS = re.compile("(\w+)")
M = Mystem()

MODEL = utils.get_pickle_file(config.path_to_model)
TFIDF = utils.get_pickle_file(config.path_to_tfidf)


def only_words(text):
    """
    Удаление лишних символов, в тексте остаются только слова
    """
    return " ".join(WORDS.findall(text))


def lemmatize(text):
    """
    Лемматизация текста
    """
    try:
        return "".join(M.lemmatize(text)).strip()
    except:
        return " "


def remove_stopwords(text, stopwords=ALL_STOPWORDS):
    """
    Удаление стоп-слов
    """
    try:
        return " ".join([token for token in text.split() if not token in stopwords])
    except:
        return ""


def preprocess(text):
    """
    Обработка текста (лемматизация + удаление стоп-слов)
    """
    return remove_stopwords(lemmatize(only_words(text.lower())))


def explore_answer(answer, num_advices_for_norm=NUM_ADVICES_FOR_NORM):
    """
    Анализ ответа и формирование рекомендаций
    :param num_advices_for_norm: количество общих рекомендаций для вывода, 5 по умолчанию
    :param answer: ответ в формате строки
    :return: список советов, если ответ классифицирован как обычный или удаленный
    """
    advices = []

    preprocessed_answer = preprocess(answer)
    target = answer_target(preprocessed_answer)

    if target == 0:
        advices.append('У Вас самый лучший ответ!')
        return advices

    eli = formatters.format_as_dict(eli5.sklearn.explain_prediction.explain_prediction_tree_classifier(
        MODEL, preprocessed_answer, vec=TFIDF))

    if target == 2:
        advices = advices_for_bad_answers(eli)
        advices = advices + random.sample(ADVICES_FOR_NORM_TARGET, num_advices_for_norm)

    if target == 1:
        advices = random.sample(ADVICES_FOR_NORM_TARGET, num_advices_for_norm)

    return advices


def answer_target(answer):
    """
    :param answer: текст ответа в форме строки
    :return: номер предсказанного класса
    """
    return MODEL.predict(TFIDF.transform([answer]))[0]


def advices_for_bad_answers(eli):
    """
    Анализ ответа, который классифицирован как удаленный, и формирование для него рекомендаций
    :param eli: DataFrame, созданный из объекта eli5.base.Explanation для текущего ответа
    :return: список советов для ответа с классом удаленный
    """

    advices = []
    features = []

    eli = eli['targets'][2]['feature_weights']['pos']
    for item in sorted(eli, key=lambda x: x['weight'], reverse=True):
        if (item['weight'] > 0.001) & (item['feature'] != '<BIAS>'):
            features.append(item['feature'])

    for href_word in HREF_WORDS:
        if any(href_word in feature for feature in features):
            advices.append('убрать ссылки из вашего сообщения.')
            break

    for img_word in IMG_WORDS:
        if any(img_word in feature for feature in features):
            advices.append('убрать изображение из вашего сообщения.')
            break

    for video_word in VIDEO_WORDS:
        if any(video_word in feature for feature in features):
            advices.append('убрать видео из вашего сообщения.')
            break

    bad_words = [feature for feature in features if (RU_WORDS.match(feature))]

    if bad_words:
        advices.append(f'убрать или заменить следующие слова: {(", ").join([word for word in bad_words])}')

    return advices
