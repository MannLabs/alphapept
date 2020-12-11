from PyQt5.QtCore import QDir, QThread, QProcess, pyqtSignal, Qt, QAbstractTableModel, QCoreApplication
from PyQt5.QtWidgets import QMessageBox, QListWidget, QDialog, QFileDialog, QTableWidgetItem, QPlainTextEdit, QSpinBox, QCheckBox, QDoubleSpinBox, QTreeWidget, QTreeWidgetItem, QComboBox, QAbstractScrollArea, QPushButton, QTableWidget, QWidget, QVBoxLayout, QLabel
from PyQt5.QtCore import pyqtSlot


import os

from functools import partial

import alphapept.interface

import yaml
from time import sleep, time
import logging
import pandas as pd
import qdarkstyle

import threading, queue


_this_file = os.path.abspath(__file__)
_this_directory = os.path.dirname(_this_file)

SETTINGS_TEMPLATE_PATH = os.path.join(_this_directory,  "settings_template.yaml")
LOGO_PATH = os.path.join(_this_directory, "img", "logo_200px.png")
ICON_PATH = os.path.join(_this_directory, "img", "logo.ico")
BUSY_INDICATOR_PATH = os.path.join(_this_directory, "img", "busy_indicator.gif")


if not os.path.isfile(ICON_PATH):
    raise FileNotFoundError('Logo not found - Path {}'.format(ICON_PATH))

if not os.path.isfile(BUSY_INDICATOR_PATH):
    raise FileNotFoundError(
        'Busy Indicator - Path {}'.format(BUSY_INDICATOR_PATH)
    )

class FileSelector(QWidget):

    def __init__(self, header):
        super().__init__()
        self.title = 'FileSelection'
        self.left = 0
        self.top = 0
        self.width = 600
        self.height = 200
        self.files = []
        self.header = header
        self.setAcceptDrops(True)
        self.initUI()

    def initUI(self):
        self.setWindowTitle(self.title)
        self.setGeometry(self.left, self.top, self.width, self.height)
        self.createTable()

        # Add box layout, add table to box layout and add box layout to widget
        self.layout = QVBoxLayout()
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)

        self.layout.addWidget(self.tableWidget)
        self.setLayout(self.layout)

        # Show widget
        self.show()

    def createTable(self):
        # Create table
        HEADER_LABELS = self.header
        HEADER_LABELS.append("Remove")

        self.tableWidget = QTableWidget()
        self.tableWidget.setRowCount(0)
        self.tableWidget.setColumnCount(len(HEADER_LABELS))
        self.tableWidget.setHorizontalHeaderLabels(HEADER_LABELS)
        self.tableWidget.setSizeAdjustPolicy(
            QAbstractScrollArea.AdjustToContents
        )
        self.tableWidget.doubleClicked.connect(self.on_click)

    @pyqtSlot()
    def on_click(self):
        for currentQTableWidgetItem in self.tableWidget.selectedItems():
            print(
                currentQTableWidgetItem.row(),
                currentQTableWidgetItem.column(),
                currentQTableWidgetItem.text()
            )

    def dragMoveEvent(self, event):
        event.accept()

    def path_from_drop(self, event):
        paths = []
        for url in event.mimeData().urls():
            path = url.toLocalFile()
            paths.append(path)
        return paths

    def drop_has_valid_url(self, event):
        if not event.mimeData().hasUrls():
            return False
        else:
            return True

    def dragEnterEvent(self, event):
        if self.drop_has_valid_url(event):
            event.accept()
        else:
            event.ignore()

    def dropEvent(self, event):
        """ Loads  when dropped into the scene """
        paths = self.path_from_drop(event)
        for path in paths:
            logging.info("Dropped file {}.".format(path))
        self.open(paths)

    def open(self, path):
        """
        Used in subclass
        """
        pass

    def set_files(self):
        n_files = len(self.files)
        self.tableWidget.setRowCount(n_files)
        self.remove_btns = []
        for i in range(n_files):
            self.tableWidget.setItem(i, 0, QTableWidgetItem(self.files[i]))
            btn = QPushButton('X')
            self.remove_btns.append(btn)
            self.tableWidget.setCellWidget(i, len(self.header)-1, btn)
            btn.clicked.connect(self.remove_file)

        self.tableWidget.resizeColumnsToContents()

    def remove_file(self):
        sending_button = self.sender()
        index = self.remove_btns.index(sending_button)
        del self.files[index]
        self.set_files()

    def read_table(self):
        table = []

        for row in range(self.tableWidget.rowCount()):
            entry = []
            for column in range(self.tableWidget.columnCount()-1):
                widgetItem = self.tableWidget.item(row, column)
                if (widgetItem and widgetItem.text):
                    entry.append(widgetItem.text())
                else:
                    entry.append(None)
            table.append(entry)

        return pd.DataFrame(table, columns=self.header[:-1])

    def set_table(self, table):
        self.remove_btns = []
        self.files = []
        columns = table.columns
        self.tableWidget.setRowCount(len(table))
        for row in range(len(table)):
            for idx, col in enumerate(columns):
                self.tableWidget.setItem(
                    row,
                    idx,
                    QTableWidgetItem(table.iloc[row, col])
                )
            btn = QPushButton('X')
            self.remove_btns.append(btn)
            btn.clicked.connect(self.remove_file)
            self.tableWidget.setCellWidget(row, idx+1, btn)

            self.files.append(table.iloc[row, 0])

        self.tableWidget.resizeColumnsToContents()


