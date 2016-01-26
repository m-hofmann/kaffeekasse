class Event:
    pass


class Observable:
    def __init__(self):
        self.callbacks = []

    def register(self, callback):
        self.callbacks.append(callback)

    def unregister(self, callback):
        self.callbacks.remove(callback)

    def notify_all(self, event=None):
        for function in self.callbacks:
            function(event)
