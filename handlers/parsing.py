import asyncio
import json
import os
from aiogram import types
from selenium.common import NoSuchElementException, TimeoutException, StaleElementReferenceException, WebDriverException
from selenium.webdriver import Chrome, Keys
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.support.ui import WebDriverWait
from urllib3.exceptions import MaxRetryError

from create_bot import bot
from selenium.webdriver.chrome.service import Service
from selenium import webdriver
from keyboards import client_kb

path_to_driver = os.getcwd() + "/" + "drivers/chromedriver.exe"
path_to_clients = os.getcwd() + "/" + "json/clients"
path_to_admins_statistics = os.getcwd() + "/" + "json/admins/statistics"
path_to_admins_settings = os.getcwd() + "/" + "json/admins/settings"
path_to_admins_techsup = os.getcwd() + "/" + "json/admins/techsup"
path_to_admins_settings_ban_users = path_to_admins_settings + "/" + "ban_users.json"
path_to_parsing = os.getcwd() + "/" + "json/parsing"

options = webdriver.ChromeOptions()
options.add_argument('--no-sandbox')
options.add_argument("--disable-blink-features=AutomationControlled")
options.add_argument('--headless')
options.add_argument('--disable-dev-shm-usage')

service_chrome = Service(path_to_driver)


async def mail_parsing(name_file: str):
    global path_to_parsing
    path_to_current_client_parsing = path_to_parsing + "/" + name_file
    with open(path_to_current_client_parsing, 'r', encoding='utf8') as file:
        current_client_parsing = json.load(file)
    user_id = int(name_file[:name_file.find('.')])
    for tender in range(len(current_client_parsing["active_tenders"])):
        array_for_file = []
        array_for_file2 = []

        driver = Chrome(executable_path=path_to_driver, options=options, service=service_chrome)
        task1 = asyncio.create_task(parsing_zakupki_for_mail(driver,
                                                             array_for_file,
                                                             current_client_parsing["active_tenders"][tender],
                                                             current_client_parsing["zakon"][tender],
                                                             current_client_parsing["prices"][tender],
                                                             name_file,
                                                             tender))
        driver2 = Chrome(executable_path=path_to_driver, options=options, service=service_chrome)
        task2 = asyncio.create_task(parsing_sber_for_mail(driver2,
                                                          array_for_file2,
                                                          current_client_parsing["active_tenders"][tender],
                                                          current_client_parsing["prices"][tender],
                                                          name_file,
                                                          tender))
        await task1
        await task2
        while not task1.done() and not task2.done():
            print("a")
        array_for_file = list(array_for_file + array_for_file2)
        for i in range(len(array_for_file)):
            current_client_parsing["tenders_view_yet"][tender].append(array_for_file[i][0])
            stroke = array_for_file[i][6]
            stroke = stroke[stroke.find('"') + 1:]
            stroke = stroke[:stroke.find('"')]
            keyboard = await client_kb.answer_search_link_and_unsub(stroke)
            answer = "По тендеру: " + current_client_parsing["active_tenders"][tender] + ", новая заявка\n"
            answer += "*Заявка*: " + array_for_file[i][0] + "\n*Объект закупки*: " + array_for_file[i][1] + \
                      "\n*Заказчик*: " + array_for_file[i][2] + "\n*Начальная цена*: " + array_for_file[i][3] + \
                      "\n*Размещено*: " + array_for_file[i][4] + "\n*Окончание подачи заявок*: " \
                      + array_for_file[i][5] + "\n"
            await bot.send_message(user_id,
                                   answer,
                                   reply_markup=keyboard, parse_mode="Markdown")
            await asyncio.sleep(1)
        try:
            driver.quit()
        finally:
            pass
        try:
            driver2.quit()
        finally:
            pass
    with open(path_to_current_client_parsing, 'w', encoding='utf8') as file:
        json.dump(current_client_parsing, file, ensure_ascii=False)


