import time
 
#First Method
def greet_them(people):
    for person in people:
        print("Hello Dear " + person + ". How are you?")
        time.sleep(0.5)
 
#Second Method
def assign_id(people):
    i = 1
    for person in people:
        print("Hey! {}, your id is {}.".format(person, i))
        i += 1
        time.sleep(0.5)
 
 
people = ['Richard', 'Dinesh', 'Elrich', 'Gilfoyle', 'Gevin']
 
t = time.time()
 
greet_them(people)
assign_id(people)
 
print("Woaahh!! My work is finished..")
print("I took " + str(time.time() - t))