class RawFileSelector(FileSelector):
    def __init__(self, header):
        super().__init__(header)

    def open(self, paths):
        for path in paths:
            path = os.path.normpath(path)

            files = self.files

            new_files = []
            if path.endswith('.d'):
                new_files.append(path)
            if path.endswith('.raw'):
                new_files.append(path)
            for dirpath, dirnames, filenames in os.walk(path):
                for dirname in [d for d in dirnames if d.endswith('.d')]:  # Bruker
                    new_file = os.path.join(dirpath, dirname)
                    new_files.append(new_file)
                for filename in [
                    f for f in filenames if f.lower().endswith('.raw')
                ]:  # Thermo
                    new_file = os.path.join(dirpath, filename)
                    new_files.append(new_file)
            for new_file in new_files:
                if new_file not in files:
                    files.append(new_file)

            files.sort()
            self.files = files
            self.set_files()


class FastaFileSelector(FileSelector):
    def __init__(self, header):
        super().__init__(header)

    def open(self, paths):
        for path in paths:
            path = os.path.normpath(path)
            print(path)

            files = self.files
            new_files = []
            if path.endswith('.fasta'):
                new_files.append(path)

            for dirpath, dirnames, filenames in os.walk(path):
                for filename in [
                    f for f in filenames if f.lower().endswith('.fasta')
                ]:  # Thermo
                    new_file = os.path.join(dirpath, filename)
                    new_files.append(new_file)

            for new_file in new_files:
                if new_file not in files:
                    files.append(new_file)

            files.sort()
            self.files = files
            self.set_files()


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
        self.buffer = []
        self.worker = threading.Thread(target=self.write_log, daemon=True).start()

    def write_log(self):
        """
        PyQt does not display logs correctly when sending them too quickly.
        Collect multiple and update every time interval.
        """
        TIME = 0.1
        last = time()
        while True:
            now = time()
            if (now-last) > TIME:
                if len(self.buffer) > 0:
                    msg = [self.format(_) for _ in self.buffer]
                    self.buffer = []
                    msg = '\n'.join(msg)
                    self.widget.appendPlainText(msg)
                    self.widget.verticalScrollBar().setValue(
                        self.widget.verticalScrollBar().maximum()
                    )
                    last = now

    def emit(self, record):
        self.buffer.append(record)

