from foo import *
from bar import *

try:
    print foo_
except NameError:
    print "passed foo"
print _foo
print __foo
print ___foo

print bar
try:
    print _bar
except NameError:
    print "passed _bar"
try:
    print __bar
except NameError:
    print "passed __bar"
try:
    print ___bar
except NameError:
    print "passed ___bar"