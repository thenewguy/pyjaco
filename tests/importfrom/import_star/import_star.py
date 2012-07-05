from foo import *

run()
print msg

def run():
	print "not foo run"

msg = "not foo msg"
	
run()
print msg