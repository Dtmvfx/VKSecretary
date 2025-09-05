import os
import random
import sys
from datetime import datetime
from time import sleep
import time
from PySide6.QtCore import Qt, Signal, QObject, QThread
from PySide6.QtWidgets import QApplication, QWidget, QVBoxLayout, QCheckBox, QPushButton, QTextEdit, QSplitter, QGroupBox, QSizePolicy, QLineEdit
from patchright.sync_api import sync_playwright
#-----------------------------------------------------------------------------------------------------------------------
id_account = ''; worker_thread = None
with open('stop_words.txt', 'r', encoding='utf-8') as f: stop_words: list[str] = f.read().split(',')
#-----------------------------------------------------------------------------------------------------------------------
def page_goto(page, url, signals, wait_until='load'):
    try: page.goto(url, timeout=180000)
    except Exception:
        for i in range(2):
            try: page.reload()
            except Exception:
                if i == 4: signals.log_signal.emit(f'!ЗАВИСАНИЕ СТРАНИЦЫ! Адрес: [{url}] недоступен длительное время. Перезапусти при необходимости неотработанные функции позже.')
                continue
            break

#-----------------------------------------------------------------------------------------------------------------------
def start_vk(page, signals):
    try:
        global id_account
        page_goto(page, 'https://vk.ru', signals)
        signals.log_signal.emit(f'У ВАС 3 МИНУТЫ НА ВХОД ПО QR-коду')
        page.wait_for_selector('//*[text()="Профиль"]', timeout=180000)
        if page.locator('//*[@aria-label="Закрыть"]').is_visible(): page.click('//*[@aria-label="Закрыть"]')
        page.click('//*[text()="Профиль"]')
        id_account = page.locator('//li[@id="l_pr"]/a[@href]').get_attribute('href')
        signals.log_signal.emit(f'\n<<<<<<<<<<<<<<<<<<<<<<<<< СТАРТ ОСНОВНОГО АККАУНТА ВК // id: {id_account} >>>>>>>>>>>>>>>>>>>>>\n\n')
    except Exception as e: signals.log_signal.emit(f'!КРИТИЧЕСКАЯ ОШИБКА!: НЕ УДАЛСЯ СТАРТ ВК // {e}\n\n')

def liking_vk(page, signals):
    stories = 0; posts = 0
    try:
        signals.log_signal.emit('\n~~~~~~~~~~~~~~~~~~~~~~ ЛАЙКИНГ [ВК] ~~~~~~~~~~~~~~~~~~~~~~\n')
        name_my_community = line_edit.text()
        if name_my_community: group_for_like_list = [f'https://vk.ru{id_account}', name_my_community]
        else: group_for_like_list = [f'https://vk.ru{id_account}']

        for group in group_for_like_list:
            page_goto(page, group, signals)
            page.evaluate("window.scrollBy(0, 3000)"); sleep(3)
            for post_number in range (5):
                try: page.locator('//a[@class="notifier_close_wrap"]').first.click(timeout=1000)
                except Exception: pass
                el = page.locator('//*[@class ="_post_content"]').nth(post_number)
                el_html = el.inner_html()
                if 'class="PostButtonReactions__icon "' in el_html:
                    page.locator('//div[@class="PostButtonReactions__icon "]').first.click()
                    page.locator('//*[@title="Поделиться"]').nth(post_number).click()
                    page.get_by_placeholder("Введите имя получателя или название чата").press_sequentially('мои репосты', delay=100)
                    if page.get_by_test_id("box_layout").get_by_text("мои репосты").count() > 0:
                       page.get_by_test_id("box_layout").get_by_text("мои репосты").click()
                       page.click('//*[@id="like_share_send"]')
                    else: page.click('//*[@aria-label="Закрыть"][not (@data-testid)]')
        signals.log_signal.emit('Мои группы/профили ВК: полайкано и отрепощено')
        page_goto(page, 'https://vk.ru', signals); sleep(10)
        page.get_by_test_id('story_card_stories').nth(2).click()
        if page.locator('//div[@class="stories_volume_control high"]').count()>0: page.click('//div[@class="stories_volume_control high"]')
        for stories in range(51):
            box = page.get_by_test_id('story_like_button').bounding_box()
            page.get_by_test_id('story_like_button').click(delay=1500)
            page.mouse.click(box["x"] + 200, box["y"])
        page.locator('//*[@class="stories_layer_close"]').click()
        page_goto(page, 'https://vk.ru', signals)
        for posts in range (151):
            page.mouse.wheel(0, 1400); page.hover('(//div[@class="PostButtonReactions__icon "])[1]')
            page.keyboard.press('ArrowUp'); page.keyboard.press('ArrowUp')
            page.locator('(//div[@class="PostButtonReactions__icon "])[1]').click() #250 likes posts
        signals.log_signal.emit(f'Контент ВК: Отлайкано {stories} историй и {posts} постов\n')
    except  Exception: signals.log_signal.emit(f'Контент ВК: Отлайкано {stories} историй и {posts} постов\n')

