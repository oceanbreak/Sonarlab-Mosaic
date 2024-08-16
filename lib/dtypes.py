

class GKpoint(tuple):

    def __init__(self, *args):
        if len(*args) != 2:
            raise TypeError

    def __str__(self):
        pt = super().__str__()
        return f'GK point: {pt}'
    
class MapPoint(tuple):

    def __init__(self, *args):
        if len(*args) != 2:
            raise TypeError

    def __str__(self):
        pt = super().__str__()
        return f'Map point: {pt}'
    

if __name__ == '__main__':

    a = GKpoint((4.6, 5.5))
    for i in a:
        print(i)

    i,k = a
    print(i,k)
