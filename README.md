# joesnewbalanceoutlet.com Парсер

https://www.joesnewbalanceoutlet.com/


### Описание
Парсер принимает на вход продуктовые ссылки и собирает информацию о товарах (все варианты по цветам и размерам). На выходе получаем json файл с собранной информацией

### Установка

Выполните команды

```
git clone git@github.com:NASTY-SMIT/joesnewbalanceoutlet_parser.git
pip3 install -r joesnewbalanceoutlet_parser/requirements.txt
cd joesnewbalanceoutlet_parser
```

Создайте в корне проекта файл .env и впишите туда данные о прокси и debug режиме, пример оформления можно посмотреть в файле .env.example

```
DEBUG=True
PROXIES_JSON=[{"url":"...","user":"...","pass":"..."},{"url":"...","user":"...","pass":"..."}]
```

## Запуск

Вариант 1 - командой

```
python3 main.py
```

Вариант 2 - через bash файл
```
sudo bash stocks.sh
```

#### Итоговый файл уже собранных товаров лежит в корне проекта joesnewbalanceoutlet_com-stocks-2026-04-16_16-12.json