#-----------------------------------------------------------------------------------------------------------------------
def dell_out_requests_api_web_vk(page, signals):
    try:
        signals.log_signal.emit(f'\n~~~~~~~~~~~~~~~~~~~~~~ УДАЛЯЕМ ИСХОДЯЩИЕ ЗАЯВКИ В ДРУЗЬЯ И ПОДПИСКИ [ВК] ~~~~~~~~~~~~~~~~~~~~~~\n')
        dell_out_request = 0
        page_goto(page, 'https://vk.ru/friends?section=out_requests', signals, wait_until='domcontentloaded')
        for _ in range(5): page.mouse.wheel(0, 99999)
        for element in  page.locator('//*[text()="Отменить заявку" or text()="Отписаться"]').element_handles():
            element.click(); dell_out_request += 1
        signals.log_signal.emit(f' Из id: {id_account} удалено [{dell_out_request}] исходяшек. Прощайте!\n')
    except Exception as e: signals.log_signal.emit(f'\n!!!!!ЧТО-ТО СЛОМАЛОСЬ В УДАЛЯШКЕ ИСХОДЯШЕК [ВК]!!!!! // ошибка: {e}\n')

# ----------------------------------------------------------------------------------------------------------------------
def incoming_requests_vk(page, signals):
    try:
        signals.log_signal.emit(f'\n~~~~~~~~~~~~~~~~~~~~~~ СМОТРИМ ВХОДЯЩИЕ ЗАЯВКИ В ДРУЗЬЯ [ВК] ~~~~~~~~~~~~~~~~~~~~~~\n            Блок по дефолту: ЧС // СТОП-СЛОВО // ВОЗРАСТ (<20) // ЛИМИТ ДРУЗЕЙ (<500)\n')
        page_goto(page, 'https://vk.ru/friends?section=requests', signals)
        while page.locator('//*[text()="Новые"]').count()>0:
            with page.expect_navigation():
                page.locator('//div[@data-testid="userrichcell-name"]').nth(0).click()
            if page.locator('//span[@class="vkuiHeader__contentIn"][.//text()="Друзья"]/following-sibling::span').count() > 0:
                user_friends = int(page.locator('//span[@class="vkuiHeader__contentIn"][.//text()="Друзья"]/following-sibling::span').inner_text().replace('\u00a0', '').strip())
            else: user_friends = int(page.locator('//span[@class="vkuiHeader__contentIn"][.//text()="Подписчики"]/following-sibling::span').inner_text().replace('\u00a0', '').strip())
            page.click('//span[text()="Подробнее"]')
            user_info_lower = page.inner_text('//div[contains(@class,"ProfileFullInfoModal")]').lower()
            if page.locator('//a[contains(@href, "/search/people?c[name]=0&birth_year=")]').count() > 0:
                year_of_birth = int(page.inner_text('//a[contains(@href, "/search/people?c[name]=0&birth_year=")]').split()[0])
            else: year_of_birth = 0
            page.click('//div[@data-testid="modal-close-button"]'); page.click('text="Друзья"')
            if (any(word in user_info_lower for word in stop_words)
                or user_friends < 500
                or year_of_birth > 2005):
                page.click('text="Отклонить заявку"'); signals.log_signal.emit(f'Юзер ОТКЛОНЁН // Инфо: {user_info_lower}\n------------------------------')
            else: page.click('text="Принять заявку"'); signals.log_signal.emit(f'Юзер ПРИНЯТ в друзья // Инфо: {user_info_lower}\n------------------------------')
            page_goto(page, 'https://vk.ru/friends?section=requests', signals)
        else: signals.log_signal.emit('Новых заявок в друзья пока нет\n'); return
    except Exception as e: signals.log_signal.emit(f'\n!!!!!ЧТО-ТО СЛОМАЛОСЬ ПРИ ПРОВЕРКЕ ВХОДЯЩИХ ЗАЯВОК [ВК]!!!!! // ошибка: {e}\n')

