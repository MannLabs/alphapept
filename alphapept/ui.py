from PyQt5.QtCore import QUrl, QSize, QCoreApplication, Qt
from PyQt5.QtWidgets import QFileDialog, QMessageBox, QTableView, QTabWidget, QProgressBar, QGroupBox, QComboBox, QPushButton, QStackedWidget, QWidget, QMainWindow, QApplication, QStyleFactory, QHBoxLayout, QVBoxLayout, QLabel, QSpacerItem, QSizePolicy
from PyQt5.QtGui import QIcon, QPixmap, QMovie, QDesktopServices


import sys
import os
import traceback


from alphapept.stylesheets import (
    big_font,
    version_font,
    logo_font,
    progress_style_1,
    progress_style_2,
    progress_style_4,
)
from alphapept.ui_classes import FastaFileSelector, QTextEditLogger, searchThread, External, RawFileSelector, SettingsEdit, pandasModel

import yaml
import psutil
from qroundprogressbar import QRoundProgressBar
import logging
import pandas as pd
import qdarkstyle


dark_stylesheet = qdarkstyle.load_stylesheet_pyqt5()

_this_file = os.path.abspath(__file__)
_this_directory = os.path.dirname(_this_file)

SETTINGS_TEMPLATE_PATH = os.path.join(
    _this_directory,
    "settings_template.yaml"
 )
LOGO_PATH = os.path.join(_this_directory, "img", "logo_200px.png")
ICON_PATH = os.path.join(_this_directory, "img", "logo.ico")
BUSY_INDICATOR_PATH = os.path.join(
    _this_directory,
    "img",
    "busy_indicator.gif"
)

# Get Version

VERSION_NO = "0.2.8-dev0"

URL_DOCUMENTATION = "https://mannlabs.github.io/alphapept/"
URL_ISSUE = "https://github.com/MannLabs/alphapept/issues"
URL_CONTRIBUTE = "https://github.com/MannLabs/alphapept/blob/master/CONTRIBUTING.md"

if not os.path.isfile(ICON_PATH):
    raise FileNotFoundError('Logo not found - Path {}'.format(ICON_PATH))

if not os.path.isfile(BUSY_INDICATOR_PATH):
    raise FileNotFoundError(
        'Busy Indicator - Path {}'.format(BUSY_INDICATOR_PATH)
    )


def cancel_dialogs():
    dialogs = [_ for _ in _dialogs]
    for dialog in dialogs:
        if isinstance(dialog, ProgressDialog):
            dialog.cancel()
        else:
            dialog.close()
    QCoreApplication.instance().processEvents()  # just in case...


