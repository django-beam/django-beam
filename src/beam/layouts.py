class HTML:
    is_html = True

    def __init__(self, content):
        self.content = content


class VirtualField:
    is_virtual = True

    def __init__(self, verbose_name, callback):
        self.verbose_name = verbose_name
        self.callback = callback

    def get_value(self, obj=None):
        return self.callback(obj)
