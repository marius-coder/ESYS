# -*- coding: cp1252 -*-

from copy import copy
from unicodedata import decimal
import pandas as pd
import numpy as np
from Wirtschaft import Econ

profileBases = ["A0","B0","C0","A1","A2","A3","B1","B2","B3","C1","C2","C3","D1","D2","D3"]

class Initializer():
    def __init__(self, path) -> None:
        
        self.data = pd.read_csv(path, sep= ";", decimal= ",")
        self.profiles = {}

        for base in profileBases:
            #Sortieren des Dataframes nach Profilbasis
            dfSlice = self.data.filter(like= base, axis = 1)
            #Alle Überschriften kombinieren
            combined = '\t'.join(dfSlice.columns)

            toAdd = {
                "Demand" : np.zeros(35036),
                "Production" : np.zeros(35036),
                "Electric Vehicle" : np.zeros(35036),
                "Heatpump" : np.zeros(35036)}
            if "Conso" in combined:
                toAdd["Demand"] = dfSlice[f"{base} Conso"].values.tolist()
                try:
                    toAdd["Demand"] = [item for sublist in toAdd["Demand"] for item in sublist]
                except:
                    pass
            if "Prod" in combined:
                toAdd["Production"] = dfSlice.filter(like= "Prod", axis = 1).values.tolist()     
                try:
                    toAdd["Production"] = [item for sublist in toAdd["Production"] for item in sublist]
                except:
                    pass
            if "EV" in combined:
                toAdd["Electric Vehicle"] = dfSlice.filter(like= "EV", axis = 1).values.tolist()
                toAdd["Electric Vehicle"] = [item for sublist in toAdd["Electric Vehicle"] for item in sublist]
            if "HP" in combined:
                toAdd["Heatpump"] = dfSlice.filter(like= "HP", axis = 1).values.tolist()
                toAdd["Heatpump"] = [item for sublist in toAdd["Heatpump"] for item in sublist]
            
            self.profiles[base] = toAdd


       

profiles = Initializer("test.csv")
class Profile(Econ):

    def __init__(self, name):    
        if any(substring in name for substring in ["A0","B0","C0"]):
            self.type = "Consumer"
        else:
            self.type = "Prosumer"
        self.name = name
        

        if "EV" in name:     
            name = name.split("_")[0]
            self.demand = copy(profiles.profiles[name]["Electric Vehicle"])
            self.production = copy(profiles.profiles[name]["Production"])
        elif "HP" in name:
            name = name.split("_")[0]
            self.demand = copy(profiles.profiles[name]["Heatpump"])
            self.production = copy(profiles.profiles[name]["Production"])
        else:
            self.demand = copy(profiles.profiles[name]["Demand"])
            self.production = copy(profiles.profiles[name]["Production"])


        #Datatracking
        self.residualLoad = np.zeros(35036)

        self.selfConsumptionBeforeCom = np.zeros(35036)
        self.gridDemandBeforeCom = np.zeros(35036)
        self.gridFeedInBeforeCom = np.zeros(35036)

        self.selfConsumptionAfterCom = np.zeros(35036)
        self.gridDemandAfterCom = np.zeros(35036)
        self.gridFeedInAfterCom = np.zeros(35036)






   
def CreateProfiles(startConditions):
    ret = []

    for key,val in startConditions.items():
        for _ in range(val):
            ret.append(Profile(key))

    return ret


