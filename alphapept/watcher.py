#!/usr/bin/python

import sys
from PyQt5.QtCore import Qt, QSize, QThread, pyqtSignal
from PyQt5.QtWidgets import (QWidget, QLabel,
                             QVBoxLayout, QApplication, QPlainTextEdit, QPushButton)

import logging
import os
import time

root = logging.getLogger()
root.setLevel(logging.DEBUG)

handler = logging.StreamHandler(sys.stdout)
handler.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
root.addHandler(handler)

MINIMUM_FILE_SIZE = 100

with open("alphapept/__init__.py") as version_file:
    version = version_file.read().strip().split('__version__ = ')[1][1:-1]

def check_new_files(path):
    """
    Check for new files in folder
    """
    new_files = []

    for dirpath, dirnames, filenames in os.walk(path):

        for dirname in [d for d in dirnames if d.endswith('.d')]: #Bruker
            new_file = os.path.join(dirpath, dirname)
            base, ext = os.path.splitext(dirname)
            npz_path = os.path.join(dirpath, base+'.npz')
            hdf_path = os.path.join(dirpath, base+'.hdf')

            if (not os.path.exists(npz_path)) | (not os.path.exists(hdf_path)):
                new_files.append(new_file)

        for filename in [f for f in filenames if f.lower().endswith('.raw')]: #Thermo
            new_file = os.path.join(dirpath, filename)
            base, ext = os.path.splitext(filename)
            npz_path = os.path.join(dirpath, base+'.npz')
            hdf_path = os.path.join(dirpath, base+'.hdf')

            if (not os.path.exists(npz_path)) | (not os.path.exists(hdf_path)):
                new_files.append(new_file)

    return new_files

class QTextEditLogger(logging.Handler):
    def __init__(self, parent):
        super().__init__()
        self.widget = QPlainTextEdit(parent)
        self.widget.setReadOnly(True)

    def emit(self, record):
        msg = self.format(record)
        self.widget.appendPlainText(msg)
        self.widget.verticalScrollBar().setValue(self.widget.verticalScrollBar().maximum())


class WatchThread(QThread):
    signal = pyqtSignal('PyQt_PyObject')
    stats_signal = pyqtSignal('PyQt_PyObject')

    def __init__(self):
        QThread.__init__(self)
        self.path = ""

        self.files_processed = 0
        self.gb_processed = 0
        self.bruker_files = 0
        self.raw_files = 0
        self.failed = 0

        self.start_time = 0

    # run method gets called when we start the thread
    def run(self):

        self.start_time = time.time()
        report = self.signal.emit
        stats_update = self.stats_signal.emit
        path = self.path
        report('Started watching folder {}.'.format(path))
        self.running = True

        # Start processing new files
        import copy
        from alphapept.settings import load_settings
        settings = load_settings('default_settings.yaml')
        from alphapept.io import raw_to_npz
        from alphapept.feature_finding import find_and_save_features

        refresh_rate = 5

        while self.running:
            new_files = check_new_files(path)

            stats_update('Files processed {} \t GB {:.2f} \t Bruker {} \t Raw {} \t Running time {:.2f} h'.format(self.files_processed, self.gb_processed, self.bruker_files, self.raw_files, (time.time()-self.start_time)/60/60))

            if len(new_files) > 0:
                report('Found file(s) withouth *.npz or *.hdf')

                for file in new_files:

                    report('Checking file {}.'.format(file))

                    if file.endswith('.d'):
                        #Bruker
                        to_check = os.path.join(file, 'analysis.tdf_bin')
                    else:
                        to_check = file

                    filesize = os.path.getsize(to_check)

                    writing = True
                    while writing:
                        time.sleep(1)
                        report('Checking Filesize: {:,} Bytes.'.format(filesize))
                        new_filesize = os.path.getsize(to_check)
                        if filesize == new_filesize:
                            writing  = False
                        else:
                            filesize = new_filesize

                    if filesize/1024/1024 > MINIMUM_FILE_SIZE: #bytes, kbytes, mbytes

                        file_set = copy.deepcopy(settings)

                        base, ext = os.path.splitext(file)
                        npz_path = base +'.npz'
                        hdf_path = base +'.hdf'
                        to_process = (file, file_set)

                        if not os.path.exists(npz_path):
                            report('File conversion for file {}.'.format(file))
                            raw_to_npz(to_process)
                            report('Complete.')
                        else:
                            report('*.npz exists for {}'.format(file))

                        if not os.path.exists(hdf_path):
                            report('Feature finding for file {}.'.format(file))
                            try:
                                find_and_save_features(to_process)
                            except FileNotFoundError:
                                self.failed += 1
                            report('Complete.')
                        else:
                            report('*.hdf exists for {}'.format(file))

                        self.files_processed +=1
                        self.gb_processed += filesize / 1024**3
                        if file.endswith('.d'):
                            self.bruker_files += 1
                        else:
                            self.raw_files += 1
                        stats_update('Files processed {} \t {:.2f} GB \t Bruker {} \t Raw {} \t Fail {} \t Running time {:.2f} h'.format(self.files_processed, self.gb_processed, self.bruker_files, self.raw_files, self.failed, (time.time()-self.start_time)/60/60))

            time.sleep(refresh_rate)

    def stop(self):
        self.running = False