async def parsing_zakupki(driver: Chrome, array_for_file: list, callback: types.CallbackQuery,
                          bot_answer: types.Message):
    global path_to_clients, path_to_parsing
    await bot_answer.edit_text("Загрузка из zakupki.gov.ru .")
    path_to_current_client = path_to_clients + "/" + str(callback.from_user.id) + "/search.json"
    with open(path_to_current_client, 'r', encoding='utf8') as file:
        current_client_search = json.load(file)
    url = "https://zakupki.gov.ru/" \
          "epz/order/extendedsearch/results.html?searchString=" + current_client_search["message_for_search"] + \
          "&morphology=on" \
          "&search-filter=Дате+размещения&pageNumber=1&sortDirection=false&recordsPerPage=_10" \
          "&showLotsInfoHidden=false&sortBy=UPDATE_DATE"

    if current_client_search["modify_button"][0] == 1:
        url += "&fz44=on"
    if current_client_search["modify_button"][1] == 1:
        url += "&fz223=on"
    if current_client_search["modify_button"][2] == 1:
        url += "&fz94=on"
    if current_client_search["modify_button"][3] == 1:
        url += "&ppRf615=on"

    url += "&af=on&priceFromGeneral=" + str(current_client_search["price_min"]) + \
           "&priceToGeneral=" + str(current_client_search["price_max"]) + "&currencyIdGeneral=-1"
    driver.get(url)
    pages = driver.find_element(By.CLASS_NAME, "paginator.align-self-center.m-0")
    pages_new = pages.find_elements(By.CLASS_NAME, "page")
    await bot_answer.edit_text("Загрузка из zakupki.gov.ru ..")
    try:
        pages_count = int(pages_new[len(pages_new) - 1].text)
    except IndexError:
        await bot.send_message(callback.from_user.id, "По вашему запросу нет результатов на zakupki.gov.ru")
        return
    order_numbers = []
    purchase_volumes = []
    client_names = []
    begin_prices = []
    start_dates = []
    end_dates = []
    links = []
    await bot_answer.edit_text("Загрузка из zakupki.gov.ru ...")
    for page in range(pages_count):
        url = "https://zakupki.gov.ru/" \
              "epz/order/extendedsearch/results.html?searchString=" + current_client_search["message_for_search"] + \
              "&morphology=on" \
              "&search-filter=Дате+размещения&pageNumber=" + \
              str(page + 1) + "&sortDirection=false&recordsPerPage=_10" \
                              "&showLotsInfoHidden=false&sortBy=UPDATE_DATE"

        if current_client_search["modify_button"][0] == 1:
            url += "&fz44=on"
        if current_client_search["modify_button"][1] == 1:
            url += "&fz223=on"
        if current_client_search["modify_button"][2] == 1:
            url += "&fz94=on"
        if current_client_search["modify_button"][3] == 1:
            url += "&ppRf615=on"

        url += "&af=on&priceFromGeneral=" + str(current_client_search["price_min"]) + \
               "&priceToGeneral=" + str(current_client_search["price_max"]) + "&currencyIdGeneral=-1"
        driver.get(url)
        result_total = driver.find_element(By.CLASS_NAME, "search-results__total")
        try:
            result_total_int = int(result_total.text[:result_total.text.find(' ')])
        except ValueError:
            return
        quotes = driver.find_elements(By.CLASS_NAME, "search-registry-entry-block.box-shadow-search-input")
        for quote in quotes:
            try:
                quote_number = quote.find_element(By.CLASS_NAME, "registry-entry__header-mid__number")
            except MaxRetryError:
                continue
            order_numbers.append(quote_number.text)
            quote_purchase_volume = quote.find_element(By.CLASS_NAME, "registry-entry__body-value")
            purchase_volumes.append(quote_purchase_volume.text)
            quote_client_name = quote.find_element(By.CLASS_NAME, "registry-entry__body-href")
            client_names.append(quote_client_name.text)
            quote_begin_price = quote.find_element(By.CLASS_NAME, "price-block__value")
            begin_prices.append(quote_begin_price.text)

            quote_second = quote.find_element(By.CLASS_NAME, "data-block.mt-auto")
            quote_dates = quote_second.find_elements(By.CLASS_NAME, "data-block__value")
            i = 0
            for quote_date in quote_dates:
                if i == 1:
                    i += 1
                elif i == 0:
                    start_dates.append(quote_date.text)
                    i += 1
                else:
                    end_dates.append(quote_date.text)
            quote_link = quote_number.find_element(By.CSS_SELECTOR, "div.registry-entry__header-mid__number [href]")
            links.append(quote_link.get_attribute('href'))
            await bot_answer.edit_text("Загружено " + str(len(order_numbers)) +
                                       " заявок из " + str(result_total_int) + " с сайта zakupki.gov.ru")
            await asyncio.sleep(1)
    for i in range(len(order_numbers)):
        array_for_file.append([])
        array_for_file[i].append(order_numbers[i])
        array_for_file[i].append(purchase_volumes[i])
        array_for_file[i].append(client_names[i])
        array_for_file[i].append(begin_prices[i] + " руб")
        array_for_file[i].append(start_dates[i])
        try:
            array_for_file[i].append(end_dates[i])
        except IndexError:
            array_for_file[i].append("НЕТ")
        stroke = '=HYPERLINK("' + links[i] + '"' + ',"ОТКРЫТЬ")'
        array_for_file[i].append(stroke)


