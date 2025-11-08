import csv
import json
import os
import re

from colorama import Fore, init
from prettytable import PrettyTable

init()

RED = "\033[0;31;40m"  # RED
GREEN = "\033[0;32;40m"  # GREEN
YELLOW = "\033[0;33;40m"  # YELLOW
BLUE = "\033[0;34;40m"  # BLUE
RESET = "\033[0m"  # Reset

table_of_TODO = PrettyTable(["Time: ", "TODO list:", "Comments: "])

table_of_command = PrettyTable(["Command: ", "Do: "])
table_of_command.add_row(
    [
        RESET + YELLOW + "add" + RESET,
        RESET + BLUE + "Добавляем элемент в таблицу" + RESET,
    ]
)
table_of_command.add_row(
    [RESET + YELLOW + "print_table" + RESET, RESET + BLUE + "Выводим таблицу" + RESET]
)
table_of_command.add_row(
    [
        RESET + YELLOW + "save_result" + RESET,
        RESET + BLUE + "Сохраняет результат" + RESET,
    ]
)
table_of_command.add_row(
    [
        RESET + YELLOW + "list_files" + RESET,
        RESET + BLUE + "Список имеющихся файлов" + RESET,
    ]
)
table_of_command.add_row(
    [
        RESET + YELLOW + "add_column" + RESET,
        RESET + BLUE + "Создать новые столбцы для таблицы" + RESET,
    ]
)
table_of_command.add_row(
    [
        RESET + YELLOW + "open_file" + RESET,
        RESET + BLUE + "Открывает файл, в котором сохранена таблица" + RESET,
    ]
)
table_of_command.add_row(
    [RESET + YELLOW + "delete_file" + RESET, RESET + BLUE + "Удаление файла" + RESET]
)
table_of_command.add_row(
    [
        RESET + YELLOW + "delete" + RESET,
        RESET + BLUE + "Удаляем строку из таблицы по номеру строки" + RESET,
    ]
)
table_of_command.add_row(
    [RESET + YELLOW + "delete_all" + RESET, RESET + BLUE + "Удаляем все строки" + RESET]
)
table_of_command.add_row(
    [
        RESET + YELLOW + "delete_column" + RESET,
        RESET + BLUE + "Удаляет указанный столбец" + RESET,
    ]
)
table_of_command.add_row(
    [
        RESET + YELLOW + "clear_all" + RESET,
        RESET + BLUE + "Возвращаем таблицу в первоначальное состояние" + RESET,
    ]
)
table_of_command.add_row(
    [RESET + YELLOW + "clear_all" + RESET, RESET + BLUE + "Возвращаем таблицу в первоначальное состояние" + RESET]
)
table_of_command.add_row(
    [RESET + YELLOW + "edit" + RESET, RESET + BLUE + "Редактировать строку по номеру" + RESET]
)
table_of_command.add_row(
    [RESET + YELLOW + "find" + RESET, RESET + BLUE + "Поиск по задачам и комментариям" + RESET]
)
table_of_command.add_row(
    [RESET + YELLOW + "export_json" + RESET, RESET + BLUE + "Экспорт таблицы в JSON" + RESET]
)
table_of_command.add_row(
    [RESET + YELLOW + "import_json" + RESET, RESET + BLUE + "Импорт таблицы из JSON" + RESET]
)
table_of_command.add_row(
    [RESET + YELLOW + "close" + RESET, RESET + BLUE + "Выключить программу" + RESET]
)

# автосохранение
AUTOSAVE = True
AUTOSAVE_FILE = "tasks_autosave.csv"

def check_time_format(time_str):
    """
    Проверяет формат времени и нормализует его в "HH:MM".
    Возвращает строку "HH:MM" при корректном вводе или False при ошибке.
    """
    if not isinstance(time_str, str):
        print("Неверный ввод: ожидается строка формата XX:XX")
        return False

    time_str = time_str.strip()
    pattern = r"^(\d{1,2}):(\d{1,2})$"
    match = re.match(pattern, time_str)
    if not match:
        print("Неверный ввод, должно быть XX:XX")
        return False

    hours, minutes = map(int, match.groups())

    if hours < 0 or hours > 23:
        print(f"Неверный час: {hours}. Допустимый диапазон 00-23.")
        return False

    if minutes < 0 or minutes > 59:
        print(f"Неверная минута: {minutes}. Допустимый диапазон 00-59.")
        return False

    return f"{hours:02d}:{minutes:02d}"


def save_to_csv(filename):
    try:
        with open(filename, "w", newline="", encoding="utf-8") as file:
            writer = csv.writer(file)
            writer.writerow(table_of_TODO.field_names)
            for row in table_of_TODO._rows:
                writer.writerow(row)
    except Exception as e:
        print("Ошибка при сохранении:", e)


