import webbrowser

from PyQt6.QtCore import Qt, QThreadPool
from PyQt6.QtGui import QColor, QFont, QPalette
from PyQt6.QtWidgets import (
    QCheckBox,
    QDialog,
    QFormLayout,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QStyle,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QScrollArea,
    QFrame,
    QWidget,
)

from .helpers import get_logger
from .toggleswitch import ToggleSwitch


RED_QPUSHBUTTON_STYLE = """
            QPushButton {
                background-color: #F44336;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 5px 10px;
            }
            QPushButton:hover {
                background-color: #E53935;
            }
            QPushButton:pressed {
                background-color: #D32F2F;
            }
        """
GREEN_QPUSHBUTTON_STYLE = """
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 5px 10px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:pressed {
                background-color: #3e8e41;
            }
        """

BLUE_QPUSHBUTTON_STYLE = """
            QPushButton {
                background-color: #2196F3;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 5px 10px;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
            QPushButton:pressed {
                background-color: #1565C0;
            }
        """


class AddRowDialog(QDialog):
    def __init__(self):
        super().__init__()

        # 设置固定大小
        self.setMinimumSize(380, 100)

        self.pageid_input = QLineEdit()
        self.deck_input = QLineEdit()
        # 新增
        input_layout = QFormLayout()
        input_layout.addRow("Notion PageID:", self.pageid_input)
        input_layout.addRow("Target Deck:", self.deck_input)

        self.ok_button = QPushButton("OK")
        self.cancel_button = QPushButton("Cancel")

        button_layout = QHBoxLayout()
        button_layout.addWidget(self.ok_button)
        button_layout.addWidget(self.cancel_button)

        layout = QVBoxLayout()
        layout.addLayout(input_layout)
        layout.addLayout(button_layout)
        self.setLayout(layout)

        self.ok_button.clicked.connect(self.accept)
        self.cancel_button.clicked.connect(self.reject)

    def accept(self):
        if not self.pageid_input.text() or not self.deck_input.text():
            # 两个输入框都不能为空, 弹出错误提示，并且不关闭对话框
            QMessageBox.warning(self, "Warning", "Please input the Notion PageID and Target Deck name.")
            return
        else:
            # 检查deck是否合法
            if self.deck_input.text().startswith("::"):
                QMessageBox.warning(self, "Warning", f"Deck name cannot start with {self.deck_input.text()[0]}.")
                return
            elif self.deck_input.text().endswith("::"):
                QMessageBox.warning(self, "Warning", f"Deck name cannot end with {self.deck_input.text()[-1]}.")
                return
            # 移除空格
            deck_name = self.deck_input.text().strip()
            self.deck_input.setText(deck_name)

            cur_pageid = self.pageid_input.text().strip()
            self.pageid_input.setText(cur_pageid)

            if "-" in self.pageid_input.text():
                # 移除 - 符号
                cur_pageid = self.pageid_input.text().replace("-", "")
                self.pageid_input.setText(cur_pageid)

            if len(self.pageid_input.text()) != 32:  # 18cc2a7c7ba74d2b9b3fdd9f83d591f1
                QMessageBox.warning(
                    self,
                    "Warning",
                    "<p>Notion PageID must be 32 characters long or 36 characters long with '-'.</p>"
                    "<p>Examples: </p>"
                    "<ul>"
                    "<li style='margin-bottom:10px;'>18cc2a7c7ba74d2b9b3fdd9f83d591e1</li>"
                    "<li style='margin-bottom:10px;'>18cc2a7c-7ba7-4d2b-9b3f-dd9f83d591e1</li>"
                    "</ul>",
                )
                return

        super().accept()

    def reject(self):
        super().reject()


