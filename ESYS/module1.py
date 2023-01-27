# -*- coding: cp1252 -*-

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import locale
locale.setlocale(locale.LC_NUMERIC, "de_DE")


plt.rcdefaults()

# Tell matplotlib to use the locale we set above
plt.rcParams['axes.formatter.use_locale'] = True
from openpyxl import load_workbook 

from mpl_toolkits.mplot3d import Axes3D
from matplotlib.colors import LightSource
import seaborn as sns
SharedData = pd.read_csv("./Output/Ergebnis_SharedGen_2.csv", sep=";", decimal =",", encoding = "cp1252")
SharedData = SharedData.iloc[1:]
SharedData = SharedData.reset_index(drop=True)
batGr��e = np.linspace(0,1000,11)
sharedkWp = np.linspace(0,500,11)



def PlotData(data, column, title, xlabel, ylabel, zlabel, nameFile):

    dataInvestKosten = pd.DataFrame()
    #dataInvestKosten = dataInvestKosten.set_index(batGr��e)
    #dataInvestKosten.columns = sharedkWp
    #column = "Ersparnisse Consumer"
    count = 0
    for bat in range(11):    
        interInner = []
        for shared in range(11):
            #print(SharedData[column][count])
            interInner.append(data[column][count])
            count += 1
        dataInvestKosten[str(bat)] = interInner

    #dataInvestKosten.to_csv("Test.csv", sep= ";", decimal = ",", encoding= "cp1252")
    dataInvestKosten = dataInvestKosten.set_index(sharedkWp)
    dataInvestKosten.columns = batGr��e

    x,y = np.meshgrid(batGr��e, sharedkWp)
    z = dataInvestKosten.values

    fig, ax = plt.subplots(subplot_kw=dict(projection='3d'))

    rgb = LightSource(270, 45).shade(z, cmap=plt.cm.gist_earth, vert_exag=0.1, blend_mode='soft')
    surf = ax.plot_surface(x, y, z, facecolors=rgb,
                            linewidth=0)
    ax.set_title(title)
    ax.ticklabel_format(useOffset=False, style='plain')
    ax.set_xlabel(ylabel)
    ax.set_ylabel(xlabel)
    ax.zaxis.set_rotate_label(False) 
    ax.set_zlabel(zlabel, rotation = 90,labelpad=10)
    #fig.colorbar(surf)
    plt.savefig(f"./Output/{nameFile}_3D.png", bbox_inches='tight')
    plt.show()

    sns.heatmap(dataInvestKosten, cmap="gist_earth", cbar_kws={'label': zlabel})
    plt.ylabel(xlabel)
    plt.xlabel(ylabel)
    plt.title(title)
    plt.savefig(f"./Output/{nameFile}_2D.png", bbox_inches='tight')
    plt.show()
    dataInvestKosten.to_csv(f"./Output/csv/{nameFile}.csv",sep=";", decimal= ",", encoding= "cp1252")
    



    
PlotData(SharedData,column= "Investkosten", title= "Investkosten", xlabel= "Gr��e der shared Generation in kWp", 
            ylabel= "Gr��e des Stromspeichers in kWh", zlabel= "Investkosten in �", nameFile= "Investkosten")

PlotData(SharedData,column= "Ersparnisse Prosumer", title= "Ersparnisse Prosumer", xlabel= "Gr��e der shared Generation in kWp", 
            ylabel= "Gr��e des Stromspeichers in kWh", zlabel= "Ersparnisse Prosumer in �", nameFile= "Ersparnisse Prosumer")

PlotData(SharedData,column= "Ersparnisse Consumer", title= "Ersparnisse Consumer", xlabel= "Gr��e der shared Generation in kWp", 
            ylabel= "Gr��e des Stromspeichers in kWh", zlabel= "Ersparnisse Consumer in �", nameFile= "Ersparnisse Consumer")

PlotData(SharedData,column= "F�rderkosten", title= "F�rderkosten", xlabel= "Gr��e der shared Generation in kWp", 
            ylabel= "Gr��e des Stromspeichers in kWh", zlabel= "F�rderkosten in �", nameFile= "F�rderkosten")

PlotData(SharedData,column= "Netzbezug", title= "Netzbezug", xlabel= "Gr��e der shared Generation in kWp", 
            ylabel= "Gr��e des Stromspeichers in kWh", zlabel= "Netzbezug in kWh", nameFile= "Netzbezug")

