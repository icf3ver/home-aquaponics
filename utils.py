import math

class WindowedLinkedList():
    # The default value is a floating point NaN array
    def __init__(self, window_size, default_val=None):
        self.window_size = window_size
        if default_val:
            self.ll = default_val
        else:
            self.ll = [float("NaN")] * window_size
    
    def push(self, e):
        self.ll = [e] + self.ll[:-1]
    
    def as_arr(self, e):
        return self.ll
