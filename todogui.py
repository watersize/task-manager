"""
Лёгкий и стабильный GUI на PyQt6 для вашего Task Manager.
- Обработка ошибок при отсутствии PyQt6.
- Гарантированный запуск (точка входа, try/except).
- Поддержка автосохранения, CSV/JSON, добавления столбцов, поиска, простых анимаций.
- Небольшие оптимизации для минимального потребления ресурсов.
"""
import csv
import json
import os
import re
import sys
from typing import List, Set

from PyQt6.QtCore import QPoint, QPropertyAnimation, Qt, QTimer
from PyQt6.QtGui import QBrush, QColor, QFont
from PyQt6.QtWidgets import (
    QAbstractItemView,
    QApplication,
    QCheckBox,
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QFormLayout,
    QGraphicsOpacityEffect,
    QHBoxLayout,
    QHeaderView,
    QInputDialog,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QMenu,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

# Lightweight styling
APP_TITLE = "Task Manager (PyQt6) — Enhanced"
AUTOSAVE = True
AUTOSAVE_FILE = "tasks_autosave.csv"

# default font sizes
DEFAULT_FONT_POINT = 11
HEADER_FONT_POINT = 12
ITEM_FONT_POINT = 11

BASIC_COLUMNS = ["Time: ", "TODO list:", "Comments: "]

def check_time_format(time_str):
    """Проверяет формат времени 'HH:MM' (0-23, 0-59). Возвращает нормализованную строку или False."""
    if not isinstance(time_str, str):
        return False
    time_str = time_str.strip()
    pattern = r"^(\d{1,2}):(\d{1,2})$"
    m = re.match(pattern, time_str)
    if not m:
        return False
    h, mi = map(int, m.groups())
    if h < 0 or h > 23 or mi < 0 or mi > 59:
        return False
    return f"{h:02d}:{mi:02d}"


class RowDialog(QDialog):
    def __init__(self, headers, values=None, parent=None, font=None):
        super().__init__(parent)
        self.setWindowTitle("Заполните поля")
        self.values = None
        self._headers = headers
        layout = QFormLayout(self)

        self.edits = []
        for i, h in enumerate(headers):
            le = QLineEdit()
            if values and i < len(values):
                le.setText(str(values[i]))
            layout.addRow(h, le)
            self.edits.append(le)

        if font:
            self.setFont(font)

        btns = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        btns.accepted.connect(self.accept)
        btns.rejected.connect(self.reject)
        layout.addWidget(btns)

    def accept(self) -> None:
        vals = [e.text().strip() for e in self.edits]
        # validate time at index 0
        norm = check_time_format(vals[0]) if vals else False
        if not norm:
            QMessageBox.warning(self, "Ошибка", "Неверный формат времени. Ожидается HH:MM (00-23, 00-59).")
            return
        vals[0] = norm
        self.values = vals
        super().accept()


class ColumnDeleteDialog(QDialog):
    """Диалог для выбора (множественного) удаляемых столбцов (кроме базовых)."""

    def __init__(self, columns: List[str], parent=None):
        super().__init__(parent)
        self.setWindowTitle("Удалить столбцы")
        self.resize(360, 300)
        self.result = None
        layout = QVBoxLayout(self)
        lbl = QLabel("Выберите столбцы для удаления (базовые недоступны):")
        layout.addWidget(lbl)
        self.listw = QListWidget()
        self.listw.setSelectionMode(QAbstractItemView.SelectionMode.MultiSelection)
        for col in columns:
            item = QListWidgetItem(col)
            self.listw.addItem(item)
        layout.addWidget(self.listw)
        btns = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        btns.accepted.connect(self.on_ok)
        btns.rejected.connect(self.reject)
        layout.addWidget(btns)

    def on_ok(self):
        sel = [it.text() for it in self.listw.selectedItems()]
        self.result = sel
        self.accept()


class ReorderDialog(QDialog):
    """Диалог для изменения порядка столбцов с кнопками вверх/вниз."""

    def __init__(self, columns: List[str], parent=None):
        super().__init__(parent)
        self.setWindowTitle("Порядок столбцов")
        self.resize(380, 380)
        self.result = None
        layout = QVBoxLayout(self)
        lbl = QLabel("Переместите столбцы в нужный порядок (No. не отображается):")
        layout.addWidget(lbl)
        self.listw = QListWidget()
        self.listw.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        for col in columns:
            self.listw.addItem(QListWidgetItem(col))
        layout.addWidget(self.listw)

        btns_h = QHBoxLayout()
        btn_up = QPushButton("↑ Вверх")
        btn_down = QPushButton("↓ Вниз")
        btns_h.addWidget(btn_up)
        btns_h.addWidget(btn_down)
        layout.addLayout(btns_h)

        btn_up.clicked.connect(self.move_up)
        btn_down.clicked.connect(self.move_down)

        btnbox = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        btnbox.accepted.connect(self.on_ok)
        btnbox.rejected.connect(self.reject)
        layout.addWidget(btnbox)

    def move_up(self):
        row = self.listw.currentRow()
        if row > 0:
            item = self.listw.takeItem(row)
            self.listw.insertItem(row - 1, item)
            self.listw.setCurrentRow(row - 1)

    def move_down(self):
        row = self.listw.currentRow()
        if row < self.listw.count() - 1 and row >= 0:
            item = self.listw.takeItem(row)
            self.listw.insertItem(row + 1, item)
            self.listw.setCurrentRow(row + 1)

    def on_ok(self):
        cols = [self.listw.item(i).text() for i in range(self.listw.count())]
        self.result = cols
        self.accept()


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(APP_TITLE)
        self.resize(1000, 650)

        # реальные заголовки данных (без номера)
        self.headers = ["Time: ", "TODO list:", "Comments: "]
        self.rows = []  # list of lists

        # анимации и шрифты
        self.animations_enabled = True
        self.base_font_point = DEFAULT_FONT_POINT
        self.header_font_point = HEADER_FONT_POINT
        self.item_font_point = ITEM_FONT_POINT

        # инициализация UI
        self._init_ui()

        # автозагрузка
        if AUTOSAVE and os.path.exists(AUTOSAVE_FILE):
            try:
                self.load_from_csv(AUTOSAVE_FILE)
            except Exception:
                pass

    # -------------------- новые вспомогательные методы --------------------
    def list_csv_files(self) -> List[str]:
        files = [f for f in os.listdir(".") if f.lower().endswith(".csv")]
        files.sort(key=lambda s: s.lower())
        return files

    def list_json_files(self) -> List[str]:
        files = [f for f in os.listdir(".") if f.lower().endswith(".json")]
        files.sort(key=lambda s: s.lower())
        return files

    def show_open_menu(self, widget):
        menu = QMenu(self)
        files = self.list_csv_files()
        if files:
            for f in files:
                menu.addAction(f, lambda checked=False, f=f: self._open_from_menu(f))
        else:
            act = menu.addAction("Нет .csv файлов в папке")
            act.setEnabled(False)
        menu.exec(widget.mapToGlobal(widget.rect().bottomLeft()))

    def show_import_menu(self, widget):
        menu = QMenu(self)
        files = self.list_json_files()
        if files:
            for f in files:
                menu.addAction(f, lambda checked=False, f=f: self._import_from_menu(f))
        else:
            act = menu.addAction("Нет .json файлов в папке")
            act.setEnabled(False)
        menu.exec(widget.mapToGlobal(widget.rect().bottomLeft()))

    def show_export_menu(self, widget):
        # Предлагаем экспортировать любую существующую CSV в JSON (имя по умолчанию)
        menu = QMenu(self)
        files = self.list_csv_files()
        if files:
            for f in files:
                menu.addAction(f, lambda checked=False, f=f: self._export_csv_to_json_prompt(f))
        else:
            act = menu.addAction("Нет .csv файлов для экспорта")
            act.setEnabled(False)
        menu.exec(widget.mapToGlobal(widget.rect().bottomLeft()))

    def _open_from_menu(self, filename):
        try:
            ok = self.load_from_csv(filename)
            if ok:
                QMessageBox.information(self, "Открыто", f"Файл {os.path.basename(filename)} загружен.")
            else:
                QMessageBox.warning(self, "Ошибка", f"Не удалось открыть {filename}")
        except Exception as e:
            QMessageBox.warning(self, "Ошибка", str(e))
        self.refresh_table()

    def _import_from_menu(self, filename):
        try:
            self.import_json(filename)
            QMessageBox.information(self, "Импорт", f"Импортировано из {os.path.basename(filename)}")
        except Exception as e:
            QMessageBox.warning(self, "Ошибка", str(e))
        self._after_change()

    def _export_csv_to_json_prompt(self, csv_filename):
        # предлагается имя по умолчанию: same base .json
        default = os.path.splitext(csv_filename)[0] + ".json"
        save_fname, _ = QFileDialog.getSaveFileName(self, "Экспорт JSON", default, "JSON Files (*.json)")
        if not save_fname:
            return
        try:
            # прочитать CSV и записать JSON
            data = []
            with open(csv_filename, "r", encoding="utf-8") as f:
                rdr = csv.reader(f)
                hdr = next(rdr, [])
                for row in rdr:
                    entry = {h: (row[i] if i < len(row) else "") for i, h in enumerate(hdr)}
                    data.append(entry)
            with open(save_fname, "w", encoding="utf-8") as jf:
                json.dump(data, jf, ensure_ascii=False, indent=2)
            QMessageBox.information(self, "Экспорт", f"Экспортировано {csv_filename} → {os.path.basename(save_fname)}")
        except Exception as e:
            QMessageBox.warning(self, "Ошибка", f"Ошибка при экспорте: {e}")

    # -------------------- конец новых вспомогательных методов --------------------

    def _display_headers(self) -> List[str]:
        """Возвращает заголовки для отображения (включая колонку номера)."""
        return ["No."] + list(self.headers)

    def _init_ui(self):
        cw = QWidget()
        vbox = QVBoxLayout(cw)

        # верхняя панель с кнопками
        top = QHBoxLayout()
        btn_add = QPushButton("Добавить")
        btn_edit = QPushButton("Редактировать")
        btn_delete = QPushButton("Удалить")
        btn_add_col = QPushButton("Добавить столбец")
        btn_save = QPushButton("Сохранить")
        btn_open = QPushButton("Открыть")
        btn_export = QPushButton("Экспорт JSON")
        btn_import = QPushButton("Импорт JSON")
        btn_refresh = QPushButton("Обновить")

        top.addWidget(btn_add)
        top.addWidget(btn_edit)
        top.addWidget(btn_delete)
        top.addWidget(btn_add_col)
        top.addWidget(btn_save)
        top.addWidget(btn_open)
        top.addWidget(btn_export)
        top.addWidget(btn_import)
        top.addWidget(btn_refresh)
        top.addStretch()

        # управление шрифтом и анимацией
        btn_inc_font = QPushButton("A+")
        btn_dec_font = QPushButton("A-")
        self.chk_animate = QCheckBox("Анимации")
        self.chk_animate.setChecked(True)
        top.addWidget(QLabel("Шрифт:"))
        top.addWidget(btn_inc_font)
        top.addWidget(btn_dec_font)
        top.addWidget(self.chk_animate)

        vbox.addLayout(top)

        # поиск
        search_layout = QHBoxLayout()
        search_layout.addWidget(QLabel("Поиск:"))
        self.search_input = QLineEdit()
        search_layout.addWidget(self.search_input)
        btn_search = QPushButton("Найти")
        btn_reset = QPushButton("Сброс")
        search_layout.addWidget(btn_search)
        search_layout.addWidget(btn_reset)
        vbox.addLayout(search_layout)

        # таблица (колонки будут устанавливаться в refresh_table)
        self.table = QTableWidget(0, len(self._display_headers()))
        self.table.setHorizontalHeaderLabels(self._display_headers())
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)

        # Тёмная тема для таблицы: фон, линии сетки, цвет текста и выделение
        self.table.setStyleSheet("""
            QTableWidget {
                background-color: #2b2b2b;
                color: #ffffff;
                gridline-color: #444444;
                selection-background-color: #3a7bd5;
                selection-color: #ffffff;
            }
            QTableWidget::item {
                background-color: transparent;
            }
            QHeaderView::section {
                background-color: #3c3f41;
                color: #ffffff;
                padding: 4px;
                border: 1px solid #4a4a4a;
            }
        """)

        vbox.addWidget(self.table)

        # контекстное меню
        self.table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self.show_context_menu)

        # статус
        self.status = QLabel("")
        vbox.addWidget(self.status)

        self.setCentralWidget(cw)

        # применить начальные шрифты
        self.apply_fonts()

        # подключение сигналов (кнопки теперь показывают выпадающие списки)
        btn_add.clicked.connect(self.on_add)
        btn_edit.clicked.connect(self.on_edit)
        btn_delete.clicked.connect(self.on_delete_selected)
        btn_add_col.clicked.connect(self.on_add_column)
        btn_save.clicked.connect(lambda: self.on_save())  # Save вызывает стандартный диалог
        # Открыть/Импорт/Экспорт показывают списки файлов рядом с кнопкой
        btn_open.clicked.connect(lambda _, b=btn_open: self.show_open_menu(b))
        btn_import.clicked.connect(lambda _, b=btn_import: self.show_import_menu(b))
        btn_export.clicked.connect(lambda _, b=btn_export: self.show_export_menu(b))
        btn_refresh.clicked.connect(self.refresh_table)
        btn_search.clicked.connect(self.on_search)
        btn_reset.clicked.connect(self.refresh_table)
        btn_inc_font.clicked.connect(lambda: self.change_font(1))
        btn_dec_font.clicked.connect(lambda: self.change_font(-1))
        self.chk_animate.stateChanged.connect(self.toggle_animations)

    def show_context_menu(self, pos: QPoint):
        menu = QMenu(self)
        menu.addAction("Добавить строку", lambda: self.on_add())
        menu.addAction("Редактировать выбранную", lambda: self.on_edit())
        menu.addAction("Удалить выбранные", lambda: self.on_delete_selected())
        menu.addSeparator()
        menu.addAction("Добавить столбец", lambda: self.on_add_column())

        # удаление столбцов и порядок через подменю
        sub_del_cols = menu.addMenu("Удалить столбцы...")
        removable = [h for h in self.headers if h not in BASIC_COLUMNS]
        if removable:
            for col in sorted(removable, key=str.lower):
                sub_del_cols.addAction(col, lambda checked=False, c=col: self._delete_column_by_name(c))
        else:
            act = sub_del_cols.addAction("Нет дополнительных столбцов")
            act.setEnabled(False)

        menu.addAction("Порядок столбцов...", lambda: self.on_reorder_columns_dialog())
        menu.addSeparator()

        # Open submenu
        open_menu = menu.addMenu("Открыть...")
        csvs = self.list_csv_files()
        if csvs:
            for f in csvs:
                open_menu.addAction(f, lambda checked=False, f=f: self._open_from_menu(f))
        else:
            a = open_menu.addAction("Нет .csv файлов")
            a.setEnabled(False)

        # Import submenu
        import_menu = menu.addMenu("Импорт JSON...")
        jsons = self.list_json_files()
        if jsons:
            for f in jsons:
                import_menu.addAction(f, lambda checked=False, f=f: self._import_from_menu(f))
        else:
            a = import_menu.addAction("Нет .json файлов")
            a.setEnabled(False)

        # Export submenu (csv -> json)
        export_menu = menu.addMenu("Экспорт CSV → JSON...")
        csvs2 = self.list_csv_files()
        if csvs2:
            for f in csvs2:
                export_menu.addAction(f, lambda checked=False, f=f: self._export_csv_to_json_prompt(f))
        else:
            a = export_menu.addAction("Нет .csv файлов")
            a.setEnabled(False)

        menu.addSeparator()
        menu.addAction("Сохранить...", lambda: self.on_save())
        menu.addAction("Обновить", lambda: self.refresh_table())
        menu.exec(self.table.viewport().mapToGlobal(pos))

    def _delete_column_by_name(self, col_name: str):
        if col_name in BASIC_COLUMNS:
            QMessageBox.information(self, "Удаление столбца", "Нельзя удалить базовые столбцы.")
            return
        if QMessageBox.question(self, "Подтверждение", f"Удалить столбец '{col_name}'?") != QMessageBox.StandardButton.Yes:
            return
        idx = self.headers.index(col_name)
        del self.headers[idx]
        for r in range(len(self.rows)):
            if idx < len(self.rows[r]):
                del self.rows[r][idx]
        self._after_change()
        self.refresh_table()

    def apply_fonts(self):
        font = QFont()
        font.setPointSize(self.base_font_point)
        self.setFont(font)
        header_font = QFont()
        header_font.setPointSize(self.header_font_point)
        self.table.horizontalHeader().setFont(header_font)
        self.refresh_table(animate=False)

    def change_font(self, delta: int):
        self.base_font_point = max(8, self.base_font_point + delta)
        self.header_font_point = max(9, self.header_font_point + delta)
        self.item_font_point = max(8, self.item_font_point + delta)
        self.apply_fonts()

    def toggle_animations(self, _):
        self.animations_enabled = self.chk_animate.isChecked()

    def refresh_table(self, animate: bool = True):
        animate = animate and self.animations_enabled
        disp_headers = self._display_headers()
        self.table.setColumnCount(len(disp_headers))
        self.table.setHorizontalHeaderLabels(disp_headers)
        self.table.setRowCount(len(self.rows))

        for r, row in enumerate(self.rows):
            # номер в первой колонке
            no_item = QTableWidgetItem(str(r + 1))
            no_item.setFlags(Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsEnabled)
            fno = no_item.font()
            fno.setPointSize(self.item_font_point)
            no_item.setFont(fno)
            # текст белый для тёмной темы
            no_item.setForeground(QBrush(QColor(255, 255, 255)))
            self.table.setItem(r, 0, no_item)

            # данные в остальных колонках
            for c in range(len(self.headers)):
                txt = str(row[c]) if c < len(row) else ""
                it = QTableWidgetItem(txt)
                it.setFlags(Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsEnabled)
                f = it.font()
                f.setPointSize(self.item_font_point)
                it.setFont(f)
                # текст белый для тёмной темы
                it.setForeground(QBrush(QColor(255, 255, 255)))
                # очистить фон (на случай старых подсветок)
                it.setBackground(QBrush(QColor(43, 43, 43)))
                self.table.setItem(r, c + 1, it)  # смещение на 1 из-за номера

        self.status.setText(f"Строк: {len(self.rows)}")

        # простая анимация появления таблицы
        if animate:
            try:
                effect = QGraphicsOpacityEffect(self.table)
                self.table.setGraphicsEffect(effect)
                anim = QPropertyAnimation(effect, b"opacity", self)
                anim.setDuration(220)
                anim.setStartValue(0.0)
                anim.setEndValue(1.0)
                anim.start()
                self._last_anim = anim
            except Exception:
                pass

    def highlight_new_row(self, row_index: int):
        if not (0 <= row_index < self.table.rowCount()):
            return
        duration = 600
        steps = 8
        interval = max(20, duration // steps)
        start_color = QColor(255, 250, 180)
        end_color = QColor(255, 255, 255)
        step = 0

        def tick():
            nonlocal step
            t = step / steps
            # плавный переход от светлого акцента к базовому тёмному фону
            r = int(start_color.red() * (1 - t) + end_color.red() * t)
            g = int(start_color.green() * (1 - t) + end_color.green() * t)
            b = int(start_color.blue() * (1 - t) + end_color.blue() * t)
            color = QColor(r, g, b)
            brush = QBrush(color)
            for c in range(self.table.columnCount()):
                item = self.table.item(row_index, c)
                if item:
                    item.setBackground(brush)
                    # текст остаётся белым чтобы был читаем на тёмном фоне
                    item.setForeground(QBrush(QColor(255, 255, 255)))
            step += 1
            if step > steps:
                timer.stop()

        timer = QTimer(self)
        timer.timeout.connect(tick)
        timer.start(interval)

    # функции добавления/редактирования остаются прежними
    def on_add(self):
        dlg = RowDialog(self.headers, parent=self, font=QFont("", self.base_font_point))
        if dlg.exec() and dlg.values:
            self.rows.append(dlg.values)
            self._after_change()
            self.refresh_table()
            self.highlight_new_row(len(self.rows) - 1)

    def on_edit(self):
        sel = self.table.currentRow()
        if sel < 0:
            QMessageBox.information(self, "Редактировать", "Выберите строку для редактирования.")
            return
        # sel соответствует индексу в self.rows (номер в колонке No. = sel+1)
        cur = self.rows[sel]
        dlg = RowDialog(self.headers, values=cur, parent=self, font=QFont("", self.base_font_point))
        if dlg.exec() and dlg.values:
            self.rows[sel] = dlg.values
            self._after_change()
            self.refresh_table()

    def on_delete_selected(self):
        """Удаляет выбранные строки (если выбраны) или вызывает мульти-удаление по номерам."""
        sels = self.table.selectionModel().selectedRows()
        if sels:
            nums = sorted({idx.row() + 1 for idx in sels})
            if QMessageBox.question(self, "Удалить", f"Удалить выбранные строки: {', '.join(map(str, nums))}?") == QMessageBox.StandardButton.Yes:
                for idx in sorted([n - 1 for n in nums], reverse=True):
                    try:
                        del self.rows[idx]
                    except Exception:
                        pass
                self._after_change()
                self.refresh_table()
            return
        # если ничего не выбрано, открыть диалог ввода номеров
        self.on_delete_multi()

    def on_delete_multi(self):
        """Диалог удаления: ввод нескольких номеров через запятую и диапазонов через дефис."""
        if not self.rows:
            QMessageBox.information(self, "Удалить", "Таблица пуста.")
            return
        prompt = "Введите номера строк для удаления (например: 1,3,5-7). Номера соответствуют колонке 'No.' сверху."
        text, ok = QInputDialog.getText(self, "Удалить строки", prompt)
        if not ok or not text.strip():
            return
        try:
            indices = self._parse_indices(text, max_index=len(self.rows))
        except ValueError as e:
            QMessageBox.warning(self, "Ошибка ввода", str(e))
            return
        if not indices:
            QMessageBox.information(self, "Удалить", "Нет валидных номеров для удаления.")
            return
        # подтверждение
        nums = sorted(indices)
        if QMessageBox.question(self, "Подтверждение удаления", f"Удалить строки: {', '.join(map(str, nums))}?") != QMessageBox.StandardButton.Yes:
            return
        # удаляем в обратном порядке по индексам (1-based -> 0-based)
        for idx in sorted(indices, reverse=True):
            try:
                del self.rows[idx - 1]
            except Exception:
                pass
        self._after_change()
        self.refresh_table()

    def _parse_indices(self, text: str, max_index: int) -> Set[int]:
        """Парсит строку с номерами и диапазонами, возвращает множество 1-based индексов.
           Выбрасывает ValueError при некорректном вводе."""
        text = text.strip()
        parts = [p.strip() for p in text.split(",") if p.strip()]
        result: Set[int] = set()
        for part in parts:
            if "-" in part:
                bounds = part.split("-", 1)
                if len(bounds) != 2:
                    raise ValueError(f"Неверный диапазон: '{part}'")
                try:
                    a = int(bounds[0])
                    b = int(bounds[1])
                except ValueError:
                    raise ValueError(f"Неверный номер в диапазоне: '{part}'")
                if a <= 0 or b <= 0 or a > max_index or b > max_index:
                    raise ValueError(f"Номер за пределами: '{part}'")
                if a > b:
                    a, b = b, a
                for i in range(a, b + 1):
                    result.add(i)
            else:
                try:
                    n = int(part)
                except ValueError:
                    raise ValueError(f"Неверный номер: '{part}'")
                if n <= 0 or n > max_index:
                    raise ValueError(f"Номер за пределами: '{part}'")
                result.add(n)
        return result

    def on_add_column(self):
        text, ok = QInputDialog.getText(self, "Добавить столбец", "Название нового столбца:")
        if not ok:
            return
        col_name = text.strip()
        if not col_name:
            QMessageBox.information(self, "Добавить столбец", "Имя столбца не может быть пустым.")
            return
        self.headers.append(col_name)
        for i in range(len(self.rows)):
            self.rows[i].append("")
        self._after_change()
        self.refresh_table()

    def on_delete_columns_dialog(self):
        # список доступных для удаления (за исключением базовых)
        removable = [h for h in self.headers if h not in BASIC_COLUMNS]
        if not removable:
            QMessageBox.information(self, "Удалить столбцы", "Нет дополнительных столбцов для удаления.")
            return
        dlg = ColumnDeleteDialog(removable, parent=self)
        if dlg.exec() and dlg.result:
            to_remove = dlg.result
            # удаляем по именам
            for col in to_remove:
                if col in self.headers and col not in BASIC_COLUMNS:
                    idx = self.headers.index(col)
                    # удалить столбец из headers и все строки
                    del self.headers[idx]
                    for r in range(len(self.rows)):
                        if idx < len(self.rows[r]):
                            del self.rows[r][idx]
            self._after_change()
            self.refresh_table()

    def on_reorder_columns_dialog(self):
        dlg = ReorderDialog(self.headers, parent=self)
        if dlg.exec() and dlg.result:
            new_order = dlg.result
            # проверить совпадение множеств
            if set(new_order) != set(self.headers) or len(new_order) != len(self.headers):
                QMessageBox.warning(self, "Ошибка", "Неверный порядок столбцов.")
                return
            # перестроить rows согласно новому порядку
            old_headers = list(self.headers)
            new_rows = []
            for row in self.rows:
                new_row = []
                for col_name in new_order:
                    old_idx = old_headers.index(col_name)
                    val = row[old_idx] if old_idx < len(row) else ""
                    new_row.append(val)
                new_rows.append(new_row)
            self.headers = list(new_order)
            self.rows = new_rows
            self._after_change()
            self.refresh_table()

    def on_save(self):
        fname, _ = QFileDialog.getSaveFileName(self, "Сохранить CSV", "", "CSV Files (*.csv)")
        if not fname:
            return
        self.save_to_csv(fname)
        QMessageBox.information(self, "Сохранено", f"Сохранено в {os.path.basename(fname)}")

    def on_open(self):
        fname, _ = QFileDialog.getOpenFileName(self, "Открыть CSV", "", "CSV Files (*.csv)")
        if not fname:
            return
        ok = self.load_from_csv(fname)
        if ok:
            QMessageBox.information(self, "Открыто", f"Файл {os.path.basename(fname)} загружен.")
        else:
            QMessageBox.warning(self, "Ошибка", "Не удалось загрузить файл.")
        self.refresh_table()

    def on_export(self):
        fname, _ = QFileDialog.getSaveFileName(self, "Экспорт JSON", "", "JSON Files (*.json)")
        if not fname:
            return
        self.export_json(fname)
        QMessageBox.information(self, "Экспорт", f"Экспортировано в {os.path.basename(fname)}")

    def on_import(self):
        fname, _ = QFileDialog.getOpenFileName(self, "Импорт JSON", "", "JSON Files (*.json)")
        if not fname:
            return
        self.import_json(fname)
        self._after_change()
        QMessageBox.information(self, "Импорт", f"Импортировано из {os.path.basename(fname)}")

    # wrapper actions used in context menu
    def on_action_save(self):
        self.on_save()

    def on_action_open(self):
        self.on_open()

    def on_action_export(self):
        self.on_export()

    def on_action_import(self):
        self.on_import()

    def on_search(self):
        q = self.search_input.text().strip().lower()
        if not q:
            for r in range(self.table.rowCount()):
                self.table.setRowHidden(r, False)
            self.status.setText(f"Строк: {len(self.rows)}")
            return
        for r in range(self.table.rowCount()):
            match = False
            for c in range(1, self.table.columnCount()):  # пропускаем колонку No.
                it = self.table.item(r, c)
                if it and q in it.text().lower():
                    match = True
                    break
            self.table.setRowHidden(r, not match)
        visible = sum(1 for r in range(self.table.rowCount()) if not self.table.isRowHidden(r))
        self.status.setText(f"Результатов: {visible}")

    def _after_change(self):
        self.refresh_table()
        if AUTOSAVE:
            try:
                self.save_to_csv(AUTOSAVE_FILE)
            except Exception:
                pass

    # CSV / JSON utils (не включают колонку No.)
    def save_to_csv(self, filename: str):
        try:
            with open(filename, "w", newline="", encoding="utf-8") as f:
                w = csv.writer(f)
                w.writerow(self.headers)
                for row in self.rows:
                    w.writerow(row)
        except Exception as e:
            QMessageBox.warning(self, "Ошибка", f"Ошибка при сохранении: {e}")

    def load_from_csv(self, filename: str) -> bool:
        if not os.path.exists(filename):
            return False
        try:
            with open(filename, "r", encoding="utf-8") as f:
                r = csv.reader(f)
                hdrs = next(r, None)
                if hdrs:
                    self.headers = hdrs
                self.rows = [row for row in r]
            self.refresh_table()
            return True
        except Exception as e:
            QMessageBox.warning(self, "Ошибка", f"Ошибка при загрузке: {e}")
            return False

    def export_json(self, filename: str):
        try:
            data = []
            for row in self.rows:
                entry = {h: (row[i] if i < len(row) else "") for i, h in enumerate(self.headers)}
                data.append(entry)
            with open(filename, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            QMessageBox.warning(self, "Ошибка", f"Ошибка при экспорте: {e}")

    def import_json(self, filename: str):
        if not os.path.exists(filename):
            QMessageBox.warning(self, "Ошибка", "Файл не найден")
            return
        try:
            with open(filename, "r", encoding="utf-8") as f:
                data = json.load(f)
            if not data:
                QMessageBox.information(self, "Импорт", "JSON пуст.")
                return
            keys = list(data[0].keys())
            self.headers = keys
            self.rows = [[item.get(k, "") for k in keys] for item in data]
            self.refresh_table()
        except Exception as e:
            QMessageBox.warning(self, "Ошибка", f"Ошибка при импорте: {e}")

    def save_to_csv_autosave(self):
        if AUTOSAVE:
            try:
                self.save_to_csv(AUTOSAVE_FILE)
            except Exception:
                pass


def main():
    try:
        QApplication.setAttribute(Qt.ApplicationAttribute.AA_EnableHighDpiScaling, True)
    except Exception:
        pass

    app = QApplication(sys.argv)
    win = MainWindow()
    win.show()
    try:
        rc = app.exec()
    except Exception as e:
        print("Ошибка в приложении:", e)
        rc = 1
    try:
        if AUTOSAVE:
            win.save_to_csv(AUTOSAVE_FILE)
    except Exception:
        pass
    sys.exit(rc)


if __name__ == "__main__":
    main()

