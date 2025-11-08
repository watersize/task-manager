import csv
import json
import os
import re
import sys

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QApplication,
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QFormLayout,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

# Lightweight styling
APP_TITLE = "Task Manager (PyQt6)"
AUTOSAVE = True
AUTOSAVE_FILE = "tasks_autosave.csv"


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
    def __init__(self, headers, values=None, parent=None):
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

        btns = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        btns.accepted.connect(self.accept)
        btns.rejected.connect(self.reject)
        layout.addWidget(btns)

    def accept(self) -> None:
        vals = [e.text().strip() for e in self.edits]
        # validate time at index 0
        norm = check_time_format(vals[0])
        if not norm:
            QMessageBox.warning(self, "Ошибка", "Неверный формат времени. Ожидается HH:MM (00-23,00-59).")
            return
        vals[0] = norm
        self.values = vals
        super().accept()


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(APP_TITLE)
        self.resize(900, 600)
        self.headers = ["Time: ", "TODO list:", "Comments: "]
        self.rows = []  # list of lists
        self._init_ui()
        if AUTOSAVE and os.path.exists(AUTOSAVE_FILE):
            self.load_from_csv(AUTOSAVE_FILE)

    def _init_ui(self):
        cw = QWidget()
        vbox = QVBoxLayout(cw)
        # Top controls
        top = QHBoxLayout()
        btn_add = QPushButton("Добавить")
        btn_edit = QPushButton("Редактировать")
        btn_delete = QPushButton("Удалить")
        btn_save = QPushButton("Сохранить CSV")
        btn_open = QPushButton("Открыть CSV")
        btn_export = QPushButton("Экспорт JSON")
        btn_import = QPushButton("Импорт JSON")
        btn_refresh = QPushButton("Обновить")

        for btn in (btn_add, btn_edit, btn_delete, btn_save, btn_open, btn_export, btn_import, btn_refresh):
            top.addWidget(btn)

        top.addStretch()
        vbox.addLayout(top)

        # Search
        search_layout = QHBoxLayout()
        search_layout.addWidget(QLabel("Поиск:"))
        self.search_input = QLineEdit()
        search_layout.addWidget(self.search_input)
        btn_search = QPushButton("Найти")
        btn_reset = QPushButton("Сброс")
        search_layout.addWidget(btn_search)
        search_layout.addWidget(btn_reset)
        vbox.addLayout(search_layout)

        # Table
        self.table = QTableWidget(0, len(self.headers))
        self.table.setHorizontalHeaderLabels(self.headers)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        vbox.addWidget(self.table)

        # Status
        self.status = QLabel("")
        vbox.addWidget(self.status)

        self.setCentralWidget(cw)

        # Connects
        btn_add.clicked.connect(self.on_add)
        btn_edit.clicked.connect(self.on_edit)
        btn_delete.clicked.connect(self.on_delete)
        btn_save.clicked.connect(self.on_save)
        btn_open.clicked.connect(self.on_open)
        btn_export.clicked.connect(self.on_export)
        btn_import.clicked.connect(self.on_import)
        btn_refresh.clicked.connect(self.refresh_table)
        btn_search.clicked.connect(self.on_search)
        btn_reset.clicked.connect(self.refresh_table)

    def refresh_table(self):
        # Rebuild table columns if headers changed
        self.table.setColumnCount(len(self.headers))
        self.table.setHorizontalHeaderLabels(self.headers)
        self.table.setRowCount(len(self.rows))
        for r, row in enumerate(self.rows):
            for c in range(len(self.headers)):
                txt = str(row[c]) if c < len(row) else ""
                it = QTableWidgetItem(txt)
                it.setFlags(Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsEnabled)
                self.table.setItem(r, c, it)
        self.status.setText(f"Строк: {len(self.rows)}")

    def on_add(self):
        dlg = RowDialog(self.headers, parent=self)
        if dlg.exec() and dlg.values:
            self.rows.append(dlg.values)
            self._after_change()

    def on_edit(self):
        sel = self.table.currentRow()
        if sel < 0:
            QMessageBox.information(self, "Редактировать", "Выберите строку для редактирования.")
            return
        cur = self.rows[sel]
        dlg = RowDialog(self.headers, values=cur, parent=self)
        if dlg.exec() and dlg.values:
            self.rows[sel] = dlg.values
            self._after_change()

    def on_delete(self):
        sel = self.table.currentRow()
        if sel < 0:
            QMessageBox.information(self, "Удалить", "Выберите строку для удаления.")
            return
        if QMessageBox.question(self, "Удалить", f"Удалить строку #{sel+1}?") == QMessageBox.StandardButton.Yes:
            del self.rows[sel]
            self._after_change()

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

    def on_search(self):
        q = self.search_input.text().strip().lower()
        if not q:
            return
        # show only matching rows
        for r in range(self.table.rowCount()):
            match = False
            for c in range(self.table.columnCount()):
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
            self.save_to_csv(AUTOSAVE_FILE)

    # CSV / JSON utils
    def save_to_csv(self, filename):
        try:
            with open(filename, "w", newline="", encoding="utf-8") as f:
                w = csv.writer(f)
                w.writerow(self.headers)
                for row in self.rows:
                    w.writerow(row)
        except Exception as e:
            QMessageBox.warning(self, "Ошибка", f"Ошибка при сохранении: {e}")

    def load_from_csv(self, filename):
        if not os.path.exists(filename):
            return False
        try:
            with open(filename, "r", encoding="utf-8") as f:
                r = csv.reader(f)
                hdrs = next(r)
                self.headers = hdrs
                self.rows = [row for row in r]
            self.refresh_table()
            return True
        except Exception as e:
            QMessageBox.warning(self, "Ошибка", f"Ошибка при загрузке: {e}")
            return False

    def export_json(self, filename):
        try:
            data = []
            for row in self.rows:
                entry = {h: (row[i] if i < len(row) else "") for i, h in enumerate(self.headers)}
                data.append(entry)
            with open(filename, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            QMessageBox.warning(self, "Ошибка", f"Ошибка при экспорте: {e}")

    def import_json(self, filename):
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

    # convenience
    def save_to_csv_autosave(self):
        if AUTOSAVE:
            self.save_to_csv(AUTOSAVE_FILE)


def main():
    app = QApplication(sys.argv)
    win = MainWindow()
    win.show()
    rc = app.exec()
    # on exit, autosave
    if AUTOSAVE:
        win.save_to_csv(AUTOSAVE_FILE)
    sys.exit(rc)


if __name__ == "__main__":
    main()