async def parsing_sber(driver: Chrome, array_for_file: list, callback: types.CallbackQuery,
                       bot_answer: types.Message):
    global path_to_clients
    await asyncio.sleep(2)
    path_to_current_client = path_to_clients + "/" + str(callback.from_user.id) + "/search.json"
    with open(path_to_current_client, 'r', encoding='utf8') as file:
        current_client_search = json.load(file)
    await bot_answer.edit_text("Загрузка из sberbank-ast.ru .")
    driver.get("https://www.sberbank-ast.ru/")
    await asyncio.sleep(3)
    quote = driver.find_element(By.CLASS_NAME, "master_open_content")
    quote = quote.find_element(By.CLASS_NAME, "container.default_search")
    quote = quote.find_element(By.CLASS_NAME, "col-xs-8.col-md-8")
    quote = quote.find_element(By.CLASS_NAME, "default_search_border")
    quote = quote.find_element(By.ID, "txtUnitedPurchaseSearch")
    quote.clear()
    quote.send_keys(str(current_client_search["message_for_search"]), Keys.ENTER)
    button_filter = driver.find_element(By.ID, "filters")
    button_filter = button_filter.find_element(By.CLASS_NAME, "element-in-one-row.simple-button.orange-background")
    button_filter.click()
    await asyncio.sleep(1)
    filters = driver.find_element(By.CLASS_NAME, "filter-table")
    filters = filters.find_elements(By.CLASS_NAME, "range-filter-content")
    i = 0
    price = [str(current_client_search["price_min"]), str(current_client_search["price_max"])]
    await bot_answer.edit_text("Загрузка из sberbank-ast.ru ..")
    await asyncio.sleep(2)
    for item in filters:
        start_cena = item.find_element(By.CLASS_NAME, "numeric.mustBeCleaned.esfilter-input")
        start_cena.send_keys(price[i])
        i += 1
    etap_provedeniya = driver.find_element(By.CLASS_NAME, "filter-table")
    etap_provedeniya = etap_provedeniya.find_elements(By.CLASS_NAME, "last")
    for item in etap_provedeniya:
        item = item.find_element(By.CLASS_NAME, "shortdict-filter-choose-button")
        item.click()
        await asyncio.sleep(1)
        break
    etap_provedeniya = driver.find_element(By.ID, "shortDictionaryModal")
    etap_provedeniya = etap_provedeniya.find_element(By.CLASS_NAME, "modal-content-body")
    etap_provedeniya = etap_provedeniya.find_elements(By.CLASS_NAME, "mustBeCleaned")
    id_number = 0
    for item in etap_provedeniya:
        if item.text.find("Подача") >= 0:
            id_number = int(item.get_attribute('id')) - 3
            break
    etap_provedeniya = driver.find_element(By.ID, "shortDictionaryModal")
    etap_provedeniya = etap_provedeniya.find_element(By.CLASS_NAME, "modal-content-body")
    etap_provedeniya = etap_provedeniya.find_element(By.CLASS_NAME, "modal-content-scroller")
    await bot_answer.edit_text("Загрузка из sberbank-ast.ru ...")
    try:
        etap_provedeniya = etap_provedeniya.find_element(By.ID, str(id_number))
    except NoSuchElementException:
        print("Не найдено активных заявок")
        return
    etap_provedeniya.click()
    await asyncio.sleep(1)
    etap_provedeniya = driver.find_element(By.ID, "shortDictionaryModal")
    etap_provedeniya = etap_provedeniya.find_element(By.CLASS_NAME, "modal-footer")
    etap_provedeniya = etap_provedeniya.find_element(By.CLASS_NAME, "simple-button.green-background")
    etap_provedeniya.click()
    await asyncio.sleep(1)
    search_beg = driver.find_element(By.ID, "specialFilters")
    search_beg = search_beg.find_element(By.ID, "OkCansellBtns")
    search_beg = search_beg.find_element(By.CLASS_NAME, "simple-button.green-background")
    search_beg.click()
    await asyncio.sleep(1)
    check_counts = driver.find_element(By.ID, "statisticAreaContainer")
    check_counts = check_counts.find_element(By.ID, "statisticArea")
    check_counts = check_counts.find_element(By.CLASS_NAME, "statsPH")
    request_counts = int(check_counts.text.replace(' ', ''))
    pages = driver.find_element(By.ID, "pager")
    pages = pages.find_elements(By.ID, "pageButton")
    try:
        pages = int(pages[len(pages) - 3].text)
    except ValueError:
        await bot_answer.edit_text("sberbank-ast.ru не нашел результатов")
        return
    begin_prices = []
    client_names = []
    purchase_volumes = []
    start_dates = []
    end_dates = []
    order_numbers = []
    links = []
    k = 0
    for page in range(pages):
        if page != 0:
            driver.execute_script("window.scrollTo(0, 0)")
            await asyncio.sleep(1)
            new_page = driver.find_element(By.ID, "pager")
            new_page = new_page.find_elements(By.ID, "pageButton")
            new_page = new_page[len(new_page) - 2].find_element(By.CLASS_NAME, "pager-button.pagerElem")
            ActionChains(driver).move_to_element(new_page).click().perform()
            await asyncio.sleep(2)
        requests = driver.find_element(By.ID, "resultTable")
        requests = requests.find_elements(By.CLASS_NAME, "purch-reestr-tbl-div")
        for request in requests:
            try:
                stroke = "№ " + request.find_element(By.CLASS_NAME, "es-el-code-term").text
                order_numbers.append(stroke)
                stroke = request.find_element(By.CLASS_NAME, "es-el-amount").text
                stroke = stroke[:stroke.find('.')]
                stroke += " руб"
            except StaleElementReferenceException:
                stroke = "None"
            begin_prices.append(stroke)
            try:
                client_names.append(request.find_element(By.CLASS_NAME, "es-el-org-name").text)
            except StaleElementReferenceException:
                client_names.append("None")
            try:
                purchase_volumes.append(request.find_element(By.CLASS_NAME, "es-el-name").text)
            except StaleElementReferenceException:
                purchase_volumes.append("None")
            try:
                stroke = request.find_element(By.CSS_SELECTOR, "span[content='leaf:PublicDate']").text
                stroke = stroke[:stroke.find(' ')]
            except StaleElementReferenceException:
                stroke = "None"
            start_dates.append(stroke)
            try:
                end_dates.append(request.find_element(By.CSS_SELECTOR, "span[content='leaf:EndDate']").text)
            except StaleElementReferenceException:
                end_dates.append("None")
            await asyncio.sleep(1)
            option_buttons = request.find_element(By.CLASS_NAME, "dotted-botom.last")
            option_buttons = option_buttons.find_element(By.CSS_SELECTOR,
                                                         "input[class='link-button'][value ='/  Просмотр']")
            option_buttons.click()
            await asyncio.sleep(1)
            try:
                WebDriverWait(driver, 5).until(ec.presence_of_element_located((By.CLASS_NAME, 'submenu-link')))
            except TimeoutException:
                driver.refresh()
            driver.switch_to.window(driver.window_handles[-1])
            links.append(driver.current_url)
            await bot_answer.edit_text("Загружено " + str(len(order_numbers)) +
                                       " заявок из " + str(request_counts) + " с сайта sberbank-ast.ru")
            driver.close()
            try:
                driver.switch_to.window(driver.window_handles[0])
            finally:
                pass
            await asyncio.sleep(1)
        k += 1
    for i in range(len(order_numbers)):
        if order_numbers[i] == "":
            continue
        array_for_file.append([])
        array_for_file[i].append(order_numbers[i])
        array_for_file[i].append(purchase_volumes[i])
        array_for_file[i].append(client_names[i])
        array_for_file[i].append(begin_prices[i])
        array_for_file[i].append(start_dates[i])
        try:
            array_for_file[i].append(end_dates[i])
        except IndexError:
            array_for_file[i].append("НЕТ")
        stroke = '=HYPERLINK("' + links[i] + '"' + ',"ОТКРЫТЬ")'
        array_for_file[i].append(stroke)


