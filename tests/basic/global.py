counter = 0
s1 = "s1"
s2 = "s2"
s3 = "s3"

def run():
    global counter
    global s1,s2,s3
    counter += 1
    print "run called " + str(counter) + " time(s)" + s1 + s2 + s3
    
run()
run()