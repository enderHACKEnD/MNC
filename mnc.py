import json
from mcstatus import JavaServer
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading
import os

# ===== НАСТРОЙКА =====
NODE_PREFIXES = ["a"]
NODE_COUNT = 1
DOMAIN = "Domen.com"
START_PORT = 25000 
END_PORT = 26000 
THREADS = 10 
OUTPUT_FILE = "servers.json" 

lock = threading.Lock()
existing_set = set()
total_checked = [0]

# Сохранение данных
if os.path.exists(OUTPUT_FILE):
    try:
        with open(OUTPUT_FILE, "r", encoding="utf-8") as f:
            for s in json.load(f):
                existing_set.add(f"{s['host']}:{s['port']}")
    except Exception:
        existing_set = set()

def save_server(server):
    """Добавляем один сервер в JSON без чтения всего файла"""
    if not os.path.exists(OUTPUT_FILE) or os.stat(OUTPUT_FILE).st_size == 0:
        data = []
    else:
        with open(OUTPUT_FILE, "r+", encoding="utf-8") as f:
            try:
                data = json.load(f)
            except json.JSONDecodeError:
                data = []
    data.append(server)
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

def check_nodes_port(node_number, port, total):
    """Проверяет все ноды с одним номером на одном порту"""
    for prefix in NODE_PREFIXES:
        try:
            node = f"{prefix}{node_number}.{DOMAIN}"
            server = JavaServer.lookup(f"{node}:{port}")
            status = server.status()
            key = f"{node}:{port}"
            with lock:
                if key not in existing_set:
                    server_data = {
                        "host": node,
                        "port": port,
                        "online": True,
                        "players_online": status.players.online,
                        "players_max": status.players.max,
                        "version": status.version.name
                    }
                    existing_set.add(key)
                    save_server(server_data)
                    print(f"\n[+] Найден новый сервер: {key} | "
                          f"{status.players.online}/{status.players.max} | {status.version.name}")
        except Exception:
            pass
    
    with lock:
        total_checked[0] += 1
        print(f"Проверено: {total_checked[0]}/{total} - все ноды {node_number} на порту {port}", end="\r")

def main():
    # Генерируем все комбинации номер_ноды:порт
    tasks = []
    for node_number in range(1, NODE_COUNT + 1):
        for port in range(START_PORT, END_PORT + 1):
            tasks.append((node_number, port))
    
    total = len(tasks)
    total_nodes = len(NODE_PREFIXES) * NODE_COUNT
    total_combinations = total_nodes * (END_PORT - START_PORT + 1)
    
    print(f"Начинаю сканирование {total_combinations} комбинаций")
    print(f"Проверяю все префиксы ({', '.join(NODE_PREFIXES)}) для каждого номера ноды одновременно")
    print(f"Используется {THREADS} потоков")
    
    # Проверяем все комбинации одновременно
    with ThreadPoolExecutor(max_workers=THREADS) as executor:
        futures = [executor.submit(check_nodes_port, node_number, port, total) 
                  for node_number, port in tasks]
        
        for future in as_completed(futures):
            try:
                future.result()
            except Exception as e:
                print(f"\n Ошибка: {e}")

    print(f"\nСканирование завершено. Всего найдено {len(existing_set)} серверов.")

if __name__ == "__main__":
    main()
