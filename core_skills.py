import random

rand_list = [ random.randrange(1,20) for i in range(10)]

list_comprehension_below_10 = [ num for num in rand_list if num < 10 ]

def find_below_10(num):
    if num < 10:
        return num
list_comprehension_below_10_with_filter = list(filter(find_below_10, rand_list))
