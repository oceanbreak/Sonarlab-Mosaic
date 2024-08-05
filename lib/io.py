import numpy as np



def npToCsv(out_name : str, array : np.ndarray):
    """
    Write np array to csv
    """
    if len(array.shape) != 2:
        print('Dimensions must be 2')
    with open(out_name, 'w') as f_write:
        for i in range(array.shape[0]):
            line_list = [str(array[i,j]) for j in range(array.shape[1])]
            f_write.write(';'.join(line_list) + '\n')
    print(f'{out_name} write successfully')


