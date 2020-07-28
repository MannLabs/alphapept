from PyQt5.QtCore import QUrl, QSize, QThread, pyqtSignal, Qt, QAbstractTableModel, QCoreApplication
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *

import sys
import os

from functools import partial

from .stylesheets import (
    big_font,
    version_font,
    logo_font,
    progress_style,
    busy_style,
    progress_style_1,
    progress_style_2,
    progress_style_3,
    progress_style_4,
)

from .runner import run_alphapept

import yaml
import numpy as np
from time import time, sleep
import psutil
from qroundprogressbar import QRoundProgressBar
import logging
import pandas as pd
import qdarkstyle
import os


dark_stylesheet = qdarkstyle.load_stylesheet_pyqt5()

_this_file = os.path.abspath(__file__)
_this_directory = os.path.dirname(_this_file)
SETTINGS_TEMPLATE_PATH = os.path.join(_this_directory,  "settings_template.yaml")

ICON_PATH = os.path.join(_this_directory, "img", "logo_200px.png")
BUSY_INDICATOR_PATH = os.path.join(_this_directory, "img", "busy_indicator.gif")

# Get Version

VERSION_NO = "0.2.1-dev0"

URL_DOCUMENTATION = "https://en.wikipedia.org/wiki/Documentation"
URL_ISSUE = "https://en.wikipedia.org/wiki/Issue"
URL_CONTRIBUTE = "https://en.wikipedia.org/wiki/Contribution"



if not os.path.isfile(ICON_PATH):
    print(ICON_PATH)
    raise FileNotFoundError('Logo not found')

if not os.path.isfile(BUSY_INDICATOR_PATH):
    print(BUSY_INDICATOR_PATH)
    raise FileNotFoundError('Busy Indicator')

def cancel_dialogs():
    dialogs = [_ for _ in _dialogs]
    for dialog in dialogs:
        if isinstance(dialog, ProgressDialog):
            dialog.cancel()
        else:
            dialog.close()
    QCoreApplication.instance().processEvents()  # just in case...

class pandasModel(QAbstractTableModel):

    """
    Taken from https://learndataanalysis.org/display-pandas-dataframe-with-pyqt5-qtableview-widget/
    """

    def __init__(self, data):
        QAbstractTableModel.__init__(self)
        self._data = data

    def rowCount(self, parent=None):
        return self._data.shape[0]

    def columnCount(self, parnet=None):
        return self._data.shape[1]

    def data(self, index, role=Qt.DisplayRole):
        if index.isValid():
            if role == Qt.DisplayRole:
                return str(self._data.iloc[index.row(), index.column()])
        return None

    def headerData(self, col, orientation, role):
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            return self._data.columns[col]
        return None






class QTextEditLogger(logging.Handler):
    def __init__(self, parent):
        super().__init__()
        self.widget = QPlainTextEdit(parent)
        self.widget.setReadOnly(True)

    def emit(self, record):
        msg = self.format(record)
        self.widget.appendPlainText(msg)
        self.widget.verticalScrollBar().setValue(self.widget.verticalScrollBar().maximum())


class searchThread(QThread):
    """
    Thread to run the search
    """

    current_progress_update = pyqtSignal(float)
    global_progress_update = pyqtSignal(float)
    task_update = pyqtSignal(str)

    def __init__(self, settings):
        QThread.__init__(self)
        self.settings = settings

    def update_current_progress(self, progress):
        self.current_progress_update.emit(progress)

    def update_global_progress(self, progress):
        self.global_progress_update.emit(progress)

    def update_task(self, task):
        self.task_update.emit(task)

    def run(self):
        features, df_calib = run_alphapept(self.settings, self.update_global_progress, self.update_current_progress, self.update_task)

        self.features = features
        self.df = df_calib


class External(QThread):
    """
    Runs a counter thread to update the system stats
    """

    countChanged = pyqtSignal(int)

    def run(self):
        count = 0
        while True:
            count += 1
            sleep(0.5)
            self.countChanged.emit(count)
            count -= 1

