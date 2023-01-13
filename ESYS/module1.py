# -*- coding: cp1252 -*-

import numpy as np
import pandas as pd

from openpyxl import load_workbook 

data= pd.DataFrame()

data["test1"] = [1]
data["test2"] = [2]
data["test3"] = [3]

book = load_workbook("Test.xlsx")
writer = pd.ExcelWriter("Test.xlsx", engine='openpyxl')

writer.book = book
writer.sheets = dict((ws.title, ws) for ws in book.worksheets)
data.to_excel(writer, sheet_name= "Test", header= None,index=None,
                     startcol= 2, startrow= 2)
writer.save()
writer.close()
