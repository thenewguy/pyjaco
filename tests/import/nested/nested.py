import foo
s = foo.Foo()

import foo.bar
print s == foo.Foo()
print foo.bar.Bar()

import foo
print foo.bar.Bar()
print s == foo.Foo()