class PageDeckTable(QWidget):
    def __init__(self, notion_pages):
        super().__init__()

        # 设置字体, 11号, 不加粗
        font = QFont("Arial", 11, QFont.Weight.Normal)
        self.setFont(font)

        # 创建一个 QTableWidget
        self.table = QTableWidget(0, 5)
        self.table.setHorizontalHeaderLabels(["PageID", "TargetDeck", "Recursive", "AbsUpdate", "IncUpdate"])
        self.table.horizontalHeader().sectionDoubleClicked.connect(self.header_double_clicked)
        # 鼠标移动到 Recursive 上时显示提示
        # self.table.horizontalHeaderItem(2).setToolTip(
        #     "Recursive: If checked, the plugin will sync the subpages of the page."
        # )

        # 表格内容居中
        self.table.horizontalHeader().setDefaultAlignment(Qt.AlignmentFlag.AlignCenter)
        self.table.verticalHeader().setDefaultAlignment(Qt.AlignmentFlag.AlignCenter)

        # 表 不显示行号
        self.table.verticalHeader().setVisible(False)

        # 设置表格样式
        self.table.setStyleSheet("""
            QTableWidget {
                border: 1px solid #d3d3d3;
                gridline-color: #d3d3d3;
                background-color: #f0f0f0;
                selection-background-color: #e0e0e0;
            }
            QTableWidget::item {
                padding: 5px;
                border: 1px solid #d3d3d3;
            }
            QHeaderView::section {
                background-color: #d3d3d3;
                padding: 2px;
                border: 1px solid #d3d3d3;
            }
        """)

        # 设置表格列自适应宽度
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setStretchLastSection(True)

        # 创建按钮
        self.add_button = QPushButton("Add Item")
        self.delete_button = QPushButton("Delete Item")

        self.add_button.setStyleSheet(GREEN_QPUSHBUTTON_STYLE)
        self.delete_button.setStyleSheet(RED_QPUSHBUTTON_STYLE)

        # 连接按钮的点击事件
        self.add_button.clicked.connect(self.add_row)
        self.delete_button.clicked.connect(self.delete_row)

        # 按钮布局
        button_layout = QHBoxLayout()
        button_layout.addWidget(self.add_button)
        button_layout.addWidget(self.delete_button)

        # 下划线提示按钮，点击后显示帮助信息
        question_layout = QHBoxLayout()  # 向左对齐
        question_label = QLabel("🤷Have a question about this table?")
        question_button = QPushButton("Click me!")  # 按钮中字体向左, 颜色为灰色
        question_button.setStyleSheet(
            "QPushButton { border: none; color: #333; text-align: left; text-decoration: underline; padding-left: 0; }"
        )
        question_button.setToolTip("Click here to get help.")
        question_button.setStyleSheet(
            "QPushButton { border: none; color: #333; text-align: left; text-decoration: underline; padding-left: 0; }"
            "QPushButton:pressed { background-color: none; }"
        )
        question_button.clicked.connect(self.question_widget)
        question_layout.addWidget(question_label)
        question_layout.addWidget(question_button)
        question_layout.addStretch()

        # 创建布局
        layout = QVBoxLayout()
        layout.addWidget(self.table)
        layout.addLayout(button_layout)
        layout.setSpacing(10)  # 间隔一点距离
        layout.addLayout(question_layout)

        self.setLayout(layout)

        # 初始化表格
        self.init_table(notion_pages)

    def question_widget(self):
        msg_box = QMessageBox(self)
        msg_box.setWindowTitle("Help")
        msg_box.setIcon(QMessageBox.Icon.NoIcon)
        msg_box.setText(
            """
<p><b>Bảng này dùng để cấu hình cài đặt đồng bộ cho các trang Notion.</b><br>
Ý nghĩa các cột như sau:<br><br>

<b>• PageID</b>: Mã định danh duy nhất của trang Notion. Bạn có thể tìm thấy PageID trong URL của trang.<br>
Ví dụ: nếu URL là https://www.notion.so/username/18cc2a7c7ba74d2b9b3fdd9f83d591e1?pvs=4<br>
thì PageID là: 18cc2a7c7ba74d2b9b3fdd9f83d591e1.<br><br>

<b>• TargetDeck</b>: Tên bộ thẻ (deck) trong Anki mà trang Notion sẽ được đồng bộ vào. Nếu deck chưa tồn tại trong Anki, addon sẽ tự động tạo mới.<br>
Để tạo sub-deck, dùng dấu ':' để phân tách. Ví dụ: math:algebra nghĩa là trang sẽ được đồng bộ vào sub-deck algebra thuộc deck math.<br><br>

<b>• Recursive</b>: Nếu bật, addon sẽ đồng bộ cả các trang con của PageID.<br>
<i>Lưu ý: Tính năng này chỉ khả dụng với gói Notion Business.</i><br><br>

<b>• AbsUpdate</b> (Absolute Update – Cập nhật toàn bộ): Nếu bật, addon sẽ đồng bộ lại toàn bộ deck Anki theo nội dung trong Notion.
Các thẻ đã tồn tại trong deck nhưng không còn trong Notion sẽ bị xoá.<br><br>

<b>• IncUpdate</b> (Incremental Update – Cập nhật tăng dần): Nếu bật, addon chỉ thêm các thẻ mới vào deck.
Các thẻ đã có trong deck sẽ không bị xoá.<br><br>

<b>Lưu ý</b>: AbsUpdate và IncUpdate không thể bật cùng lúc. Nếu không chọn cả hai, addon sẽ không cập nhật trang này.
</p>
"""
        )
        msg_box.exec()

    def init_table(self, notion_pages):
        for page in notion_pages:
            pageid = page["page_id"]
            deck = page["target_deck"]
            recursive = page["recursive"]
            incremental_update = page["incremental_update"]
            absolute_update = page["absolute_update"]

            # 如果absolute_update 和 incremental_update 都为True, 则都为False
            if absolute_update and incremental_update:
                incremental_update = False
                absolute_update = False

            self.add_row_(pageid, deck, recursive, absolute=absolute_update, relative=incremental_update)

    def add_row_(self, pageid, deck, recursive=True, absolute=False, relative=True):
        row_position = self.table.rowCount()
        self.table.insertRow(row_position)
        # 1 位置是 pageid, 2 位置是 deck, 3 位置是 recursive, 4 位置是 absolute, 5 位置是 relative
        self.table.setItem(row_position, 0, QTableWidgetItem(pageid))
        self.table.setItem(row_position, 1, QTableWidgetItem(deck))
        self.table.setCellWidget(row_position, 2, QCheckBox())
        self.table.setCellWidget(row_position, 3, QCheckBox())
        self.table.setCellWidget(row_position, 4, QCheckBox())

        # 1 2位置居中
        self.table.item(row_position, 0).setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        self.table.item(row_position, 1).setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        # 美化复选框的样式, 复选框居中
        self.table.cellWidget(row_position, 2).setStyleSheet("QCheckBox { margin-left: 43%; margin-right: 50%; }")
        self.table.cellWidget(row_position, 3).setStyleSheet("QCheckBox { margin-left: 43%; margin-right: 50%; }")
        self.table.cellWidget(row_position, 4).setStyleSheet("QCheckBox { margin-left: 43%; margin-right: 50%; }")

        self.table.cellWidget(row_position, 2).setChecked(recursive)
        self.table.cellWidget(row_position, 3).setChecked(absolute)
        self.table.cellWidget(row_position, 4).setChecked(relative)
        # 设置互斥选择框
        self.table.cellWidget(row_position, 3).pressed.connect(
            lambda: self.table.cellWidget(row_position, 4).setChecked(False)
        )
        self.table.cellWidget(row_position, 4).pressed.connect(
            lambda: self.table.cellWidget(row_position, 3).setChecked(False)
        )

    def add_row(self):
        # 弹出一个对话框，同时获取输入的数据
        dialog = AddRowDialog()
        if dialog.exec() == QDialog.DialogCode.Accepted:
            pageid = dialog.pageid_input.text()
            deck = dialog.deck_input.text()
            self.add_row_(pageid, deck)

    def delete_row(self):
        selected_items = self.table.selectedItems()
        if selected_items:
            row = selected_items[0].row()
            self.table.removeRow(row)
        else:
            QMessageBox.warning(self, "Warning", "Please select a row to delete.")

    def header_double_clicked(self, column):
        # 如果点击的是绝对更新或相对更新的表头，则全选或全不选
        # 选中的列全选，未选中的列全不选
        if column in [3, 4]:
            anthor_column = 3 if column == 4 else 4
            for row in range(self.table.rowCount()):
                self.table.cellWidget(row, column).setChecked(True)
                self.table.cellWidget(row, anthor_column).setChecked(False)
        elif column == 1:
            # 如果点击的是 deck 的表头，则排序
            self.table.sortItems(column)

    def clear_inputs(self):
        self.pageid_input.clear()
        self.deck_input.clear()

    def get_table_data(self):
        data = []
        for row in range(self.table.rowCount()):
            pageid = self.table.item(row, 0).text()
            deck = self.table.item(row, 1).text()
            recursive = self.table.cellWidget(row, 2).isChecked()
            absolute = self.table.cellWidget(row, 3).isChecked()
            relative = self.table.cellWidget(row, 4).isChecked()
            data.append(
                {
                    "page_id": pageid,
                    "target_deck": deck,
                    "recursive": recursive,
                    "absolute_update": absolute,
                    "incremental_update": relative,
                }
            )
        return data


