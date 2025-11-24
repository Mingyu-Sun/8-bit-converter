import sys
import numpy as np
import soundfile as sf

from basic_pitch.inference import predict
from basic_pitch import ICASSP_2022_MODEL_PATH

from PyQt6 import QtWidgets

# Run the following command to re-generate updated GUI: pyuic6 mainwindow.ui -o main_window.py
from main_window import Ui_MainWindow


""" ==================== Config ==================== """
INPUT_FILE = "../input/1.wav"
OUTPUT_PATH = "../output/1.wav"
OUTPUT_SR = 44100

class MainWindow(QtWidgets.QMainWindow, Ui_MainWindow):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setupUi(self)


if __name__ == "__main__":
    # app = QtWidgets.QApplication(sys.argv)
    #
    # window = MainWindow()
    # window.show()
    # app.exec()

    data, sr= sf.read(INPUT_FILE)

    # convert multi-channel audio to monophonic
    if data.ndim > 1:
        data = data.mean(axis=1)

    # predict returns a PrettyMIDI object directly in the second argument
    _, midi_data, _ = predict(
        INPUT_FILE,
        ICASSP_2022_MODEL_PATH
    )

    events = []
    for inst in midi_data.instruments:
        for note in inst.notes:
            # Store as tuple: (Time, Type, NoteNumber)
            # Type 1 = Note ON, Type 0 = Note OFF
            events.append((note.start, 1, note.pitch))
            events.append((note.end, 0, note.pitch))

    # Sort by timestamp (item 0 in tuple).
    events.sort(key=lambda x: x[0])

    dt = 1.0 / OUTPUT_SR

    audio_buffer = []
    current_time = 0.0

    # "active_voices" replaces the custom Tree/Node structure.
    # maps Note_Number -> Current_Phase
    active_voices = {}

    # Iterate through the sorted timeline
    for timestamp, event_type, note_pitch in events:

        # A. Generate audio for the gap between the last event and this one
        duration = timestamp - current_time

        if duration > 0:
            num_samples = int(duration * OUTPUT_SR)
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

    # Write out output audio file
    sf.write(OUTPUT_PATH, full_audio, OUTPUT_SR)






