val = "hello"
class Bar(object):
    val = "goodbye"
    def notify(self):
        print val + ' ' + self.val
def run():
    Bar().notify()