class SmoothProgress(threading.Thread):
    """
    Worker to smooth progress output

    """
    def __init__ (self, callback):
        super().__init__(daemon=True)
        self.current_progress = 0
        self.new_progress = 0
        self.update_time = 2
        self.min_update_time = 0.2
        self.splits = 30
        self.callback = callback
        self.old_set = 0
        self.min_change = 0.001 #0.1%

    def run (self):
        sleep_time = self.update_time
        while True:
            sleep(sleep_time)

            if (self.new_progress == 1) or abs(self.current_progress-self.new_progress)<self.min_change:
                to_set = self.new_progress
                self.current_progress = self.new_progress
            else:
                delta = (self.new_progress - self.current_progress) / self.splits #move there in 60s

                time_multiplier = delta/self.min_change
                sleep_time = self.update_time/time_multiplier
                if sleep_time < self.min_update_time:
                    sleep_time = self.min_update_time

                self.current_progress = self.current_progress+self.min_change
                to_set = self.current_progress

            if self.old_set != to_set:
                self.callback(to_set)
                self.old_set = to_set

    def set_progress(self, progress):
        self.new_progress = progress

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
        self.progress = SmoothProgress(callback=self.global_progress_update.emit)
        self.progress.start()

    def update_current_progress(self, progress):
        self.current_progress_update.emit(progress)

    def update_global_progress(self, progress):
        self.global_progress_update.emit(progress)

    def update_task(self, task):
        self.task_update.emit(task)

    def run(self):
        logging.info('Starting SearchThread')

        try:
            alphapept.interface.run_complete_workflow(
                self.settings,
                logger_set = True,
                callback=self.update_current_progress,
                callback_overall = self.progress.set_progress,
                callback_task = self.update_task,
            )
        except Exception as e:
            logging.error('Error occured. {}'.format(e))


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