class UerInfoWidget(QWidget):
    def __init__(self, user_info, user_manager=None, addon_manager=None, sync_setting_widget=None, logined=False):
        super().__init__()

        self.sync_setting_widget = sync_setting_widget

        self.addon_manager = addon_manager

        # 开启一个线程用来登录
        self.login_thread_pool = QThreadPool.globalInstance()

        self.logger = get_logger("UerInfoWidget", True)

        # 设置字体, 11号, 不加粗
        font = QFont("Arial", 11, QFont.Weight.Normal)
        self.setFont(font)

        palette = self.palette()
        palette.setColor(QPalette.ColorRole.Window, QColor(240, 240, 240))
        self.setPalette(palette)

        self.logined = logined
        # 如果已经登录，则显示 user_email 和 password, 右边显示注销按钮
        # 如果未登录，则显示 user_email 和 password 输入框，右边显示登录按钮

        self.user_email_input = QLineEdit()
        self.user_password_input = QLineEdit()

        self.user_email_input.setText(user_info["user_email"])
        self.user_password_input.setText(user_info["password"])

        self.logger.info(f"login state:{logined}")
        self.login_logout_button = QPushButton("Login" if not logined else "Logout")
        self.signup_dashboard_button = QPushButton("Sign Up" if not logined else "Dashboard")

        # 设置输入框样式
        self.user_email_input.setStyleSheet("QLineEdit { border: 1px solid #ccc; padding: 5px; border-radius: 5px; }")
        self.user_password_input.setStyleSheet(
            "QLineEdit { border: 1px solid #ccc; padding: 5px; border-radius: 5px; }"
        )

        # 设置按钮样式
        self.login_logout_button.setStyleSheet(BLUE_QPUSHBUTTON_STYLE)
        # self.login_logout_button.addStyleSheet("QPushButton { padding: 5px 10px; border-radius: 5px; }")
        self.signup_dashboard_button.setStyleSheet(GREEN_QPUSHBUTTON_STYLE)
        # self.signup_dashboard_button.setStyleSheet("QPushButton { padding: 5px 10px; border-radius: 5px; }")

        # 总的上下布局
        layout = QVBoxLayout()

        # 用户 邮箱 和 密码 输入框
        user_info_layout = QGridLayout()
        user_info_layout.addWidget(QLabel("User Email:", font=font), 0, 0)
        user_info_layout.addWidget(self.user_email_input, 0, 1)
        user_info_layout.addWidget(QLabel("Password:", font=font), 1, 0)
        user_info_layout.addWidget(self.user_password_input, 1, 1)

        # 登录/注销 和 注册/访问 按钮
        button_layout = QHBoxLayout()
        button_layout.addWidget(self.login_logout_button)
        button_layout.addWidget(self.signup_dashboard_button)

        # 下划线提示按钮，点击后显示帮助信息
        question_layout = QHBoxLayout()  # 向左对齐
        question_label = QLabel("🙋 Is it necessary to login?")
        question_button = QPushButton("Click me get answer!")  # 按钮中字体向左, 颜色为灰色
        question_button.setStyleSheet(
            "QPushButton { border: none; color: #333; text-align: left; text-decoration: underline; padding-left: 0; }"
        )
        question_button.setToolTip("Click here to get help.")
        question_button.setStyleSheet(
            "QPushButton { border: none; color: #333; text-align: left; text-decoration: underline; padding-left: 0; }"
            "QPushButton:pressed { background-color: none; }"
        )
        question_button.clicked.connect(self.question_widget)
        question_layout.addWidget(question_label)
        question_layout.addWidget(question_button)
        question_layout.addStretch()

        layout.addLayout(user_info_layout)
        layout.addLayout(button_layout)
        layout.addLayout(question_layout)
        layout.setSpacing(10)  # 间隔一点距离
        self.setLayout(layout)

        # 按钮的点击事件
        self.login_logout_button.clicked.connect(self.handle_login_logout)
        self.signup_dashboard_button.clicked.connect(self.handle_signup_dashboard)

        if self.logined:
            self.handle_login_post()

    def handle_login_logout(self):
        if self.logined:
            self.handle_logout()
        else:
            self.handle_login()

    def handle_signup_dashboard(self):
        if self.logined:
            print("dashboard")
            # 打开浏览器, 跳转到 www.baidu.com
            webbrowser.open("https://www.notion2anki.com/auth/dashboard")
        else:
            print("signup")
            # 打开浏览器, 跳转到 www.baidu.com
            webbrowser.open("https://www.notion2anki.com/auth/signup")

    def handle_login(self):
        self.addon_manager.handle_login(self.user_email_input.text(), self.user_password_input.text())

    def handle_login_post(self):
        """登录后处理"""

        self.logined = True
        self.login_logout_button.setText("Logout")
        self.signup_dashboard_button.setText("Dashboard")
        self.user_email_input.setEnabled(False)
        self.user_password_input.setEnabled(False)

        # login_logout_button 按钮背景颜色改为红色
        self.login_logout_button.setStyleSheet(RED_QPUSHBUTTON_STYLE)

        # 自动同步设置按钮 启用
        self.sync_setting_widget.flash_auto_sync_checkbox(True)

    def handle_logout(self):
        self.logined = False
        self.login_logout_button.setText("Login")
        self.signup_dashboard_button.setText("Sign Up")
        self.user_email_input.setEnabled(True)
        self.user_password_input.setEnabled(True)
        # login_logout_button 按钮背景颜色改为蓝色
        self.login_logout_button.setStyleSheet(
            "QPushButton { background-color: #007bff; color: white; padding: 5px 10px; border-radius: 5px; }"
        )

        # 把 access_token、refresh_token、user_info 清空
        self.addon_manager.handle_logout()
        # 自动同步设置按钮 禁用
        self.sync_setting_widget.flash_auto_sync_checkbox(False)

    def get_user_info(self):
        return {
            "user_email": self.user_email_input.text(),
            "password": self.user_password_input.text(),
        }

    def question_widget(self):
        text = (
            "<p><b>Is it necessary to login?</b></p>"
            "<p>No, you can use the plugin without logging in. However, there are some limitations:</p>"
            "<ul>"
            "<li style='margin-bottom:10px;'>Sync up to 1 pages from Notion to Anki.</li>"
            "<li style='margin-bottom:10px;'>Sync up to 25 notes per page.</li>"
            "</ul>"
            "<p>To remove these limitations, log in to your account.</p>"
            "<p>Visit the <a href='https://www.notion2anki.com'>website</a> for more information.</p>"
        )

        msg_box = QMessageBox(self)
        msg_box.setWindowTitle("Help")
        msg_box.setIcon(QMessageBox.Icon.NoIcon)
        msg_box.setText(text)
        msg_box.exec()