async def parsing_zakupki_for_mail(driver: Chrome, array_for_file: list, tender_name: str, zakon: list,
                                   prices: list, name_file: str, tender: int):
    global path_to_clients, path_to_parsing
    url = "https://zakupki.gov.ru/" \
          "epz/order/extendedsearch/results.html?searchString=" + tender_name + \
          "&morphology=on" \
          "&search-filter=Дате+размещения&pageNumber=1&sortDirection=false&recordsPerPage=_10" \
          "&showLotsInfoHidden=false&sortBy=UPDATE_DATE"
    path_to_current_client_parsing = path_to_parsing + "/" + name_file
    with open(path_to_current_client_parsing, 'r', encoding='utf8') as file:
        current_client_parsing = json.load(file)
    if zakon[0] == 1:
        url += "&fz44=on"
    if zakon[1] == 1:
        url += "&fz223=on"
    if zakon[2] == 1:
        url += "&fz94=on"
    if zakon[3] == 1:
        url += "&ppRf615=on"

    url += "&af=on&priceFromGeneral=" + str(prices[0]) + \
           "&priceToGeneral=" + str(prices[1]) + "&currencyIdGeneral=-1"
    try:
        driver.get(url)
    except WebDriverException:
        await asyncio.sleep(2)
        driver.get(url)
    pages = driver.find_element(By.CLASS_NAME, "paginator.align-self-center.m-0")
    pages_new = pages.find_elements(By.CLASS_NAME, "page")
    try:
        pages_count = int(pages_new[len(pages_new) - 1].text)
    except IndexError:
        return
    order_numbers = []
    purchase_volumes = []
    client_names = []
    begin_prices = []
    start_dates = []
    end_dates = []
    links = []
    for page in range(pages_count):
        url = "https://zakupki.gov.ru/" \
              "epz/order/extendedsearch/results.html?searchString=" + tender_name + \
              "&morphology=on" \
              "&search-filter=Дате+размещения&pageNumber=" + \
              str(page + 1) + "&sortDirection=false&recordsPerPage=_10" \
                              "&showLotsInfoHidden=false&sortBy=UPDATE_DATE"

        if zakon[0] == 1:
            url += "&fz44=on"
        if zakon[1] == 1:
            url += "&fz223=on"
        if zakon[2] == 1:
            url += "&fz94=on"
        if zakon[3] == 1:
            url += "&ppRf615=on"

        url += "&af=on&priceFromGeneral=" + str(prices[0]) + \
               "&priceToGeneral=" + str(prices[1]) + "&currencyIdGeneral=-1"
        driver.get(url)
        quotes = driver.find_elements(By.CLASS_NAME, "search-registry-entry-block.box-shadow-search-input")
        for quote in quotes:
            quote_number = quote.find_element(By.CLASS_NAME, "registry-entry__header-mid__number")
            have_tender_view_yet = False
            for i in range(len(current_client_parsing["tenders_view_yet"][tender])):
                if quote_number.text == \
                        current_client_parsing["tenders_view_yet"][tender][i]:
                    have_tender_view_yet = True
                    break
            if not have_tender_view_yet:
                order_numbers.append(quote_number.text)
            else:
                continue
            quote_purchase_volume = quote.find_element(By.CLASS_NAME, "registry-entry__body-value")
            purchase_volumes.append(quote_purchase_volume.text)
            quote_client_name = quote.find_element(By.CLASS_NAME, "registry-entry__body-href")
            client_names.append(quote_client_name.text)
            quote_begin_price = quote.find_element(By.CLASS_NAME, "price-block__value")
            begin_prices.append(quote_begin_price.text)

            quote_second = quote.find_element(By.CLASS_NAME, "data-block.mt-auto")
            quote_dates = quote_second.find_elements(By.CLASS_NAME, "data-block__value")
            i = 0
            for quote_date in quote_dates:
                if i == 1:
                    i += 1
                elif i == 0:
                    start_dates.append(quote_date.text)
                    i += 1
                else:
                    end_dates.append(quote_date.text)
            quote_link = quote_number.find_element(By.CSS_SELECTOR, "div.registry-entry__header-mid__number [href]")
            links.append(quote_link.get_attribute('href'))
            await asyncio.sleep(1)
    for i in range(len(order_numbers)):
        array_for_file.append([])
        array_for_file[i].append(order_numbers[i])
        array_for_file[i].append(purchase_volumes[i])
        array_for_file[i].append(client_names[i])
        array_for_file[i].append(begin_prices[i] + " руб")
        array_for_file[i].append(start_dates[i])
        try:
            array_for_file[i].append(end_dates[i])
        except IndexError:
            array_for_file[i].append("НЕТ")
        stroke = '=HYPERLINK("' + links[i] + '"' + ',"ОТКРЫТЬ")'
        array_for_file[i].append(stroke)


