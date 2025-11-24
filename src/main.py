import os, sys, copy, time
import numpy as np
import soundfile as sf

from basic_pitch.inference import predict
from basic_pitch import ICASSP_2022_MODEL_PATH

from PyQt6 import QtCore, QtWidgets, QtMultimedia
import pyqtgraph as pg
# Run the following command to re-generate updated GUI: pyuic6 mainwindow.ui -o main_window.py
from src.main_window import Ui_MainWindow

from event_min_heap import EventMinHeap
from event_red_black_tree import EventRBTree

""" ==================== Helper ==================== """
def sec_to_minsec(sec):
    minute, second = divmod(sec, 60)
    return '%02d:%02d' % (minute, second)

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

    def choose_file(self):
        self.INPUT_PATH, _ = QtWidgets.QFileDialog.getOpenFileName(
            self,
            "Select a File",
            "~/input",
            "Audio (*.wav *.mp3 *.flac)"
        )
        if self.INPUT_PATH:
            self.INPUT_DATA, self.INPUT_SR = sf.read(self.INPUT_PATH)

            # convert multi-channel audio to monophonic
            if self.INPUT_DATA.ndim > 1:
                self.INPUT_DATA = self.INPUT_DATA.mean(axis=1)

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

        # predict returns a PrettyMIDI object containing transcribed MIDI data
        _, midi_data, _ = predict(
            self.INPUT_PATH,
            ICASSP_2022_MODEL_PATH
        )

        events = []
        for inst in midi_data.instruments:
            for note in inst.notes:
                # Store as tuple: (Timestamp, Type, NoteNumber)
                # Type 1 = Note ON, Type 0 = Note OFF
                events.append((note.start, 1, note.pitch))
                events.append((note.end, 0, note.pitch))

        self.num_data_points.setText(f"Number of Audio Frames (N) = {len(events)}")

        copy1, copy2, copy3 = [copy.deepcopy(events) for _ in range(3)]

        ''' data structure comparisons '''
        # Python built-in list sort, by Timestamp (item 0 in tuple)
        t0 = time.perf_counter()
        copy1.sort(key=lambda x: x[0])
        t1 = time.perf_counter() - t0
        self.runtime1.setText(f"Runtime: {t1 * 1000:.2f} ms")

        # Self-implemented Min Heap
        t0 = time.perf_counter()
        heap = EventMinHeap()
        heap.build(copy2)
        heap_sorted_events = []
        while not heap.empty():
            heap_sorted_events.append(heap.pop())
        t2 = time.perf_counter() - t0
        self.runtime2.setText(f"Runtime: {t2 * 1000:.2f} ms")
        self.num_comp_2.setText(f"# comparisons: {heap.key_comparisons}")
        self.num_swap_2.setText(f"# swaps: {heap.swaps}")

        # Self-implemented Red-Black Tree
        t0 = time.perf_counter()
        rbt = EventRBTree()
        for timestamp, evt_type, note in copy3:
            rbt.push(timestamp, evt_type, note)
        rbt_sorted_events = []
        while not rbt.empty():
            rbt_sorted_events.append(rbt.pop_next())
        t3 = time.perf_counter() - t0

        self.runtime3.setText(f"Runtime: {t3 * 1000:.2f} ms")
        self.num_comp_3.setText(f"# comparisons: {rbt.key_comparisons}")
        self.num_rot_3.setText(f"# rotations: {rbt.rotations}")

        dt = 1.0 / self.OUTPUT_SR

        audio_buffer = []
        current_time = 0.0

        # Maps Note_Number -> Current_Phase
        active_voices = {}

        # Iterate through the sorted timeline
        for timestamp, event_type, note_pitch in copy1:

            # A. Generate audio for the gap between the last event and this one
            duration = timestamp - current_time

            if duration > 0:
                num_samples = int(duration * self.OUTPUT_SR)
                if num_samples > 0:
                    # Create an array filled with zero for this chunk
                    chunk = np.zeros(num_samples)

                    if active_voices:
                        t = np.arange(num_samples) * dt

                        for pitch, phase in active_voices.items():
                            # pitch-to-frequency conversion
                            freq = 440.0 * (2.0 ** ((pitch - 69) / 12.0))

                            # 8-Bit Square Wave
                            wave = np.sign(np.sin(2 * np.pi * freq * t + phase))
                            chunk += wave * 0.1  # Volume scaling

                            # Update phase for the next chunk to prevent clicking
                            active_voices[pitch] += 2 * np.pi * freq * (num_samples * dt)
                            active_voices[pitch] %= (2 * np.pi)

                    audio_buffer.append(chunk)
                    current_time += (num_samples * dt)

            if event_type == 1:  # Note ON
                if note_pitch not in active_voices:
                    active_voices[note_pitch] = 0.0  # Start phase at 0
            else:  # Note OFF
                if note_pitch in active_voices:
                    del active_voices[note_pitch]

        # Concatenate all chunks
        full_audio = np.concatenate(audio_buffer)

        # Normalize (prevent distortion)
        max_val = np.max(np.abs(full_audio))
        if max_val > 0:
            full_audio = full_audio / max_val

        self.OUTPUT_DATA = full_audio

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



if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)

    window = MainWindow()
    window.show()
    app.exec()






