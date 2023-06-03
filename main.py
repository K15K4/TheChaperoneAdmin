import os
import sys

import psycopg2
from PyQt6 import QtCore, QtGui, QtWidgets
from PyQt6.QtWidgets import QGridLayout, QLabel, QLineEdit, QPushButton


class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.setGeometry(100, 100, 600, 400)
        # Установка размера окна

        # Создание виджета для окна авторизации
        self.login_widget = LoginWidget()
        self.setCentralWidget(self.login_widget)

        # Подключение сигнала авторизации к обработчику
        self.login_widget.login_signal.connect(self.on_login)

    def on_login(self, user_id):
        # Подключение к базе данных
        conn = psycopg2.connect(
            dbname="postgres",
            user="kiska",
            password="5973",
            host="localhost",
            port="5432"
        )

        # Получение данных о пользователе
        cur = conn.cursor()
        cur.execute(f"""SELECT * FROM "User" WHERE "id_User"='{user_id}'""")
        user_data = cur.fetchone()
        # Получение данных о роли пользователя
        cur.execute(f"""SELECT "name_Roles" FROM "Roles" WHERE "id_Roles"='{user_data[9]}'""")
        role_name = cur.fetchone()[0]
        # Создание виджета для работы с базой данных
        self.database_widget = DatabaseWidget(role_name)
        self.setCentralWidget(self.database_widget)
        # Закрытие соединения с базой данных
        cur.close()
        conn.close()


class LoginWidget(QtWidgets.QWidget):
    # Сигнал авторизации
    login_signal = QtCore.pyqtSignal(int)

    def __init__(self):
        super().__init__()
        self.setWindowTitle('Login Form')
        self.resize(300, 200)
        layout = QGridLayout()
        label_name = QLabel('<font size="4"> Username </font>')
        self.login_edit = QLineEdit()
        self.login_edit.setPlaceholderText('Please enter your username')
        layout.addWidget(label_name, 0, 0)
        layout.addWidget(self.login_edit, 0, 1)
        label_password = QLabel('<font size="4"> Password </font>')
        self.password_edit = QLineEdit()
        self.password_edit.setEchoMode(QtWidgets.QLineEdit.EchoMode.Password)
        self.password_edit.setPlaceholderText('Please enter your password')
        layout.addWidget(label_password, 1, 0)
        layout.addWidget(self.password_edit, 1, 1)
        login_button = QPushButton('Login')
        login_button.clicked.connect(self.on_login)
        layout.addWidget(login_button, 2, 0, 1, 2)
        layout.setRowMinimumHeight(2, 75)
        self.setLayout(layout)


    def on_login(self):
        # Получение логина и пароля пользователя
        login = self.login_edit.text()
        password = self.password_edit.text()

        # Подключение к базе данных
        conn = psycopg2.connect(
            dbname="postgres",
            user="kiska",
            password="5973",
            host="localhost",
            port="5432"
        )

        # Поиск пользователя в базе данных
        cur = conn.cursor()
        query = f"""SELECT "id_User" FROM "User" WHERE "log_User" = '{login}' AND "pass_User" = '{password}';"""
        cur.execute(query)
        user_id = cur.fetchone()
        # Отправка сигнала авторизации
        if user_id is not None:
            self.login_signal.emit(user_id[0])
        # Закрытие соединения с базой данных
        cur.close()
        conn.close()