# ----------------------------------------------------------------------------------------------------------------------
def outgoing_requests_vk(page, signals):
    try:
        signals.log_signal.emit(f'\n~~~~~~~~~~~~~~~~~~~~~~ ПОСЫЛАЕМ ИСХОДЯЩИЕ ЗАЯВКИ В ДРУЗЬЯ [ВК] ~~~~~~~~~~~~~~~~~~~~~~\n          Блок по дефолту: ЧС // СТОП-СЛОВО // ВОЗРАСТ (<20) // ЛИМИТ ДРУЗЕЙ (<500) // ЗАКРЫТЫЙ ПРОФИЛЬ\n')
        out_requests = 0

        while out_requests < 30:
            page_goto(page, 'https://vk.ru/friends?section=all', signals)

            start_time = time.time(); stop_time = random.randint(1, 20); link_ff_list = []
            for _ in range (100):
                page.mouse.wheel(0, 99999)
                if time.time() - start_time > stop_time: break

            page.click(f'(//div[@data-testid="userrichcell-after"])[{random.randint(1, 10)}]')
            link_ff = page.locator('//a[@data-testid="dropdownactionsheet-item"]').get_attribute('href')
            page_goto(page, f'https://vk.ru{link_ff}', signals)
            page.click('//div[@role="tablist"]//*[text()="Друзья онлайн"]')
            online_frs_cnt = int(page.locator('//span[text()="Друзья онлайн"]/following-sibling::span').inner_text())

            for i in range (0, online_frs_cnt):
                if page.locator(f'//div[@data-index="{i}"]//a').count() < 1: page.evaluate("window.scrollBy(0, 700)")
                try:
                    link_ff = page.locator(f'(//div[@data-index="{i}"]//a)[1]').get_attribute('href')
                    link_ff_list.append(link_ff)
                except Exception: break

            for link in link_ff_list:
                try:
                    page_goto(page, link, signals)
                    if page.locator('//span[text()="Добавить в друзья"]').count() < 1: continue
                    user_friends = int(page.locator('//span[@class="vkuiHeader__contentIn"][.//text()="Друзья"]/following-sibling::span').inner_text().replace('\u00a0', '').strip())

                    page.click('//span[text()="Подробнее"]')
                    user_info_lower: str = page.inner_text('//div[contains(@class,"ProfileFullInfoModal")]').lower().replace('\n', ', ')
                    if page.locator('//a[contains(@href, "/search/people?c[name]=0&birth_year=")]').count() > 0:
                        year_of_birth = int(page.inner_text('//a[contains(@href, "/search/people?c[name]=0&birth_year=")]').split()[0])
                    else: year_of_birth = 0
                    page.click('//div[@data-testid="modal-close-button"]')
                    if (any(word in user_info_lower for word in stop_words)
                        or user_friends < 500
                        or year_of_birth > 2005): continue
                    else:
                        page.click('//span[text()="Добавить в друзья"]')
                        out_requests += 1
                        signals.log_signal.emit(f'Заявка [{out_requests}] отправлена // ИНФО: {user_info_lower}\n------------------------------------------------------------')
                        if out_requests == 30: break
                except Exception: continue
    except Exception as e: signals.log_signal.emit(f'\n!!!!!ЧТО-ТО СЛОМАЛОСЬ ПРИ ОТПРАВКЕ ИСХОДЯШЕК [ВК]!!!!! // ошибка: {e}\n')

