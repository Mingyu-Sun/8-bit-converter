class FrameMinHeap:
    def __init__(self):
        self._heap = []

        # instrumentation counters
        self.key_comparisons = 0
        self.swaps = 0
        self.pushes = 0
        self.pops = 0

    # ========== helpers ==========
    def _parent(self, i):
        return (i - 1) // 2
    def _leftchild(self, i):
        return 2 * i + 1
    def _rightchild(self, i):
        return 2 * i + 2
    def _less(self, i, j):
        self.key_comparisons += 1
        return self._heap[i][0] < self._heap[j][0]
    def _swap(self, i, j):
        self.swaps += 1
        self._heap[i], self._heap[j] = self._heap[j], self._heap[i]

    # ========== heapify up/down ==========
    def _heapify_up(self, idx):
        while idx > 0:
            parent = self._parent(idx)
            if self._less(idx, parent):
                self._swap(parent, idx)
                idx = parent
            else:
                break

    def _heapify_down(self, idx):
        n = len(self._heap)
        while True:
            left = self._leftchild(idx)
            right = self._rightchild(idx)
            smallest = idx

            if (left < n) and (self._less(left, smallest)):
                smallest = left
            if (right < n) and (self._less(right, smallest)):
                smallest = right

            if smallest == idx:
                break

            self._swap(idx, smallest)
            idx = smallest

    # ========== public methods ==========
    def __len__(self):
        return len(self._heap)

    def build(self, frames):
        self._heap = [(t, m) for (t, m) in frames]
        n = len(self._heap)
        # last parent index = (n // 2) - 1
        for i in range(n // 2 - 1, -1, -1):
            self._heapify_down(i)

    def push(self, time, midi):
        self.pushes += 1
        self._heap.append((time, midi))
        self._heapify_up(len(self._heap) - 1)

    def pop(self):
        if not self._heap:
            raise IndexError("heap is empty")
        self.pops += 1
        root = self._heap[0]
        last = self._heap.pop()
        if self._heap:
            self._heap[0] = last
            self._heapify_down(0)
        return root

    def peek(self):
        if not self._heap:
            raise IndexError("heap is empty")
        return self._heap[0]

    def empty(self):
        return len(self._heap) == 0

    def reset_counters(self):
        self.key_comparisons = 0
        self.swaps = 0
        self.pushes = 0
        self.pops = 0