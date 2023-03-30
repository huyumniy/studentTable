import mysql.connector
import requests
import re
from selenium import webdriver
from bs4 import BeautifulSoup
from selenium.webdriver.common.by import By
from aiogram import Bot, Dispatcher, executor, types

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton

bot = Bot(token='TOKEN')
dp = Dispatcher(bot)

db = mysql.connector.connect(
    host="127.0.0.1",
    user="root",
    password="PASSWORD",
    database="studentdb"
)
mycursor = db.cursor()

temp = {"photo": None, "keyboard": None, "caption": None}
telegram_id = None

def dbsave(student, group, id):
    if dbchecker(student) == False:
        mycursor.execute("INSERT INTO students (fullname) VALUES (%s)", (student,))
        db.commit()
        std_id = mycursor.lastrowid
    else:
        mycursor.execute("SELECT\
            id FROM students WHERE fullname=(%s)", (student,))
        std_id = mycursor.fetchone()[0]
    mycursor.execute("INSERT INTO web_table (web_id, student_id, groupName) VALUES (%s, %s, %s)", (id, std_id, group,))
    db.commit()


def dbchecker(fullname):
    mycursor.execute("SELECT\
         fullname FROM students WHERE fullname=(%s)", (fullname,))
    return bool (mycursor.fetchall())


def dbGetId(fullname):
    mycursor.execute("SELECT\
         id FROM students WHERE fullname=(%s)", (fullname,))
    for std_id in mycursor:
        std_inner = std_id[0]
        if len(std_id) == 0:
            return False
    mycursor.execute("SELECT\
         web_id FROM web_table WHERE student_id=(%s)", (std_inner,))
    inner_id_lst = []
    for id in mycursor:
        for inner_id in id:
            inner_id_lst.append(inner_id)
    return inner_id_lst


def dbExtractDate(web_id):
    mycursor.execute("SELECT date_time FROM web_table WHERE web_id=%s", (web_id,))
    return str(mycursor.fetchone()[0])


def dbDateRefresh(web_id):
    mycursor.execute("UPDATE web_table SET date_time = CURRENT_TIMESTAMP WHERE web_id = %s", (web_id,))
    db.commit()

def dbPhotoSave(id, photo_data):
    mycursor.execute("UPDATE web_table SET photo_data = %s WHERE web_id = %s", (photo_data, id,))
    db.commit()


def dbPhotoChecker(id):
    mycursor.execute("SELECT photo_data FROM web_table WHERE web_id=%s", (id,))
    return bool(mycursor.fetchone()[0])


def dbPhotoExtract(id):
    mycursor.execute("SELECT photo_data FROM web_table WHERE web_id=%s", (id,))
    return mycursor.fetchone()[0]


def dbGetStudentIdByTelegramId(telegram_id):
    mycursor.execute("SELECT student_id FROM telegram WHERE telegram_id=%s", (telegram_id,))
    student = mycursor.fetchone()[0]
    return student


def dbCheckTelegramIdByStudentId(student_id):
    mycursor.execute("SELECT telegram_id FROM telegram WHERE student_id=%s", (student_id,))
    return bool(mycursor.fetchone())


def dbGetTelegramIdByStudentId(student_id):
    mycursor.execute("SELECT telegram_id FROM telegram WHERE student_id=%s", (student_id,))
    return mycursor.fetchone()[0]


def dbTelegramIdSave(telegram_id, student_id):
    mycursor.execute("INSERT INTO telegram (student_id, telegram_id) VALUES (%s, %s)", (student_id, telegram_id,))
    db.commit()


def dbGetPhotoByStudentId(student_id):
    mycursor.execute("SELECT photo_data FROM web_table WHERE student_id=%s",(student_id,))
    results = mycursor.fetchall()
    return [row[0] for row in results if row[0] != None]


def dbTelegramIdCheck(id):
    mycursor.execute("SELECT telegram_id FROM telegram WHERE telegram_id=%s", (id,))
    return bool(mycursor.fetchall())


def dbDeleteRowByTelegramId(telegram_id):
    mycursor.execute("DELETE FROM telegram WHERE telegram_id=%s", (telegram_id,))
    db.commit()


def dbGetFullnameByStudentId(id):
    mycursor.execute("SELECT fullname FROM students WHERE id=%s", (id,))
    return mycursor.fetchone()[0]


def dbGetStudentIdByFullname(fullname):
    mycursor.execute("SELECT id FROM students WHERE fullname=%s", (fullname,))
    return mycursor.fetchone()[0]


