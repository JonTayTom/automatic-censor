from config import TOKEN
from aiogram import Bot, types
from aiogram.dispatcher import Dispatcher
from aiogram.utils import executor

from string import punctuation
import Levenshtein as Lev
import json
import pymorphy2


bot = Bot(token=TOKEN)
dp = Dispatcher(bot)


morph = pymorphy2.MorphAnalyzer()


@dp.message_handler(commands=['start'])
async def process_start_command(message: types.Message):
    await message.reply("Привет!\nЯ готов!")


@dp.message_handler()  # commands='mend'
async def process_mend_command(message: types.Message):

    with open('forb_words.json', encoding='utf-8') as frb_wds:
        forbidden_words = json.load(frb_wds)

    def transformator(dict_word, text_word):  # согласование по падежу
        mot1 = morph.parse(dict_word)[0]  # берем слово из словаря
        mot2 = morph.parse(text_word)[0]  # берем слово из предложения
        mot1 = mot1.inflect({mot2.tag.number, mot2.tag.case}).word
        return mot1

    def dist_Lev(a, b):  # расстояние Левенштейна
        dist = Lev.distance(a, b)
        return dist

    def without_punct(segment):  # дезинфекция от знаков препинания
        random_1 = ''
        for symbol in segment:
            if symbol not in punctuation:
                random_1 += symbol
        return random_1

    def if_capital(com, term, mot, flag):  # проверяем, писалось ли слово с заглавной буквы
        if flag:
            return com + mot.capitalize() + term
        else:
            return com + mot + term

    def test_validity(parole):  # пытаемся распознать непонятное слово
        for juron in forbidden_words.keys():
            juron = juron.lower()
            for i in range(len(parole)):
                fragment = parole[i:i + len(parole)]
                if dist_Lev(fragment, juron) <= len(juron) * 0.25:
                    return juron
                else:
                    return parole

    text = message.text.strip().split()
    phrase_out = []
    bad_words_count = 0

    for text_word in text:
        capital = False  # заглавная/строчная - автоматом на строчную
        gob = True  # good or bad - нецензурное слово / обычное, когда что печатать - автоматом на 'good'
        group1, group2 = "", ""  # знаки препинания до и после
        if text_word[0] in punctuation:  # проверка на знаки препинания в начале слова
            group1 = text_word[0]
        if text_word[-1] in punctuation:  # проверка на знаки препинания в конце слова
            group2 = text_word[-1]
        processed_word = without_punct(text_word)  # очистка от знаков препинания
        if processed_word[0].isupper():  # заглавная или строчная буква
            capital = True
        processed_word = test_validity(processed_word.lower())  # пытаемся распознать непонятные слова
        for b_w_key in forbidden_words.keys():  # проходимся по нашему словарю
            form_1 = morph.parse(processed_word.upper())[0].normal_form  # берем начальную форму
            form_2 = morph.parse(b_w_key)[0].normal_form  # то же самое
            if dist_Lev(form_1, form_2) <= len(form_2) * 0.25:  # не совсем понятно почему, но без нее не работает!!!
                if '#' not in forbidden_words[b_w_key]:
                    x1 = transformator(forbidden_words[b_w_key], processed_word.upper())  # если не мат, то согласуем замену
                else:
                    x1 = forbidden_words[b_w_key]  # если мат, то заменяем решётками из словаря
                phrase_out.append(if_capital(group1, group2, x1, capital))
                bad_words_count += 1
                gob = False  # слово ненормативное, мы его напечатали сразу выше
                break  # если мы нашли это слово в словаре, больше не нужно по нему проходиться
        if gob:  # если нормативное, то печатаем как оно было
            phrase_out.append(if_capital(group1, group2, processed_word, capital))
        else:
            gob = True  # иначе изменяем флаг и идём далее
    if bad_words_count != 0:
        await message.reply(f"Готово! Вот цензурированный текст: {' '.join(phrase_out)}\nЗаменено слов: {bad_words_count}")
        await message.delete()
    else:
        await message.reply("Матов не найдено. Всё хорошо!")

if __name__ == '__main__':
    executor.start_polling(dp)
    