class DatabaseWidget(QtWidgets.QWidget):
    def __init__(self, role_name):
        super().__init__()

        # Создание элементов интерфейса
        self.table_selector_label = QtWidgets.QLabel("Выберите таблицу:")
        self.table_selector = QtWidgets.QComboBox()
        self.table_selector.addItems(["AdStatus", "Advertisment", "Bodywork", "Car", "CarCat", "City", "Color",
                                      "DamageStatus", "Engine", "FuelType", "Handlebar", "Mark", "Metro", "Models",
                                      "Roles", "Transmission", "TypeOfEngine", "User", "UserStatus", "Wheeldrive"])
        self.table_view = QtWidgets.QTableView()
        self.save_button = QtWidgets.QPushButton("Сохранить")
        self.add_button = QtWidgets.QPushButton("Добавить")
        self.add_button.clicked.connect(self.show_add_dialog)

        # Создание лэйаута для элементов интерфейса
        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(self.table_selector_label)
        layout.addWidget(self.table_selector)
        layout.addWidget(self.table_view)
        layout.addWidget(self.add_button)
        layout.addWidget(self.save_button)
        self.logout_button = QtWidgets.QPushButton("Выход", clicked=self.return_to_auth)
        layout.addWidget(self.logout_button, alignment=QtCore.Qt.AlignmentFlag.AlignTop | QtCore.Qt.AlignmentFlag.AlignRight)

        self.setLayout(layout)

        # Установка прав доступа в зависимости от роли пользователя
        if role_name == "Admin":
            pass
        elif role_name == "Content manager":
            self.table_selector.clear()
            self.table_selector.addItems(["Mark", "Models", "CarCat", "Color", "Engine", "FuelType", "Handlebar", "Mark",
                                          "Models", "Transmission", "TypeOfEngine", "Wheeldrive"])
        elif role_name == "User manager":
            self.table_selector.clear()
            self.table_selector.addItem("User")
        elif role_name == "Product manager":
            self.table_selector.clear()
            self.table_selector.addItems(["Car", "Advertisment"])

        # Подключение таблицы к базе данных
        self.conn = psycopg2.connect(
            dbname="postgres",
            user="kiska",
            password="5973",
            host="localhost",
            port="5432"
        )
        self.cur = self.conn.cursor()

        self.cur.execute(f'SELECT * FROM "{self.table_selector.currentText()}" LIMIT 0')
        columns = [desc[0] for desc in self.cur.description]

        self.cur.execute(f'SELECT * FROM "{self.table_selector.currentText()}"')
        table_data = self.cur.fetchall()
        self.table_model = QtGui.QStandardItemModel(len(table_data), len(table_data[0]), self)
        self.table_model.setHorizontalHeaderLabels(columns)
        for i, row in enumerate(table_data):
            for j, cell in enumerate(row):
                self.table_model.setItem(i, j, QtGui.QStandardItem(str(cell)))
        self.table_view.setModel(self.table_model)
        # Подключение обработчика к изменению выбранной таблицы
        self.table_selector.currentIndexChanged.connect(self.on_table_changed)

        # Подключение обработчика к сохранению данных
        self.save_button.clicked.connect(self.save_table_data)

    def on_table_changed(self):
        # Подключение таблицы к базе данных
        self.cur.execute(f'SELECT * FROM "{self.table_selector.currentText()}"')
        table_data = self.cur.fetchall()

        if self.cur.description is None:
            print("Ошибка: переменная self.cur.description не установлена")
            return

        self.table_model.clear()
        self.table_model.setRowCount(len(table_data))
        self.table_model.setColumnCount(len(table_data[0]))
        columns = [desc[0] for desc in self.cur.description]
        self.table_model.setHorizontalHeaderLabels(columns)
        for i, row in enumerate(table_data):
            for j, cell in enumerate(row):
                self.table_model.setItem(i, j, QtGui.QStandardItem(str(cell)))

    def save_table_data(self):
        # Получение данных из таблицы и их сохранение в базе данных
        rows = self.table_model.rowCount()
        cols = self.table_model.columnCount()

        for row in range(rows):
            values = []
            for col in range(cols):
                value = self.table_model.item(row, col).text()
                values.append(value)
            values_str = "', '".join(values)
            query = f"""UPDATE "{self.table_selector.currentText()}" SET {', '.join([f'"{self.table_model.horizontalHeaderItem(col).text()}" = %s' for col in range(cols)])} WHERE "{self.table_model.horizontalHeaderItem(0).text()}" = '{values[0]}'"""
            self.cur.execute(query, values)
            self.conn.commit()

            # Отображение сообщения об успешном сохранении
        QtWidgets.QMessageBox.information(self, "Уведомление", "Изменения успешно сохранены!")

    def show_add_dialog(self):
        add_dialog = AddDialog(self, self.cur)
        add_dialog.exec()

    def return_to_auth(self):
        os.execl(sys.executable, sys.executable, *sys.argv)