async def parsing_sber_for_mail(driver: Chrome, array_for_file: list, tender_name: str,
                                prices: list, name_file: str, tender: int):
    global path_to_parsing
    path_to_current_client_parsing = path_to_parsing + "/" + name_file
    with open(path_to_current_client_parsing, 'r', encoding='utf8') as file:
        current_client_parsing = json.load(file)
    try:
        driver.get("https://www.sberbank-ast.ru/")
    except WebDriverException:
        await asyncio.sleep(2)
        driver.get("https://www.sberbank-ast.ru/")
    await asyncio.sleep(2)
    try:
        quote = driver.find_element(By.CLASS_NAME, "master_open_content")
    except MaxRetryError:
        driver = Chrome(executable_path=path_to_driver, options=options, service=service_chrome)
        driver.get("https://www.sberbank-ast.ru/")
        quote = driver.find_element(By.CLASS_NAME, "master_open_content")
    quote = quote.find_element(By.CLASS_NAME, "container.default_search")
    quote = quote.find_element(By.CLASS_NAME, "col-xs-8.col-md-8")
    quote = quote.find_element(By.CLASS_NAME, "default_search_border")
    quote = quote.find_element(By.ID, "txtUnitedPurchaseSearch")
    quote.clear()
    try:
        quote.send_keys(tender_name, Keys.ENTER)
    except:
        print("err 501 parsing")
        await asyncio.sleep(1)
        quote.send_keys(tender_name, Keys.ENTER)
    button_filter = driver.find_element(By.ID, "filters")
    button_filter = button_filter.find_element(By.CLASS_NAME, "element-in-one-row.simple-button.orange-background")
    button_filter.click()
    await asyncio.sleep(1)
    filters = driver.find_element(By.CLASS_NAME, "filter-table")
    filters = filters.find_elements(By.CLASS_NAME, "range-filter-content")
    i = 0
    price = [str(prices[0]), str(prices[1])]
    for item in filters:
        start_cena = item.find_element(By.CLASS_NAME, "numeric.mustBeCleaned.esfilter-input")
        start_cena.send_keys(price[i])
        i += 1
    etap_provedeniya = driver.find_element(By.CLASS_NAME, "filter-table")
    etap_provedeniya = etap_provedeniya.find_elements(By.CLASS_NAME, "last")
    for item in etap_provedeniya:
        item = item.find_element(By.CLASS_NAME, "shortdict-filter-choose-button")
        item.click()
        await asyncio.sleep(1)
        break
    etap_provedeniya = driver.find_element(By.ID, "shortDictionaryModal")
    etap_provedeniya = etap_provedeniya.find_element(By.CLASS_NAME, "modal-content-body")
    etap_provedeniya = etap_provedeniya.find_elements(By.CLASS_NAME, "mustBeCleaned")
    id_number = 0
    for item in etap_provedeniya:
        if item.text.find("Подача") >= 0:
            id_number = int(item.get_attribute('id')) - 3
            break
    etap_provedeniya = driver.find_element(By.ID, "shortDictionaryModal")
    etap_provedeniya = etap_provedeniya.find_element(By.CLASS_NAME, "modal-content-body")
    etap_provedeniya = etap_provedeniya.find_element(By.CLASS_NAME, "modal-content-scroller")
    try:
        etap_provedeniya = etap_provedeniya.find_element(By.ID, str(id_number))
    except NoSuchElementException:
        return
    etap_provedeniya.click()
    await asyncio.sleep(1)
    etap_provedeniya = driver.find_element(By.ID, "shortDictionaryModal")
    etap_provedeniya = etap_provedeniya.find_element(By.CLASS_NAME, "modal-footer")
    etap_provedeniya = etap_provedeniya.find_element(By.CLASS_NAME, "simple-button.green-background")
    etap_provedeniya.click()
    await asyncio.sleep(1)
    search_beg = driver.find_element(By.ID, "specialFilters")
    search_beg = search_beg.find_element(By.ID, "OkCansellBtns")
    search_beg = search_beg.find_element(By.CLASS_NAME, "simple-button.green-background")
    search_beg.click()
    await asyncio.sleep(1)
    pages = driver.find_element(By.ID, "pager")
    pages = pages.find_elements(By.ID, "pageButton")
    try:
        pages = int(pages[len(pages) - 3].text)
    except ValueError:
        return
    begin_prices = []
    client_names = []
    purchase_volumes = []
    start_dates = []
    end_dates = []
    order_numbers = []
    links = []
    k = 0
    for page in range(pages):
        if page != 0:
            driver.execute_script("window.scrollTo(0, 0)")
            await asyncio.sleep(1)
            new_page = driver.find_element(By.ID, "pager")
            new_page = new_page.find_elements(By.ID, "pageButton")
            new_page = new_page[len(new_page) - 2].find_element(By.CLASS_NAME, "pager-button.pagerElem")
            ActionChains(driver).move_to_element(new_page).click().perform()
            await asyncio.sleep(2)
        requests = driver.find_element(By.ID, "resultTable")
        requests = requests.find_elements(By.CLASS_NAME, "purch-reestr-tbl-div")
        for request in requests:
            try:
                stroke = "№ " + request.find_element(By.CLASS_NAME, "es-el-code-term").text
                have_tender_view_yet = False
                for i in range(len(current_client_parsing["tenders_view_yet"][tender])):
                    if stroke == \
                            current_client_parsing["tenders_view_yet"][tender][i]:
                        have_tender_view_yet = True
                        break
                if not have_tender_view_yet:
                    order_numbers.append(stroke)
                else:
                    continue
                stroke = request.find_element(By.CLASS_NAME, "es-el-amount").text
                stroke = stroke[:stroke.find('.')]
                stroke += " руб"
            except StaleElementReferenceException:
                continue
            begin_prices.append(stroke)
            try:
                client_names.append(request.find_element(By.CLASS_NAME, "es-el-org-name").text)
            except StaleElementReferenceException:
                client_names.append("None")
            try:
                purchase_volumes.append(request.find_element(By.CLASS_NAME, "es-el-name").text)
            except StaleElementReferenceException:
                purchase_volumes.append("None")
            try:
                stroke = request.find_element(By.CSS_SELECTOR, "span[content='leaf:PublicDate']").text
                stroke = stroke[:stroke.find(' ')]
            except StaleElementReferenceException:
                stroke = "None"
            start_dates.append(stroke)
            try:
                end_dates.append(request.find_element(By.CSS_SELECTOR, "span[content='leaf:EndDate']").text)
            except StaleElementReferenceException:
                end_dates.append("None")
            await asyncio.sleep(1)
            option_buttons = request.find_element(By.CLASS_NAME, "dotted-botom.last")
            option_buttons = option_buttons.find_element(By.CSS_SELECTOR,
                                                         "input[class='link-button'][value ='/  Просмотр']")
            option_buttons.click()
            await asyncio.sleep(1)
            try:
                WebDriverWait(driver, 5).until(ec.presence_of_element_located((By.CLASS_NAME, 'submenu-link')))
            except TimeoutException:
                driver.refresh()
            driver.switch_to.window(driver.window_handles[-1])
            links.append(driver.current_url)
            driver.close()
            try:
                driver.switch_to.window(driver.window_handles[0])
            finally:
                pass
            await asyncio.sleep(1)
        k += 1
    for i in range(len(order_numbers)):
        if order_numbers[i] == "":
            continue
        array_for_file.append([])
        array_for_file[i].append(order_numbers[i])
        array_for_file[i].append(purchase_volumes[i])
        array_for_file[i].append(client_names[i])
        array_for_file[i].append(begin_prices[i])
        array_for_file[i].append(start_dates[i])
        try:
            array_for_file[i].append(end_dates[i])
        except IndexError:
            array_for_file[i].append("НЕТ")
        stroke = '=HYPERLINK("' + links[i] + '"' + ',"ОТКРЫТЬ")'
        array_for_file[i].append(stroke)
