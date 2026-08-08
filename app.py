import sys
import platform
import socket
import subprocess
import time
import os
from pathlib import Path

import psutil

from PySide6.QtCore import QTimer, Qt
from PySide6.QtWidgets import (
    QApplication,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QStackedWidget,
    QTableWidget,
    QTableWidgetItem,
    QPlainTextEdit,
    QProgressBar,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)


class TerminalInput(QLineEdit):
    def __init__(self, owner):
        super().__init__()
        self.owner = owner

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Up:
            self.owner.terminal_history_up()
            return

        if event.key() == Qt.Key_Down:
            self.owner.terminal_history_down()
            return

        super().keyPressEvent(event)


class LinuxCommandCenter(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Sysora - demonbazillionz")
        self.resize(1100, 700)

        self.current_path = Path.home()

        self.build_ui()
        self.update_system_info()
        self.load_files()
        self.load_packages()
        self.update_developer()

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_system_info)
        self.timer.start(1000)

        self.process_timer = QTimer(self)
        self.process_timer.timeout.connect(self.update_processes)
        self.process_timer.start(1500)

    def build_ui(self):
        main_widget = QWidget()
        main_widget.setAttribute(Qt.WA_StyledBackground, True)
        main_layout = QHBoxLayout(main_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        sidebar = QFrame()
        sidebar.setObjectName("sidebar")
        sidebar.setFixedWidth(230)

        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setContentsMargins(20, 25, 20, 20)
        sidebar_layout.setSpacing(10)

        logo = QLabel("SYSORA")
        logo.setObjectName("logo")

        subtitle = QLabel("demonbazillionz")
        subtitle.setObjectName("subtitle")

        sidebar_layout.addWidget(logo)
        sidebar_layout.addWidget(subtitle)
        sidebar_layout.addSpacing(30)

        self.pages = QStackedWidget()

        self.pages.addWidget(self.create_dashboard_page())   # 0
        self.pages.addWidget(self.create_system_page())      # 1
        self.pages.addWidget(self.create_processes_page())   # 2
        self.pages.addWidget(self.create_network_page())     # 3
        self.pages.addWidget(self.create_files_page())       # 4
        self.pages.addWidget(self.create_packages_page())    # 5
        self.pages.addWidget(self.create_developer_page())   # 6
        self.pages.addWidget(self.create_terminal_page())    # 7

        navigation = [
            ("◉  Dashboard", 0),
            ("▣  System", 1),
            ("▤  Packages", 5),
            ("◈  Network", 3),
            ("□  Files", 4),
            ("⚙  Processes", 2),
            ("⌘  Developer", 6),
            (">_  Terminal", 7),
        ]

        self.nav_buttons = []

        for text, page_index in navigation:
            button = QPushButton(text)
            button.setObjectName("navButton")
            button.setCheckable(True)
            button.setProperty("page_index", page_index)
            button.clicked.connect(
                lambda checked=False, index=page_index:
                self.switch_page(index)
            )
            self.nav_buttons.append(button)
            sidebar_layout.addWidget(button)

        sidebar_layout.addStretch()

        version = QLabel("v1.1.0 • System 2.0")
        version.setObjectName("version")
        sidebar_layout.addWidget(version)

        main_layout.addWidget(sidebar)
        main_layout.addWidget(self.pages)

        self.setCentralWidget(main_widget)
        self.apply_style()

        self.switch_page(0)

    def switch_page(self, index):
        self.pages.setCurrentIndex(index)

        if hasattr(self, "nav_buttons"):
            for button in self.nav_buttons:
                button.setChecked(
                    button.property("page_index") == index
                )

    def create_dashboard_page(self):
        page = QWidget()
        page.setObjectName("dashboardPage")

        layout = QVBoxLayout(page)
        layout.setContentsMargins(35, 30, 35, 30)
        layout.setSpacing(18)

        header_row = QHBoxLayout()

        header_box = QVBoxLayout()
        header = QLabel("SYSTEM OVERVIEW")
        header.setObjectName("header")

        subtitle = QLabel("LIVE SYSTEM MONITOR")
        subtitle.setObjectName("subtitle")

        header_box.addWidget(header)
        header_box.addWidget(subtitle)

        header_row.addLayout(header_box)
        header_row.addStretch()

        self.dashboard_status = QLabel("● SYSTEM ONLINE")
        self.dashboard_status.setObjectName("status")
        header_row.addWidget(self.dashboard_status, 0, Qt.AlignTop)

        layout.addLayout(header_row)

        cards = QHBoxLayout()
        cards.setSpacing(12)

        self.cpu_value = QLabel("--")
        self.ram_value = QLabel("--")
        self.disk_value = QLabel("--")

        self.cpu_bar = QProgressBar()
        self.ram_bar = QProgressBar()
        self.disk_bar = QProgressBar()

        self.cpu_bar.setTextVisible(False)
        self.ram_bar.setTextVisible(False)
        self.disk_bar.setTextVisible(False)

        for title, value, bar in [
            ("CPU", self.cpu_value, self.cpu_bar),
            ("RAM", self.ram_value, self.ram_bar),
            ("DISK", self.disk_value, self.disk_bar),
        ]:
            card = QFrame()
            card.setObjectName("metricCard")

            card_layout = QVBoxLayout(card)
            card_layout.setContentsMargins(16, 14, 16, 14)

            title_label = QLabel(title)
            title_label.setObjectName("cardTitle")
            value.setObjectName("metricValue")

            bar.setFixedHeight(6)

            card_layout.addWidget(title_label)
            card_layout.addWidget(value)
            card_layout.addWidget(bar)

            cards.addWidget(card)

        layout.addLayout(cards)

        info = QFrame()
        info.setObjectName("info")
        info_layout = QVBoxLayout(info)

        title = QLabel("SYSTEM INFORMATION")
        title.setObjectName("sectionTitle")
        info_layout.addWidget(title)

        self.os_label = QLabel()
        self.kernel_label = QLabel()
        self.hostname_label = QLabel()
        self.uptime_label = QLabel()

        for label in [
            self.os_label,
            self.kernel_label,
            self.hostname_label,
            self.uptime_label,
        ]:
            label.setObjectName("infoRow")
            info_layout.addWidget(label)

        layout.addWidget(info)

        activity = QFrame()
        activity.setObjectName("info")
        activity_layout = QVBoxLayout(activity)

        activity_title = QLabel("RESOURCE ACTIVITY")
        activity_title.setObjectName("sectionTitle")
        activity_layout.addWidget(activity_title)

        self.activity_label = QLabel(
            "Monitoring CPU, memory and storage in real time..."
        )
        self.activity_label.setObjectName("subtitle")
        activity_layout.addWidget(self.activity_label)

        layout.addWidget(activity)
        layout.addStretch()

        return page

    def create_system_page(self):
        page = QWidget()
        page.setObjectName("systemPage")

        outer_layout = QVBoxLayout(page)
        outer_layout.setContentsMargins(35, 30, 35, 30)
        outer_layout.setSpacing(12)

        header_row = QHBoxLayout()

        header_box = QVBoxLayout()
        header = QLabel("SYSTEM")
        header.setObjectName("header")

        subtitle = QLabel(
            "SYSTEM 2.0 • HARDWARE, RESOURCES & LINUX STATUS"
        )
        subtitle.setObjectName("subtitle")

        header_box.addWidget(header)
        header_box.addWidget(subtitle)

        header_row.addLayout(header_box)
        header_row.addStretch()

        self.system_live_status = QLabel("● LIVE")
        self.system_live_status.setObjectName("status")
        header_row.addWidget(self.system_live_status, 0, Qt.AlignTop)

        refresh_button = QPushButton("↻  REFRESH")
        refresh_button.setObjectName("toolButton")
        refresh_button.clicked.connect(self.update_system_info)
        header_row.addWidget(refresh_button, 0, Qt.AlignTop)

        outer_layout.addLayout(header_row)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setObjectName("systemScroll")

        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(0, 5, 8, 10)
        content_layout.setSpacing(12)

        # -----------------------------------------------------
        # RESOURCE CARDS
        # -----------------------------------------------------
        resources = QGridLayout()
        resources.setSpacing(10)

        self.system_cpu_value = QLabel("--")
        self.system_ram_value = QLabel("--")
        self.system_disk_value = QLabel("--")
        self.system_swap_value = QLabel("--")

        self.system_cpu_bar = QProgressBar()
        self.system_ram_bar = QProgressBar()
        self.system_disk_bar = QProgressBar()
        self.system_swap_bar = QProgressBar()

        self.system_cpu_detail = QLabel("Loading...")
        self.system_ram_detail = QLabel("Loading...")
        self.system_disk_detail = QLabel("Loading...")
        self.system_swap_detail = QLabel("Loading...")

        cards = [
            ("CPU", self.system_cpu_value, self.system_cpu_bar, self.system_cpu_detail),
            ("MEMORY", self.system_ram_value, self.system_ram_bar, self.system_ram_detail),
            ("STORAGE", self.system_disk_value, self.system_disk_bar, self.system_disk_detail),
            ("SWAP", self.system_swap_value, self.system_swap_bar, self.system_swap_detail),
        ]

        for index, (title, value, bar, detail) in enumerate(cards):
            card = QFrame()
            card.setObjectName("systemMetricCard")
            card_layout = QVBoxLayout(card)
            card_layout.setContentsMargins(14, 12, 14, 12)
            card_layout.setSpacing(6)

            title_label = QLabel(title)
            title_label.setObjectName("cardTitle")

            value.setObjectName("systemMetricValue")
            bar.setFixedHeight(6)
            bar.setTextVisible(False)

            detail.setObjectName("systemDetail")

            card_layout.addWidget(title_label)
            card_layout.addWidget(value)
            card_layout.addWidget(bar)
            card_layout.addWidget(detail)

            resources.addWidget(card, index // 2, index % 2)

        content_layout.addLayout(resources)

        # -----------------------------------------------------
        # CPU + MEMORY
        # -----------------------------------------------------
        hardware_grid = QGridLayout()
        hardware_grid.setSpacing(10)

        cpu_frame = QFrame()
        cpu_frame.setObjectName("info")
        cpu_layout = QVBoxLayout(cpu_frame)

        cpu_title = QLabel("CPU DETAILS")
        cpu_title.setObjectName("sectionTitle")
        cpu_layout.addWidget(cpu_title)

        self.system_cpu_model = QLabel()
        self.system_cpu_cores = QLabel()
        self.system_cpu_threads = QLabel()
        self.system_cpu_freq = QLabel()
        self.system_cpu_load = QLabel()
        self.system_cpu_per_core = QLabel()

        for label in [
            self.system_cpu_model,
            self.system_cpu_cores,
            self.system_cpu_threads,
            self.system_cpu_freq,
            self.system_cpu_load,
            self.system_cpu_per_core,
        ]:
            label.setObjectName("infoRow")
            label.setWordWrap(True)
            cpu_layout.addWidget(label)

        memory_frame = QFrame()
        memory_frame.setObjectName("info")
        memory_layout = QVBoxLayout(memory_frame)

        memory_title = QLabel("MEMORY DETAILS")
        memory_title.setObjectName("sectionTitle")
        memory_layout.addWidget(memory_title)

        self.system_ram_total = QLabel()
        self.system_ram_used = QLabel()
        self.system_ram_available = QLabel()
        self.system_ram_cached = QLabel()
        self.system_swap_detail_label = QLabel()

        for label in [
            self.system_ram_total,
            self.system_ram_used,
            self.system_ram_available,
            self.system_ram_cached,
            self.system_swap_detail_label,
        ]:
            label.setObjectName("infoRow")
            memory_layout.addWidget(label)

        hardware_grid.addWidget(cpu_frame, 0, 0)
        hardware_grid.addWidget(memory_frame, 0, 1)

        content_layout.addLayout(hardware_grid)

        # -----------------------------------------------------
        # STORAGE
        # -----------------------------------------------------
        storage_frame = QFrame()
        storage_frame.setObjectName("info")
        storage_layout = QVBoxLayout(storage_frame)

        storage_title_row = QHBoxLayout()
        storage_title = QLabel("FILESYSTEMS & STORAGE")
        storage_title.setObjectName("sectionTitle")
        storage_title_row.addWidget(storage_title)
        storage_title_row.addStretch()

        self.system_storage_summary = QLabel("--")
        self.system_storage_summary.setObjectName("subtitle")
        storage_title_row.addWidget(self.system_storage_summary)

        storage_layout.addLayout(storage_title_row)

        self.system_storage_table = QTableWidget()
        self.system_storage_table.setColumnCount(5)
        self.system_storage_table.setHorizontalHeaderLabels([
            "MOUNT",
            "FILESYSTEM",
            "TOTAL",
            "USED",
            "FREE",
        ])
        self.system_storage_table.setEditTriggers(
            QTableWidget.NoEditTriggers
        )
        self.system_storage_table.setSelectionBehavior(
            QTableWidget.SelectRows
        )
        self.system_storage_table.setAlternatingRowColors(True)
        self.system_storage_table.verticalHeader().setVisible(False)
        self.system_storage_table.setMaximumHeight(220)

        storage_layout.addWidget(self.system_storage_table)
        content_layout.addWidget(storage_frame)

        # -----------------------------------------------------
        # LINUX + POWER + SENSORS
        # -----------------------------------------------------
        details_grid = QGridLayout()
        details_grid.setSpacing(10)

        linux_frame = QFrame()
        linux_frame.setObjectName("info")
        linux_layout = QVBoxLayout(linux_frame)

        linux_title = QLabel("LINUX")
        linux_title.setObjectName("sectionTitle")
        linux_layout.addWidget(linux_title)

        self.system_os = QLabel()
        self.system_kernel = QLabel()
        self.system_arch = QLabel()
        self.system_hostname = QLabel()
        self.system_shell = QLabel()
        self.system_desktop = QLabel()
        self.system_window_manager = QLabel()
        self.system_uptime = QLabel()
        self.system_boot = QLabel()

        for label in [
            self.system_os,
            self.system_kernel,
            self.system_arch,
            self.system_hostname,
            self.system_shell,
            self.system_desktop,
            self.system_window_manager,
            self.system_uptime,
            self.system_boot,
        ]:
            label.setObjectName("infoRow")
            label.setWordWrap(True)
            linux_layout.addWidget(label)

        power_frame = QFrame()
        power_frame.setObjectName("info")
        power_layout = QVBoxLayout(power_frame)

        power_title = QLabel("POWER")
        power_title.setObjectName("sectionTitle")
        power_layout.addWidget(power_title)

        self.system_battery = QLabel()
        self.system_power_status = QLabel()
        self.system_battery_time = QLabel()
        self.system_battery_health = QLabel()

        for label in [
            self.system_battery,
            self.system_power_status,
            self.system_battery_time,
            self.system_battery_health,
        ]:
            label.setObjectName("infoRow")
            label.setWordWrap(True)
            power_layout.addWidget(label)

        sensor_frame = QFrame()
        sensor_frame.setObjectName("info")
        sensor_layout = QVBoxLayout(sensor_frame)

        sensor_title = QLabel("HARDWARE SENSORS")
        sensor_title.setObjectName("sectionTitle")
        sensor_layout.addWidget(sensor_title)

        self.system_temperatures = QLabel()
        self.system_fans = QLabel()
        self.system_sensors_note = QLabel()
        self.system_sensors_note.setObjectName("subtitle")

        for label in [
            self.system_temperatures,
            self.system_fans,
            self.system_sensors_note,
        ]:
            label.setObjectName("infoRow")
            label.setWordWrap(True)
            sensor_layout.addWidget(label)

        details_grid.addWidget(linux_frame, 0, 0)
        details_grid.addWidget(power_frame, 0, 1)
        details_grid.addWidget(sensor_frame, 0, 2)

        content_layout.addLayout(details_grid)

        # Legacy labels retained for compatibility with the existing
        # dashboard/update code.
        self.system_info_labels = {}

        scroll.setWidget(content)
        outer_layout.addWidget(scroll, 1)

        return page

    # =========================================================
    # PROCESSES 2.0
    # =========================================================

    def create_processes_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(35, 30, 35, 30)
        layout.setSpacing(12)

        header = QLabel("PROCESSES")
        header.setObjectName("header")

        subtitle = QLabel(
            "PROCESS MANAGER • LIVE SYSTEM ACTIVITY"
        )
        subtitle.setObjectName("subtitle")

        layout.addWidget(header)
        layout.addWidget(subtitle)

        toolbar = QHBoxLayout()
        toolbar.setSpacing(8)

        self.process_search = QLineEdit()
        self.process_search.setPlaceholderText(
            "Search by PID or process name..."
        )
        self.process_search.textChanged.connect(
            self.filter_processes
        )

        self.process_sort = QComboBox()
        self.process_sort.addItems([
            "CPU ↓",
            "RAM ↓",
            "PID ↑",
            "NAME ↑",
        ])
        self.process_sort.currentIndexChanged.connect(
            self.update_processes
        )

        refresh_button = QPushButton("↻  REFRESH")
        refresh_button.setObjectName("toolButton")
        refresh_button.clicked.connect(self.update_processes)

        toolbar.addWidget(self.process_search, 1)
        toolbar.addWidget(self.process_sort)
        toolbar.addWidget(refresh_button)

        layout.addLayout(toolbar)

        self.process_table = QTableWidget()
        self.process_table.setColumnCount(8)
        self.process_table.setHorizontalHeaderLabels([
            "PID",
            "NAME",
            "USER",
            "STATUS",
            "CPU %",
            "RAM",
            "THREADS",
            "NICE",
        ])
        self.process_table.setEditTriggers(
            QTableWidget.NoEditTriggers
        )
        self.process_table.setSelectionBehavior(
            QTableWidget.SelectRows
        )
        self.process_table.setSelectionMode(
            QTableWidget.SingleSelection
        )
        self.process_table.setAlternatingRowColors(True)
        self.process_table.verticalHeader().setVisible(False)

        layout.addWidget(self.process_table, 1)

        actions = QHBoxLayout()
        actions.setSpacing(8)

        details_button = QPushButton("▣  DETAILS")
        details_button.setObjectName("toolButton")
        details_button.clicked.connect(
            self.show_process_details
        )

        terminate_button = QPushButton("⏹  TERMINATE")
        terminate_button.setObjectName("toolButton")
        terminate_button.clicked.connect(
            lambda: self.control_process("terminate")
        )

        kill_button = QPushButton("✕  KILL")
        kill_button.setObjectName("toolButton")
        kill_button.clicked.connect(
            lambda: self.control_process("kill")
        )

        stop_button = QPushButton("Ⅱ  STOP")
        stop_button.setObjectName("toolButton")
        stop_button.clicked.connect(
            lambda: self.control_process("stop")
        )

        resume_button = QPushButton("▶  RESUME")
        resume_button.setObjectName("toolButton")
        resume_button.clicked.connect(
            lambda: self.control_process("resume")
        )

        actions.addWidget(details_button)
        actions.addStretch()
        actions.addWidget(resume_button)
        actions.addWidget(stop_button)
        actions.addWidget(terminate_button)
        actions.addWidget(kill_button)

        layout.addLayout(actions)

        self.process_status = QLabel(
            "Monitoring running processes..."
        )
        self.process_status.setObjectName("subtitle")
        layout.addWidget(self.process_status)

        return page

    def update_processes(self):
        """Refresh the Processes 2.0 table with live process information."""
        if not hasattr(self, "process_table"):
            return

        query = self.process_search.text().strip().lower() if hasattr(self, "process_search") else ""
        sort_mode = self.process_sort.currentIndex() if hasattr(self, "process_sort") else 0

        processes = []

        for process in psutil.process_iter(
            ["pid", "name", "username", "status", "cpu_percent",
             "memory_info", "num_threads", "nice"]
        ):
            try:
                info = process.info
                name = info.get("name") or "Unknown"
                pid = info.get("pid")

                if query and query not in name.lower() and query not in str(pid):
                    continue

                memory_info = info.get("memory_info")
                ram_mb = (
                    memory_info.rss / (1024 ** 2)
                    if memory_info else 0.0
                )

                processes.append({
                    "pid": pid,
                    "name": name,
                    "user": info.get("username") or "-",
                    "status": info.get("status") or "-",
                    "cpu": float(info.get("cpu_percent") or 0.0),
                    "ram": ram_mb,
                    "threads": int(info.get("num_threads") or 0),
                    "nice": info.get("nice"),
                })

            except (
                psutil.NoSuchProcess,
                psutil.AccessDenied,
                psutil.ZombieProcess,
            ):
                continue

        if sort_mode == 0:
            key = lambda x: x["cpu"]
            reverse = True
        elif sort_mode == 1:
            key = lambda x: x["ram"]
            reverse = True
        elif sort_mode == 2:
            key = lambda x: x["pid"]
            reverse = False
        else:
            key = lambda x: x["name"].lower()
            reverse = False

        processes.sort(key=key, reverse=reverse)

        self.process_table.setUpdatesEnabled(False)
        self.process_table.setRowCount(len(processes))

        for row, item in enumerate(processes):
            values = [
                str(item["pid"]),
                item["name"],
                item["user"],
                item["status"],
                f'{item["cpu"]:.1f}%',
                f'{item["ram"]:.1f} MB',
                str(item["threads"]),
                str(item["nice"]) if item["nice"] is not None else "-",
            ]

            for column, value in enumerate(values):
                cell = QTableWidgetItem(value)
                if column in (0, 4, 5, 6, 7):
                    cell.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                self.process_table.setItem(row, column, cell)

        self.process_table.setUpdatesEnabled(True)

        if hasattr(self, "process_status"):
            self.process_status.setText(
                f"{len(processes)} processes shown • updated live"
            )

        # Keep the selected PID if possible.
        if hasattr(self, "_selected_pid") and self._selected_pid is not None:
            for row in range(self.process_table.rowCount()):
                item = self.process_table.item(row, 0)
                if item and item.text() == str(self._selected_pid):
                    self.process_table.selectRow(row)
                    break

    def filter_processes(self):

        self.update_processes()

    def get_selected_process(self):
        selected = self.process_table.selectedItems()

        if not selected:
            return None

        pid_item = self.process_table.item(
            selected[0].row(),
            0
        )

        if not pid_item:
            return None

        try:
            return int(pid_item.text())
        except ValueError:
            return None

    def control_process(self, action):
        pid = self.get_selected_process()

        if pid is None:
            QMessageBox.warning(
                self,
                "No Process Selected",
                "Select a process first."
            )
            return

        try:
            process = psutil.Process(pid)
            name = process.name()

            if action == "terminate":
                reply = QMessageBox.question(
                    self,
                    "Terminate Process",
                    f"Terminate '{name}' (PID {pid})?",
                    QMessageBox.Yes | QMessageBox.No,
                    QMessageBox.No,
                )

                if reply != QMessageBox.Yes:
                    return

                process.terminate()

            elif action == "kill":
                reply = QMessageBox.warning(
                    self,
                    "Kill Process",
                    f"Force kill '{name}' (PID {pid})?\n\n"
                    "This may cause data loss.",
                    QMessageBox.Yes | QMessageBox.No,
                    QMessageBox.No,
                )

                if reply != QMessageBox.Yes:
                    return

                process.kill()

            elif action == "stop":
                process.suspend()

            elif action == "resume":
                process.resume()

            self.process_status.setText(
                f"{action.upper()} sent to {name} (PID {pid})"
            )

            QTimer.singleShot(
                500,
                self.update_processes
            )

        except psutil.NoSuchProcess:
            QMessageBox.warning(
                self,
                "Process Gone",
                f"Process {pid} no longer exists."
            )

        except psutil.AccessDenied:
            QMessageBox.critical(
                self,
                "Permission Denied",
                f"Sysora does not have permission to control PID {pid}."
            )

        except psutil.ZombieProcess:
            QMessageBox.warning(
                self,
                "Zombie Process",
                f"PID {pid} is a zombie process."
            )

        except psutil.Error as error:
            QMessageBox.critical(
                self,
                "Process Error",
                str(error)
            )

    def show_process_details(self):
        pid = self.get_selected_process()

        if pid is None:
            QMessageBox.warning(
                self,
                "No Process Selected",
                "Select a process first."
            )
            return

        try:
            process = psutil.Process(pid)

            with process.oneshot():
                name = process.name()
                status = process.status()

                try:
                    username = process.username()
                except psutil.AccessDenied:
                    username = "Access denied"

                parent = process.ppid()
                create_time = process.create_time()
                cpu = process.cpu_percent()
                memory = process.memory_info()
                memory_mb = memory.rss / (1024 ** 2)
                threads = process.num_threads()
                nice = process.nice()

                try:
                    exe = process.exe()
                except psutil.AccessDenied:
                    exe = "Access denied"

                try:
                    cwd = process.cwd()
                except psutil.AccessDenied:
                    cwd = "Access denied"

                try:
                    cmdline = " ".join(process.cmdline())
                except psutil.AccessDenied:
                    cmdline = "Access denied"

        except psutil.NoSuchProcess:
            QMessageBox.warning(
                self,
                "Process Gone",
                f"Process {pid} no longer exists."
            )
            return

        except psutil.AccessDenied:
            QMessageBox.warning(
                self,
                "Access Denied",
                f"Sysora cannot inspect PID {pid}."
            )
            return

        dialog = QDialog(self)
        dialog.setWindowTitle(
            f"Process Inspector • {name}"
        )
        dialog.resize(700, 500)

        layout = QVBoxLayout(dialog)

        title = QLabel(
            f"{name}  •  PID {pid}"
        )
        title.setObjectName("header")
        layout.addWidget(title)

        info = QFrame()
        info.setObjectName("info")

        grid = QGridLayout(info)

        details = [
            ("PID", str(pid)),
            ("Name", name),
            ("Status", status),
            ("User", username),
            ("Parent PID", str(parent)),
            ("CPU", f"{cpu:.1f}%"),
            ("RAM", f"{memory_mb:.1f} MB"),
            ("Threads", str(threads)),
            ("Nice", str(nice)),
            (
                "Started",
                time.strftime(
                    "%Y-%m-%d %H:%M:%S",
                    time.localtime(create_time)
                ),
            ),
            ("Executable", exe or "Unavailable"),
            ("Working Directory", cwd or "Unavailable"),
        ]

        for row, (key, value) in enumerate(details):
            key_label = QLabel(key)
            key_label.setObjectName("cardTitle")

            value_label = QLabel(value)
            value_label.setWordWrap(True)
            value_label.setTextInteractionFlags(
                Qt.TextSelectableByMouse
            )

            grid.addWidget(key_label, row, 0)
            grid.addWidget(value_label, row, 1)

        layout.addWidget(info)

        command_title = QLabel("COMMAND LINE")
        command_title.setObjectName("sectionTitle")
        layout.addWidget(command_title)

        command = QPlainTextEdit()
        command.setReadOnly(True)
        command.setPlainText(
            cmdline or "Unavailable"
        )
        command.setMaximumHeight(100)

        layout.addWidget(command)

        buttons = QDialogButtonBox(
            QDialogButtonBox.Close
        )
        buttons.rejected.connect(dialog.reject)

        layout.addWidget(buttons)

        dialog.exec()

    def create_network_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(35, 30, 35, 30)
        layout.setSpacing(15)

        header = QLabel("NETWORK")
        header.setObjectName("header")

        subtitle = QLabel("NETWORK STATUS & INTERFACES")
        subtitle.setObjectName("subtitle")

        layout.addWidget(header)
        layout.addWidget(subtitle)

        info = QFrame()
        info.setObjectName("info")
        info_layout = QVBoxLayout(info)

        self.network_status = QLabel("● STATUS          Checking...")
        self.network_status.setObjectName("status")

        self.network_hostname = QLabel("Hostname        --")
        self.network_ip = QLabel("Local IP        --")

        info_layout.addWidget(self.network_status)
        info_layout.addWidget(self.network_hostname)
        info_layout.addWidget(self.network_ip)

        layout.addWidget(info)

        interfaces_title = QLabel("NETWORK INTERFACES")
        interfaces_title.setObjectName("sectionTitle")
        layout.addWidget(interfaces_title)

        self.interface_table = QTableWidget()
        self.interface_table.setColumnCount(3)
        self.interface_table.setHorizontalHeaderLabels(
            ["INTERFACE", "STATUS", "IPv4 ADDRESS"]
        )
        self.interface_table.setEditTriggers(
            QTableWidget.NoEditTriggers
        )
        self.interface_table.setSelectionBehavior(
            QTableWidget.SelectRows
        )
        self.interface_table.setAlternatingRowColors(True)
        self.interface_table.verticalHeader().setVisible(False)

        layout.addWidget(self.interface_table)
        layout.addStretch()

        return page

    def create_packages_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(35, 30, 35, 30)
        layout.setSpacing(12)

        header = QLabel("PACKAGES")
        header.setObjectName("header")

        subtitle = QLabel("ARCH LINUX PACKAGE CENTER • PACMAN")
        subtitle.setObjectName("subtitle")

        layout.addWidget(header)
        layout.addWidget(subtitle)

        stats = QHBoxLayout()
        stats.setSpacing(12)

        self.package_installed = QLabel("--")
        self.package_explicit = QLabel("--")
        self.package_orphans = QLabel("--")

        for title, value in [
            ("INSTALLED", self.package_installed),
            ("EXPLICIT", self.package_explicit),
            ("ORPHANS", self.package_orphans),
        ]:
            card = QFrame()
            card.setObjectName("card")
            card_layout = QVBoxLayout(card)

            title_label = QLabel(title)
            title_label.setObjectName("cardTitle")
            value.setObjectName("cardValue")

            card_layout.addWidget(title_label)
            card_layout.addWidget(value)

            stats.addWidget(card)

        layout.addLayout(stats)

        search_layout = QHBoxLayout()
        search_layout.setSpacing(8)

        self.package_search = QLineEdit()
        self.package_search.setPlaceholderText(
            "Search installed packages..."
        )
        self.package_search.returnPressed.connect(
            self.search_packages
        )

        search_button = QPushButton("SEARCH")
        search_button.setObjectName("toolButton")
        search_button.clicked.connect(self.search_packages)

        refresh_button = QPushButton("↻")
        refresh_button.setObjectName("toolButton")
        refresh_button.setToolTip("Refresh package list")
        refresh_button.clicked.connect(self.load_packages)

        search_layout.addWidget(self.package_search)
        search_layout.addWidget(search_button)
        search_layout.addWidget(refresh_button)

        layout.addLayout(search_layout)

        self.package_table = QTableWidget()
        self.package_table.setColumnCount(2)
        self.package_table.setHorizontalHeaderLabels(
            ["PACKAGE", "VERSION"]
        )
        self.package_table.setEditTriggers(
            QTableWidget.NoEditTriggers
        )
        self.package_table.setSelectionBehavior(
            QTableWidget.SelectRows
        )
        self.package_table.setAlternatingRowColors(True)
        self.package_table.verticalHeader().setVisible(False)

        layout.addWidget(self.package_table)

        self.package_status = QLabel("Loading packages...")
        self.package_status.setObjectName("subtitle")
        layout.addWidget(self.package_status)

        return page

    def run_command(self, command):
        try:
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                timeout=15,
                check=False,
            )
            return result.returncode, result.stdout, result.stderr
        except (OSError, subprocess.SubprocessError) as error:
            return -1, "", str(error)

    def load_packages(self):
        if not hasattr(self, "package_table"):
            return

        code, stdout, stderr = self.run_command(
            ["pacman", "-Q"]
        )

        if code != 0:
            self.package_status.setText(
                f"pacman error: {stderr.strip() or 'Unable to read packages'}"
            )
            return

        packages = []

        for line in stdout.splitlines():
            parts = line.rsplit(" ", 1)

            if len(parts) == 2:
                packages.append((parts[0], parts[1]))

        packages.sort(key=lambda item: item[0].lower())

        self.package_installed.setText(str(len(packages)))

        explicit_code, explicit_out, _ = self.run_command(
            ["pacman", "-Qe"]
        )

        explicit_count = (
            len(explicit_out.splitlines())
            if explicit_code == 0
            else 0
        )

        self.package_explicit.setText(str(explicit_count))

        orphan_code, orphan_out, _ = self.run_command(
            ["pacman", "-Qdtq"]
        )

        orphan_count = (
            len([
                line
                for line in orphan_out.splitlines()
                if line.strip()
            ])
            if orphan_code == 0
            else 0
        )

        self.package_orphans.setText(str(orphan_count))

        self.display_packages(packages)

        self.package_status.setText(
            f"{len(packages)} installed packages"
        )

    def display_packages(self, packages):
        self.package_table.setRowCount(len(packages))

        for row, (name, version) in enumerate(packages):
            self.package_table.setItem(
                row, 0, QTableWidgetItem(name)
            )
            self.package_table.setItem(
                row, 1, QTableWidgetItem(version)
            )

        self.package_table.resizeColumnsToContents()

    def search_packages(self):
        query = self.package_search.text().strip().lower()

        if not query:
            self.load_packages()
            return

        code, stdout, stderr = self.run_command(
            ["pacman", "-Q"]
        )

        if code != 0:
            self.package_status.setText(
                f"pacman error: {stderr.strip() or 'Search failed'}"
            )
            return

        matches = []

        for line in stdout.splitlines():
            parts = line.rsplit(" ", 1)

            if len(parts) == 2 and query in parts[0].lower():
                matches.append((parts[0], parts[1]))

        matches.sort(key=lambda item: item[0].lower())
        self.display_packages(matches)

        self.package_status.setText(
            f"{len(matches)} matching packages"
        )

    def create_developer_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(35, 30, 35, 30)
        layout.setSpacing(15)

        header = QLabel("DEVELOPER")
        header.setObjectName("header")

        subtitle = QLabel(
            "DEVELOPMENT ENVIRONMENT & GIT STATUS"
        )
        subtitle.setObjectName("subtitle")

        layout.addWidget(header)
        layout.addWidget(subtitle)

        env = QFrame()
        env.setObjectName("info")
        env_layout = QVBoxLayout(env)

        title = QLabel("DEVELOPMENT ENVIRONMENT")
        title.setObjectName("sectionTitle")
        env_layout.addWidget(title)

        self.dev_python = QLabel()
        self.dev_pip = QLabel()
        self.dev_venv = QLabel()
        self.dev_git = QLabel()

        env_layout.addWidget(self.dev_python)
        env_layout.addWidget(self.dev_pip)
        env_layout.addWidget(self.dev_venv)
        env_layout.addWidget(self.dev_git)

        layout.addWidget(env)

        git = QFrame()
        git.setObjectName("info")
        git_layout = QVBoxLayout(git)

        git_title = QLabel("GIT REPOSITORY")
        git_title.setObjectName("sectionTitle")
        git_layout.addWidget(git_title)

        self.dev_repo = QLabel()
        self.dev_branch = QLabel()
        self.dev_changes = QLabel()
        self.dev_repo_path = QLabel()

        git_layout.addWidget(self.dev_repo)
        git_layout.addWidget(self.dev_branch)
        git_layout.addWidget(self.dev_changes)
        git_layout.addWidget(self.dev_repo_path)

        layout.addWidget(git)

        refresh = QPushButton("↻  REFRESH DEVELOPER STATUS")
        refresh.setObjectName("toolButton")
        refresh.clicked.connect(self.update_developer)
        layout.addWidget(refresh)

        layout.addStretch()

        return page

    def developer_command(self, command):
        try:
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                timeout=5,
                check=False,
            )
            return result.returncode, result.stdout.strip()
        except (OSError, subprocess.SubprocessError):
            return -1, ""

    def update_developer(self):
        python_version = platform.python_version()
        self.dev_python.setText(
            f"Python          {python_version}"
        )

        pip_code, pip_out = self.developer_command(
            [sys.executable, "-m", "pip", "--version"]
        )

        self.dev_pip.setText(
            f"pip             {'✓ ' + pip_out if pip_code == 0 else '✗ Not available'}"
        )

        venv_active = (
            sys.prefix != getattr(
                sys,
                "base_prefix",
                sys.prefix
            )
        )

        self.dev_venv.setText(
            f"Virtual Env     {'✓ Active' if venv_active else '✗ Not active'}"
        )

        git_code, git_version = self.developer_command(
            ["git", "--version"]
        )

        self.dev_git.setText(
            f"Git             {'✓ ' + git_version if git_code == 0 else '✗ Not installed'}"
        )

        repo_code, repo_root = self.developer_command(
            ["git", "rev-parse", "--show-toplevel"]
        )

        if repo_code != 0:
            self.dev_repo.setText(
                "Repository      ✗ Not a Git repository"
            )
            self.dev_branch.setText("Branch          —")
            self.dev_changes.setText("Changes         —")
            self.dev_repo_path.setText("Path            —")
            return

        self.dev_repo.setText(
            "Repository      ✓ Git repository"
        )
        self.dev_repo_path.setText(
            f"Path            {repo_root}"
        )

        branch_code, branch = self.developer_command(
            ["git", "branch", "--show-current"]
        )

        self.dev_branch.setText(
            f"Branch          {branch if branch_code == 0 and branch else 'detached HEAD'}"
        )

        status_code, status = self.developer_command(
            ["git", "status", "--short"]
        )

        if status_code == 0:
            changes = len(status.splitlines()) if status else 0
            self.dev_changes.setText(
                f"Changes         {changes} modified/untracked"
            )
        else:
            self.dev_changes.setText(
                "Changes         Unable to read"
            )

    def create_terminal_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(35, 30, 35, 30)
        layout.setSpacing(12)

        header = QLabel("TERMINAL")
        header.setObjectName("header")

        subtitle = QLabel(
            "REAL LINUX SHELL • USER PRIVILEGES"
        )
        subtitle.setObjectName("subtitle")

        layout.addWidget(header)
        layout.addWidget(subtitle)

        self.terminal_output = QPlainTextEdit()
        self.terminal_output.setObjectName("terminalOutput")
        self.terminal_output.setReadOnly(True)
        self.terminal_output.setLineWrapMode(
            QPlainTextEdit.NoWrap
        )
        self.terminal_output.setUndoRedoEnabled(False)
        self.terminal_output.setMaximumBlockCount(5000)

        layout.addWidget(self.terminal_output, 1)

        command_layout = QHBoxLayout()
        command_layout.setSpacing(8)

        self.terminal_prompt = QLabel("$")
        self.terminal_prompt.setObjectName(
            "terminalPrompt"
        )

        self.terminal_input = TerminalInput(self)
        self.terminal_input.setPlaceholderText(
            "Enter a Linux command..."
        )
        self.terminal_input.returnPressed.connect(
            self.execute_terminal_command
        )

        clear_button = QPushButton("CLEAR")
        clear_button.setObjectName("toolButton")
        clear_button.clicked.connect(self.clear_terminal)

        command_layout.addWidget(self.terminal_prompt)
        command_layout.addWidget(
            self.terminal_input,
            1
        )
        command_layout.addWidget(clear_button)

        layout.addLayout(command_layout)

        self.terminal_cwd = QLabel()
        self.terminal_cwd.setObjectName("subtitle")
        layout.addWidget(self.terminal_cwd)

        self.terminal_history = []
        self.terminal_history_index = 0

        self.update_terminal_prompt()
        self.add_terminal_line("Sysora Terminal ready.")
        self.add_terminal_line(
            "Type 'help' for built-in commands."
        )

        return page

    def update_terminal_prompt(self):
        cwd = Path.cwd()
        home = Path.home()

        try:
            display_cwd = "~" + str(cwd.relative_to(home))

            if display_cwd == "~":
                display_cwd = "~"

        except ValueError:
            display_cwd = str(cwd)

        self.terminal_prompt.setText(
            f"{self.get_username()}@{socket.gethostname()}:"
            f"{display_cwd}$"
        )

        self.terminal_cwd.setText(
            f"Working directory: {cwd}"
        )

    @staticmethod
    def get_username():
        try:
            return Path.home().name
        except Exception:
            return "user"

    def add_terminal_line(self, text):
        self.terminal_output.appendPlainText(text)

        scrollbar = (
            self.terminal_output.verticalScrollBar()
        )

        scrollbar.setValue(
            scrollbar.maximum()
        )

    def terminal_history_up(self):
        if not self.terminal_history:
            return

        self.terminal_history_index = max(
            0,
            self.terminal_history_index - 1
        )

        self.terminal_input.setText(
            self.terminal_history[
                self.terminal_history_index
            ]
        )

        self.terminal_input.setCursorPosition(
            len(self.terminal_input.text())
        )

    def terminal_history_down(self):
        if not self.terminal_history:
            return

        self.terminal_history_index += 1

        if (
            self.terminal_history_index
            >= len(self.terminal_history)
        ):
            self.terminal_history_index = (
                len(self.terminal_history)
            )
            self.terminal_input.clear()
            return

        self.terminal_input.setText(
            self.terminal_history[
                self.terminal_history_index
            ]
        )

        self.terminal_input.setCursorPosition(
            len(self.terminal_input.text())
        )

    def execute_terminal_command(self):
        command = self.terminal_input.text().strip()

        if not command:
            return

        self.terminal_history.append(command)
        self.terminal_history_index = (
            len(self.terminal_history)
        )

        self.add_terminal_line(
            f"{self.get_username()}@{socket.gethostname()}:"
            f"{self._terminal_display_cwd()}$ {command}"
        )

        self.terminal_input.clear()

        if command == "clear":
            self.clear_terminal()
            return

        if command == "help":
            self.add_terminal_line(
                "Built-ins: cd, clear, exit"
            )
            self.add_terminal_line(
                "Other commands are executed by /bin/bash."
            )
            return

        if command == "exit":
            self.add_terminal_line(
                "Sysora Terminal cannot close the application. "
                "Use the window close button."
            )
            return

        if (
            command == "cd"
            or command.startswith("cd ")
        ):
            self.execute_cd(command)
            return

        try:
            result = subprocess.run(
                ["/bin/bash", "-lc", command],
                cwd=str(Path.cwd()),
                capture_output=True,
                text=True,
                timeout=30,
                env=None,
            )

            stdout = result.stdout
            stderr = result.stderr

            if stdout:
                self.add_terminal_line(
                    stdout.rstrip("\n")
                )

            if stderr:
                self.add_terminal_line(
                    stderr.rstrip("\n")
                )

            if result.returncode != 0:
                self.add_terminal_line(
                    f"[exit code: {result.returncode}]"
                )

        except subprocess.TimeoutExpired:
            self.add_terminal_line(
                "[command timed out after 30 seconds]"
            )

        except Exception as error:
            self.add_terminal_line(
                f"[terminal error] {error}"
            )

        self.update_terminal_prompt()

    def _terminal_display_cwd(self):
        cwd = Path.cwd()
        home = Path.home()

        try:
            relative = cwd.relative_to(home)

            return (
                "~"
                if str(relative) == "."
                else f"~/{relative}"
            )

        except ValueError:
            return str(cwd)

    def execute_cd(self, command):
        parts = command.split(maxsplit=1)

        if len(parts) == 1:
            target = Path.home()

        else:
            raw_target = parts[1].strip()

            if raw_target.startswith("-"):
                self.add_terminal_line(
                    "Sysora Terminal: 'cd -' is not supported yet."
                )
                return

            target = Path(
                raw_target
            ).expanduser()

        if not target.is_absolute():
            target = Path.cwd() / target

        target = target.resolve()

        if not target.is_dir():
            self.add_terminal_line(
                f"bash: cd: {target}: No such file or directory"
            )
            return

        try:
            os.chdir(target)
            self.update_terminal_prompt()

        except OSError as error:
            self.add_terminal_line(
                f"bash: cd: {error}"
            )

    def clear_terminal(self):
        self.terminal_output.clear()
        self.update_terminal_prompt()

    def create_files_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(35, 30, 35, 30)
        layout.setSpacing(12)

        header = QLabel("FILES")
        header.setObjectName("header")

        subtitle = QLabel("FILE SYSTEM BROWSER")
        subtitle.setObjectName("subtitle")

        layout.addWidget(header)
        layout.addWidget(subtitle)

        toolbar = QHBoxLayout()
        toolbar.setSpacing(8)

        back_button = QPushButton("←")
        back_button.setObjectName("toolButton")
        back_button.setToolTip(
            "Go to parent directory"
        )
        back_button.clicked.connect(self.go_parent)

        home_button = QPushButton("⌂")
        home_button.setObjectName("toolButton")
        home_button.setToolTip("Home directory")
        home_button.clicked.connect(self.go_home)

        refresh_button = QPushButton("↻")
        refresh_button.setObjectName("toolButton")
        refresh_button.setToolTip("Refresh")
        refresh_button.clicked.connect(
            self.load_files
        )

        self.path_edit = QLineEdit()
        self.path_edit.setPlaceholderText(
            "/path/to/directory"
        )
        self.path_edit.returnPressed.connect(
            self.go_to_path
        )

        toolbar.addWidget(back_button)
        toolbar.addWidget(home_button)
        toolbar.addWidget(refresh_button)
        toolbar.addWidget(self.path_edit)

        layout.addLayout(toolbar)

        self.file_table = QTableWidget()
        self.file_table.setColumnCount(4)
        self.file_table.setHorizontalHeaderLabels(
            ["NAME", "TYPE", "SIZE", "MODIFIED"]
        )
        self.file_table.setEditTriggers(
            QTableWidget.NoEditTriggers
        )
        self.file_table.setSelectionBehavior(
            QTableWidget.SelectRows
        )
        self.file_table.setAlternatingRowColors(True)
        self.file_table.verticalHeader().setVisible(False)
        self.file_table.cellDoubleClicked.connect(
            self.open_file_item
        )

        layout.addWidget(self.file_table)

        self.file_status = QLabel()
        self.file_status.setObjectName("subtitle")
        layout.addWidget(self.file_status)

        return page

    def load_files(self):
        if not hasattr(self, "file_table"):
            return

        try:
            entries = list(
                self.current_path.iterdir()
            )
            entries.sort(
                key=lambda p: (
                    not p.is_dir(),
                    p.name.lower()
                )
            )

        except (PermissionError, OSError) as error:
            self.file_table.setRowCount(0)
            self.file_status.setText(
                f"Cannot read directory: {error}"
            )
            return

        self.path_edit.setText(
            str(self.current_path)
        )

        self.file_table.setRowCount(
            len(entries)
        )

        for row, item in enumerate(entries):
            if item.is_dir():
                item_type = "DIRECTORY"
                size_text = "—"

            else:
                item_type = "FILE"

                try:
                    size = item.stat().st_size
                    size_text = self.format_size(size)

                except OSError:
                    size_text = "?"

            try:
                modified = time.strftime(
                    "%Y-%m-%d %H:%M",
                    time.localtime(
                        item.stat().st_mtime
                    )
                )

            except OSError:
                modified = "?"

            name_item = QTableWidgetItem(
                (
                    "📁 "
                    if item.is_dir()
                    else "📄 "
                )
                + item.name
            )

            name_item.setData(
                Qt.UserRole,
                str(item)
            )

            self.file_table.setItem(
                row,
                0,
                name_item
            )

            self.file_table.setItem(
                row,
                1,
                QTableWidgetItem(item_type)
            )

            self.file_table.setItem(
                row,
                2,
                QTableWidgetItem(size_text)
            )

            self.file_table.setItem(
                row,
                3,
                QTableWidgetItem(modified)
            )

        self.file_table.resizeColumnsToContents()

        self.file_status.setText(
            f"{len(entries)} items • "
            f"{self.current_path}"
        )

    def open_file_item(self, row, column):
        item = self.file_table.item(row, 0)

        if not item:
            return

        path = Path(
            item.data(Qt.UserRole)
        )

        if path.is_dir():
            self.current_path = path
            self.load_files()

    def go_parent(self):
        parent = self.current_path.parent

        if parent != self.current_path:
            self.current_path = parent
            self.load_files()

    def go_home(self):
        self.current_path = Path.home()
        self.load_files()

    def go_to_path(self):
        requested = Path(
            self.path_edit.text()
        ).expanduser()

        if requested.is_dir():
            self.current_path = requested.resolve()
            self.load_files()

        else:
            self.file_status.setText(
                "Directory not found."
            )

    @staticmethod
    def format_size(size):
        units = [
            "B",
            "KB",
            "MB",
            "GB",
            "TB"
        ]

        value = float(size)

        for unit in units:
            if (
                value < 1024
                or unit == units[-1]
            ):
                return f"{value:.1f} {unit}"

            value /= 1024

    @staticmethod
    def _read_os_release():
        data = {}
        try:
            with open("/etc/os-release", "r", encoding="utf-8") as file:
                for line in file:
                    if "=" not in line:
                        continue
                    key, value = line.rstrip().split("=", 1)
                    data[key] = value.strip('"')
        except OSError:
            pass

        return data

    @staticmethod
    def _format_bytes(value):
        if value is None:
            return "—"

        value = float(value)
        units = ["B", "KB", "MB", "GB", "TB", "PB"]

        for unit in units:
            if value < 1024 or unit == units[-1]:
                return f"{value:.1f} {unit}"
            value /= 1024

        return "—"

    @staticmethod
    def _format_uptime(seconds):
        seconds = max(0, int(seconds))
        days, remainder = divmod(seconds, 86400)
        hours, remainder = divmod(remainder, 3600)
        minutes, _ = divmod(remainder, 60)

        if days:
            return f"{days}d {hours}h {minutes}m"
        if hours:
            return f"{hours}h {minutes}m"
        return f"{minutes}m"

    @staticmethod
    def _environment_value(*names, fallback="Unknown"):
        for name in names:
            value = os.environ.get(name)
            if value:
                return value
        return fallback

    def _get_cpu_frequency(self):
        try:
            frequencies = psutil.cpu_freq(percpu=False)
            if frequencies:
                current = frequencies.current
                minimum = frequencies.min
                maximum = frequencies.max

                if current:
                    current_text = f"{current / 1000:.2f} GHz"
                else:
                    current_text = "Unknown"

                if maximum:
                    maximum_text = f"{maximum / 1000:.2f} GHz"
                else:
                    maximum_text = "Unknown"

                if minimum:
                    minimum_text = f"{minimum / 1000:.2f} GHz"
                else:
                    minimum_text = "Unknown"

                return (
                    f"{current_text} current • "
                    f"{minimum_text} min • {maximum_text} max"
                )
        except (AttributeError, OSError):
            pass

        return "Unavailable"

    def _get_cpu_name(self):
        name = platform.processor()

        if name:
            return name

        try:
            with open("/proc/cpuinfo", "r", encoding="utf-8") as file:
                for line in file:
                    if line.lower().startswith("model name"):
                        return line.split(":", 1)[1].strip()
        except OSError:
            pass

        return "Unknown CPU"

    def _get_sensor_data(self):
        temperatures = []
        fans = []

        try:
            sensor_groups = psutil.sensors_temperatures(
                fahrenheit=False
            )

            for group_name, entries in sensor_groups.items():
                for entry in entries:
                    if entry.current is None:
                        continue

                    label = entry.label or group_name
                    temperatures.append(
                        f"{label}: {entry.current:.1f} °C"
                    )
        except (AttributeError, OSError):
            pass

        try:
            fan_groups = psutil.sensors_fans()

            for group_name, entries in fan_groups.items():
                for entry in entries:
                    if entry.current is None:
                        continue

                    label = entry.label or group_name
                    fans.append(
                        f"{label}: {entry.current:.0f} RPM"
                    )
        except (AttributeError, OSError):
            pass

        return temperatures, fans

    def _update_storage(self):
        partitions = []
        seen_mounts = set()

        try:
            all_partitions = psutil.disk_partitions(
                all=False
            )
        except OSError:
            all_partitions = []

        for partition in all_partitions:
            mount = partition.mountpoint

            if mount in seen_mounts:
                continue

            seen_mounts.add(mount)

            try:
                usage = psutil.disk_usage(mount)
            except (PermissionError, OSError):
                continue

            partitions.append(
                (
                    mount,
                    partition.fstype or "Unknown",
                    usage.total,
                    usage.used,
                    usage.free,
                    usage.percent,
                )
            )

        # Always keep the root filesystem visible.
        if "/" not in seen_mounts:
            try:
                usage = psutil.disk_usage("/")
                partitions.insert(
                    0,
                    (
                        "/",
                        "Unknown",
                        usage.total,
                        usage.used,
                        usage.free,
                        usage.percent,
                    )
                )
            except OSError:
                pass

        partitions.sort(key=lambda item: item[0])

        self.system_storage_table.setRowCount(
            len(partitions)
        )

        total_bytes = 0
        used_bytes = 0

        for row, (
            mount,
            filesystem,
            total,
            used,
            free,
            percent,
        ) in enumerate(partitions):
            total_bytes += total
            used_bytes += used

            values = [
                mount,
                filesystem,
                self._format_bytes(total),
                f"{self._format_bytes(used)} ({percent:.0f}%)",
                self._format_bytes(free),
            ]

            for column, value in enumerate(values):
                self.system_storage_table.setItem(
                    row,
                    column,
                    QTableWidgetItem(value),
                )

        self.system_storage_table.resizeColumnsToContents()

        if partitions:
            self.system_storage_summary.setText(
                f"{self._format_bytes(used_bytes)} used / "
                f"{self._format_bytes(total_bytes)} total"
            )
        else:
            self.system_storage_summary.setText(
                "No mounted filesystems available"
            )

    def _update_power(self):
        battery = None

        try:
            battery = psutil.sensors_battery()
        except (AttributeError, OSError):
            pass

        if battery is None:
            self.system_battery.setText(
                "Battery        Not detected"
            )
            self.system_power_status.setText(
                "Power Status   No battery information"
            )
            self.system_battery_time.setText(
                "Time Remaining —"
            )
            self.system_battery_health.setText(
                "Battery Health —"
            )
            return

        percent = max(0.0, min(100.0, battery.percent))
        plugged = bool(battery.power_plugged)

        self.system_battery.setText(
            f"Battery        {percent:.0f}%"
        )

        if plugged:
            status = "Charging / AC connected"
        else:
            status = "Discharging"

        self.system_power_status.setText(
            f"Power Status   {status}"
        )

        if battery.secsleft not in (
            psutil.POWER_TIME_UNKNOWN,
            psutil.POWER_TIME_UNLIMITED,
        ) and battery.secsleft >= 0:
            self.system_battery_time.setText(
                f"Time Remaining {self._format_uptime(battery.secsleft)}"
            )
        else:
            self.system_battery_time.setText(
                "Time Remaining —"
            )

        self.system_battery_health.setText(
            "Battery Health — (not exposed by psutil)"
        )

    def update_system_info(self):
        cpu_percent = psutil.cpu_percent()
        per_core = psutil.cpu_percent(
            percpu=True
        )

        memory = psutil.virtual_memory()
        swap = psutil.swap_memory()

        try:
            root_disk = psutil.disk_usage("/")
            disk_percent = root_disk.percent
        except OSError:
            root_disk = None
            disk_percent = 0

        kernel = platform.release()
        architecture = platform.machine()
        hostname = socket.gethostname()
        cpu_name = self._get_cpu_name()

        physical_cores = (
            psutil.cpu_count(logical=False)
            or psutil.cpu_count()
            or 0
        )
        logical_cores = (
            psutil.cpu_count(logical=True)
            or physical_cores
            or 0
        )

        boot_time = psutil.boot_time()
        uptime_seconds = int(
            time.time() - boot_time
        )
        uptime = self._format_uptime(
            uptime_seconds
        )

        boot_time_text = time.strftime(
            "%Y-%m-%d %H:%M:%S",
            time.localtime(boot_time)
        )

        os_release = self._read_os_release()
        os_name = os_release.get(
            "PRETTY_NAME",
            "Arch Linux"
        )

        shell = self._environment_value(
            "SHELL",
            fallback="Unknown"
        )
        shell_name = Path(shell).name if shell != "Unknown" else shell

        desktop = self._environment_value(
            "XDG_CURRENT_DESKTOP",
            "XDG_SESSION_DESKTOP",
            fallback="Unknown"
        )

        window_manager = self._environment_value(
            "XDG_SESSION_TYPE",
            fallback="Unknown"
        )

        cpu_frequency = self._get_cpu_frequency()

        # -----------------------------------------------------
        # DASHBOARD
        # -----------------------------------------------------
        self.cpu_value.setText(
            f"{cpu_percent:.0f}%"
        )
        self.ram_value.setText(
            f"{memory.percent:.0f}%"
        )
        self.disk_value.setText(
            f"{disk_percent:.0f}%"
        )

        self.cpu_bar.setValue(
            int(max(0, min(100, cpu_percent)))
        )
        self.ram_bar.setValue(
            int(max(0, min(100, memory.percent)))
        )
        self.disk_bar.setValue(
            int(max(0, min(100, disk_percent)))
        )

        self.activity_label.setText(
            f"CPU {cpu_percent:.0f}%  •  "
            f"RAM {memory.percent:.0f}%  •  "
            f"DISK {disk_percent:.0f}%  •  "
            f"SWAP {swap.percent:.0f}%  •  "
            f"UPTIME {uptime}"
        )

        self.os_label.setText(
            f"OS              {os_name}"
        )
        self.kernel_label.setText(
            f"Kernel          {kernel}"
        )
        self.hostname_label.setText(
            f"Hostname        {hostname}"
        )
        self.uptime_label.setText(
            f"Uptime          {uptime}"
        )

        # -----------------------------------------------------
        # SYSTEM 2.0 RESOURCE CARDS
        # -----------------------------------------------------
        self.system_cpu_value.setText(
            f"{cpu_percent:.0f}%"
        )
        self.system_ram_value.setText(
            f"{memory.percent:.0f}%"
        )
        self.system_disk_value.setText(
            f"{disk_percent:.0f}%"
        )
        self.system_swap_value.setText(
            f"{swap.percent:.0f}%"
        )

        self.system_cpu_bar.setValue(
            int(max(0, min(100, cpu_percent)))
        )
        self.system_ram_bar.setValue(
            int(max(0, min(100, memory.percent)))
        )
        self.system_disk_bar.setValue(
            int(max(0, min(100, disk_percent)))
        )
        self.system_swap_bar.setValue(
            int(max(0, min(100, swap.percent)))
        )

        self.system_cpu_detail.setText(
            f"{physical_cores} physical • "
            f"{logical_cores} logical cores"
        )
        self.system_ram_detail.setText(
            f"{self._format_bytes(memory.used)} used / "
            f"{self._format_bytes(memory.total)}"
        )

        if root_disk:
            self.system_disk_detail.setText(
                f"{self._format_bytes(root_disk.used)} used / "
                f"{self._format_bytes(root_disk.total)}"
            )
        else:
            self.system_disk_detail.setText(
                "Root filesystem unavailable"
            )

        self.system_swap_detail.setText(
            f"{self._format_bytes(swap.used)} used / "
            f"{self._format_bytes(swap.total)}"
        )

        # -----------------------------------------------------
        # CPU
        # -----------------------------------------------------
        self.system_cpu_model.setText(
            f"Model          {cpu_name}"
        )
        self.system_cpu_cores.setText(
            f"Physical Cores  {physical_cores}"
        )
        self.system_cpu_threads.setText(
            f"Logical Threads {logical_cores}"
        )
        self.system_cpu_freq.setText(
            f"Frequency       {cpu_frequency}"
        )

        try:
            load_1, load_5, load_15 = os.getloadavg()
            self.system_cpu_load.setText(
                f"Load Average    "
                f"{load_1:.2f} / {load_5:.2f} / {load_15:.2f}"
            )
        except OSError:
            self.system_cpu_load.setText(
                "Load Average    Unavailable"
            )

        if per_core:
            core_text = " • ".join(
                f"C{i}: {value:.0f}%"
                for i, value in enumerate(per_core)
            )
            self.system_cpu_per_core.setText(
                f"Per Core       {core_text}"
            )
        else:
            self.system_cpu_per_core.setText(
                "Per Core       Unavailable"
            )

        # -----------------------------------------------------
        # MEMORY
        # -----------------------------------------------------
        self.system_ram_total.setText(
            f"Total          {self._format_bytes(memory.total)}"
        )
        self.system_ram_used.setText(
            f"Used           {self._format_bytes(memory.used)} "
            f"({memory.percent:.0f}%)"
        )
        self.system_ram_available.setText(
            f"Available      {self._format_bytes(memory.available)}"
        )
        self.system_ram_cached.setText(
            f"Cached         {self._format_bytes(getattr(memory, 'cached', 0))}"
        )
        self.system_swap_detail_label.setText(
            f"Swap           {self._format_bytes(swap.used)} / "
            f"{self._format_bytes(swap.total)} "
            f"({swap.percent:.0f}%)"
        )

        # -----------------------------------------------------
        # LINUX
        # -----------------------------------------------------
        self.system_os.setText(
            f"Distribution   {os_name}"
        )
        self.system_kernel.setText(
            f"Kernel         {kernel}"
        )
        self.system_arch.setText(
            f"Architecture   {architecture}"
        )
        self.system_hostname.setText(
            f"Hostname       {hostname}"
        )
        self.system_shell.setText(
            f"Shell          {shell_name}"
        )
        self.system_desktop.setText(
            f"Desktop        {desktop}"
        )
        self.system_window_manager.setText(
            f"Session        {window_manager}"
        )
        self.system_uptime.setText(
            f"Uptime         {uptime}"
        )
        self.system_boot.setText(
            f"Boot Time      {boot_time_text}"
        )

        # -----------------------------------------------------
        # STORAGE / POWER / SENSORS
        # -----------------------------------------------------
        self._update_storage()
        self._update_power()

        temperatures, fans = self._get_sensor_data()

        self.system_temperatures.setText(
            "Temperatures   " +
            (" • ".join(temperatures)
             if temperatures else "Not exposed")
        )
        self.system_fans.setText(
            "Fans           " +
            (" • ".join(fans)
             if fans else "Not exposed")
        )

        if temperatures or fans:
            self.system_sensors_note.setText(
                "Sensors supplied by the Linux kernel / psutil."
            )
        else:
            self.system_sensors_note.setText(
                "No temperature/fan sensors are exposed to psutil."
            )

        self.system_live_status.setText(
            f"● LIVE • {time.strftime('%H:%M:%S')}"
        )

        self.update_network()
        self.update_processes()

    def update_network(self):
        hostname = socket.gethostname()

        try:
            local_ip = socket.gethostbyname(
                hostname
            )

        except socket.gaierror:
            local_ip = "Unavailable"

        try:
            socket.create_connection(
                ("1.1.1.1", 53),
                timeout=1
            )
            online = True

        except OSError:
            online = False

        if online:
            self.network_status.setText(
                "● STATUS          ONLINE"
            )
            self.network_status.setObjectName(
                "status"
            )

        else:
            self.network_status.setText(
                "● STATUS          OFFLINE"
            )
            self.network_status.setObjectName(
                "statusOffline"
            )

        self.network_hostname.setText(
            f"Hostname        {hostname}"
        )

        self.network_ip.setText(
            f"Local IP        {local_ip}"
        )

        interfaces = []

        for name, addresses in (
            psutil.net_if_addrs().items()
        ):
            stats = psutil.net_if_stats().get(name)

            is_up = (
                stats.isup
                if stats
                else False
            )

            ipv4 = [
                address.address
                for address in addresses
                if address.family == socket.AF_INET
            ]

            interfaces.append(
                (
                    name,
                    "UP" if is_up else "DOWN",
                    ", ".join(ipv4) or "-"
                )
            )

        self.interface_table.setRowCount(
            len(interfaces)
        )

        for row, (
            name,
            status,
            address
        ) in enumerate(interfaces):

            self.interface_table.setItem(
                row,
                0,
                QTableWidgetItem(name)
            )

            self.interface_table.setItem(
                row,
                1,
                QTableWidgetItem(status)
            )

            self.interface_table.setItem(
                row,
                2,
                QTableWidgetItem(address)
            )

        self.interface_table.resizeColumnsToContents()

    def apply_style(self):
        self.setStyleSheet("""
            QMainWindow {
                background: #0a0a0a;
                border: 1px solid #242424;
            }

            QWidget {
                color: #eeeeee;
                font-family: "JetBrains Mono";
                font-size: 13px;
            }

            QFrame {
                background: #0a0a0a;
            }

            QWidget#dashboardPage,
            QWidget#centralWidget {
                background: #080808;
            }

            #dashboardPage {
                background: #080808;
            }

            #sidebar {
                background: #080808;
                border-right: 1px solid #202020;
            }

            #metricCard {
                background: #101010;
                border: 1px solid #242424;
                border-radius: 10px;
            }

            #metricValue {
                font-size: 30px;
                font-weight: bold;
                margin-top: 2px;
                margin-bottom: 4px;
            }

            #systemPage {
                background: #080808;
            }

            #systemScroll {
                background: #080808;
                border: none;
            }

            #systemMetricCard {
                background: #101010;
                border: 1px solid #242424;
                border-radius: 9px;
            }

            #systemMetricValue {
                font-size: 27px;
                font-weight: bold;
            }

            #systemDetail {
                color: #777777;
                font-size: 10px;
            }

            #systemScroll QScrollBar:vertical {
                background: #090909;
                width: 10px;
            }

            #systemScroll QScrollBar::handle:vertical {
                background: #292929;
                min-height: 30px;
            }


            QProgressBar {
                background: #1a1a1a;
                border: none;
                border-radius: 3px;
            }

            QProgressBar::chunk {
                background: #00d98b;
                border-radius: 3px;
            }

            #infoRow {
                color: #d0d0d0;
                padding: 3px 0;
            }

            #logo {
                font-size: 32px;
                font-weight: bold;
            }

            #subtitle {
                font-size: 9px;
                color: #777777;
            }

            #navButton {
                text-align: left;
                padding: 11px 13px;
                border: 1px solid transparent;
                border-radius: 7px;
                color: #aaaaaa;
                background: #080808;
                font-size: 13px;
            }

            #navButton:hover {
                color: #eeeeee;
                background: #121212;
                border: 1px solid #202020;
            }

            #navButton:checked {
                color: #00e59a;
                background: #101a16;
                border: 1px solid #164f3d;
                font-weight: bold;
            }

            #version {
                color: #555555;
                font-size: 10px;
            }

            #header {
                font-size: 24px;
                font-weight: bold;
            }

            #status {
                color: #00ff88;
                font-size: 11px;
            }

            #statusOffline {
                color: #ff5555;
                font-size: 11px;
            }

            #card {
                background: #111111;
                border: 1px solid #222222;
                border-radius: 8px;
            }

            #cardTitle {
                color: #777777;
                font-size: 11px;
            }

            #cardValue {
                font-size: 28px;
                font-weight: bold;
            }

            #info {
                background: #111111;
                border: 1px solid #222222;
                border-radius: 8px;
                padding: 10px;
            }

            #sectionTitle {
                font-size: 13px;
                font-weight: bold;
            }

            #terminalPrompt {
                color: #00ff88;
                font-weight: bold;
                min-width: 180px;
            }

            #terminalOutput {
                background: #050505;
                border: 1px solid #222222;
                color: #dddddd;
                font-family: "JetBrains Mono", monospace;
                font-size: 12px;
                padding: 10px;
            }

            #terminalOutput QScrollBar:vertical {
                background: #090909;
                width: 10px;
            }

            #terminalOutput QScrollBar::handle:vertical {
                background: #292929;
                min-height: 30px;
            }

            #toolButton {
                min-width: 42px;
                min-height: 34px;
                background: #151515;
                border: 1px solid #282828;
                border-radius: 6px;
            }

            #toolButton:hover {
                background: #202020;
            }

            QLineEdit {
                background: #111111;
                border: 1px solid #282828;
                border-radius: 6px;
                padding: 8px;
                color: #eeeeee;
            }

            QComboBox {
                background: #111111;
                border: 1px solid #282828;
                border-radius: 6px;
                padding: 8px;
                color: #eeeeee;
                min-width: 90px;
            }

            QComboBox QAbstractItemView {
                background: #111111;
                color: #eeeeee;
                selection-background-color: #202020;
                border: 1px solid #282828;
            }

            QTableWidget {
                background: #111111;
                border: 1px solid #222222;
                gridline-color: #222222;
                selection-background-color: #202020;
                alternate-background-color: #0e0e0e;
            }

            QHeaderView::section {
                background: #181818;
                color: #aaaaaa;
                border: none;
                padding: 8px;
                font-weight: bold;
            }

            QDialog {
                background: #0b0b0b;
            }

            QMessageBox {
                background: #0b0b0b;
            }

            QPushButton {
                color: #eeeeee;
            }
        """)


def main():
    app = QApplication(sys.argv)
    window = LinuxCommandCenter()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