class Watcher(QWidget):

    def __init__(self):
        super().__init__()
        self.initUI()
        self.setAcceptDrops(True)
        self.dragMoveEvent = self.dragEnterEvent


    def initUI(self):

        self.setMinimumSize(QSize(600, 200))

        self.log_textbox = QTextEditLogger(self)
        self.log_textbox.setFormatter(
            logging.Formatter("%(asctime)s - %(message)s", "%Y-%m-%d %H:%M:%S")
        )
        logging.getLogger().addHandler(self.log_textbox)
        logging.getLogger().setLevel(logging.INFO)


        vbox = QVBoxLayout()
        self.push_button = QPushButton('Drop Folder')
        self.push_button.setEnabled(False)
        self.stats = QLabel()
        vbox.addWidget(self.push_button)
        vbox.addWidget(self.log_textbox.widget)
        vbox.addWidget(self.stats)

        self.setLayout(vbox)

        self.setWindowTitle('AlphaPept FileWatcher {}'.format(version))

        self.push_button.clicked.connect(self.watch_folder)
        self.watch_thread = WatchThread()  # This is the thread object
        # Connect the signal from the thread to the finished method
        self.watch_thread.signal.connect(self.thread_output)
        self.watch_thread.stats_signal.connect(self.stats_update)

        self.show()

    def watch_folder(self):
        if self.push_button.text() == 'Monitor':
            self.push_button.setText('Stop')
            self.watch_thread.path = self.path
            self.watch_thread.start()

        elif self.push_button.text() == 'Stop':
            self.watch_thread.stop()
            logging.info('Stopped')
            self.push_button.setText('Monitor')

    def finished(self):
        logging.info('Task finished')

    def thread_output(self, signal):
        logging.info(signal)

    def stats_update(self, signal):
        self.stats.setText(signal)

    def path_from_drop(self, event):
        url = event.mimeData().urls()[0]
        path = url.toLocalFile()
        return path

    def drop_has_valid_url(self, event):
        if not event.mimeData().hasUrls():
            return False
        path = self.path_from_drop(event)
        if os.path.isdir(path):
            return True
        else:
            return False

    def dragEnterEvent(self, event):
        if self.drop_has_valid_url(event):
            event.accept()
        else:
            event.ignore()

    def dropEvent(self, event):
        """ Loads  when dropped into the scene """

        path = self.path_from_drop(event)
        logging.info("Set path to {}.".format(path))

        self.path = path

        self.push_button.setText('Monitor')
        self.push_button.setEnabled(True)


def main():
    app = QApplication(sys.argv)
    ex = Watcher()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
