# -*- coding: cp1252 -*-

from unicodedata import decimal
import pandas as pd
import numpy as np


profileBases = ["A0","B0","C0","A1","A2","A3","B1","B2","B3","C1","C2","C3","D1","D2","D3","Sport"]

class Initializer():
    def __init__(self, path) -> None:
        self.data = pd.read_csv(path, sep= ";", decimal= ",")
        self.profiles = {}

        for base in profileBases:
            #Sortieren des Dataframes nach Profilbasis
            dfSlice = self.data.filter(like= base, axis = 1)
            #Alle Überschriften kombinieren
            combined = '\t'.join(dfSlice.columns)
            if base != "Sport":  
                toAdd = {
                    "Demand" : [],
                    "Production" : [],
                    "Electric Vehicle" : [],
                    "Heatpump" : []}
                if "Conso" in combined:
                    toAdd["Demand"] = dfSlice[f"{base} Conso"].values.tolist()
                if "Prod" in combined:
                    toAdd["Generation"] = dfSlice.filter(like= "Prod", axis = 1).values.tolist()
                if "EV" in combined:
                    toAdd["Electric Vehicle"] = dfSlice.filter(like= "EV", axis = 1).values.tolist()
                if "HP" in combined:
                    toAdd["Heatpump"] = dfSlice.filter(like= "HP", axis = 1).values.tolist()
            
                self.profiles[base] = toAdd
            else:
                          
                for percent in ["30","100","200"]:
                    toAdd = {
                        "Demand" : [],
                        "Production" : [],
                        "Electric Vehicle" : [],
                        "Heatpump" : []}
                    if "Conso" in combined:
                        toAdd["Demand"] = dfSlice.filter(like= "Conso", axis = 1).values.tolist()
                    if "Prod" in combined:
                        toAdd["Generation"] = dfSlice.filter(like= percent, axis = 1).values.tolist()
                    self.profiles[f"{base}-{percent}"] = toAdd

       

profiles = Initializer("test.csv")
class Profile():

    def __init__(self, name):
        
        self.name = name
        self.demand = profiles.profiles[name]["Demand"]
        
def CreateProfiles(name, count=1):
    ret = []
    for _ in range(count):
        ret.append(Profile(name))

    return ret


startConditions = {
    "A0" : 0,
    "B0" : 0,
    "C0" : 0,
    "A1" : 0,
    "A2" : 0,
    "A3" : 0,
    "B1" : 0,
    "B2" : 0,
    "B3" : 0,
    "C1" : 0,
    "C2" : 0,
    "C3" : 0,
    "D1" : 0,
    "D2" : 0,
    "D3" : 0,
    "Sport-30" : 0,
    "Sport-100" : 0,
    "Sport-200" : 0
    
    }

A0 = CreateProfiles("A0", 20)


print(A0)


class Simulation():
    def __init__(self, profiles) -> None:
        self.profiles = profiles

