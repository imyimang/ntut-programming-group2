def myList():
    my_list1 = []
    my_list1.append(1)
    my_list1.append(2)
    my_list2 = [5.5,22,'Hi',3,99,22,66]
    my_list2[0]=3.3
    print(len(my_list1),sum(my_list1),my_list2.count(222))
    print(my_list2[0])
    print(my_list2[2])
    print(my_list2[-1])
    print(my_list2[:-1])
    print(my_list2[1:4])
    print(my_list2[2:3])
    print(my_list2[2:])
    list2 = my_list1 + my_list2
    list3 = my_list1*2
    print(list2, list3)
    print(list2==list2[:])
myList()