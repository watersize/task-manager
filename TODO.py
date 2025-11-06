import csv
import os
import re

from colorama import Fore, init
from prettytable import PrettyTable

init()

RED = "\033[0;31;40m" #RED
GREEN = "\033[0;32;40m" # GREEN
YELLOW = "\033[0;33;40m" # Yellow
BLUE = "\033[0;34;40m" # Blue
RESET = "\033[0m" # Reset


table_of_TODO = PrettyTable(["Time: ", "TODO list:", "Comments: "])
print(table_of_TODO)

table_of_command = PrettyTable(["Command: ", "Do: "])
table_of_command.add_row([RESET+YELLOW+"add"+RESET, RESET+BLUE+"Добавляем эллемент в таблицу"+RESET])
table_of_command.add_row([RESET+YELLOW+"print_table"+RESET, RESET+BLUE+"Выводим таблицу"+RESET])
table_of_command.add_row([RESET+YELLOW+"save_result"+RESET, RESET+BLUE+"Сохраняет результат"+RESET])
table_of_command.add_row([RESET+YELLOW+"list_files"+RESET, RESET+BLUE+"Список имеющихся файлов"+RESET])
table_of_command.add_row([RESET+YELLOW+"crate_table"+RESET, RESET+BLUE+"Создать новые столбцы для таблицы"+RESET])
table_of_command.add_row([RESET+YELLOW+"open_file"+RESET, RESET+BLUE+"Открывает файл, в котором сохранена таблица"+RESET])
table_of_command.add_row([RESET+YELLOW+"delete_file"+RESET, RESET+BLUE+"Удаление файла"+RESET])
table_of_command.add_row([RESET+YELLOW+"delete"+RESET, RESET+BLUE+"Удаляем строку из таблицы по номеру столбца"+RESET])
table_of_command.add_row([RESET+YELLOW+"delete_all"+RESET, RESET+BLUE+"Удаляем все строки"+RESET])
table_of_command.add_row([RESET+YELLOW+"close"+RESET, RESET+BLUE+"Выключить программу"+RESET])


def check_time_format(time_str):  
		pattern = r'^([0-5]?\d):([0-5]?\d)$'
		match = re.match(pattern, time_str)
		if not match:
			print("Неверный ввод, должно быть XX:XX")
			return False
		
		hours, minutes = map(int, match.groups())

		if hours > 59 or minutes > 59:
			print(f"Время {hours}:{minutes} выходит за рамки допустимого диапазона (00:00-59:59)")
			return False
		
		return True
		
while True:
	print("Введите команду, help - для помощи")
	comm = input("--> ")

	match comm:
		case 'add':
			while True:
				print("ex - для выхода")
				print("Введите занятие")
				move = input(Fore.YELLOW + "--> " + RESET)
				if move == 'ex':
						break
				
				while True:
					print("Введите время (формат XX:XX)")
					time_of_move_our = input(Fore.YELLOW + "--> " + RESET)
					if time_of_move_our == 'ex':
						break
					if check_time_format(time_of_move_our):
						break
					else:
						print("Try again")
						
				print("Введите комментарий для занятия")
				comment = input(Fore.YELLOW + "--> " + RESET)
				if comment == 'ex':
					break
				# Основные поля
				new_row = [time_of_move_our, move, comment]
				
				# Проходим по дополнительным столбцам (если ониесть)
				field_names = table_of_TODO.field_names
				for column_name in field_names[3:] :
					value = input(f"Что вы хотите записать в поле \"{column_name}\": ")
					new_row.append(value)
					
				# Добавляем строку в таблицу
				table_of_TODO.add_row(new_row)
				print(table_of_TODO)

		case 'delete':
			print("введите строку в таблице, которую надо удалить")
			num_of_delete_string = int(input("--> "))
			table_of_TODO.del_row(num_of_delete_string - 1)

		case 'print_table':
			print(table_of_TODO)

		case 'help':
			print(table_of_command)

		case 'save_result':
			print("как будет называться файл")
			name_of_file = input("--> ")
			with open(f'{name_of_file}.csv', 'w', newline='', encoding='utf-8') as file:
				writer = csv.writer(file)
				writer.writerow(table_of_TODO.field_names)
				for row in table_of_TODO._rows:
						writer.writerow(row)
	
		case 'open_file':
			print("введите название файла, который нужно открыть")
			name_file = input("--> ")
			try:
				with open(f'{name_file}.csv', 'r', encoding='utf-8') as file:
					reader = csv.reader(file)
					table_of_TODO.field_names = next(reader)
					for row in reader:
						table_of_TODO.add_row(row)
			except FileNotFoundError:
				print("Файл не найден")
		
		case 'delete_file':
			print("Введите название файла, который нужно удалить")

			filename = input("--> ")

			if os.path.exists(f"{filename}.csv"):
				confirm = input(f"удалить: {filename}.csv? (y/n): ").strip().lower()

				if confirm == 'y':
					os.remove(f"{filename}.csv")
					print(f"Файл '{filename}' удален")
				else:
					print("Операция отменена")
			else:
				print("Файл не существует")

		case 'list_files':
			files = [f for f in os.listdir('.') if f.endswith('.csv')]
			if len(files) > 0:
				print("Доступные файлы (.csv): ")
				for i, file in enumerate(files, start=1):
					print(f"{i}, {file}")
			else:
				print("Нет доступных .csv файлов")

		case 'delete_all':
			table_of_TODO.clear_rows()
		
		case "create_table":
			while True:
				print("Ваша тоблица очиститься, продоложить?")
				print("y/n")
				yes_or_no = input("--> ")
				if yes_or_no == 'y':
					while True:
						table_of_TODO.clear_rows()
						print(table_of_TODO)
						print("введите название колонки, которую хотите добавить, ex - для выхода")
						name_of_table = input("--> ")
						if name_of_table == 'ex':
							break
						table_of_TODO.add_column(name_of_table, [])
						print("Теперь таблица выглядит так")
						print(table_of_TODO)
				else:
					break

				break

		case 'close':
			break

		case _:
			print("Ошибка ввода")

	table_of_TODO.sortby = 'Time: '

print()
input()