class NotionInfoWidget(QWidget):
    def __init__(self, notion_info):
        super().__init__()

        # 设置字体, 11号, 不加粗
        font = QFont("Arial", 11, QFont.Weight.Normal)
        self.setFont(font)

        palette = self.palette()
        palette.setColor(QPalette.ColorRole.Window, QColor(240, 240, 240))
        self.setPalette(palette)

        self.notion_token_input = QLineEdit()
        self.notion_namespace_input = QLineEdit()

        # 设置输入框的样式
        self.notion_token_input.setStyleSheet("QLineEdit { border: 1px solid #ccc; padding: 5px; border-radius: 5px; }")
        self.notion_namespace_input.setStyleSheet(
            "QLineEdit { border: 1px solid #ccc; padding: 5px; border-radius: 5px; }"
        )
        # 设置输入框的默认值
        self.notion_token_input.setText(notion_info["notion_token"])
        self.notion_namespace_input.setText(notion_info["notion_namespace"])

        # 创建标签
        token_label = QLabel("Notion Token:", font=font)
        namespace_label = QLabel("Notion Namespace:", font=font)

        # 设置标签的样式
        token_label.setStyleSheet("QLabel { color: #333; }")
        namespace_label.setStyleSheet("QLabel { color: #333; }")

        # 创建帮助图标
        token_help_icon = self.create_help_icon("How could I get notion token?")
        namespace_help_icon = self.create_help_icon("How could I get notion namespace?")

        form_layout = QGridLayout()
        form_layout.addWidget(token_label, 0, 0)
        form_layout.addWidget(self.notion_token_input, 0, 1)
        form_layout.addWidget(namespace_label, 1, 0)
        form_layout.addWidget(self.notion_namespace_input, 1, 1)
        form_layout.addWidget(token_help_icon, 0, 2)
        form_layout.addWidget(namespace_help_icon, 1, 2)

        layout = QVBoxLayout()
        layout.addLayout(form_layout)
        self.setLayout(layout)

    def get_notion_info(self):
        return {
            "notion_token": self.notion_token_input.text(),
            "notion_namespace": self.notion_namespace_input.text(),
        }

    def create_help_icon(self, tooltip_text):
        help_icon = QPushButton()
        help_icon.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_MessageBoxQuestion))
        help_icon.setStyleSheet("QPushButton { border: none; }")
        help_icon.setToolTip(tooltip_text)
        help_icon.clicked.connect(lambda: self.show_help_dialog(tooltip_text))
        return help_icon

    def show_help_dialog(self, tooltip_text):
        if tooltip_text == "How could I get notion token?":
            tooltip_text = (
                "<p><b>How to get your Notion token:</b></p>"
                "<ul>"
                "<li style='margin-bottom:10px;'> Log into Notion in your web browser (e.g., Chrome).</li>"
                "<li style='margin-bottom:10px;'> Open the developer tools. (For Chrome and Edge, press <code>F12</code>, for Firefox, press <code>Ctrl+Shift+I</code>, for Safari, press </code>Option+Command+I</code>).</li>"
                "<li style='margin-bottom:10px;'> Go to the <b>Application</b> tab.</li>"
                "<li style='margin-bottom:10px;'> Click on <b>Cookies</b> and then click on the <b>Notion URL</b>. </li>"
                "<li style='margin-bottom:10px;'> Find <code>token_v2</code>. This is your Notion API token.</li>"
                "</ul>"
            )
        elif tooltip_text == "How could I get notion namespace?":
            tooltip_text = (
                "<p><b>How to get your Notion namespace:</b></p>"
                "Your Notion namespace is the part of the URL after <code>https://www.notion.so/</code>."
                "<p>Example: "
                "If your URL is <code>https://www.notion.so/cope/18cc2a7c7ba74d2b9b3fdd9f83d591e1?pvs=4</code>, then your namespace is <b>cope</b>.<p>"
                "<div style='background-color: #f0f0f0; padding: 10px; border-radius: 5px; border: 1px solid #d3d3d3;'>"
                "<b>Note:</b> The namespace is optional"
                "</div>"
            )

        msg_box = QMessageBox(self)
        msg_box.setWindowTitle("Help")
        msg_box.setIcon(QMessageBox.Icon.NoIcon)
        msg_box.setText(tooltip_text)
        msg_box.exec()


