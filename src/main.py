import os, sys
import soundfile as sf

from PyQt6 import QtCore, QtWidgets, QtMultimedia
import pyqtgraph as pg

from main_window import Ui_MainWindow

from convertion_utils import *

""" ==================== Config ==================== """
FRAME_LENGTH = 2048
HOP_LENGTH = 512     # default hop length for re-synthesize
SQUARE_AMP = 0.3     # output loudness
MIN_NOTE_DUR = 0.05   # in seconds, to drop short blips


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

    plot.hideButtons()
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
        self.LENGTH = None
        self.OUTPUT_PATH = ""
        self.OUTPUT_DATA = None
        self.OUTPUT_SR = None
        self.OUTPUT_FORMAT = ""
        self.MIDI = None
        self.TIMES = None
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
        self.analyze_btn.clicked.connect(self.analyze_runtime)

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
            self.LENGTH = len(self.INPUT_DATA) / self.INPUT_SR

            if self.OUTPUT_SR:
                self.OUTPUT_DATA = None
                self.OUTPUT_SR = None
                self.scene.clear()

            self.input_file_btn.setText(os.path.basename(self.INPUT_PATH))
            self.input_sr.setText(str(self.INPUT_SR))
            self.length.setText(f"{sec_to_minsec(self.LENGTH)}")
            self.convert_btn.setEnabled(True)

            self.plot_orig()

    def convert(self):
        if not self.INPUT_SR:
            return

        self.OUTPUT_SR = int(self.target_SR.currentText())
        self.OUTPUT_FORMAT = self.output_format.currentText()
        self.OUTPUT_PATH = f"./output/{os.path.splitext(os.path.basename(self.INPUT_PATH))[0]}_8bit{self.OUTPUT_FORMAT}"

        f0, self.TIMES = f0_extraction(self.INPUT_DATA, self.INPUT_SR, FRAME_LENGTH, HOP_LENGTH)
        self.MIDI = to_midi(f0)

        note_events = frames_to_events(self.MIDI, self.TIMES, MIN_NOTE_DUR, self.INPUT_SR)

        out_list = np.zeros_like(self.INPUT_DATA)
        out_list = synthesize_list(out_list, note_events, self.INPUT_SR, SQUARE_AMP)

        self.OUTPUT_DATA = out_list

        max_abs = np.max(np.abs(self.OUTPUT_DATA))
        if max_abs > 1.0:
            self.OUTPUT_DATA = self.OUTPUT_DATA / max_abs

        self.plot_rslt()
        self.playpause_btn.setEnabled(True)
        self.playpause_btn.setText("Play")
        self.audio_input.setEnabled(True)
        self.analyze_btn.setEnabled(True)

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

    def analyze_runtime(self):
        """ Analyze the runtime of sorting unordered frames using different data structures """
        if not self.OUTPUT_SR:
            return

        n = len(self.MIDI)
        self.num_data_points.setText(f"Number of Audio Frames (N) = {n}")

        indices = np.random.permutation(n)
        unordered_frames = [(self.TIMES[i], self.MIDI[i]) for i in indices]

        li = ds_comparison(unordered_frames)

        self.runtime1.setText(f"Runtime: {li[0]:.2f} ms")
        self.runtime2.setText(f"Runtime: {li[1]:.2f} ms")
        self.runtime3.setText(f"Runtime: {li[2]:.2f} ms")
        self.num_comp_2.setText(f"# comparisons: {li[3]}")
        self.num_swap_2.setText(f"# swaps: {li[4]}")
        self.num_comp_3.setText(f"# comparisons: {li[5]}")
        self.num_rot_3.setText(f"# rotations: {li[6]}")


if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)

    window = MainWindow()
    window.show()
    app.exec()