def getSoup(last_name):
    url = f'http://193.189.127.179:5010/site/search-student?type=time-table&SearchStudentsForm[search]=' + last_name
    req = requests.get(url)
    try: req = requests.get(url)
    except Exception: req.raise_for_status()
    result = req.content
    soup = BeautifulSoup(result, 'html.parser')
    return soup


def PhotoSave(web_id):
    table = 'http://193.189.127.179:5010/time-table/student?id=' + str(web_id)
    option = webdriver.FirefoxOptions()
    option.add_argument("--headless")
    option.add_argument("--start-maximized")
    browser = webdriver.Firefox(options=option)
    browser.get(table)
    body = browser.find_element(By.ID, 'time-tablew6')
    body.screenshot('picture.png')
    browser.quit()
    with open('picture.png', 'rb') as f:
        photo_data = f.read()
        dbPhotoSave(web_id, photo_data)


def replyButton(fullname, textArr):
    index = 0
    keyboard = InlineKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    for el in textArr:
        button = InlineKeyboardButton(text=el[0], callback_data=(str(index) + "_" + fullname))
        keyboard.add(button)

        index += 1
    return keyboard


def InlineButton(fullname, id):       
    global telegram_id  
    ikb = InlineKeyboardMarkup(row_width=2, inline_keyboard = [
        [InlineKeyboardButton(text='📥 Оновити розклад', callback_data= str(id) + "_" + fullname + "_")],
        [InlineKeyboardButton(text="◀️ Назад", callback_data="back"), InlineKeyboardButton(text='❌ Закрити', callback_data="close")]
    ])
    if dbTelegramIdCheck(telegram_id):
        ikb.inline_keyboard.insert(1, [InlineKeyboardButton(text="✂️ Розірвати зв'язок з користувачем", callback_data="remove")])
    else:
        student_id = dbGetStudentIdByFullname(fullname)
        ikb.inline_keyboard.insert(1, [InlineKeyboardButton(text="🔗 Зберегти користувача", callback_data="save_" + str(student_id))])
    return ikb


def getGroups(fullname):
    mycursor.execute("SELECT id FROM students WHERE fullname=(%s)", (fullname,))
    id = mycursor.fetchone()[0]
    mycursor.execute("SELECT groupName FROM web_table WHERE student_id=(%s)", (id,))
    return mycursor.fetchall()


def searcher(full_name):
    last_name = full_name.split(" ")[0]             # TODO: parse fields and buttons
    soup = getSoup(last_name)                       # that change the table

    tr = soup.select('tr[data-key]')
    for row in tr:
        td = row.find_all("td")
        if td[1].text == full_name:
            student = td[1].text
            group = td[4].text
            id = td[5].find('a').get('href').split('=')[1]
            dbsave(student, group, id)


@dp.message_handler(commands=['start'])     
async def start(message: types.Message):            
    await bot.delete_message(message.chat.id, message.message_id)
    await bot.send_message(message.chat.id,
     "Введіть своє прізвище, ім'я та по батькові: ")
    

@dp.message_handler(commands=['fast_student'])
async def fast_start(message: types.Message):
    telegram_id = message.from_user.id
    if not dbTelegramIdCheck(telegram_id):
        await bot.send_message(message.chat.id,
         "Введіть своє прізвище, ім'я та по батькові: ")
    else:
        studentId = dbGetStudentIdByTelegramId(telegram_id)
        photo_lst = dbGetPhotoByStudentId(studentId)
        fullname = dbGetFullnameByStudentId(studentId)
        
        groups = getGroups(fullname)
        if len(photo_lst) > 1:
            ikbd = replyButton(fullname, groups)
            temp["keyboard"] = ikbd
            temp["caption"]= "Оберіть спеціальність:"
            await bot.send_message(chat_id=message.chat.id,
                text="Оберіть спеціальність: ", reply_markup=ikbd)
        else:
            web_id = dbGetId(fullname)
            ikb = InlineButton(fullname, 0)
            date = dbExtractDate(web_id[0])
            caption = fullname +\
            ": " + groups[0][0] + "\n" + "Остання дата оновлення: " + "<em>" + date + "</em>"
            temp["keyboard"]=ikb
            temp["caption"]= caption
            temp['photo']= photo_lst[0]
            await bot.send_photo(chat_id=message.chat.id, photo=photo_lst[0], caption=caption, reply_markup=ikb, parse_mode="HTML")