PlotData(SharedData,column= "Netzeinspeisung", title= "Netzeinspeisung", xlabel= "Gr��e der shared Generation in kWp", 
            ylabel= "Gr��e des Stromspeichers in kWh", zlabel= "Netzeinspeisung in kWh", nameFile= "Netzeinspeisung")

dataAmort = pd.DataFrame()
count = 0
for i in range(11):    
    interInner = []
    for k in range(11):
        #print(SharedData[column][])
        interInner.append((SharedData["Investkosten"][count]-SharedData["F�rderkosten"][count])/(SharedData["Ersparnisse Prosumer"][count]+SharedData["Ersparnisse Consumer"][count]))
        count += 1
    dataAmort[str(i)] = interInner
dataAmort = dataAmort.set_index(sharedkWp)
dataAmort.columns = batGr��e
x,y = np.meshgrid(batGr��e, sharedkWp)
z = dataAmort.values

fig, ax = plt.subplots(subplot_kw=dict(projection='3d'))

rgb = LightSource(270, 45).shade(z, cmap=plt.cm.gist_earth, vert_exag=0.1, blend_mode='soft')
surf = ax.plot_surface(x, y, z, facecolors=rgb,
                        linewidth=0)
ax.set_title("Amortisationszeit")
ax.ticklabel_format(useOffset=False, style='plain')
ax.set_ylabel("Gr��e der shared Generation in kWp")
ax.set_xlabel("Gr��e des Stromspeichers in kWh")
ax.zaxis.set_rotate_label(False) 
ax.set_zlabel("Amortisation in Jahren", rotation = 90,labelpad=10)
plt.savefig(f"./Output/Amortisation_3D.png", bbox_inches='tight')
plt.show()

sns.heatmap(dataAmort, cmap="gist_earth", cbar_kws={'label': "Amortisation in Jahren"})
plt.xlabel("Gr��e des Stromspeichers in kWh")
plt.ylabel("Gr��e der shared Generation in kWp")
plt.title("Amortisationszeit")
plt.savefig(f"./Output/Amortisation_2D.png", bbox_inches='tight')
plt.show()
dataAmort.to_csv(f"./Output/csv/Amortisationszeit.csv",sep=";", decimal= ",", encoding= "cp1252")


dataErsp = pd.DataFrame()
count = 0
for i in range(11):    
    interInner = []
    for k in range(11):
        #print(SharedData[column][])
        interInner.append((SharedData["Ersparnisse Prosumer"][count]+SharedData["Ersparnisse Consumer"][count]))
        count += 1
    dataErsp[str(i)] = interInner
dataErsp = dataErsp.set_index(sharedkWp)
dataErsp.columns = batGr��e

x,y = np.meshgrid(batGr��e, sharedkWp)
z = dataErsp.values

fig, ax = plt.subplots(subplot_kw=dict(projection='3d'))

rgb = LightSource(270, 45).shade(z, cmap=plt.cm.gist_earth, vert_exag=0.1, blend_mode='soft')
surf = ax.plot_surface(x, y, z, facecolors=rgb,
                        linewidth=0)
ax.set_title("Gesamte Ersparnis")
ax.ticklabel_format(useOffset=False, style='plain')
ax.set_ylabel("Gr��e der shared Generation in kWp")
ax.set_xlabel("Gr��e des Stromspeichers in kWh")
ax.zaxis.set_rotate_label(False) 
ax.set_zlabel("Ersparnis in �", rotation = 90,labelpad=10)
plt.savefig(f"./Output/Ersparnisse_Gesamt_3D.png", bbox_inches='tight')
plt.show()

sns.heatmap(dataErsp, cmap="gist_earth", cbar_kws={'label': "Ersparnisse in �"})
plt.xlabel("Gr��e des Stromspeichers in kWh")
plt.ylabel("Gr��e der shared Generation in kWp")
plt.title("Ersparnisse Gesamt")
plt.savefig(f"./Output/Ersparnisse_Gesamt_2D.png", bbox_inches='tight')
plt.show()
dataErsp.to_csv(f"./Output/csv/ErsparnisGesamt.csv",sep=";", decimal= ",", encoding= "cp1252")