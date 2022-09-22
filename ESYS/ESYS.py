import pandas as pd


import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np


data = pd.read_csv("Belgian consumption and production profiles.csv", skiprows= 5, encoding = "cp1252", header =None, sep=";", decimal=".")
columnsPools = pd.read_csv("Belgian consumption and production profiles.csv", encoding = "cp1252", sep=";", decimal=".").columns
columnsProdCons = pd.read_csv("Belgian consumption and production profiles.csv", skiprows=1, encoding = "cp1252", sep=";", decimal=".").columns
dataCleaned = pd.DataFrame()

columnname = ""
for index, (col1,col2) in enumerate(zip(columnsPools, columnsProdCons)):
    col2 = col2.split(".")[0]

    if "Unnamed" not in col1:
        columnname = col1

    if any(x in col2 for x in ["Prod","Cons","Month","Year","Day"]):
        dataCleaned[f"{columnname} {col2}"] = data.iloc[2:,index]

hours = []
minutes = []
hour = 0
minute = 0
currentYear = 0
currentMonth = 0
currentDay = 0
dataCleaned = dataCleaned.reset_index()
for index in range(len(dataCleaned)):
    if dataCleaned[' Year'][index] > currentYear:
        currentYear = dataCleaned[' Year'][index]
        currentMonth = 0
        currentDay = 0

    if dataCleaned[' Month'][index] > currentMonth:
        currentMonth = dataCleaned[' Month'][index]
        currentDay = 0

    if dataCleaned[' Day'][index] > currentDay:
        currentDay = dataCleaned[' Day'][index]
        hour = 0
        minute = 0

    hours.append(str(hour))
    minutes.append(str(minute))
    minute += 15

    if hour == 24:
        hour = 0

    if minute == 60:
        hour += 1
        minute = 0



dataCleaned[' Year'] = dataCleaned[' Year'].astype('Int64').astype(str)
dataCleaned[' Month'] = dataCleaned[' Month'].astype('Int64').astype(str)
dataCleaned[' Day'] = dataCleaned[' Day'].astype('Int64').astype(str)
dataCleaned['Hour'] = hours
dataCleaned['Minute'] = minutes

dataCleaned["DateTime"] = pd.to_datetime(dataCleaned[' Year']+"."+dataCleaned[' Month']+"."+dataCleaned[' Day']+" "+dataCleaned['Hour']+":"+dataCleaned['Minute'], format= '%Y.%m.%d %H:%M')
dataCleaned = dataCleaned.set_index(dataCleaned["DateTime"])
dataCleaned.to_csv("test.csv", sep=";", decimal=",")

for i,row in enumerate(dataCleaned["Hour"]):
    if int(dataCleaned.index[i].hour) != int(row):
        print(f"Index: {dataCleaned.index[i].hour}")
        print(f"Row: {row}")
        raise ValueError(f"Bruh")

dataCleaned = dataCleaned.drop([" Year"," Month"," Day","DateTime","Hour","Minute"], axis = 1)

fig, ax = plt.subplots(figsize=(7,4))
fig.suptitle("Lastgang", fontsize = 20)
pd.set_option('display.max_columns', 500)
pd.set_option('display.width', 240)
pd.set_option('float_format', '{:.1f}'.format)
print(dataCleaned.describe())

dataPlot= dataCleaned[dataCleaned.index.month == 1]
#dataPlot = dataPlot[dataPlot.index.day == 12]
sns.lineplot( data=dataPlot["HP_C1 Conso"], ax = ax)

ax.set_xlabel("Uhrzeit", fontsize = 12)
ax.set_ylabel("Leistung", fontsize = 12)
plt.tight_layout()
plt.show()