@dp.message_handler(lambda message: re.match(r'^[А-ЯІЇЄҐґЁё][а-яіїєґё]+\s+[А-ЯІЇЄҐґЁё][а-яіїєґё]+\s+[А-ЯІЇЄҐґЁё][а-яіїєґё]+$', message.text))
async def receive(message: types.Message):
    global telegram_id
    message_text = message.text
    chat_id = message.chat.id
    temp["photo"] = None
    await bot.delete_message(chat_id, message.message_id)
    fullname = dbchecker(message_text)
    if fullname == False:
        searcher(message_text)
    id = dbGetId(message_text)
    telegram_id = message.from_user.id
    groupLst = getGroups(message_text)
    if len(groupLst) > 1:
        ikbd = replyButton(message_text, groupLst)
        temp["keyboard"] = ikbd
        temp["caption"]= "Оберіть спеціальність:"
        await bot.send_message(chat_id=chat_id,
             text="Оберіть спеціальність:", reply_markup=ikbd)
    else:
        ikb = InlineButton(message_text, 0)
        if not dbPhotoChecker(id[0]):
            await bot.send_message(chat_id, 'Зачекайте будь ласка...')
            PhotoSave(id[0])
        photo = dbPhotoExtract(id[0])
        date = dbExtractDate(id[0])
        caption = message.text +\
        ": " + groupLst[0][0] + "\n" + "Остання дата оновлення: " + "<em>" + date + "</em>"
        temp["keyboard"]=ikb
        temp["caption"]= caption
        temp['photo']=photo
        await bot.send_photo(chat_id=chat_id, caption=caption, 
        photo=photo, reply_markup=ikb, parse_mode="HTML")


@dp.callback_query_handler(lambda callback_query: callback_query.data.startswith('close'))
async def callback_exit(callback: types.CallbackQuery):
    chat_id = callback.message.chat.id
    await bot.delete_message(chat_id=chat_id, message_id=callback.message.message_id)


@dp.callback_query_handler(lambda callback_query: callback_query.data.startswith('back'))
async def callback_back(callback: types.CallbackQuery):
    chat_id = callback.message.chat.id
    await bot.delete_message(chat_id=chat_id, message_id=callback.message.message_id)
    if temp["photo"] != None:
        await bot.send_photo(chat_id=chat_id, photo=temp["photo"], caption=temp["caption"], reply_markup=temp["keyboard"], parse_mode="HTML")
    else:
        await bot.send_message(chat_id=chat_id, text=temp["caption"], reply_markup=temp["keyboard"], parse_mode="HTML")


@dp.callback_query_handler(lambda callback_query: callback_query.data.startswith('remove'))
async def callback_db_remove(callback: types.CallbackQuery):
    global telegram_id
    dbDeleteRowByTelegramId(telegram_id)
    await callback.answer("Ваші дані були успішно видалені")


@dp.callback_query_handler(lambda callback_query: callback_query.data.startswith('save'))
async def callback_db_save(callback: types.CallbackQuery):
    global telegram_id
    student_id = int(callback.data.split("_")[1])
    if not dbTelegramIdCheck(telegram_id):
        dbTelegramIdSave(telegram_id, student_id)
        await callback.answer("Ваші дані були успішно збережені")
    else:
        await callback.answer("Ваші дані вже збережені")


@dp.callback_query_handler()  
async def callback_data(callback: types.CallbackQuery):
    chat_id = callback.message["chat"]["id"]
    message_id = callback.message["message_id"]
    if not callback.message.photo:
        await bot.edit_message_text(chat_id=chat_id, message_id=message_id, text="Зачекайте будь ласка...")
    await bot.delete_message(chat_id=chat_id, message_id=message_id)
    index = int(callback.data.split("_")[0])
    fullname = callback.data.split("_")[1]
    web_id = dbGetId(fullname)[index]
    if callback.data.endswith("_") or not dbPhotoChecker(web_id):
        dbDateRefresh(web_id)
        PhotoSave(web_id)
    photo = dbPhotoExtract(web_id)
    date = dbExtractDate(web_id)
    ikb = InlineButton(fullname, index)
    group = getGroups(fullname)[index][0]
    await bot.send_photo(chat_id=chat_id,
    caption=fullname + ": " + group  + "\n" + "Остання дата оновлення: "
    + "<em>" + date + "</em>",
    photo=photo, reply_markup=ikb, parse_mode="HTML")


if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
