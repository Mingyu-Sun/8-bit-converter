import os
import soundfile as sf

from core import *

from PyQt6 import QtCore, QtWidgets, QtMultimedia
import pyqtgraph as pg

# Run the following command to re-generate updated GUI: pyuic6 src/mainwindow.ui -o src/main_window.py
from main_window import Ui_MainWindow


""" ==================== Helper ==================== """
def plot_data(waveform, data, sr):
    scene = QtWidgets.QGraphicsScene()
    waveform.setScene(scene)

    plot = pg.PlotWidget(show=True)
    plot.getPlotItem().hideAxis('bottom')
    plot.getPlotItem().hideAxis('left')

    y = data
    n = len(y)
    t = np.arange(n) / sr

    plot.plot(t, y)

    plot.setXRange(t[0], t[-1])
    plot.setYRange(-1.05, 1.05)

    vb = plot.getPlotItem().getViewBox()
    vb.setMouseEnabled(y=False)

    proxy_widget = QtWidgets.QGraphicsProxyWidget()
    proxy_widget.setWidget(plot)
    scene.addItem(proxy_widget)
    proxy_widget.resize(565, 160)
    plot.resize(565, 160)

    return scene

class MainWindow(QtWidgets.QMainWindow, Ui_MainWindow):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setupUi(self)

        """ ==================== Data ==================== """
        self.INPUT_PATH = ""
        self.INPUT_DATA = None
        self.INPUT_SR = None
        self.OUTPUT_PATH = ""
        self.OUTPUT_DATA = None
        self.OUTPUT_SR = None
        self.OUTPUT_FORMAT = ""
        self.scene = None

        """ ==================== Audio Player ==================== """
        self.player = QtMultimedia.QMediaPlayer()
        self.audio_output = QtMultimedia.QAudioOutput()
        self.player.setAudioOutput(self.audio_output)
        self.audio_output.setVolume(50)
        self.player.mediaStatusChanged.connect(self.handle_media_status_changed)

        """ ==================== Signals ==================== """
        self.input_file_btn.clicked.connect(self.choose_file)
        self.convert_btn.clicked.connect(self.convert)
        self.playpause_btn.clicked.connect(self.play_pause)

    def choose_file(self):
        self.INPUT_PATH, _ = QtWidgets.QFileDialog.getOpenFileName(
            self,
            "Select a File",
            "~/input",
            "Audio (*.wav *.mp3 *.flac)"
        )
        if self.INPUT_PATH:
            self.INPUT_DATA, self.INPUT_SR = sf.read(self.INPUT_PATH)

            self.INPUT_DATA = to_mono(self.INPUT_DATA)

            if self.OUTPUT_SR:
                self.OUTPUT_DATA = None
                self.OUTPUT_SR = None
                self.scene.clear()

            self.input_file_btn.setText(os.path.basename(self.INPUT_PATH))
            self.input_sr.setText(str(self.INPUT_SR))
            self.length.setText(f"{sec_to_minsec(len(self.INPUT_DATA) / self.INPUT_SR)}")
            self.convert_btn.setEnabled(True)

            self.plot_orig()

    def convert(self):
        if not self.INPUT_SR:
            return

        self.OUTPUT_SR = int(self.target_SR.currentText())
        self.OUTPUT_FORMAT = self.output_format.currentText()
        self.OUTPUT_PATH = f"{os.path.splitext(os.path.basename(self.INPUT_PATH))[0]}_8bit{self.OUTPUT_FORMAT}"

        events = to_events(self.INPUT_PATH)
        self.num_data_points.setText(f"Number of Audio Events (N) = {len(events)}")

        sorted_events, runtime, num_of_operation = ds_comparison(events)

        self.runtime1.setText(f"Runtime: {runtime[0] * 1000:.2f} ms")
        self.runtime2.setText(f"Runtime: {runtime[1] * 1000:.2f} ms")
        self.runtime3.setText(f"Runtime: {runtime[2] * 1000:.2f} ms")
        self.num_comp_2.setText(f"# comparisons: {num_of_operation[0]}")
        self.num_swap_2.setText(f"# swaps: {num_of_operation[1]}")
        self.num_comp_3.setText(f"# comparisons: {num_of_operation[2]}")
        self.num_rot_3.setText(f"# rotations: {num_of_operation[3]}")

        self.OUTPUT_DATA = to_8_bit(sorted_events, self.OUTPUT_SR)

        self.plot_rslt()
        self.playpause_btn.setEnabled(True)
        self.playpause_btn.setText("Play")
        self.audio_input.setEnabled(True)

        sf.write(self.OUTPUT_PATH, self.OUTPUT_DATA, self.OUTPUT_SR)

    def plot_orig(self):
        plot_data(self.waveform_orig, self.INPUT_DATA, self.INPUT_SR)

    def plot_rslt(self):
        self.scene = plot_data(self.waveform_rslt, self.OUTPUT_DATA, self.OUTPUT_SR)

    def handle_media_status_changed(self, status):
        if status == QtMultimedia.QMediaPlayer.MediaStatus.EndOfMedia:
            self.playpause_btn.setText("Play")
            self.playpause_btn.setChecked(False)

    def play_pause(self):
        if self.audio_input.currentText() == "Original":
            filepath = self.INPUT_PATH
        else:
            filepath = self.OUTPUT_PATH
        self.player.setSource(QtCore.QUrl.fromLocalFile(filepath))
        if self.playpause_btn.isChecked():
            self.playpause_btn.setText("Pause")
            self.player.play()
        else:
            self.playpause_btn.setText("Play")
            self.player.pause()

def run_gui():
    """ GUI entry point """
    app = QtWidgets.QApplication([])

    window = MainWindow()
    window.show()
    app.exec()
