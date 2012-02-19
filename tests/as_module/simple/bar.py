val = "hello"
class Bar(object):
    val = "goodbye"
    def notify(self):
        print val + ' ' + self.val
if __name__ == "__main__":
    Bar().notify()