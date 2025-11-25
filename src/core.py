# Silence basic-pitch logging
import logging
logging.basicConfig(level=logging.ERROR)
import io
from contextlib import redirect_stdout

import copy
import time
import numpy as np

from basic_pitch.inference import predict
from basic_pitch import ICASSP_2022_MODEL_PATH

from event_min_heap import EventMinHeap
from event_red_black_tree import EventRBTree

def sec_to_minsec(sec):
    """ Format seconds to minute:second """
    minute, second = divmod(sec, 60)
    return '%02d:%02d' % (minute, second)

def to_mono(data):
    """ Convert multi-channel audio to monophonic """
    if data.ndim > 1:
        data = data.mean(axis=1)
    return data

def to_events(input_path):
    """ Convert audio data to events """
    f = io.StringIO() # Silence basic-pitch logging
    with redirect_stdout(f):
        # predict returns a PrettyMIDI object containing transcribed MIDI data
        _, midi_data, _ = predict(
            input_path,
            ICASSP_2022_MODEL_PATH
        )

    events = []
    for inst in midi_data.instruments:
        for note in inst.notes:
            # Store as tuple: (Timestamp, Type, NoteNumber)
            # Type 1 = Note ON, Type 0 = Note OFF
            events.append((note.start, 1, note.pitch))
            events.append((note.end, 0, note.pitch))

    return events

def ds_comparison(events):
    """ Data structure comparisons """
    copy1, copy2, copy3 = [copy.deepcopy(events) for _ in range(3)]

    # Python built-in list sort, by Timestamp (item 0 in tuple)
    t0 = time.perf_counter()
    copy1.sort(key=lambda x: x[0])
    t1 = time.perf_counter() - t0

    # Self-implemented Min Heap
    t0 = time.perf_counter()
    heap = EventMinHeap()
    heap.build(copy2)
    heap_sorted_events = []
    while not heap.empty():
        heap_sorted_events.append(heap.pop())
    t2 = time.perf_counter() - t0

    # Self-implemented Red-Black Tree
    t0 = time.perf_counter()
    rbt = EventRBTree()
    for timestamp, evt_type, note in copy3:
        rbt.push(timestamp, evt_type, note)
    rbt_sorted_events = []
    while not rbt.empty():
        rbt_sorted_events.append(rbt.pop_next())
    t3 = time.perf_counter() - t0

    return copy1, [t1, t2, t3], [heap.key_comparisons, heap.swaps, rbt.key_comparisons, rbt.rotations]

def to_8_bit(events, sr):
    """ Re-synthesize sorted events into 8-bit style audio """
    dt = 1.0 / sr

    audio_buffer = []
    current_time = 0.0

    # Maps Note_Number -> Current_Phase
    active_voices = {}

    for timestamp, event_type, note_pitch in events:
        duration = timestamp - current_time

        if duration > 0:
            num_samples = int(duration * sr)
            if num_samples > 0:
                chunk = np.zeros(num_samples)

                if active_voices:
                    t = np.arange(num_samples) * dt

                    for pitch, phase in active_voices.items():
                        # Pitch-to-frequency conversion
                        freq = 440.0 * (2.0 ** ((pitch - 69) / 12.0))

                        # 8-Bit Square Wave
                        wave = np.sign(np.sin(2 * np.pi * freq * t + phase))
                        chunk += wave * 0.5  # Volume scaling

                        # Update phase to prevent clicking
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

    full_audio = np.concatenate(audio_buffer)

    # Normalize to prevent distortion
    max_val = np.max(np.abs(full_audio))
    if max_val > 0:
        full_audio = full_audio / max_val

    return full_audio