class SyncSettingWidget(QWidget):
    def __init__(self, sync_setting, parent_save_button=None):
        super().__init__()

        self.sync_setting = sync_setting

        # 设置字体, 11号, 不加粗
        font = QFont("Arial", 11, QFont.Weight.Normal)
        self.setFont(font)

        # 设置页面的保存按钮
        self.parent_save_button = parent_save_button

        palette = self.palette()
        palette.setColor(QPalette.ColorRole.Window, QColor(240, 240, 240))
        self.setPalette(palette)

        # 只有当 sync_every_minutes 大于 0 时，初始才会选中
        self.auto_sync_label = QLabel("Auto Sync:", font=font)
        self.auto_sync_checkbox = ToggleSwitch("", on=sync_setting["sync_every_minutes"] > 0)

        # Create input field for sync interval
        self.sync_every_minutes_label = QLabel("Sync Every Minutes:", font=font)
        self.sync_every_minutes_input = QSpinBox()
        self.sync_every_minutes_input.setMinimum(0)
        self.sync_every_minutes_input.setValue(sync_setting["sync_every_minutes"])

        # Style the input field
        self.sync_every_minutes_input.setStyleSheet(
            "QLineEdit { border: 1px solid #ccc; padding: 5px; border-radius: 5px; }"
        )

        # Help icon
        help_icon = self.create_help_icon("How dose it work?")

        # Create layout
        layout = QVBoxLayout()
        # Create checkbox layout, add help icon
        checkbox_layout = QHBoxLayout()
        checkbox_layout.addWidget(self.auto_sync_label)
        checkbox_layout.addWidget(self.auto_sync_checkbox)
        checkbox_layout.addWidget(help_icon)
        checkbox_layout.addStretch()  # Add stretch after the widgets to push them left

        # Create input layout with better spacing
        self.input_layout = QHBoxLayout()
        self.input_layout.addWidget(self.sync_every_minutes_label)
        self.input_layout.addWidget(self.sync_every_minutes_input)
        self.input_layout.addStretch()

        layout.addLayout(checkbox_layout)
        layout.addLayout(self.input_layout)
        layout.setSpacing(15)

        # Connect checkbox state change to show/hide function
        self.auto_sync_checkbox.toggled.connect(self.toggle_input_visibility)

        # Set initial visibility based on checkbox state
        self.toggle_input_visibility(self.auto_sync_checkbox.isToggled())

        self.setLayout(layout)

    def toggle_input_visibility(self, state: bool):
        self.sync_every_minutes_label.setVisible(state)
        self.sync_every_minutes_input.setVisible(state)

        # Change the text of the parent save button
        self.parent_save_button.setText("Save and AutoSync" if state else "Save")

    def get_sync_setting(self):
        return {
            "sync_every_minutes": self.sync_every_minutes_input.value() if self.auto_sync_checkbox.isToggled() else 0
        }

    def create_help_icon(self, tooltip_text):
        help_icon = QPushButton()
        help_icon.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_MessageBoxQuestion))
        help_icon.setStyleSheet("""
            QPushButton {
                border: none;
                padding: 5px;
            }
            QPushButton:hover {
                background-color: #dcdde1;
                border-radius: 15px;
            }
        """)
        help_icon.setToolTip(tooltip_text)
        help_icon.clicked.connect(lambda: self.show_help_dialog(tooltip_text))
        return help_icon

    def show_help_dialog(self, tooltip_text):
        if tooltip_text == "How dose it work?":
            tooltip_text = (
                "<p><strong>How does it work?</strong></p>"
                "<ol>"
                "<li style='margin-bottom:10px;'>The plugin will sync the Notion page to Anki every 30 minutes by default. </li>"
                "<li style='margin-bottom:10px;'>You can change the sync interval by modifying the 'Sync Every Minutes' field. Set it to 0 to disable auto sync.</li>"
                "</ol>"
            )

        msg_box = QMessageBox(self)
        msg_box.setWindowTitle("Help")
        msg_box.setIcon(QMessageBox.Icon.NoIcon)
        msg_box.setTextFormat(Qt.TextFormat.RichText)
        msg_box.setText(tooltip_text)
        msg_box.exec()

    def flash_auto_sync_checkbox(self, logined=True):
        """Custom build: auto sync always available."""
        self.auto_sync_checkbox.enable()
        self.auto_sync_checkbox.setToggle(self.sync_setting.get('sync_every_minutes',0) > 0)
        self.toggle_input_visibility(self.auto_sync_checkbox.isToggled())


