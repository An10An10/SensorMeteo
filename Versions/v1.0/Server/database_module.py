import sqlite3

DB_FILE = 'system_data.db'

def init_db():
    """Создает таблицы. Поле user_id помечено как UNIQUE для корректной работы обновлений."""
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        # Таблица 2: id (датчика), t (температура), h (влажность), p (давление)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS measurements (
                id INTEGER PRIMARY KEY,
                t REAL,
                h REAL,
                p REAL
            )
        ''')
        # Таблица 1: id, user_id (уникальный), mesto (название), list_ids (строка "1,2,3")
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS locations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER UNIQUE,
                mesto TEXT,
                list_ids TEXT
            )
        ''')
        conn.commit()

def get_measurement_by_id(sensor_id: int):
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM measurements WHERE id = ?', (sensor_id,))
        return cursor.fetchone()

def create_user(user_id: int, mesto: str = ""):
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        try:
            cursor.execute(
                'INSERT INTO locations (user_id, mesto, list_ids) VALUES (?, ?, ?)', 
                (user_id, mesto, "")
            )
            conn.commit()
            print(f"✅ Пользователь {user_id} успешно создан.")
            return True
        except sqlite3.IntegrityError:
            print(f"⚠️ Пользователь {user_id} уже существует.")
            return False

def append_sensor_to_user(user_id: int, sensor_id: int):
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT list_ids FROM locations WHERE user_id = ?', (user_id,))
        result = cursor.fetchone()

        if result:
            current_ids = [x for x in result[0].split(',') if x] if result[0] else []
            if str(sensor_id) not in current_ids:
                current_ids.append(str(sensor_id))
                new_str = ",".join(current_ids)
                cursor.execute('UPDATE locations SET list_ids = ? WHERE user_id = ?', (new_str, user_id))
        else:
            # Если юзера нет, создаем новую запись
            cursor.execute('INSERT INTO locations (user_id, mesto, list_ids) VALUES (?, ?, ?)', 
                           (user_id, "Мой дом", str(sensor_id)))
        conn.commit()

def update_user_mesto(user_id: int, coord_str: str):
    try:
        # Удаляем пробелы и делим по запятой
        parts = coord_str.replace(" ", "").split(',')
        if len(parts) != 2:
            return False
            
        lat, lon = float(parts[0]), float(parts[1])
        
        # Проверяем диапазоны широт и долгот
        if not (-90 <= lat <= 90 and -180 <= lon <= 180):
            return False
            
        with sqlite3.connect(DB_FILE) as conn:
            conn.execute('UPDATE locations SET mesto = ? WHERE user_id = ?', 
                         (f"{lat},{lon}", user_id))
            conn.commit()
        return True
    except:
        return False

def remove_sensor_from_user(user_id: int, sensor_id: int):
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        
        # 1. Получаем текущий список
        cursor.execute('SELECT list_ids FROM locations WHERE user_id = ?', (user_id,))
        result = cursor.fetchone()
        
        if result and result[0]:
            current_ids = [x for x in result[0].split(',') if x]
            
            # 2. Если такой ID есть в списке — удаляем его
            if str(sensor_id) in current_ids:
                current_ids.remove(str(sensor_id))
                
                # 3. Собираем строку обратно
                new_ids_str = ",".join(current_ids)
                
                # 4. Сохраняем обновление
                cursor.execute('UPDATE locations SET list_ids = ? WHERE user_id = ?', 
                               (new_ids_str, user_id))
                conn.commit()
                print(f"Датчик {sensor_id} отвязан от пользователя {user_id}")
                return True
        
        print(f"Датчик {sensor_id} не найден у пользователя {user_id}")
        return False

def save_measurement(sensor_id, t, h, p):
    """Сохраняет t, h и p для датчика."""
    with sqlite3.connect(DB_FILE) as conn:
        conn.execute('INSERT OR REPLACE INTO measurements (id, t, h, p) VALUES (?, ?, ?, ?)', 
                     (sensor_id, t, h, p))
        conn.commit()

def get_full_user_data(user_id):
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT mesto, list_ids FROM locations WHERE user_id = ?', (user_id,))
        user_row = cursor.fetchone()
        
        if not user_row: return None
        
        mesto, s_ids_str = user_row
        sensor_ids = [int(x) for x in s_ids_str.split(',') if x] if s_ids_str else []
        
        sensors_list = []
        for sid in sensor_ids:
            cursor.execute('SELECT t, h, p FROM measurements WHERE id = ?', (sid,))
            meas = cursor.fetchone()
            
            if meas:
                sensors_list.append({
                    "id": sid,
                    "t": meas[0],
                    "h": meas[1],
                    "p": meas[2]
                })
            else:
                sensors_list.append({"id": sid, "info": "нет данных"})
        
        return {"user_id": user_id, "mesto": mesto, "sensors": sensors_list}


def get_meas_with_check(user_id: int, sensor_id: int):
    """
    Проверяет права доступа пользователя к датчику 
    и возвращает кортеж (id, t, h, p)
    """
    data = get_full_user_data(user_id)
    if data:
        for s in data['sensors']:
            if s['id'] == sensor_id:
                return (s['id'], s.get('t'), s.get('h'), s.get('p'))
    return None

if __name__ == "__main__":
    init_db()
