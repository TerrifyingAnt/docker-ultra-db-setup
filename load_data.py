import pandas as pd
import psycopg2
from psycopg2 import sql

# Подключение к базе данных PostgreSQL
def connect_to_db():
    return psycopg2.connect(
        dbname="mobiles_db",
        user="ant",
        password="postgres",
        host="localhost",
        port="6543"
    )

# Загрузка данных из CSV
def load_csv(file_path):
    try:
        # Попробуем прочитать как CSV
        df = pd.read_excel(file_path, encoding="UTF-8")
    except UnicodeDecodeError:
        # Если возникла ошибка кодировки, попробуем другую кодировку
        df = pd.read_csv(file_path, encoding='latin1')
    except Exception:
        # Если это не CSV, попробуем прочитать как Excel
        df = pd.read_excel(file_path)
    
    # Приведем названия столбцов к нижнему регистру и удалим лишние пробелы
    df.columns = df.columns.str.strip().str.lower()
    return df

# Вставка данных в таблицу company_table
def insert_companies(cursor, companies):
    for company in companies:
        cursor.execute(
            sql.SQL("INSERT INTO company_table (id_company, name) VALUES (%s, %s) ON CONFLICT (id_company) DO NOTHING"),
            (company['id_company'], company['name'])
        )

# Вставка данных в таблицу model_table
def insert_models(cursor, models):
    for model in models:
        cursor.execute(
            sql.SQL("INSERT INTO model_table (id_model, id_company, name) VALUES (%s, %s, %s) ON CONFLICT (id_model) DO NOTHING"),
            (model['id_model'], model['id_company'], model['name'])
        )

# Вставка данных в таблицу characteristics_table
def insert_characteristics(cursor, characteristics):
    for char in characteristics:
        cursor.execute(
            sql.SQL("""
                INSERT INTO characteristics_table (id_model, weight, ram, front_camera, back_camera, processor, battery_capacity, screen_size)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (id_model) DO NOTHING
            """),
            (
                char['id_model'],
                char['weight'],
                char['ram'],
                char['front_camera'],
                char['back_camera'],
                char['processor'],
                char['battery_capacity'],
                char['screen_size']
            )
        )

# Вставка данных в таблицу region_table
def insert_regions(cursor, regions):
    for region in regions:
        cursor.execute(
            sql.SQL("INSERT INTO region_table (id_region, name) VALUES (%s, %s) ON CONFLICT (id_region) DO NOTHING"),
            (region['id_region'], region['name'])
        )

# Вставка данных в таблицу price_table
def insert_prices(cursor, prices):
    for price in prices:
        cursor.execute(
            sql.SQL("""
                INSERT INTO price_table (id_price, id_model, id_region, start_price)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (id_price) DO NOTHING
            """),
            (
                price['id_price'],
                price['id_model'],
                price['id_region'],
                price['start_price']
            )
        )

# Вставка данных в таблицу start_year_table
def insert_start_years(cursor, years):
    for year in years:
        cursor.execute(
            sql.SQL("INSERT INTO start_year_table (id_model, start_year) VALUES (%s, %s) ON CONFLICT (id_model) DO NOTHING"),
            (year['id_model'], year['start_year'])
        )

# Основная функция для загрузки данных
def main(csv_file):
    # Загрузка данных из CSV
    df = load_csv(csv_file, )

    # Проверяем наличие нужных столбцов
    required_columns = {'company name', 'model name', 'mobile weight', 'ram', 'front camera', 
                        'back camera', 'processor', 'battery capacity', 'screen size', 
                        'launched price (pakistan)', 'launched price (india)', 
                        'launched price (china)', 'launched price (usa)', 
                        'launched price (dubai)', 'launched year'}
    if not required_columns.issubset(df.columns):
        missing_columns = required_columns - set(df.columns)
        raise ValueError(f"Отсутствуют следующие столбцы: {missing_columns}")

    # Создание уникальных ID для компаний
    companies = [{'id_company': i + 1, 'name': name} for i, name in enumerate(df['company name'].unique())]
    company_map = {company['name']: company['id_company'] for company in companies}

    # Создание уникальных ID для моделей
    models = []
    for i, row in df.iterrows():
        models.append({
            'id_model': i + 1,
            'id_company': company_map[row['company name']],
            'name': row['model name']
        })

    # Создание характеристик
    characteristics = []
    for i, row in df.iterrows():
        characteristics.append({
            'id_model': i + 1,
            'weight': float(row['mobile weight'].replace('g', '').strip()),
            'ram': int(float(row['ram'].replace('GB', '').split("/")[0].strip())),
            'front_camera': int(float(row['front camera'].replace('MP', '').split("/")[0].split("+")[0].replace("Dual", "").replace("(ultrawide)", "").split(",")[0].strip())),
            'back_camera': int(float(row['back camera'].split('+')[0].replace('MP', '').split(" ")[0].strip())),
            'processor': row['processor'],
            'battery_capacity': int(row['battery capacity'].replace(',', '').replace('mAh', '').strip()),
            'screen_size': row['screen size']
        })

    # Создание регионов
    regions = [
        {'id_region': 1, 'name': 'Pakistan'},
        {'id_region': 2, 'name': 'India'},
        {'id_region': 3, 'name': 'China'},
        {'id_region': 4, 'name': 'USA'},
        {'id_region': 5, 'name': 'Dubai'}
    ]
    region_map = {region['name']: region['id_region'] for region in regions}

    # Создание цен
    prices = []
    for i, row in df.iterrows():
        for region_name, price_col in [
            ('Pakistan', 'launched price (pakistan)'),
            ('India', 'launched price (india)'),
            ('China', 'launched price (china)'),
            ('USA', 'launched price (usa)'),
            ('Dubai', 'launched price (dubai)')
        ]:
            price = row[price_col].replace('PKR ', '').replace('INR ', '').replace('CNY ', '').replace('USD ', '').replace('AED ', '').replace(',', '')
            prices.append({
                'id_price': f"{i + 1}",
                'id_model': i + 1,
                'id_region': region_map[region_name],
                'start_price': float(price.replace("¥", "").replace("�", "").replace("Not available", "0"))
            })

    # Создание годов выпуска
    start_years = []
    for i, row in df.iterrows():
        start_years.append({
            'id_model': i + 1,
            'start_year': int(row['launched year'])
        })

    # Вставка данных в базу данных
    conn = connect_to_db()
    try:
        with conn.cursor() as cursor:
            insert_companies(cursor, companies)
            insert_models(cursor, models)
            insert_characteristics(cursor, characteristics)
            insert_regions(cursor, regions)
            insert_prices(cursor, prices)
            insert_start_years(cursor, start_years)
        conn.commit()
    finally:
        conn.close()


if __name__ == "__main__":
    csv_file = "Mobiles Dataset (2025).xlsx"  # Укажите путь к вашему CSV-файлу
    main(csv_file)