class SettingsDialog(QDialog):
    def __init__(self, parent=None, config=None, addon_manager=None):
        super().__init__(parent)

        self.addon_manager = addon_manager

        self.config = config
        self.debug = "debug" in self.config and self.config["debug"]
        self.logger = get_logger(self.__class__.__name__, self.debug)

        self.logger.info("SettingsDialog init")

        notion_pages = self.config["notion_pages"]
        notion_info = {"notion_token": self.config["notion_token"], "notion_namespace": self.config["notion_namespace"]}
        sync_setting = {"sync_every_minutes": self.config["sync_every_minutes"]}

        # 按钮布局
        buttuon_layout = QHBoxLayout()
        self.save_button = QPushButton("Save")
        self.once_sync_button = QPushButton("Save and Sync Immediately")
        # self.auto_sync_button = QPushButton("AutoSync")
        self.cancel_button = QPushButton("Cancel")

        buttuon_layout.addWidget(self.save_button)
        buttuon_layout.addWidget(self.once_sync_button)
        # buttuon_layout.addWidget(self.auto_sync_button)
        buttuon_layout.addWidget(self.cancel_button)

        # Notion 同步分组
        notion_info_group = QGroupBox("Notion to Anki Config")
        notion_info_group.setFont(QFont("Arial", 11, QFont.Weight.Bold))
        notion_info_group_layout = QVBoxLayout()

        self.page_deck_table = PageDeckTable(notion_pages)
        self.notion_info_widget = NotionInfoWidget(notion_info)
        notion_info_group_layout.addWidget(self.notion_info_widget)
        notion_info_group_layout.addWidget(self.page_deck_table)
        notion_info_group.setLayout(notion_info_group_layout)

        # 同步设置 分组
        sync_setting_group = QGroupBox("Sync Setting")
        sync_setting_group.setFont(QFont("Arial", 11, QFont.Weight.Bold))
        sync_setting_group_layout = QVBoxLayout()
        self.sync_setting_widget = SyncSettingWidget(sync_setting, parent_save_button=self.save_button)
        sync_setting_group_layout.addWidget(self.sync_setting_widget)
        sync_setting_group.setLayout(sync_setting_group_layout)


        # Tổng layout (có hỗ trợ cuộn khi màn hình nhỏ)
        content_layout = QVBoxLayout()
        content_layout.addWidget(notion_info_group)
        content_layout.addWidget(sync_setting_group)
        content_layout.addLayout(buttuon_layout)
        content_layout.setSpacing(30)

        container = QWidget()
        container.setLayout(content_layout)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setWidget(container)

        main_layout = QVBoxLayout()
        main_layout.addWidget(scroll)
        self.setLayout(main_layout)

        self.save_button.clicked.connect(self.save)
        self.cancel_button.clicked.connect(self.close)
        self.once_sync_button.clicked.connect(self.sync_once)
        # self.auto_sync_button.clicked.connect(self.auto_sync)

        self.set_button_style()

        # 初始化保存按钮的文本
        self.save_button.setText(
            "Save and AutoSync" if self.sync_setting_widget.auto_sync_checkbox.isToggled() else "Save"
        )

        self.resize(720, 820)
        self.setMinimumSize(520, 620)
        self.logger.info("SettingsDialog init done")

    def set_button_style(self):
        # 设置字体
        font = QFont("Arial", 11, QFont.Weight.Bold)
        self.save_button.setFont(font)
        self.once_sync_button.setFont(font)
        # self.auto_sync_button.setFont(font)
        self.cancel_button.setFont(font)
        # 设置样式表
        self.save_button.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 10px 20px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:pressed {
                background-color: #3e8e41;
            }
        """)

        self.once_sync_button.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 10px 20px;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
            QPushButton:pressed {
                background-color: #1565C0;
            }
        """)

        # self.auto_sync_button.setStyleSheet("""
        #     QPushButton {
        #         background-color: #FFC107;
        #         color: white;
        #         border: none;
        #         border-radius: 5px;
        #         padding: 10px 20px;
        #     }
        #     QPushButton:hover {
        #         background-color: #FFA000;
        #     }
        #     QPushButton:pressed {
        #         background-color: #FF8F00;
        #     }
        # """)

        self.cancel_button.setStyleSheet("""
            QPushButton {
                background-color: #F44336;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 10px 20px;
            }
            QPushButton:hover {
                background-color: #E53935;
            }
            QPushButton:pressed {
                background-color: #D32F2F;
            }
        """)

    def save(self):
        """保存设置"""
        page_deck_data = self.page_deck_table.get_table_data()
        user_info = {'user_email': '', 'password': ''}  # login removed
        notion_info = self.notion_info_widget.get_notion_info()
        sync_setting_info = self.sync_setting_widget.get_sync_setting()

        # 检查数据类型是否合法
        if (
            not isinstance(sync_setting_info["sync_every_minutes"], int)
            and not sync_setting_info["sync_every_minutes"].isdigit()
        ):
            QMessageBox.warning(self, "Warning", "Please input a valid number for sync interval.")
            return

        # 对于 同样的 target_deck, 不能一个设置相对，一个设置绝对
        import collections

        deck_sync_type = collections.defaultdict(set)
        for page_config in page_deck_data:
            if page_config["absolute_update"]:
                deck_sync_type[page_config["target_deck"]].add("absolute")
            if page_config["incremental_update"]:
                deck_sync_type[page_config["target_deck"]].add("incremental")

        wron_deck_config = [deck for deck in deck_sync_type.keys() if len(deck_sync_type[deck]) > 1]
        if wron_deck_config:
            QMessageBox.warning(
                self,
                "Warning",
                f"These decks have conflicting sync settings: `{', '.join(wron_deck_config)}`, both absolute and incremental updates are enabled. Please choose only one.",
            )
            return

        new_config = {
            "debug": self.config["debug"],
            "notion_pages": page_deck_data,
            "user_email": user_info["user_email"],
            "user_password": user_info["password"],
            "sync_every_minutes": int(sync_setting_info["sync_every_minutes"]),
            "notion_token": notion_info["notion_token"],
            "notion_namespace": notion_info["notion_namespace"],
        }
        self.addon_manager.update_config(new_config)

        # 如果没有登录, 且没有在登录中, 那么需要登录
        # if not self.user_manager.access_token:
        #     if self.addon_manager.login_thread_pool.activeThreadCount() == 0:
        #         self.user_info_widget.handle_login()

        # 如果有自动更新,那么是需要自动更新的
        if sync_setting_info["sync_every_minutes"] > 0:
            self.addon_manager.auto_sync()

        # 关闭窗口
        self.close()

    def sync_once(self):
        """仅更新当前一次, 后面修改该按钮为立即同步"""
        self.save()  # 保存一下配置
        self.logger.info("sync once")
        self.addon_manager.is_auto_sync_flag = False
        self.addon_manager.sync()

    def auto_sync(self):
        """自动更新, 暂时用不到这个"""
        self.save()  # 保存一下配置
        print("auto sync")