class MainWindow(QMainWindow):
    def __init__(self, parent=None):
        super(MainWindow, self).__init__(parent)
        self.setWindowIcon(QIcon(ICON_PATH))
        self.title = "AlphaPept " + VERSION_NO
        self.setStyleSheet("font-size: 12pt;")
        self.setWindowTitle(self.title)

        self.initUI()

    def open_url(self, url):
        qt_url = QUrl(url)

        if not QDesktopServices.openUrl(qt_url):
            QMessageBox.warning(self, "Open Url", "Could not open url")

    def open_url_docu(self):
        self.open_url(URL_DOCUMENTATION)

    def open_URL_ISSUE(self):
        self.open_url(URL_ISSUE)

    def open_url_contrib(self):
        self.open_url(URL_CONTRIBUTE)

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
        self.logo_main.setPixmap(QPixmap(LOGO_PATH))

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

        self.btn_experiment = QPushButton("Experiment")
        self.btn_experiment.setStyleSheet(big_font)
        self.verticalLayout.addWidget(self.btn_experiment)
        self.btn_experiment.clicked.connect(self.page_files)

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

        spacerItem1 = QSpacerItem(
            20,
            40,
            QSizePolicy.Minimum,
            QSizePolicy.Expanding
        )

        self.verticalLayout.addItem(spacerItem1)
        self.verticalLayout.addWidget(self.busy_indicator)
        self.horizontalLayout.addLayout(self.verticalLayout)

        self.stackedWidget = QStackedWidget(self.centralwidget)
        self.stackedWidget.setMinimumSize(QSize(550, 600))

        # Files

        self.files = QWidget()
        self.files_layout_ = QHBoxLayout(self.files)
        self.files_layout = QVBoxLayout()
        self.label_files = QLabel("Experiment")
        self.label_files.setStyleSheet(logo_font)
        self.files_layout.addWidget(self.label_files)

        self.file_selector = RawFileSelector(
            ["Filename", "Shortname", "Fraction"]
        )
        self.files_layout.addWidget(QLabel("Experimental files"))

        self.files_layout.addWidget(self.file_selector)

        self.files_layout.addWidget(QLabel("FASTA files"))
        self.fasta_selector = FastaFileSelector(["Filename"])
        self.files_layout.addWidget(self.fasta_selector)

        self.files_layout.addItem(
            QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)
        )

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
        self.combo_settings.setStyleSheet("QListView::item {height:20px;}")
        self.combo_settings.addItem("default")
        self.settings_layout.addWidget(self.combo_settings)

        self.settingsWidget = SettingsEdit()
        self.settings_layout.addWidget(self.settingsWidget)
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

        self.performance_layout_right.addWidget(
            QLabel("RAM  {:.2f} GB".format(ram))
        )
        self.performance_layout_right.addWidget(self.progress_ram)

        self.performance_layout.addLayout(self.performance_gauge_layout)
        self.verticalLayout_7.addLayout(self.performance_layout)

        spacerItem2 = QSpacerItem(
            20,
            40,
            QSizePolicy.Minimum,
            QSizePolicy.Expanding
        )
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
        spacerItem3 = QSpacerItem(
            20,
            40,
            QSizePolicy.Minimum,
            QSizePolicy.Expanding
        )
        self.verticalLayout_5.addItem(spacerItem3)
        self.groupbox_layout.addWidget(self.groupbox_progress)
        self.run_layout.addLayout(self.groupbox_layout)
        spacerItem4 = QSpacerItem(
            20,
            40,
            QSizePolicy.Minimum,
            QSizePolicy.Expanding
        )
        self.run_layout.addItem(spacerItem4)
        self.btn_start = QPushButton("Start")
        self.btn_start.setStyleSheet(big_font)
        self.btn_start.clicked.connect(self.start)

        self.run_layout.addWidget(self.btn_start)
        self.run_layout_.addLayout(self.run_layout)
        self.stackedWidget.addWidget(self.run)
        self.explore = QWidget()

        self.verticalLayout_2 = QVBoxLayout(self.explore)

        # Explore

        self.explore_layout = QVBoxLayout()

        self.label_explore = QLabel("Explore")
        self.label_explore.setStyleSheet(logo_font)
        self.explore_layout.addWidget(self.label_explore)

        self.button_layout_explore = QHBoxLayout()
        self.verticalLayout_3 = QVBoxLayout()
        self.tabWidget = QTabWidget(self.explore)

        # Add files here.. select with dropdown columns
        self.explore_files = QComboBox()
        self.explore_files.setStyleSheet("QListView::item {height:20px;}")
        self.verticalLayout_3.addWidget(self.explore_files)

        self.explore_files.currentIndexChanged.connect(
            self.explore_file_selected
        )

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

        spacerItem5 = QSpacerItem(
            20,
            40,
            QSizePolicy.Minimum,
            QSizePolicy.Expanding
        )
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

        spacerItem6 = QSpacerItem(
            20,
            40,
            QSizePolicy.Minimum,
            QSizePolicy.Expanding
        )
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

        # Start with Experiment page
        self.stackedWidget.setCurrentIndex(0)

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
        # Load files again
        settings = self.read_settings()
        # Check which hdf files exist already and display them
        selectable = ["Select file.."]

        if 'file_paths' in settings['experiment'].keys():
            for _ in settings['experiment']['file_paths']:
                if _:
                    base, ext = os.path.splitext(_)
                    hdf_path = base+'.hdf'

                    if os.path.isfile(hdf_path):
                        selectable.append(hdf_path)

        if 'results_path' in settings['experiment'].keys():
            evidence_path = settings['experiment']['results_path']
            if evidence_path:
                if os.path.isfile(evidence_path):
                    selectable.append(evidence_path)

                self.explore_files.clear()
                self.explore_files.addItems(selectable)

    def page_help(self):
        self.stackedWidget.setCurrentIndex(4)

    def main_method_test(self):
        print('Calling main method')

    def read_settings(self):
        settings = self.settingsWidget.read_settings()

        if 'experiment' not in settings.keys():
            settings['experiment'] = {}

        files = self.file_selector.read_table()
        fasta_table = self.fasta_selector.read_table()

        paths = files['Filename'].values.tolist()

        paths = [_.replace("\\", "/") for _ in paths]

        settings['experiment']['file_paths'] = paths

        shortnames = files['Shortname'].values.tolist()

        if None in shortnames:
            logging.info(
                'Undefined shortnames found. Replacing with filename.'
            )

            for idx, _ in enumerate(paths):
                if not shortnames[idx]:
                    base, filename = os.path.split(paths[idx])
                    shortnames[idx] = filename

        settings['experiment']['shortnames'] = shortnames

        fractions = files['Fraction'].values.tolist()

        if None in fractions:
            logging.info(
                'None values in fractions found or fractions undefined. Ignoring fractions.'
            )
            fractions = []

        settings['experiment']['fractions'] = fractions

        fasta_paths = fasta_table['Filename'].values.tolist()

        fasta_paths = [_.replace("\\", "/") for _ in fasta_paths]
        settings['fasta']['fasta_paths'] = fasta_paths
        settings['experiment']['alphapept_version'] = VERSION_NO

        self.settings = settings

        return settings

    def explore_file_selected(self):
        file = self.explore_files.currentText()

        if os.path.isfile(file):
            with pd.HDFStore(file) as hdf:
                groups = hdf.keys()

            groups = [_[1:] for _ in groups]

            # Reset tab index
            self.tabWidget.clear()
            for group in groups:
                view = QTableView()
                model = pandasModel(pd.read_hdf(file, key=group))
                self.tabWidget.addTab(view, group)
                view.setModel(model)
                view.show()

    def load_settings(self):
        path, ext = QFileDialog.getOpenFileName(
            self, "Open settings file:", "", "Settings files (*.yaml)"
        )
        if path:
            with open(path, "r") as settings_file:
                # try:
                settings = yaml.load(settings_file, Loader=yaml.FullLoader)
                self.settingsWidget.set_settings(settings)
                ex_settings = settings['experiment']
                fasta_settings = settings['fasta']

                self.fasta_selector.set_table(pd.DataFrame(
                    [fasta_settings['fasta_paths']]).T
                )
                self.file_selector.set_table(
                    pd.DataFrame(
                        [
                            ex_settings['file_paths'],
                            ex_settings['shortnames'],
                            ex_settings['fractions']
                        ]
                    ).T
                )

                logging.info('Loaded settings from {}.'.format(path))
                # except Exception as e:
                    # logging.error('The following error occured loading the settings field: {}'.format(e))

    def save_settings(self):
        settings = self.read_settings()
        path, ext = QFileDialog.getSaveFileName(
            self, "Save settings to:", "", "Settings file (*.yaml)"
        )

        if path:
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

        self.read_settings()

        self.settingsWidget.disable_settings()

        self.btn_start.setText('Running..')
        self.btn_start.setEnabled(False)

        settings = self.read_settings()

        self.searchthread = searchThread(settings)

        self.searchthread.current_progress_update.connect(
            self.progress_current_changed
        )
        self.searchthread.global_progress_update.connect(
            self.progress_overall_changed
        )
        # self.searchthread.task_update.connect(self.current_step_changed)

        self.searchthread.start()

        self.searchthread.finished.connect(self.complete)

    def complete(self):

        self.btn_start.setText('Start')
        self.btn_start.setEnabled(True)

        self.movie.stop()
        # self.movie.setVisible(False)


def main(close=False):
    app = QApplication(sys.argv)
    app.setStyle(QStyleFactory.create("Fusion"))

    main_window = MainWindow()
    main_window.show()
    app.processEvents()

    def excepthook(type, value, tback):
        cancel_dialogs()
        message = "".join(traceback.format_exception(type, value, tback))
        errorbox = QMessageBox.critical(
            window,
            "An error occured",
            message
        )
        errorbox.exec_()
        sys.__excepthook__(type, value, tback)

    sys.excepthook = excepthook

    if close:
        sys.exit()
    else:
        sys.exit(app.exec_())


if __name__ == "__main__":

    main()
