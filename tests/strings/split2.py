x = str("a / b / c / d")

print x.split("/")
print x.split(" /")
print x.split(" / ")
print x.split(" / ", 0)
print x.split(" / ", 1)
print x.split(" / ", 2)

x = str("xxxxxxxxx")
print x.split("x", 0)
print x.split("x", 1)
print x.split("x", 2)
print x.split("x", 3)
print x.split("y")