# ----------------------------------------------------------------------------------------------------------------------
def send_invite_in_my_groups_vk(page, signals):
    try:
        capcha = False; invite_cnt = 0; name_my_community = line_edit.text()
        if not name_my_community: return
        page_goto(page, name_my_community, signals)
        page.hover('//button[@aria-label="Ещё"]')
        page.click('text="Пригласить друзей"')
        while not capcha:
            if page.locator('//div[@data-testid="notifier_baloon_wrap"]').count() > 0 or page.locator('//iframe[@width="100%"]').count() > 0:
                capcha = True; break
            page.click('text="Выслать приглашение"')
            invite_cnt += 1; sleep(1)

        signals.log_signal.emit('Выход по лимиту (40 приглашений в день/до 20 за раз) или капче')
        signals.log_signal.emit(f'Отправлено [{invite_cnt-1}] приглашений в: {name_my_community}\n')
    except Exception as e: signals.log_signal.emit(f'\n!!!!!ЧТО-ТО СЛОМАЛОСЬ В ОТПРАВКЕ ИНВАЙТОВ [ВК]!!!!! // ошибка: {e}\n')

#-----------------------------------------------------------------------------------------------------------------------
def update_log(message):
    current_time = datetime.now().strftime('%H:%M:%S')
    log_message = f"[{current_time}:] {message}"
    log_output.append(log_message)
    with open(f".log\\log{datetime.now().strftime("%d-%m-%Y")}.txt", "a", encoding="utf-8") as log_file:
        log_file.write(log_message + "\n")  # Запись лога в файл

class WorkerSignals(QObject):
    log_signal = Signal(str)

class WorkerThread(QThread):
    def __init__(self, signals):
        super().__init__()
        self.signals = signals
    def run(self):
        run_playwright(self.signals)

# Функция для запуска потока
def start_playwright_thread():
    global worker_thread
    signals = WorkerSignals()
    signals.log_signal.connect(update_log)
    worker_thread = WorkerThread(signals)
    worker_thread.start()

def run_def_vk(page, signals):
    if cbox_function_vk[4].isChecked(): send_invite_in_my_groups_vk(page, signals)
    if cbox_function_vk[0].isChecked(): liking_vk(page, signals)
    if cbox_function_vk[1].isChecked(): incoming_requests_vk(page, signals)
    if cbox_function_vk[2].isChecked(): dell_out_requests_api_web_vk(page, signals)
    if cbox_function_vk[3].isChecked(): outgoing_requests_vk(page, signals)