def load_from_csv(filename):
    if not os.path.exists(filename):
        return False
    try:
        with open(filename, "r", encoding="utf-8") as file:
            reader = csv.reader(file)
            cols = next(reader)
            table_of_TODO.field_names = cols
            table_of_TODO.clear_rows()
            for row in reader:
                table_of_TODO.add_row(row)
        return True
    except Exception as e:
        print("Ошибка при загрузке:", e)
        return False


def export_json(filename):
    data = []
    for row in table_of_TODO._rows:
        entry = {name: value for name, value in zip(table_of_TODO.field_names, row)}
        data.append(entry)
    try:
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print("Ошибка при экспорте в JSON:", e)


def import_json(filename):
    if not os.path.exists(filename):
        print("Файл не найден")
        return
    try:
        with open(filename, "r", encoding="utf-8") as f:
            data = json.load(f)
        if not data:
            print("JSON пустой")
            return
        # Установим поля как ключи первого объекта
        keys = list(data[0].keys())
        table_of_TODO.field_names = keys
        table_of_TODO.clear_rows()
        for item in data:
            row = [item.get(k, "") for k in keys]
            table_of_TODO.add_row(row)
    except Exception as e:
        print("Ошибка при импорте из JSON:", e)


# автозагрузка при старте, если есть файл автосохранения
if AUTOSAVE and os.path.exists(AUTOSAVE_FILE):
    load_from_csv(AUTOSAVE_FILE)

def prompt_int(prompt_text):
    try:
        return int(input(prompt_text))
    except ValueError:
        return None

