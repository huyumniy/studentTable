import json
import requests
from os.path import exists
from selenium import webdriver
from bs4 import BeautifulSoup
from selenium.webdriver.common.by import By
from aiogram import Bot, Dispatcher, executor, types


bot = Bot(token="5385147452:AAEQHoHBmcQnsrQLy7Ikw1bDztuSAcq4T9w")
dp = Dispatcher(bot)


def creator(data):
    with open('data.json', 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4, ensure_ascii=False)


def replacer(key):
    if ' ' in key:
        x = key.replace(' ', '_')
    return x


def values():
    if exists('data.json'):
        with open('data.json', 'r', encoding='utf-8') as f:
            lst = []
            file = json.load(f)
            for k in file.keys():
                lst.append(k)
        return lst


def searcher(last_name):
    index = 1
    index1 = 0
    url = f'http://193.189.127.179:5010/site/search-student?type=time-table&SearchStudentsForm%5Bsearch%5D=' + last_name
    req = requests.get(url)
    try:
        req.raise_for_status()
    except Exception as exc:
        print('There was a problem:\n%s' % exc)
        quit()
    result = req.content
    dictionary = {}
    soup = BeautifulSoup(result, 'lxml')
    students = soup.find('table', class_='table table-bordered table-hover table-sm').find('tbody').find_all('td')
    hrefs = soup.find('table', class_='table table-bordered table-hover table-sm').find('tbody').find_all('a')
    border = len(soup.find('table', class_='table table-bordered table-hover table-sm').find('tbody').find_all('a'))
    for i in range(1, border + 1):
        dictionary[replacer(students[index].text)] = hrefs[index1].get('href').split('?')[1]
        index += 6
        index1 += 1    
    if exists('data.json'):
        with open('data.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
            data.update(dictionary)
            creator(data)
    else:
        with open('data.json', 'w', encoding='utf-8') as f:
            json.dump(dictionary, f, indent=4, ensure_ascii=False)
    return dictionary

    
@dp.message_handler(commands=['start', 'help'])
async def start(message: types.Message):
    await bot.send_message(message.chat.id, 'Введіть своє прізвище')


if exists('data.json'):
    @dp.message_handler(commands=values())
    async def start(message: types.Message):
        with open('data.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
            for k, v in data.items():    
                if k.lower() == message.text.split('/')[1].lower():
                    await bot.send_message(message.chat.id, 'Зачекайте будь ласка, обробляю фото...')
                    table = 'http://193.189.127.179:5010/time-table/student?' + v
                    option = webdriver.FirefoxOptions()
                    option.add_argument("--headless")
                    option.add_argument("--disable-dev-shm-usage")
                    option.add_argument("--no-sandbox")
                    browser = webdriver.Firefox(executable_path='geckodriver.exe', options=option)
                    browser.get(table)
                    body = browser.find_element(By.ID, 'time-tablew6')
                    body.screenshot('picture.png')
                    browser.quit()
                    photo = open('picture.png', 'rb')
                    await bot.send_photo(message.chat.id, photo)



@dp.message_handler()
async def receive(message: types.Message):
    if exists('data.json'):
        with open('data.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
            markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
            for k in data.keys():
                if message.text.lower() in k.lower():
                    markup.add(types.KeyboardButton('/' + k))
            else:
                searcher(message.text)
    else:
        searcher(message.text)
    try:
        await bot.send_message(message.chat.id, 'Оберіть свого героя', parse_mode='html', reply_markup=markup)
    except:
        await bot.send_message(message.chat.id, 'База оновлена! Введіть знову ваше прізвище')


if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