class SettingsEdit(QWidget):
    def __init__(self, fasta_selector = None, file_selector = None, results_path = None):
        super().__init__()
        self.setAcceptDrops(True)

        self.initUI()
        self.fasta_selector = fasta_selector
        self.file_selector = file_selector
        self.results_path = results_path

    def initUI(self):
        # Add box layout, add table to box layout and add box layout to widget
        self.layout = QVBoxLayout()
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)

        self.treeWidget = QTreeWidget()

        self.layout.addWidget(self.treeWidget)
        self.setLayout(self.layout)

        # Show widget
        self.show()
        self.init_tree()

    def path_from_drop(self, event):
        url = event.mimeData().urls()[0]
        path = url.toLocalFile()
        base, extension = os.path.splitext(path)
        return path, extension

    def drop_has_valid_url(self, event):
        if not event.mimeData().hasUrls():
            return False
        path, extension = self.path_from_drop(event)
        if extension.lower() not in [".yaml", ".hdf", ".raw", ".fasta"]:
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

        if extension == ".yaml":

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
                    text = widget.text()
                    if text == '':
                        text = None
                    settings[category][widget_name] = text
                elif isinstance(widget, QComboBox):
                    settings[category][widget_name] = widget.currentText()
                elif isinstance(widget, QListWidget):
                    item_list = [
                        str(
                            widget.item(i).text()
                        ) for i in range(widget.count())
                    ]
                    settings[category][widget_name] = item_list
                elif isinstance(widget, QCheckBox):
                    state = widget.checkState()
                    if state == 2:
                        state = True
                    else:
                        state = False
                    settings[category][widget_name] = state
                # elif isinstance(widget, QLabel):
                elif isinstance(widget, dict):
                    checked = []
                    for _ in widget.keys():
                        if widget[_].checkState(1) == Qt.Checked:
                            checked.append(_)
                    settings[category][widget_name] = checked
                else:
                    raise NotImplementedError(
                        "Widget class {} not supported.".format(
                            widget.__class__
                        )
                    )

        return settings

    def set_path(self, category, subcategory):
        filetype = self.settings_template[category][subcategory]["filetype"]

        filetype_str = "".join(["*." + _ + ", " for _ in filetype])[:-2]
        folder = self.settings_template[category][subcategory]["folder"]

        if folder:
            path = QFileDialog.getExistingDirectory(self, "Select directory")
        else:
            dialog = QFileDialog(self)
            dialog.setWindowTitle('Select path')
            dialog.setNameFilter(filetype_str)
            dialog.setDirectory(QDir.currentPath())
            dialog.setFileMode(QFileDialog.AnyFile)

            if dialog.exec_() == QDialog.Accepted:
                path = dialog.selectedFiles()[0]
                path, ext = os.path.splitext(path)
                if not ext:
                    ext = filetype[0]
                    path = path+'.'+ext
            else:
                path = None
        if path:
            self.categories[category]["widgets"][subcategory].setText(path)

    def init_tree(self):

        header = QTreeWidgetItem(["Parameter", "Value", "Description"])

        self.treeWidget.setHeaderItem(
            header
        )  # Another alternative is setHeaderLabels(["Tree","First",...])

        self.treeWidget.header().resizeSection(0, 300)
        self.treeWidget.header().resizeSection(1, 150)

        # Main Categories

        with open(SETTINGS_TEMPLATE_PATH, "r") as config_file:
            self.settings_template = yaml.load(
                config_file,
                Loader=yaml.FullLoader
            )

        self.categories = {}

        for category in self.settings_template.keys():
            if category != 'experiment':
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

                    elif type == "placeholder":
                        default_state = self.settings_template[category][subcategory][
                            "default"
                        ]
                        widgets[subcategory] = QLabel(default_state)

                    elif type == "list":
                        default_state = self.settings_template[category][subcategory][
                            "default"
                        ]
                        widgets[subcategory] = QListWidget()
                        widgets[subcategory].setMaximumHeight(40)

                        for _ in default_state:
                            widgets[subcategory].addItem(_)

                    else:
                        raise NotImplementedError('Category not implemented {} - {}'.format(category, subcategory))

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
                elif isinstance(widget, QListWidget):
                    widget.setEnabled(False)
                elif isinstance(widget, dict):
                    for _ in widget.keys():
                        widget[_].setFlags(Qt.NoItemFlags)
                else:
                    raise NotImplementedError(
                        "Widget class {} not supported.".format(
                            widget.__class__
                        )
                    )
    # def enable_settings(self):

    def set_settings(self, settings):
        for category in settings.keys():
            if category not in ['experiment', 'summary']:
                for subcategory in settings[category].keys():
                    if subcategory != 'fasta_paths':
                        value = settings[category][subcategory]
                        if subcategory in self.categories[category]["widgets"]:
                            widget = self.categories[category]["widgets"][subcategory]
                            if isinstance(widget, QSpinBox):
                                widget.setValue(value)
                            elif isinstance(widget, QDoubleSpinBox):
                                widget.setValue(value)
                            elif isinstance(widget, QPushButton):
                                widget.setText(value)
                            elif isinstance(widget, QListWidget):
                                for _ in value:
                                    widget.addItem(_)
                            elif isinstance(widget, QComboBox):
                                # Find and set
                                idx = widget.findText(value)
                                widget.setCurrentIndex(idx)
                            elif isinstance(widget, QCheckBox):
                                if value:
                                    widget.setCheckState(2)
                                else:
                                    widget.setCheckState(0)
                            elif isinstance(widget, dict):
                                for _ in widget.keys():
                                    widget[_].setCheckState(1, Qt.Unchecked)
                                if value:
                                    for _ in value:
                                        widget[_].setCheckState(1, Qt.Checked)

                            else:
                                raise NotImplementedError(
                                    "Cannot set widget class {}.".format(
                                        widget.__class__
                                    )
                                )

        if 'experiment' in settings:
            ex_settings = settings['experiment']
            self.file_selector.set_table(
                pd.DataFrame(
                    [
                        ex_settings['file_paths'],
                        ex_settings['shortnames'],
                        ex_settings['fractions']
                    ]
                ).T
            )

            self.results_path.setText(ex_settings['results_path'])

        if 'fasta' in settings:
            fasta_settings = settings['fasta']

            self.fasta_selector.set_table(pd.DataFrame(
                [fasta_settings['fasta_paths']]).T
            )



        QMessageBox.about(self, "Information", "Settings loaded.")