def main():
    while True:
        print("Введите команду, help - для помощи")
        comm = input("--> ").strip()

        match comm:
            case "add":
                while True:
                    print("ex - для выхода")
                    print("Введите занятие")
                    move = input(Fore.YELLOW + "--> " + RESET)
                    if move == "ex":
                        break

                    while True:
                        print("Введите время (формат XX:XX)")
                        time_of_move_our = input(Fore.YELLOW + "--> " + RESET)
                        if time_of_move_our == "ex":
                            break
                        normalized = check_time_format(time_of_move_our)
                        if normalized:
                            time_of_move_our = normalized
                            break
                        else:
                            print("Попробуйте снова")

                    if time_of_move_our == "ex":
                        break

                    print("Введите комментарий для занятия")
                    comment = input(Fore.YELLOW + "--> " + RESET)
                    if comment == "ex":
                        break

                    additional_columns = []
                    for column_name in table_of_TODO.field_names[3:]:
                        value = (
                            input(
                                f"Заполните поле '{column_name}' (оставьте пустым, если ничего не вводить): "
                            )
                            or ""
                        )
                        additional_columns.append(value)

                    new_row = [time_of_move_our, move, comment] + additional_columns
                    table_of_TODO.add_row(new_row)
                    print(table_of_TODO)
                    if AUTOSAVE:
                        save_to_csv(AUTOSAVE_FILE)

            case "delete":
                print("Введите номер строки в таблице, которую нужно удалить")
                num = prompt_int("--> ")
                if num is None:
                    print("Ожидалось число.")
                else:
                    try:
                        table_of_TODO.del_row(num - 1)
                        if AUTOSAVE:
                            save_to_csv(AUTOSAVE_FILE)
                    except IndexError:
                        print("Строка с таким номером не найдена.")

            case "print_table":
                print(table_of_TODO)

            case "help":
                print(table_of_command)

            case "save_result":
                print("Как будет называться файл?")
                name_of_file = input("--> ")
                save_to_csv(f"{name_of_file}.csv")
                print("Сохранено.")
                if AUTOSAVE:
                    save_to_csv(AUTOSAVE_FILE)

            case "open_file":
                print("Введите название файла, который нужно открыть")
                name_file = input("--> ")
                if load_from_csv(f"{name_file}.csv"):
                    print("Файл загружен.")
                else:
                    print("Не удалось открыть файл.")
                print(table_of_TODO)

            case "delete_file":
                print("Введите название файла, который нужно удалить")
                filename = input("--> ")
                if os.path.exists(f"{filename}.csv"):
                    confirm = input(f"Удалить файл {filename}.csv? (y/n): ").strip().lower()
                    if confirm == "y":
                        os.remove(f"{filename}.csv")
                        print(f"Файл '{filename}' удалён")
                    else:
                        print("Операция отменена")
                else:
                    print("Файл не существует")

            case "list_files":
                files = [f for f in os.listdir(".") if f.endswith(".csv")]
                if len(files) > 0:
                    print("Доступные файлы (.csv): ")
                    for i, file in enumerate(files, start=1):
                        print(f"{i}. {file}")
                else:
                    print("Нет доступных .csv файлов")

            case "delete_all":
                confirm = input("Удалить все строки? (y/n): ").strip().lower()
                if confirm == "y":
                    table_of_TODO.clear_rows()
                    if AUTOSAVE:
                        save_to_csv(AUTOSAVE_FILE)
                    print("Все строки удалены.")

            case "add_column":
                while True:
                    print("Ваша таблица очистится, продолжить?")
                    print("y/n")
                    yes_or_no = input("--> ")
                    if yes_or_no == "y":
                        table_of_TODO.clear_rows()
                        print(table_of_TODO)
                        print(
                            "Введите название колонки, которую хотите добавить, ex - для выхода"
                        )
                        name_of_table = input("--> ")
                        if name_of_table == "ex":
                            break
                        table_of_TODO.add_column(name_of_table, [])
                        print("Теперь таблица выглядит так:")
                        print(table_of_TODO)
                        if AUTOSAVE:
                            save_to_csv(AUTOSAVE_FILE)
                    else:
                        break

            case "delete_column":
                print("Удаление столбца")
                print(
                    "Введите название столбца, который хотите удалить, или введите 'all' для удаления всех столбцов, кроме трех базовых"
                )
                col_to_delete = input("--> ")
                if col_to_delete.lower() == "all":
                    basic_columns = ["Time: ", "TODO list:", "Comments: "]
                    for col in table_of_TODO.field_names[:]:
                        if col not in basic_columns:
                            table_of_TODO.del_column(col)
                    if AUTOSAVE:
                        save_to_csv(AUTOSAVE_FILE)
                elif col_to_delete in table_of_TODO.field_names:
                    table_of_TODO.del_column(col_to_delete)
                    if AUTOSAVE:
                        save_to_csv(AUTOSAVE_FILE)
                else:
                    print("Такого столбца не существует!")

            case "clear_all":
                confirm = input("Восстановить таблицу в исходное состояние? (y/n): ").strip().lower()
                if confirm == "y":
                    table_of_TODO.clear()
                    table_of_TODO.field_names = ["Time: ", "TODO list:", "Comments: "]
                    if AUTOSAVE:
                        save_to_csv(AUTOSAVE_FILE)
                    print("Таблица восстановлена в исходное состояние.")

            case "edit":
                print("Введите номер строки для редактирования")
                num = prompt_int("--> ")
                if num is None:
                    print("Ожидалось число.")
                else:
                    idx = num - 1
                    try:
                        row = table_of_TODO._rows[idx]
                        print("Текущая строка:", row)
                        # редактируем по полям
                        new_row = []
                        for i, col in enumerate(table_of_TODO.field_names):
                            cur = row[i] if i < len(row) else ""
                            val = input(f"{col} (текущее: '{cur}') - оставить пустым для сохранения: ")
                            if val == "":
                                new_row.append(cur)
                            else:
                                if i == 0:
                                    norm = check_time_format(val)
                                    if not norm:
                                        print("Время не изменено (неправильный формат).")
                                        new_row.append(cur)
                                    else:
                                        new_row.append(norm)
                                else:
                                    new_row.append(val)
                        table_of_TODO._rows[idx] = new_row
                        if AUTOSAVE:
                            save_to_csv(AUTOSAVE_FILE)
                    except IndexError:
                        print("Строка с таким номером не найдена.")

            case "find":
                print("Введите поисковую строку")
                q = input("--> ").strip().lower()
                if not q:
                    print("Пустой запрос")
                else:
                    results = PrettyTable(table_of_TODO.field_names)
                    for r in table_of_TODO._rows:
                        # ищем в каждой ячейке
                        if any(q in str(cell).lower() for cell in r):
                            results.add_row(r)
                    if results.rowcount == 0:
                        print("Ничего не найдено")
                    else:
                        print(results)

            case "export_json":
                print("Как назвать файл для экспорта (без расширения)?")
                name = input("--> ").strip()
                if name:
                    export_json(f"{name}.json")
                    print("Экспорт выполнен.")

            case "import_json":
                print("Какой JSON-файл импортировать (без расширения)?")
                name = input("--> ").strip()
                if name:
                    import_json(f"{name}.json")
                    if AUTOSAVE:
                        save_to_csv(AUTOSAVE_FILE)
                    print("Импорт выполнен.")

            case "close":
                # при выходе сохраняем автосохранение
                if AUTOSAVE:
                    save_to_csv(AUTOSAVE_FILE)
                break

            case _:
                print("Ошибка ввода")

        table_of_TODO.sortby = "Time: "

if __name__ == "__main__":
    main()