id_columns = {

    'AdStatus': {'id_column': 'id_AdStat', 'name_column': 'name_AdStat'},
    'Advertisment': {'id_column': 'id_Ad', 'name_column': 'comm_Ad', 'car_Ad_id': 'Car.id_Car',
                     'loc_Ad_id': 'Metro.id_Met', 'status_Ad_id': 'AdStatus.id_AdStat', 'user_Ad_id': 'User.id_User'},
    'Bodywork': {'id_column': 'id_Body', 'name_column': 'name_Body'},
    'Car': {'id_column': 'id_Car', 'name_column': 'vin_Car', 'body_Car_id': 'Bodywork.id_Body',
            'cat_Car_id': 'CarCat.id_CarCat', 'color_Car_id': 'Color.id_Color', 'damage_Car_id': 'DamageStatus.id_Dam',
            'engine_Car_id': 'Engine.id_Engine', 'handle_Car_id': 'Handlebar.id_Hand', 'model_Car_id': 'Models.id_Mod',
            'trans_Car_id': 'Transmission.id_Trans', 'user_Car_id': 'User.id_User', 'wheel_Car_id': 'Wheeldrive.id_Wheel'},
    'CarCat': {'id_column': 'id_CarCat', 'name_column': 'name_Cat'},
    'City': {'id_column': 'id_City', 'name_column': 'name_City'},
    'Color': {'id_column': 'id_Color', 'name_column': 'name_Color'},
    'DamageStatus': {'id_column': 'id_Dam', 'name_column': 'name_Dam'},
    'Engine': {'id_column': 'id_Engine', 'name_column': 'name_Engine', 'fuel_Engine_id': 'FuelType.id_Fuel',
               'type_Engine_id': 'TypeOfEngine.id_TypeEng'},
    'FuelType': {'id_column': 'id_Fuel', 'name_column': 'name_Fuel'},
    'Handlebar': {'id_column': 'id_Hand', 'name_column': 'name_Hand'},
    'Mark': {'id_column': 'id_Mark', 'name_column': 'name_Mark'},
    'Metro': {'id_column': 'id_Met', 'name_column': 'name_Met', 'name_City_id': 'City.id_City'},
    'Models': {'id_column': 'id_Mod', 'name_column': 'name_Mod'},
    'Roles': {'id_column': 'id_Roles', 'name_column': 'name_Roles'},
    'Transmission': {'id_column': 'id_Trans', 'name_column': 'name_Trans'},
    'TypeOfEngine': {'id_column': 'id_TypeEng', 'name_column': 'name_TypeEng'},
    'User': {'id_column': 'id_User', 'name_column': 'log_User', 'city_User_id': 'City.id_City',
             'role_User_id': 'Roles.id_Roles', 'status_User_id': 'UserStatus.id_UserStat'},
    'UserStatus': {'id_column': 'id_UserStat', 'name_column': 'name_UserStat'},
    'Wheeldrive': {'id_column': 'id_Wheel', 'name_column': 'name_Wheel'}
}


class AddDialog(QtWidgets.QDialog):
    def __init__(self, parent, cur):
        super().__init__(parent)
        self.cur = cur

        self.setWindowTitle("Добавление записи")

        self.input_widgets = []
        self.input_layout = QtWidgets.QFormLayout()

        self.table_name_label = QtWidgets.QLabel(parent.table_selector.currentText())
        self.input_layout.addRow("Таблица:", self.table_name_label)

        columns = [desc[0] for desc in self.cur.description]
        id_column = id_columns[parent.table_selector.currentText()]['id_column']
        name_column = id_columns[parent.table_selector.currentText()]['name_column']

        tables = list(id_columns.keys())
        for column_name in columns[1:]:
            if column_name == id_column:
                input_widget = QtWidgets.QLineEdit()
            elif parent.table_selector.currentText() in tables and id_columns[parent.table_selector.currentText()].get(
                    column_name):
                # column is a foreign key
                input_widget = QtWidgets.QComboBox()
                input_widget.setEditable(False)
                related_table_name = id_columns[parent.table_selector.currentText()].get(column_name).split('.')[0]
                related_name_column = id_columns.get(related_table_name, {}).get('name_column')
                if related_table_name and related_name_column:
                    self.cur.execute(
                        f'SELECT "{id_columns[related_table_name]["id_column"]}", "{related_name_column}" FROM "{related_table_name}"')
                    items = self.cur.fetchall()
                    for item in items:
                        input_widget.addItem(item[1], item[0])
            else:
                input_widget = QtWidgets.QLineEdit()
            self.input_widgets.append(input_widget)
            self.input_layout.addRow(column_name + ":", input_widget)

        self.setLayout(self.input_layout)

        self.save_button = QtWidgets.QPushButton("Сохранить")
        self.save_button.clicked.connect(self.save_data)
        self.input_layout.addWidget(self.save_button)

    def save_data(self):
        values = []
        for widget in self.input_widgets:
            if isinstance(widget, QtWidgets.QComboBox):
                values.append(widget.currentData())
            else:
                values.append(widget.text())
        values_string = ", ".join([f"'{value}'" for value in values])
        table_name = self.parent().table_selector.currentText()
        query = f"""INSERT INTO "{table_name}" VALUES(DEFAULT, {values_string})"""

        try:
            self.parent().cur.execute(query)
            self.parent().conn.commit()
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "Ошибка", "Не удалось сохранить запись: " + str(e))
        else:
            self.parent().on_table_changed()
            self.accept()


if __name__ == "__main__":
    app = QtWidgets.QApplication([])
    main_window = MainWindow()
    main_window.show()
    app.exec()