def run_playwright(signals):

    if not cbox_profiles_vk[0].isChecked() and not cbox_profiles_vk[1].isChecked():
        signals.log_signal.emit('\n~~~~~~~~~~~~~~~~~~~~~~ [ ВЫБЕРИ АККАУНТЫ ДЛЯ РАБОТЫ ] ~~~~~~~~~~~~~~~~~~~~~~\n'); return

    btn.setEnabled(False)
    line_edit.setEnabled(False)
    for cbox in cbox_function_vk + cbox_profiles_vk:
        cbox.setEnabled(False)
    active_cbox_vk = [cbox.text() for cbox in cbox_function_vk if cbox.isChecked()]
    if  not active_cbox_vk: active_cbox_vk.append('Нет активных функций')

    signals.log_signal.emit(f'{datetime.now().strftime("%d-%m-%Y")}: [[[[[[[[[[[[[[[ С Т А Р Т    V K S e c r e t a r y ]]]]]]]]]]]]]]]'
                            f'\n\nАКТИВНЫЕ ФУНКЦИИ ДЛЯ ВК:\n\n{'\n '.join(item for item in active_cbox_vk)}\n')
    os.environ['PLAYWRIGHT_BROWSERS_PATH'] = '0'
    p = sync_playwright().start()
    browser = p.chromium.launch(executable_path="C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe",
                                args=["--disable-blink-features=AutomationControlled"],
                                headless=False, slow_mo=1000)
    context = browser.new_context(locale='en-US')
    context.set_default_timeout(60000)
    page = context.new_page()

    page.goto("https://intoli.com/blog/not-possible-to-block-chrome-headless/chrome-headless-test.html")
    if page.locator('text="missing (passed)"').is_visible(): signals.log_signal.emit('WebDriver не обнаружен')
    else: signals.log_signal.emit('\n!ВНИМАНИЕ! WebDriver ОБНАРУЖЕН')
    page.goto("https://www.browserscan.net/"); sleep(15)
    if page.locator('//a[@href="/bot-detection"]/preceding-sibling::span[1]').text_content() == 'Yes': signals.log_signal.emit('!ВНИМАНИЕ! Bot Detection НЕ ПРОЙДЕН')
    else: signals.log_signal.emit('Bot Detection пройден')

    if cbox_profiles_vk[0].isChecked(): start_vk(page, signals); run_def_vk(page, signals)

    signals.log_signal.emit('\n\n~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ [ работа завершена ] ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~\n\n')
    os.system('powershell -c (New-Object Media.SoundPlayer "end.wav").PlaySync();')  # sound
    btn.setEnabled(True)
    for cbox in cbox_function_vk + cbox_profiles_vk:
        cbox.setEnabled(True)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    dark_style = (
        "QWidget { background-color: #2E2E2E; color: #FFFFFF; } "
        "QCheckBox { background-color: #2E2E2E; color: #FFFFFF; font-size: 13px; } "
        "QTextEdit { background-color: #000000; color: #FFFFFF; font-size: 14px; } "
        "QPushButton { background-color: #4A4A4A; color: #FFFFFF; border: 1px solid #5A5A5A; font-size: 15px; } "
        "QPushButton:hover { background-color: #5A5A5A; }"
    )
    app.setStyleSheet(dark_style)
    w = QWidget()
    w.setWindowTitle('[VK_Secretary]')
    w.resize(1400, 350)
    layout = QVBoxLayout()
    splitter = QSplitter(Qt.Orientation.Horizontal)
    checkbox_widget = QWidget()
    checkbox_layout = QVBoxLayout()
    group1 = QGroupBox("Профили ВК")
    cbox_profiles_vk = [QCheckBox('[PROFILE VK : 1]')]
    layout1 = QVBoxLayout()
    group1.setLayout(layout1)
    for cb in cbox_profiles_vk:
        cb.setChecked(True)
        layout1.addWidget(cb)
    group1.setFixedSize(400, 80)
    group2 = QGroupBox("Выполняемые функции ВК")
    cbox_function_vk = [
        QCheckBox('[ЛАЙКИ/РЕПОСТЫ (акки, посты и истории)]'),
        QCheckBox('[ПРОВЕРКА ВХОДЯЩИХ ЗАЯВОК В ДРУЗЬЯ]'),
        QCheckBox('[УДАЛЕНИЕ ИСХОДЯЩИХ ЗАЯВОК В ДРУЗЬЯ]'),
        QCheckBox('[ОТПРАВИТЬ 30 ЗАЯВОК В ДРУЗЬЯ]'),
        QCheckBox('[ОТПРАВИТЬ ПРИГЛАШЕНИЯ В ГРУППУ (лимит:20/40)]')
    ]
    layout2 = QVBoxLayout()
    group2.setLayout(layout2)
    for cb in cbox_function_vk:
        cb.setChecked(True)
        layout2.addWidget(cb)
    line_edit = QLineEdit()
    line_edit.setPlaceholderText("адрес группы для инвайта: https://...")
    layout2.addWidget(line_edit)
    group2.setFixedSize(400, 200)
    def check_groups():
        if not (cbox_profiles_vk[0].isChecked()):
            for cb in cbox_function_vk:
                cb.setChecked(False)
    def key_press_event(event):
        if event.key() == 16777220:
            start_playwright_thread()
    for cb in cbox_profiles_vk + cbox_function_vk:
        cb.stateChanged.connect(check_groups)
    checkbox_layout.addWidget(group1)
    checkbox_layout.addWidget(group2)
    checkbox_widget.setLayout(checkbox_layout)
    log_output = QTextEdit()
    log_output.resize(1100, 300)
    log_output.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)
    log_output.setReadOnly(True)
    splitter.addWidget(checkbox_widget)
    splitter.addWidget(log_output)
    btn = QPushButton('ВЫПОЛНИТЬ ПРОГРАММУ С ВЫБРАННЫМИ ОПЦИЯМИ')
    btn.clicked.connect(start_playwright_thread)
    layout.addWidget(splitter)
    layout.addWidget(btn)
    w.setLayout(layout)
    w.show()
    w.keyPressEvent = key_press_event
    sys.exit(app.exec())
#-----------------------------------------------------------------------------------------------------------------------



