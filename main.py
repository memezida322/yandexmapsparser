#Python 3.11.7
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import pandas as pd
from selenium.webdriver.chrome.options import Options
import time
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.keys import Keys
import random

chrome_options = Options()
chrome_options.add_argument('--disable-gpu')
chrome_options.add_argument('--start-maximized')
driver = webdriver.Chrome(options=chrome_options)

data = []
with open('cities_ru.txt', 'r', encoding='utf-8') as file:
    cities = file.read().splitlines()

for city in cities:
    driver.get('https://yandex.ru/maps/')
    time.sleep(1)
    search_input = driver.find_element(By.CLASS_NAME, "input__control._bold")
    time.sleep(0.5)
    search_input.send_keys(f'Ваш запрос {city}')
    button = WebDriverWait(driver, 10).until(EC.visibility_of_element_located((By.ID, '0:0')))
    button.click()
    time.sleep(2)

    current_snippets_count = 0
    new_snippets = None
    scroll_offset = 395

    while True:
        try:
            scrollbar_thumb = driver.find_element(By.CLASS_NAME, 'scroll__scrollbar-track')
            ActionChains(driver).click_and_hold(scrollbar_thumb).move_by_offset(0, scroll_offset).release().perform()

            # Ожидание появления новых элементов
            WebDriverWait(driver, 2).until(lambda d: len(d.find_elements(By.CLASS_NAME, 'search-snippet-view')) > current_snippets_count)

            new_snippets = driver.find_elements(By.CLASS_NAME, 'search-snippet-view')

            if len(new_snippets) == current_snippets_count:
                print(len(new_snippets))
                # Проверка наличия элемента "search-list-view__spinner"
                spinner = driver.find_elements(By.CLASS_NAME, 'search-list-view__spinner')
                if spinner:
                    # Ожидание исчезновения элемента "search-list-view__spinner"
                    WebDriverWait(driver, 3).until(EC.invisibility_of_element_located((By.CLASS_NAME, 'search-list-view__spinner')))
                    # Восстановление смещения на 130 пикселей
                    scroll_offset = 110
                else:
                    # Уменьшение смещения на 60 пикселей, если больше или равно 8
                    if scroll_offset >= 8:
                        scroll_offset = scroll_offset / 2
                    else:
                        break  # Прерывание цикла, если смещение меньше 8 пикселей
                    # Прокрутка на уменьшенное смещение
                    ActionChains(driver).click_and_hold(scrollbar_thumb).move_by_offset(0, scroll_offset).release().perform()
            else:
                # Если собраны новые элементы, увеличиваем смещение до 500 и продолжаем прокрутку
                scroll_offset = 590
                current_snippets_count = len(new_snippets)

        except Exception as e:
            if "move target out of bounds" in str(e):
                print("Произошла ошибка: move target out of bounds")
                scroll_offset = 500

                while scroll_offset > 0:
                    scrollbar_thumb = driver.find_element(By.CLASS_NAME, 'scroll__scrollbar-track')
                    ActionChains(driver).click_and_hold(scrollbar_thumb).move_by_offset(0, scroll_offset).release().perform()

                    try:
                        # Ожидание появления новых элементов
                        WebDriverWait(driver, 3).until(lambda d: len(d.find_elements(By.CLASS_NAME, 'search-snippet-view')) > current_snippets_count)
                        new_snippets = driver.find_elements(By.CLASS_NAME, 'search-snippet-view')
                        if new_snippets:
                            current_snippets_count = len(new_snippets)
                            break  # Прерывание цикла, если прокрутка прошла успешно и новые элементы найдены
                        else:
                            continue  # Продолжение цикла для продолжения прокрутки
                    except Exception as e:
                        if "move target out of bounds" in str(e):
                            scroll_offset //= 2  # Уменьшение смещения вдвое
                        else:
                            print(f"Произошла ошибка во время прокрутки: {e}")
                            break  # Выход из цикла при другой ошибке
                else:
                    print("Ошибка: невозможно выполнить прокрутку. Продолжение сбора данных.")
                    continue

            else:
                print(f"Произошла ошибка во время прокрутки: {e}")
                break  # Выход из цикла при другой ошибке 

    # Сбор данных из сниппетов
    if new_snippets:
        for snippet in new_snippets:
            try:
                # Получение текста заголовка сниппета
                title = snippet.find_element(By.CLASS_NAME, 'search-business-snippet-view__title').text
                
                working_status = snippet.find_element(By.CLASS_NAME, 'search-business-snippet-view__optional')
                time.sleep(0.1)
                snippet.click()

                # Инициализация переменных для сбора данных
                phone_number = vkontakte = whatsapp = telegram = site = None
                
                # Сбор номера телефона
                try:
                    phone_number_clk = WebDriverWait(driver, 0.5).until(EC.element_to_be_clickable((By.CLASS_NAME, 'card-phones-view__phone-number')))
                    phone_number_clk.click()
                    phone_number = driver.find_element(By.CLASS_NAME, 'card-phones-view__phone-number').text
                except:
                    pass  # Пропуск, если информация недоступна

                try:
                    vkontakte = driver.find_element(By.XPATH, '//*[contains(@aria-label, "Соцсети, vkontakte")]').get_attribute('href')
                    whatsapp = driver.find_element(By.XPATH, '//*[contains(@aria-label, "Соцсети, whatsapp")]').get_attribute('href')
                    telegram = driver.find_element(By.XPATH, '//*[contains(@aria-label, "Соцсети, telegram")]').get_attribute('href')
                    site = driver.find_element(By.CSS_SELECTOR, 'div.action-button-view._type_web a').get_attribute('href')
                except:
                    pass  # Пропуск, если информация недоступна

                data.append({
                    'City': city,
                    'Title': title,
                    'Number': phone_number,
                    'VKontakte': vkontakte,
                    'Whatsapp': whatsapp,
                    'Telegram': telegram,
                    'Site': site
                })

                # Возврат на страницу результатов поиска
                driver.back()
                WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CLASS_NAME, 'scroll__content')))

            except Exception as e:
                print(f"Произошла ошибка во время сбора данных из сниппета: {e}")
                continue  # Продолжение цикла в случае возникновения исключения

# Код для сохранения данных в Excel
df = pd.DataFrame(data)
df.to_excel('output1.xlsx', index=False)
driver.quit()
print("Данные собраны и сохранены в Excel.")