class MainWindow(QMainWindow):
    def __init__(self, parent=None):
        super(MainWindow, self).__init__(parent)
        self.setWindowIcon(QIcon("ICON_PATH"))
        self.title = "AlphaPept " + VERSION_NO
        self.setStyleSheet("font-size: 12pt;")

        self.initUI()

    def open_url(self, url):
        qt_url = QUrl(url)

        if not QtGui.QDesktopServices.openUrl(qt_url):
            QtGui.QMessageBox.warning(self, "Open Url", "Could not open url")

    def open_url_docu(self):
        self.open_url(URL_DOCUMENTATION)

    def open_URL_ISSUE(self):
        self.open_url(URL_ISSUE)

    def open_url_contrib(self):
        self.open_url(URL_CONTRIBUTE)

    def path_from_drop(self, event):
        url = event.mimeData().urls()[0]
        path = url.toLocalFile()
        base, extension = os.path.splitext(path)
        return path, extension

    def drop_has_valid_url(self, event):
        if not event.mimeData().hasUrls():
            return False
        path, extension = self.path_from_drop(event)
        if extension.lower() not in [".yaml", ".npz", ".raw", ".fasta"]:
            return False
        return True

    def dragEnterEvent(self, event):
        if self.drop_has_valid_url(event):
            event.accept()
        else:
            event.ignore()

    def dropEvent(self, event):
        """ Loads  when dropped into the scene """

        path, extension = self.path_from_drop(event)

        logging.info("Dropped file {}.".format(path))

        if extension == ".fasta":
            if "fasta" in self.categories.keys():
                if "fasta_path" in self.categories["fasta"]["widgets"].keys():
                    self.categories["fasta"]["widgets"]["fasta_path"].setText(path)
                    logging.info("Set FASTA file as {}.".format(path))

        elif extension == ".raw":
            if "raw" in self.categories.keys():
                if "raw_path" in self.categories["raw"]["widgets"].keys():
                    self.categories["raw"]["widgets"]["raw_path"].setText(path)
                    logging.info("Set raw file as {}.".format(path))

        elif extension == ".npz":
            # Npz is either library or converted raw file
            x = np.load(path, mmap_mode="r")  # only memory map

            fields = x.files
            if "fasta_dict" in fields:
                if "fasta" in self.categories.keys():
                    if "library_path" in self.categories["fasta"]["widgets"].keys():
                        self.categories["fasta"]["widgets"]["library_path"].setText(
                            path
                        )
                        logging.info("Set library path to {}.".format(path))

            elif "scan_list_ms1" in fields:
                if "raw" in self.categories.keys():
                    if "raw_path_npz" in self.categories["raw"]["widgets"].keys():
                        self.categories["raw"]["widgets"]["raw_path_npz"].setText(path)
                        logging.info("Set raw path of npz to {}.".format(path))
            else:
                print(x.files)
                print("NPZ container not understood.")
                raise NotImplementedError

        elif extension == ".yaml":

            with open(path, "r") as settings_file:
                settings = yaml.load(settings_file, Loader=yaml.FullLoader)
            self.set_settings(settings)
            logging.info("Loaded settings from {}.".format(path))
        else:
            print("Extension not found {}".format(extension))
            raise NotImplementedError

    def read_settings(self):
        settings = {}

        for category in self.categories.keys():

            settings[category] = {}
            for widget_name in self.categories[category]["widgets"].keys():

                widget = self.categories[category]["widgets"][widget_name]
                if isinstance(widget, QSpinBox):
                    settings[category][widget_name] = widget.value()
                elif isinstance(widget, QDoubleSpinBox):
                    settings[category][widget_name] = widget.value()
                elif isinstance(widget, QPushButton):
                    settings[category][widget_name] = widget.text()
                elif isinstance(widget, QComboBox):
                    settings[category][widget_name] = widget.currentText()
                elif isinstance(widget, QCheckBox):
                    state = widget.checkState()
                    if state == 2:
                        state = True
                    else:
                        state = False
                    settings[category][widget_name] = state
                elif isinstance(widget, dict):
                    checked = []
                    for _ in widget.keys():
                        if widget[_].checkState(1) == Qt.Checked:
                            checked.append(_)
                    settings[category][widget_name] = checked
                else:
                    print(widget.__class__)
                    print("This should never happen..")
                    raise NotImplementedError

        return settings

    def disable_settings(self):
        """
        Disable editing of settings
        """
        for category in self.categories.keys():
            for widget_name in self.categories[category]["widgets"].keys():
                widget = self.categories[category]["widgets"][widget_name]
                if isinstance(widget, QSpinBox):
                    widget.setEnabled(False)
                elif isinstance(widget, QDoubleSpinBox):
                    widget.setEnabled(False)
                elif isinstance(widget, QPushButton):
                    widget.setEnabled(False)
                elif isinstance(widget, QComboBox):
                    widget.setEnabled(False)
                elif isinstance(widget, QCheckBox):
                    widget.setEnabled(False)
                elif isinstance(widget, dict):
                    for _ in widget.keys():
                        widget[_].setFlags(Qt.NoItemFlags)
                else:
                    print(widget.__class__)
                    print("This should never happen..")
                    raise NotImplementedError
    #def enable_settings(self):

    def set_settings(self, settings):
        for category in settings.keys():
            for subcategory in settings[category].keys():
                value = settings[category][subcategory]
                widget = self.categories[category]["widgets"][subcategory]
                if isinstance(widget, QSpinBox):
                    widget.setValue(value)
                elif isinstance(widget, QDoubleSpinBox):
                    widget.setValue(value)
                elif isinstance(widget, QPushButton):
                    widget.setText(value)
                elif isinstance(widget, QComboBox):
                    # Find and set
                    idx = widget.findText(value)
                    widget.setCurrentIndex(idx)
                elif isinstance(widget, QCheckBox):
                    if value:
                        widget.setCheckState(2)
                    else:
                        widget.setState(False)
                elif isinstance(widget, dict):
                    checked = []
                    for _ in widget.keys():
                        widget[_].setCheckState(1, Qt.Unchecked)
                    if value:
                        for _ in value:
                            widget[_].setCheckState(1, Qt.Checked)

                else:
                    print("Error")
                    raise NotImplementedError

    def initUI(self):
        # Read Hardware
        n_cpu = psutil.cpu_count()
        memory = psutil.virtual_memory()
        ram = memory.total / 1024 / 1024 / 1024
        system_info = "CPU {} - Cores\nRAM {:.2f} GB ".format(n_cpu, ram)
        self.cpu_utilization = 0
        self.hardware = system_info
        self.ram_utilization = 0
        self.overall_progress = 0
        self.resize(1024, 800)
        self.setMinimumSize(QSize(1024, 800))

        self.centralwidget = QWidget(self)
        self.centralwidget.setStyleSheet(dark_stylesheet)

        self.horizontalLayout = QHBoxLayout(self.centralwidget)

        self.horizontalLayout.setContentsMargins(0, 0, 0, 0)
        self.horizontalLayout.setSpacing(0)

        self.verticalLayout = QVBoxLayout()

        self.logo_main = QLabel(self)
        self.logo_main.setPixmap(QPixmap("logo_200px.png"))

        self.verticalLayout.addWidget(self.logo_main)

        self.logo_label = QLabel("AlphaPept")
        self.logo_label.setStyleSheet(logo_font)
        self.logo_label.setAlignment(Qt.AlignCenter)
        self.verticalLayout.addWidget(self.logo_label)

        self.logo_version = QLabel(VERSION_NO)
        self.logo_version.setStyleSheet(version_font)
        self.verticalLayout.addWidget(self.logo_version)

        self.logo_version.setAlignment(Qt.AlignCenter)

        self.busy_indicator = QLabel(self)

        self.movie = QMovie(BUSY_INDICATOR_PATH)
        self.busy_indicator.setMovie(self.movie)
        self.busy_indicator.setAlignment(Qt.AlignCenter)

        spacerItem = QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)
        self.verticalLayout.addItem(spacerItem)

        self.btn_settings = QPushButton("Files")
        self.btn_settings.setStyleSheet(big_font)
        self.verticalLayout.addWidget(self.btn_settings)
        self.btn_settings.clicked.connect(self.page_files)

        self.btn_settings = QPushButton("Settings")
        self.btn_settings.setStyleSheet(big_font)
        self.verticalLayout.addWidget(self.btn_settings)
        self.btn_settings.clicked.connect(self.page_settings)

        self.btn_run = QPushButton("Run")
        self.btn_run.setStyleSheet(big_font)
        self.verticalLayout.addWidget(self.btn_run)
        self.btn_run.clicked.connect(self.page_run)

        self.btn_explore = QPushButton("Explore")
        self.btn_explore.setStyleSheet(big_font)
        self.verticalLayout.addWidget(self.btn_explore)
        self.btn_explore.clicked.connect(self.page_explore)

        self.btn_help = QPushButton("Help")
        self.btn_help.setStyleSheet(big_font)
        self.verticalLayout.addWidget(self.btn_help)
        self.btn_help.clicked.connect(self.page_help)

        spacerItem1 = QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)

        self.verticalLayout.addItem(spacerItem1)
        self.verticalLayout.addWidget(self.busy_indicator)
        self.horizontalLayout.addLayout(self.verticalLayout)

        self.stackedWidget = QStackedWidget(self.centralwidget)
        self.stackedWidget.setMinimumSize(QSize(550, 600))


        # Files

        self.files = QWidget()
        self.files_layout_ = QHBoxLayout(self.files)
        self.files_layout = QVBoxLayout()
        self.label_files = QLabel("Files")
        self.label_files.setStyleSheet(logo_font)
        self.files_layout.addWidget(self.label_files)
        self.files_layout.addItem(QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding))

        self.files_layout_.addLayout(self.files_layout)
        self.stackedWidget.addWidget(self.files)


        # Settings

        self.settings = QWidget()
        self.settings_layout_ = QHBoxLayout(self.settings)
        self.settings_layout = QVBoxLayout()
        self.label_settings = QLabel("Settings")
        self.label_settings.setStyleSheet(logo_font)
        self.settings_layout.addWidget(self.label_settings)
        self.combo_settings = QComboBox()
        self.combo_settings.addItem("default")
        self.settings_layout.addWidget(self.combo_settings)
        self.treeWidget = QTreeWidget(self.settings)

        self.init_tree()
        self.settings_layout.addWidget(self.treeWidget)
        self.button_layout = QHBoxLayout()
        self.btn_load_settings = QPushButton("Load")
        self.btn_load_settings.setStyleSheet(big_font)
        self.button_layout.addWidget(self.btn_load_settings)
        self.btn_load_settings.clicked.connect(self.load_settings)

        self.btn_save_settings = QPushButton("Save")
        self.btn_save_settings.setStyleSheet(big_font)
        self.button_layout.addWidget(self.btn_save_settings)
        self.btn_save_settings.clicked.connect(self.save_settings)

        self.btn_check_settings = QPushButton("Check")
        self.btn_check_settings.setStyleSheet(big_font)
        self.button_layout.addWidget(self.btn_check_settings)
        self.btn_check_settings.clicked.connect(self.check_settings)

        self.settings_layout.addLayout(self.button_layout)
        self.settings_layout_.addLayout(self.settings_layout)
        self.stackedWidget.addWidget(self.settings)


        # RUN

        self.run = QWidget()

        self.run_layout_ = QHBoxLayout(self.run)
        self.run_layout = QVBoxLayout()

        self.label_run = QLabel("Run")
        self.label_run.setStyleSheet(logo_font)
        self.run_layout.addWidget(self.label_run)

        self.groupbox_layout = QVBoxLayout()
        self.groupbox_performance = QGroupBox(self.run)
        self.groupbox_performance.setTitle("")
        self.verticalLayout_7 = QVBoxLayout(self.groupbox_performance)
        self.performance_layout = QVBoxLayout()

        # Elements:
        self.performance_gauge_layout = QHBoxLayout()
        # (left <> Right)

        self.performance_layout_left = QVBoxLayout()
        self.performance_layout_right = QVBoxLayout()

        self.performance_gauge_layout.addLayout(self.performance_layout_left)
        spacerItem_performance = QSpacerItem(
            20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding
        )
        self.performance_gauge_layout.addItem(spacerItem_performance)
        self.performance_gauge_layout.addLayout(self.performance_layout_right)

        # Left side: One big gauge for overall progress

        self.progress_overall = QRoundProgressBar()
        self.progress_overall.setBarStyle(QRoundProgressBar.BarStyle.DONUT)
        self.progress_overall.setMinimumSize(200, 200)
        self.progress_overall.setValue(0)

        self.performance_layout_left.addWidget(QLabel("Overall Progress"))
        self.performance_layout_left.addWidget(self.progress_overall)

        self.progress_overall.setStyleSheet(
            "alternate-background-color: rgb(25,35,45); selection-background-color:rgb(109, 236, 185);"
        )

        # Right side
        self.progress_cpu = QProgressBar()
        self.progress_cpu.setValue(self.cpu_utilization)
        self.progress_cpu.setStyleSheet(progress_style_1)

        self.progress_ram = QProgressBar()
        self.progress_ram.setValue(self.ram_utilization)
        self.progress_ram.setStyleSheet(progress_style_4)

        self.progress_current = QProgressBar()
        self.progress_current.setValue(0)
        self.progress_current.setStyleSheet(progress_style_2)

        self.current_task_label = QLabel("")
        self.performance_layout_right.addWidget(self.current_task_label)
        self.performance_layout_right.addWidget(self.progress_current)

        self.performance_layout_right.addWidget(QLabel("CPU"))
        self.performance_layout_right.addWidget(self.progress_cpu)

        self.performance_layout_right.addWidget(QLabel("RAM  {:.2f} GB".format(ram)))
        self.performance_layout_right.addWidget(self.progress_ram)

        self.performance_layout.addLayout(self.performance_gauge_layout)
        self.verticalLayout_7.addLayout(self.performance_layout)

        spacerItem2 = QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)
        self.verticalLayout_7.addItem(spacerItem2)
        self.groupbox_layout.addWidget(self.groupbox_performance)
        self.groupbox_progress = QGroupBox(self.run)

        self.groupbox_progress.setTitle("")

        self.verticalLayout_5 = QVBoxLayout(self.groupbox_progress)
        self.layout_progress = QVBoxLayout()
        self.label_progress_header = QLabel("Log")
        self.layout_progress.addWidget(self.label_progress_header)

        self.log_textbox = QTextEditLogger(self.groupbox_progress)
        self.log_textbox.setFormatter(
            logging.Formatter("%(asctime)s - %(message)s", "%Y-%m-%d %H:%M:%S")
        )
        logging.getLogger().addHandler(self.log_textbox)
        logging.getLogger().setLevel(logging.INFO)

        self.layout_progress.addWidget(self.log_textbox.widget)

        self.verticalLayout_5.addLayout(self.layout_progress)
        spacerItem3 = QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)
        self.verticalLayout_5.addItem(spacerItem3)
        self.groupbox_layout.addWidget(self.groupbox_progress)
        self.run_layout.addLayout(self.groupbox_layout)
        spacerItem4 = QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)
        self.run_layout.addItem(spacerItem4)
        self.btn_start = QPushButton("Start")
        self.btn_start.setStyleSheet(big_font)
        self.btn_start.clicked.connect(self.start)

        self.run_layout.addWidget(self.btn_start)
        self.run_layout_.addLayout(self.run_layout)
        self.stackedWidget.addWidget(self.run)
        self.explore = QWidget()

        self.verticalLayout_2 = QVBoxLayout(self.explore)

        #Explore

        self.explore_layout = QVBoxLayout()

        self.label_explore = QLabel("Explore")
        self.label_explore.setStyleSheet(logo_font)
        self.explore_layout.addWidget(self.label_explore)

        self.button_layout_explore = QHBoxLayout()
        self.verticalLayout_3 = QVBoxLayout()
        self.tabWidget = QTabWidget(self.explore)
        self.tab_features = QWidget()
        self.verticalLayout_4 = QVBoxLayout(self.tab_features)
        self.table_features = QTableView(self.tab_features)
        self.table_features.show()
        self.verticalLayout_4.addWidget(self.table_features)
        self.tabWidget.addTab(self.tab_features, "Features")
        self.tab_peptides = QWidget()
        self.horizontalLayout_4 = QHBoxLayout(self.tab_peptides)
        self.table_peptides = QTableView(self.tab_peptides)
        self.horizontalLayout_4.addWidget(self.table_peptides)
        self.tabWidget.addTab(self.tab_peptides, "Peptides")
        self.tab_plot = QWidget()

        self.horizontalLayout_6 = QHBoxLayout(self.tab_plot)
        self.verticalLayout_6 = QVBoxLayout()
        self.horizontalLayout_8 = QHBoxLayout()
        self.combo_plot = QComboBox(self.tab_plot)

        self.combo_plot.addItem("1")
        self.combo_plot.addItem("2")
        self.combo_plot.addItem("3")
        self.horizontalLayout_8.addWidget(self.combo_plot)
        self.btn_plot = QPushButton("Plot")
        self.btn_plot.setStyleSheet(big_font)

        self.horizontalLayout_8.addWidget(self.btn_plot)
        self.verticalLayout_6.addLayout(self.horizontalLayout_8)
        self.widget_plot = QWidget(self.tab_plot)

        self.verticalLayout_6.addWidget(self.widget_plot)
        self.horizontalLayout_6.addLayout(self.verticalLayout_6)
        self.tabWidget.addTab(self.tab_plot, "Plot")
        self.verticalLayout_3.addWidget(self.tabWidget)
        self.button_layout_explore.addLayout(self.verticalLayout_3)
        self.explore_layout.addLayout(self.button_layout_explore)
        self.verticalLayout_2.addLayout(self.explore_layout)
        self.stackedWidget.addWidget(self.explore)
        self.layout_help_main = QWidget()
        self.layout_help_main.setObjectName("layout_help_main")
        self.horizontalLayout_2 = QHBoxLayout(self.layout_help_main)
        self.horizontalLayout_2.setObjectName("horizontalLayout_2")
        self.layout_help = QVBoxLayout()
        self.layout_help.setObjectName("layout_help")

        self.label_help = QLabel("Help")
        self.label_help.setStyleSheet(logo_font)
        self.layout_help.addWidget(self.label_help)

        self.layout_help_btns = QVBoxLayout()

        spacerItem5 = QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)
        self.layout_help_btns.addItem(spacerItem5)

        # Buttons for Help
        self.btn_documentation = QPushButton("Documentation")
        self.btn_documentation.setStyleSheet(big_font)
        self.btn_documentation.clicked.connect(self.open_url_docu)

        self.layout_help_btns.addWidget(self.btn_documentation)
        self.btn_report = QPushButton("Report Issue")
        self.btn_report.setStyleSheet(big_font)
        self.btn_report.clicked.connect(self.open_URL_ISSUE)

        self.layout_help_btns.addWidget(self.btn_report)
        self.btn_contribute = QPushButton("Contribute")
        self.btn_contribute.setStyleSheet(big_font)
        self.layout_help_btns.addWidget(self.btn_contribute)
        self.btn_contribute.clicked.connect(self.open_url_contrib)

        spacerItem6 = QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)
        self.layout_help_btns.addItem(spacerItem6)
        self.layout_help.addLayout(self.layout_help_btns)
        self.horizontalLayout_2.addLayout(self.layout_help)
        self.stackedWidget.addWidget(self.layout_help_main)
        self.horizontalLayout.addWidget(self.stackedWidget)
        self.setCentralWidget(self.centralwidget)

        self.stackedWidget.setCurrentIndex(0)
        self.tabWidget.setCurrentIndex(0)

        self.calc = External()

        self.calc.countChanged.connect(self.onCountChanged)
        self.calc.start()

        logging.info("AlphaPept version {} started.".format(VERSION_NO))

        # Start with Run page
        self.stackedWidget.setCurrentIndex(2)

    def onCountChanged(self, value):
        cpu = psutil.cpu_percent()
        self.progress_cpu.setValue(int(cpu))
        memory = psutil.virtual_memory()
        self.progress_ram.setValue(int(memory.percent))

    def page_files(self):
        self.stackedWidget.setCurrentIndex(0)

    def page_settings(self):
        self.stackedWidget.setCurrentIndex(1)

    def page_run(self):
        self.stackedWidget.setCurrentIndex(2)

    def page_explore(self):
        self.stackedWidget.setCurrentIndex(3)

    def page_help(self):
        self.stackedWidget.setCurrentIndex(4)

    def init_tree(self):

        header = QTreeWidgetItem(["Parameter", "Value", "Description"])

        self.treeWidget.setHeaderItem(
            header
        )  # Another alternative is setHeaderLabels(["Tree","First",...])

        self.treeWidget.header().resizeSection(0, 300)
        self.treeWidget.header().resizeSection(1, 150)

        # Main Categories

        with open(SETTINGS_TEMPLATE_PATH, "r") as config_file:
            self.settings_template = yaml.load(config_file, Loader=yaml.FullLoader)

        self.categories = {}

        for category in self.settings_template.keys():
            self.categories[category] = {}
            self.categories[category]["Tree"] = QTreeWidgetItem(
                self.treeWidget, [category]
            )

            fields = {}
            widgets = {}

            self.categories[category]["fields"] = fields
            self.categories[category]["widgets"] = widgets

            for subcategory in self.settings_template[category]:
                fields[subcategory] = QTreeWidgetItem(
                    self.categories[category]["Tree"], [subcategory]
                )

                type = self.settings_template[category][subcategory]["type"]

                if type == "spinbox":
                    widgets[subcategory] = QSpinBox()
                    widgets[subcategory].setMinimum(
                        self.settings_template[category][subcategory]["min"]
                    )
                    widgets[subcategory].setMaximum(
                        self.settings_template[category][subcategory]["max"]
                    )
                    widgets[subcategory].setValue(
                        self.settings_template[category][subcategory]["default"]
                    )
                    widgets[subcategory].setFocusPolicy(Qt.StrongFocus)

                elif type == "doublespinbox":
                    widgets[subcategory] = QDoubleSpinBox()
                    widgets[subcategory].setMinimum(
                        self.settings_template[category][subcategory]["min"]
                    )
                    widgets[subcategory].setMaximum(
                        self.settings_template[category][subcategory]["max"]
                    )
                    widgets[subcategory].setValue(
                        self.settings_template[category][subcategory]["default"]
                    )
                    widgets[subcategory].setFocusPolicy(Qt.StrongFocus)

                elif type == "combobox":
                    widgets[subcategory] = QComboBox()
                    for _ in self.settings_template[category][subcategory]["value"]:
                        widgets[subcategory].addItem(_)

                    default_idx = widgets[subcategory].findText(
                        self.settings_template[category][subcategory]["default"]
                    )
                    widgets[subcategory].setCurrentIndex(default_idx)
                    widgets[subcategory].setFocusPolicy(Qt.StrongFocus)

                elif type == "checkbox":
                    widgets[subcategory] = QCheckBox()
                    default_state = self.settings_template[category][subcategory][
                        "default"
                    ]
                    widgets[subcategory].setChecked(default_state)

                elif type == "path":
                    # Make path clickable
                    default = self.settings_template[category][subcategory]["default"]
                    widgets[subcategory] = QPushButton(default)
                    widgets[subcategory].clicked.connect(
                        partial(self.set_path, category, subcategory)
                    )

                elif type == "checkgroup":
                    pass

                else:
                    print(category, subcategory)
                    raise NotImplementedError

                if subcategory in widgets.keys():
                    self.treeWidget.setItemWidget(
                        fields[subcategory], 1, widgets[subcategory]
                    )
                    try:
                        description = self.settings_template[category][subcategory][
                            "description"
                        ]
                        self.treeWidget.setItemWidget(
                            fields[subcategory], 2, QLabel(description)
                        )
                    except KeyError:
                        pass

                if type == "checkgroup":
                    elements = self.settings_template[category][subcategory]["value"]

                    widgets[subcategory] = {}
                    # ADD children
                    for _ in elements.keys():
                        widgets[subcategory][_] = QTreeWidgetItem(
                            fields[subcategory], ["", _, elements[_]]
                        )
                        widgets[subcategory][_].setCheckState(1, Qt.Unchecked)

                    default = self.settings_template[category][subcategory]["default"]

                    for _ in default:
                        widgets[subcategory][_].setCheckState(1, Qt.Checked)

                    description = self.settings_template[category][subcategory][
                        "description"
                    ]
                    self.treeWidget.setItemWidget(
                        fields[subcategory], 2, QLabel(description)
                    )

        self.setAcceptDrops(True)
        self.dragMoveEvent = self.dragEnterEvent

    def set_path(self, category, subcategory):
        filetype = self.settings_template[category][subcategory]["filetype"]

        filetype_str = "".join(["*." + _ + ", " for _ in filetype])[:-2]
        folder = self.settings_template[category][subcategory]["folder"]

        if folder:
            path = QFileDialog.getExistingDirectory(self, "Select directory")
        else:
            path, ext = QFileDialog.getOpenFileName(self, "Open file", "", filetype_str)
        if path:
            self.categories[category]["widgets"][subcategory].setText(path)

    def load_settings(self):
        path, ext = QFileDialog.getOpenFileName(
            self, "Open settings file:", "", "Settings files (*.yaml)"
        )
        if path:
            with open(path, "r") as settings_file:
                settings = yaml.load(settings_file, Loader=yaml.FullLoader)
                self.set_settings(settings)
                self.categories["general"]["widgets"]["settings_path"].setText(path)

    def save_settings(self):
        settings = self.read_settings()
        path, ext = QFileDialog.getSaveFileName(
            self, "Save settings to:", "", "Settings files (*.yaml)"
        )

        if path:
            self.categories["general"]["widgets"]["settings_path"].setText(path)
            with open(path, "w") as file:
                yaml.dump(settings, file)

    def check_settings(self):
        # TODO: Sanity check for settings
        print("not implemented yet..")

    def progress_current_changed(self, value):
        self.progress_current.setValue(int(value*100))

    def progress_overall_changed(self, value):
        self.progress_overall.setValue(value)

    def current_step_changed(self, task):
        print(task)
        logging.info(task)
        self.current_task_label.setText(task)



    def start(self):
        logging.info("Started processing.")

        self.movie.start()

        self.disable_settings()
        self.btn_start.setText('Running..')
        self.btn_start.setEnabled(False)

        settings = self.read_settings()


        self.searchthread = searchThread(settings)

        self.searchthread.current_progress_update.connect(self.progress_current_changed)
        self.searchthread.global_progress_update.connect(self.progress_overall_changed)
        self.searchthread.task_update.connect(self.current_step_changed)

        self.searchthread.start()

        self.searchthread.finished.connect(self.complete)

    def complete(self):

        self.btn_start.setText('Start')
        self.btn_start.setEnabled(True)

        self.df = self.searchthread.df
        self.features = self.searchthread.features

        model = pandasModel(self.df)
        self.table_peptides.setModel(model)

        model = pandasModel(self.features)
        self.table_features.setModel(model)

        self.movie.stop()
        #self.movie.setVisible(False)


def main():
    app = QApplication(sys.argv)
    app.setStyle(QStyleFactory.create("Fusion"))
    form = MainWindow()
    form.show()

    app.processEvents()

    sys.exit(app.exec_())

    def excepthook(type, value, tback):
        cancel_dialogs()
        message = "".join(traceback.format_exception(type, value, tback))
        errorbox = QMessageBox.critical(
            window, "An error occured", message
        )
        errorbox.exec_()
        sys.__excepthook__(type, value, tback)

    sys.excepthook = excepthook

    sys.exit(app.exec_())


if __name__ == "__main__":

    main()
