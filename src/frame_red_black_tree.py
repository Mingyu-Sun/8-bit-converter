RED = True
BLACK = False

class RBNode:
    def __init__(self, time=None, midi=None, color=RED, left=None, right=None, parent=None):
        self.time = time
        self.midi = midi
        self.color = color
        self.left = left
        self.right = right
        self.parent = parent

class FrameRBTree:
    def __init__(self):
        self.NIL = RBNode(color=BLACK)
        self.NIL.left = self.NIL.right = self.NIL.parent = self.NIL
        self.root = self.NIL

        # instrumentation counters
        self.key_comparisons = 0
        self.rotations = 0
        self.inserts = 0
        self.deletes = 0

    # ========== helpers ==========
    def _less(self, t1, t2):
        self.key_comparisons += 1
        return t1 < t2

    def _minimum(self, node):
        while node.left != self.NIL:
            node = node.left
        return node

    # ========== rotations ==========
    def _left_rotate(self, x):
        self.rotations += 1
        y = x.right
        x.right = y.left
        if y.left != self.NIL:
            y.left.parent = x
        y.parent = x.parent
        if x.parent == self.NIL:
            self.root = y
        elif x == x.parent.left:
            x.parent.left = y
        else:
            x.parent.right = y
        y.left = x
        x.parent = y

    def _right_rotate(self, y):
        self.rotations += 1
        x = y.left
        y.left = x.right
        if x.right != self.NIL:
            x.right.parent = y
        x.parent = y.parent
        if y.parent == self.NIL:
            self.root = x
        elif y == y.parent.right:
            y.parent.right = x
        else:
            y.parent.left = x
        x.right = y
        y.parent = x

    # ========== insertion ==========
    def push(self, time, midi):
        self.inserts += 1
        node = RBNode(time=time, midi=midi, color=RED,
                      left=self.NIL, right=self.NIL, parent=self.NIL)

        y = self.NIL
        x = self.root
        while x != self.NIL:
            y = x
            # send equal times to the right subtree
            if self._less(node.time, x.time):
                x = x.left
            else:
                x = x.right
        node.parent = y
        if y == self.NIL:
            self.root = node
        elif self._less(node.time, y.time):
            y.left = node
        else:
            y.right = node

        # fix RB properties
        self._insert_fixup(node)

    def _insert_fixup(self, z):
        while z.parent.color == RED:
            if z.parent == z.parent.parent.left:
                y = z.parent.parent.right  # uncle
                if y.color == RED:
                    # case 1
                    z.parent.color = BLACK
                    y.color = BLACK
                    z.parent.parent.color = RED
                    z = z.parent.parent
                else:
                    if z == z.parent.right:
                        # case 2
                        z = z.parent
                        self._left_rotate(z)
                    # case 3
                    z.parent.color = BLACK
                    z.parent.parent.color = RED
                    self._right_rotate(z.parent.parent)
            else:
                # mirror
                y = z.parent.parent.left
                if y.color == RED:
                    z.parent.color = BLACK
                    y.color = BLACK
                    z.parent.parent.color = RED
                    z = z.parent.parent
                else:
                    if z == z.parent.left:
                        z = z.parent
                        self._right_rotate(z)
                    z.parent.color = BLACK
                    z.parent.parent.color = RED
                    self._left_rotate(z.parent.parent)
        self.root.color = BLACK

    # ========== deletion ==========
    def _transplant(self, u, v):
        if u.parent == self.NIL:
            self.root = v
        elif u == u.parent.left:
            u.parent.left = v
        else:
            u.parent.right = v
        v.parent = u.parent

    def _delete_node(self, z):
        y = z
        y_original_color = y.color
        if z.left == self.NIL:
            x = z.right
            self._transplant(z, z.right)
        elif z.right == self.NIL:
            x = z.left
            self._transplant(z, z.left)
        else:
            y = self._minimum(z.right)
            y_original_color = y.color
            x = y.right
            if y.parent == z:
                x.parent = y
            else:
                self._transplant(y, y.right)
                y.right = z.right
                y.right.parent = y
            self._transplant(z, y)
            y.left = z.left
            y.left.parent = y
            y.color = z.color
        if y_original_color == BLACK:
            self._delete_fixup(x)

    def _delete_fixup(self, x):
        while x != self.root and x.color == BLACK:
            if x == x.parent.left:
                w = x.parent.right
                if w.color == RED:
                    # case 1
                    w.color = BLACK
                    x.parent.color = RED
                    self._left_rotate(x.parent)
                    w = x.parent.right
                if w.left.color == BLACK and w.right.color == BLACK:
                    # case 2
                    w.color = RED
                    x = x.parent
                else:
                    if w.right.color == BLACK:
                        # case 3
                        w.left.color = BLACK
                        w.color = RED
                        self._right_rotate(w)
                        w = x.parent.right
                    # case 4
                    w.color = x.parent.color
                    x.parent.color = BLACK
                    w.right.color = BLACK
                    self._left_rotate(x.parent)
                    x = self.root
            else:
                # mirror
                w = x.parent.left
                if w.color == RED:
                    w.color = BLACK
                    x.parent.color = RED
                    self._right_rotate(x.parent)
                    w = x.parent.left
                if w.right.color == BLACK and w.left.color == BLACK:
                    w.color = RED
                    x = x.parent
                else:
                    if w.left.color == BLACK:
                        w.right.color = BLACK
                        w.color = RED
                        self._left_rotate(w)
                        w = x.parent.left
                    w.color = x.parent.color
                    x.parent.color = BLACK
                    w.left.color = BLACK
                    self._right_rotate(x.parent)
                    x = self.root
        x.color = BLACK

    # ========== public methods ==========
    def __len__(self):
        def _count(node):
            if node == self.NIL:
                return 0
            return 1 + _count(node.left) + _count(node.right)
        return _count(self.root)

    def pop_next(self):
        if self.root == self.NIL:
            raise IndexError("pop from empty RBTree")
        node = self._minimum(self.root)
        self.deletes += 1
        self._delete_node(node)
        return node.time, node.midi

    def empty(self) -> bool:
        return self.root == self.NIL

    def reset_counters(self):
        self.key_comparisons = 0
        self.rotations = 0
        self.inserts = 0
        self.deletes = 0
