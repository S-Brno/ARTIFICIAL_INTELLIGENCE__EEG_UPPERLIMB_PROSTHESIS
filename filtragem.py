import numpy as np
import pandas as pd

filename = 'pré-filtro'
channel  = []
delimiter = ';'

if ".csv" not in filename:           
    filename += ".csv"

with open(filename, 'r') as f:
    data_csv = f.readlines()  
    data_csv.pop(0) 
    for linha in data_csv:

        e = linha.split('\n')
        channel.append(float(e[0].replace(',', ".")))
       
a = np.array(channel)
print(a[0])
b = pd.unique(a)



f = 'filtrado.csv'
with open(f, "w+") as f:
    for z in range(len(b)):
        linha = str(b[z]) + '\n'
        f.write(linha)

