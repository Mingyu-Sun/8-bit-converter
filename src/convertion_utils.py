import time, copy, heapq

import numpy as np
import librosa

from frame_min_heap import FrameMinHeap
from frame_red_black_tree import FrameRBTree

def sec_to_minsec(sec):
    minute, second = divmod(sec, 60)
    return '%02d:%02d' % (minute, second)

class NoteEvent:
    def __init__(self, start, end, note):
        self.start = start
        self.end = end
        self.note = note

def to_mono(data):
    if data.ndim > 1:
        data = data.mean(axis=1)
    return data

def square_wave(f, t):
    return np.sign(np.sin(2 * np.pi * f * t))

def f0_extraction(data, sr, frame_length, hop_length):
    f0, _, _ = librosa.pyin(
        data,
        fmin=87.3,        # frequency of F2
        fmax=1046.5,      # frequency of C6
        sr=sr,
        frame_length=frame_length,
        hop_length=hop_length,
    )
    times = librosa.frames_to_time(np.arange(len(f0)), sr=sr, hop_length=hop_length)
    return f0, times

def to_midi(f0):
    # Convert Hz -> MIDI, keep only voiced frames
    midi = np.full_like(f0, fill_value=np.nan, dtype=float)
    voiced_idx = ~np.isnan(f0)
    midi[voiced_idx] = librosa.hz_to_midi(f0[voiced_idx])

    # Round to nearest semitone
    return np.round(midi)

def frames_to_events(midi, times, min_note_dur, sr):
    events = []
    current_note = None
    current_start = None

    for i, note in enumerate(midi):
        t = times[i]
        if np.isnan(note):
            # end current note if any
            if current_note is not None:
                events.append((current_start, t, current_note))
                current_note = None
                current_start = None
            continue

        if current_note is None:
            # start new note
            current_note = note
            current_start = t
        else:
            # if note changed, close old, start new
            if note != current_note:
                events.append((current_start, t, current_note))
                current_note = note
                current_start = t

    # close tail
    if current_note is not None:
        events.append((current_start, times[-1], current_note))

    # filter out super-short notes
    filtered_events = []
    for start, end, note in events:
        dur = end - start
        if dur >= min_note_dur:
            filtered_events.append((start, end, int(note)))

    events = filtered_events

    note_events = []
    for start, end, midi_note in events:
        start_sample = int(start * sr)
        end_sample = int(end * sr)
        note_events.append(
            NoteEvent(start_sample, end_sample, midi_note)
        )

    return note_events

def synthesize_event(out, ev, sr, square_amp):
    freq = librosa.midi_to_hz(ev.note)
    start_sample = max(0, ev.start)
    end_sample = min(len(out), ev.end)
    if end_sample <= start_sample:
        return

    n = end_sample - start_sample
    t = np.arange(n) / sr
    wave = square_wave(freq, t) * square_amp
    if n > 10:
        fade_len = min(200, n // 4)
        fade_in = np.linspace(0, 1, fade_len)
        fade_out = np.linspace(1, 0, fade_len)
        wave[:fade_len] *= fade_in
        wave[-fade_len:] *= fade_out

    out[start_sample:end_sample] += wave

def synthesize_list(out, note_events, sr, square_amp):
    for ev in note_events:
        synthesize_event(out, ev, sr, square_amp)
    return out

def sort_heapq(frames):
    heapq.heapify(frames)

    times_sorted = []
    midi_sorted  = []
    while len(frames):
        t, m = heapq.heappop(frames)
        times_sorted.append(t)
        midi_sorted.append(m)

def sort_min_heap(frames):
    heap = FrameMinHeap()

    heap.build(frames)

    times_sorted = []
    midi_sorted  = []
    while not heap.empty():
        t, m = heap.pop()
        times_sorted.append(t)
        midi_sorted.append(m)

    return heap.key_comparisons, heap.swaps

def sort_rbt(frames):
    rbt = FrameRBTree()

    for t, m in frames:
        rbt.push(t, m)

    times_sorted = []
    midi_sorted  = []
    while not rbt.empty():
        t, m = rbt.pop_next()
        times_sorted.append(t)
        midi_sorted.append(m)

    return rbt.key_comparisons, rbt.rotations

def ds_comparison(unordered_frames):
    copy1 = copy.deepcopy(unordered_frames)
    copy2 = copy.deepcopy(unordered_frames)
    copy3 = copy.deepcopy(unordered_frames)

    t0 = time.perf_counter()
    sort_heapq(copy1)
    t1 = time.perf_counter() - t0

    t0 = time.perf_counter()
    num_comp_2, num_swap_2 = sort_min_heap(copy2)
    t2 = time.perf_counter() - t0

    t0 = time.perf_counter()
    num_comp_3, num_rot_3 = sort_rbt(copy3)
    t3 = time.perf_counter() - t0

    return [t1 * 1000, t2 * 1000, t3 * 1000, num_comp_2, num_swap_2, num_comp_3, num_rot_3]