# -*- coding: cp1252 -*-

import numpy as np
import pandas as pd



data= pd.DataFrame()

data["test1"] = [0,1,2]
data["test2"] = [3,4,5]
data["test3"] = [6,7,7]

writer = pd.ExcelWriter("Wirtschaftliche_Bewertung.xlsx", engine='openpyxl')
data.to_excel(writer, sheet_name= "Test", header= None,index=None,
                     startcol= 2, startrow= 2)
