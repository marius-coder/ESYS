# -*- coding: cp1252 -*-

import numpy as np
import pandas as pd
from tqdm import tqdm
from profileInitializer import CreateProfiles
from Batterie import Batterie
from openpyxl import load_workbook 
startConditions = {
    "A0" : 16,
    "B0" : 12,
    "C0" : 7,
    "A1" : 4,
    "B1" : 6,
    "C1" : 2,
    "C1_EV" : 2,
    "C1_HP" : 6,
    "A2" : 2,
    "B2" : 5,
    "C2" : 3,
    "C2_EV" : 3,
    "C2_HP" : 7,
    "D2_HP" : 0,
    "D2" : 2,
    "D2_EV" : 0,
    "A3" : 0,
    "B3" : 3,
    "C3" : 3,
    "C3_EV" : 5,
    "C3_HP" : 0,
    "D3_HP" : 6,
    "D3" : 0,
    "D3_EV" : 6}





class Simulation():

    def __init__(self, profiles, econParameters, var_kapMAX, sharedGenerationkWp = 0,peerToPeer= False, sharedGeneration= False, netMetering= False) -> None:
        self.profiles = profiles
        self.battery = Batterie(var_EntTiefe = 0.2, var_Effizienz = 0.95,var_kapMAX = var_kapMAX, infoAmount= 35036)

        if sharedGeneration == True:
            self.sharedGenerationkWp = sharedGenerationkWp
        else:
            self.sharedGenerationkWp = 0
        def interpolate(inp, fi):
            i, f = int(fi // 1), fi % 1  # Split floating-point index into whole & fractional parts.
            j = i+1 if f > 0 else i  # Avoid index error.
            return (1-f) * inp[i] + f * inp[j]

        inp = np.genfromtxt("PV_1kWp.csv")
        new_len = 35036

        delta = (len(inp)-1) / (new_len-1)
        outp = [interpolate(inp, i*delta) for i in range(new_len)]
        self.sharedGenerationProfile = [value * sharedGenerationkWp for value in outp]

        self.gridDemand = np.zeros(35036)
        self.gridFeedIn = np.zeros(35036)
        self.peerToPeer = peerToPeer
        self.sharedGeneration = sharedGeneration
        self.netMetering = netMetering
        self.econParameters = econParameters

        self.selfConsumptionBeforeCom = np.zeros(35036)
        self.selfConsumptionAfterCom = np.zeros(35036)
        
    def CalcBatteryEEG(self, residualDemandSum, timestep):
        SumEnergytoAllocate = min(abs(self.battery.AvailableEnergy()),residualDemandSum)
        toRet = 0
        if SumEnergytoAllocate > 0:
            for building in self.profiles:
                allocatedEnergy = SumEnergytoAllocate / residualDemandSum * building.residualLoad[timestep]
                toRet += allocatedEnergy
                building.residualLoad[timestep] -= allocatedEnergy
                building.gridDemandAfterCom[timestep] -= allocatedEnergy
            return residualDemandSum - toRet

    def CalcBatteryEEGladen(self, residualEnergySum, timestep):
        SumEnergytoAllocate = min(abs(self.battery.AvailableSpace()),abs(residualEnergySum))
        toRet = 0
        if round(SumEnergytoAllocate,6) > 0:
            for building in self.profiles:                
                allocatedEnergy = abs(SumEnergytoAllocate / residualEnergySum * building.residualLoad[timestep])
                toRet += allocatedEnergy

                building.residualLoad[timestep] += allocatedEnergy
                building.gridFeedInAfterCom[timestep] -= allocatedEnergy

            return residualEnergySum - toRet


    def CalcEEG(self, timestep, residualProductionSum, residualDemandSum, checkResidualProdSum):
        SumEnergytoAllocate = min(abs(residualProductionSum),residualDemandSum)
        for building in self.profiles:
            if building.residualLoad[timestep] > 0:
                #Einspeisung dynamisch aufteilen
                allocatedEnergy = SumEnergytoAllocate / residualDemandSum * building.residualLoad[timestep]
                building.residualLoad[timestep] -= allocatedEnergy
                checkResidualProdSum += allocatedEnergy
                #Daten loggen                
                #demand = building.demand[timestep] + building.demandEV[timestep] + building.demandHP[timestep]
                building.selfConsumptionAfterCom[timestep] = building.selfConsumptionBeforeCom[timestep] #Eigenverbrauch nach E-Gemeinschaft
                building.gridDemandAfterCom[timestep] = building.demand[timestep] - (building.selfConsumptionAfterCom[timestep] + allocatedEnergy) #Netzbezug nach E-Gemeinschaft
                building.gridFeedInAfterCom[timestep] = building.gridFeedInBeforeCom[timestep] #Netzeinspeisung nach E-Gemeinschaft   
                
            elif building.residualLoad[timestep] < 0:
                #Residuallast dynamisch aufteilen
                allocatedEnergy = abs(SumEnergytoAllocate / residualProductionSum * building.residualLoad[timestep])
                building.residualLoad[timestep] -= allocatedEnergy
                #checkResidualProdSum += allocatedEnergy
                #Daten loggen
                #demand = building.demand[timestep] + building.demandEV[timestep] + building.demandHP[timestep]
                building.selfConsumptionAfterCom[timestep] = building.selfConsumptionBeforeCom[timestep]
                building.gridDemandAfterCom[timestep] = building.gridDemandBeforeCom[timestep]
                building.gridFeedInAfterCom[timestep] = abs(building.residualLoad[timestep])
        return checkResidualProdSum

    def Simulate(self,verbose = False):

        for timestep in range(35036):
            for building in self.profiles:
                #Residuallast der einzelnen Gebäude ermitteln
                if self.sharedGeneration:
                    building.production[timestep] += self.sharedGenerationProfile[timestep]/len(self.profiles) #Shared Generation hinzufügen zu Produktion. Hier wäre auch eine nicht Gleichmäßige Aufteilung zu machen
                #demand = building.demand[timestep] + building.demandEV[timestep] + building.demandHP[timestep]
                building.residualLoad[timestep] = building.demand[timestep] - building.production[timestep]
                building.selfConsumptionBeforeCom[timestep] = min(building.demand[timestep], building.production[timestep]) #Eigenverbrauch vor E-Gemeinschaft
                building.gridDemandBeforeCom[timestep] = building.demand[timestep] - building.selfConsumptionBeforeCom[timestep] #Netzbezug vor E-Gemeinschaft
                building.gridFeedInBeforeCom[timestep] = abs(building.production[timestep] - building.selfConsumptionBeforeCom[timestep]) #Netzeinspeisung vor E-Gemeinschaft

            #Summe der gesamten Residuallast der Gemeinschaft ermitteln
            residualDemandSum = sum([building.residualLoad[timestep] for building in self.profiles if building.residualLoad[timestep] > 0])
            residualProductionSum = sum([building.residualLoad[timestep] for building in self.profiles if building.residualLoad[timestep] < 0])
            #print(f"Timestep: {timestep}")

            if verbose == True:
                
                print(f"residualDemandSum: {residualDemandSum}")
                print(f"residualProductionSum: {residualProductionSum}")
                print("----------------------------------------------------")

            #Direktzuweisung für andere Gebäude
            
            checkResidualProdSum = 0
            allocatedEnergy =  0
            if self.peerToPeer == True:
                checkResidualProdSum = self.CalcEEG(timestep= timestep, residualProductionSum= residualProductionSum, residualDemandSum= residualDemandSum, checkResidualProdSum= checkResidualProdSum)
                #Kontrolle ob die gesamte Verfügbare Energie verteilt woren ist (Auf 6 Kommastellen)
                if round(checkResidualProdSum,6) != round(min(abs(residualProductionSum),residualDemandSum),6):                
                    raise ValueError(f"Allocated Energy must be 0. It is {allocatedEnergy - min(abs(residualProductionSum),residualDemandSum)}")
                if round(residualDemandSum,6) < 0:
                    raise ValueError(f"Demand Energy must be grater than 0. It is {round(residualDemandSum,6)}")
            
            else:
                checkResidualProdSum = 0
                allocatedEnergy =  0

            #negative Residuallast updaten
            residualProductionSum += round(checkResidualProdSum,6)
            residualDemandSum -= round(checkResidualProdSum,6)

            #Falls nach der direktzuweisung noch Energie übrig ist, wird der gemeinschaftsspeicher befüllt
            if residualProductionSum < 0:
                residualProductionSum = abs(residualProductionSum)
                self.CalcBatteryEEGladen(residualEnergySum= residualProductionSum, timestep= timestep)
                #Batterie Laden
                residualProductionSum = self.battery.Laden(qtoLoad= residualProductionSum, timestep= timestep)
                #restliche Energie in das Netz einspeisen
                self.gridFeedIn[timestep] = residualProductionSum
                 
            if round(residualDemandSum,6) > 0:
                #Batterie entladen
                self.CalcBatteryEEG(residualDemandSum= residualDemandSum, timestep= timestep)
                residualDemandSum = self.battery.Entladen(qtoTake= residualDemandSum, timestep= timestep)
                #restliche Energie aus dem Netz beziehen
                self.gridDemand[timestep] = residualDemandSum

            #self.battery.Entladen(qttoTake= 5, )
            self.battery.TestBattery(timestep= timestep)
            self.TestFlowsHourly(timestep= timestep)

        for building in self.profiles:
            building.SetAttributes(antEnergie= self.econParameters["antEnergie"], antAbgabe= self.econParameters["antAbgabe"]
                                   , antSteuer= self.econParameters["antSteuer"], priceDemand= self.econParameters["priceDemand"], 
                                   priceFeedIn= self.econParameters["priceFeedIn"])
            building.gridCostsBeforeCom = building.CalcGridDemand(building.gridDemandBeforeCom, mode= "Normal")
            building.gridCompFeedInBeforeCom = building.CalcGridFeedIn(building.gridFeedInBeforeCom, mode= "Normal")

            building.gridCostsAfterCom = building.CalcGridDemand(gridDemand= building.gridDemandBeforeCom, mode= "EC", gridDemandEC= building.gridDemandAfterCom)
            building.gridCompFeedInAfterCom = building.CalcGridFeedIn(gridFeedIn= building.gridFeedInBeforeCom, mode= "EC", gridFeedInEC= building.gridFeedInAfterCom)

            building.CalcNetMetering(gridDemand= building.gridDemandBeforeCom, gridFeedIn= building.gridFeedInBeforeCom)
            if verbose == True:
                print(f"Gebäude: {building.name}")
                print(f"Gebäudebezug Davor: {sum(building.gridDemandBeforeCom)}")
                print(f"Gebäudebezug Danach: {sum(building.gridDemandAfterCom)}")
                print(f"Gebäudeeinspeisung Davor: {sum(building.gridFeedInBeforeCom)}")
                print(f"Gebäudeeinspeisung Danach: {sum(building.gridFeedInAfterCom)}")

        costsBefore = 0
        compBefore = 0
        
        costsAfter = 0
        compAfter = 0
        costsAfterNetMetering = 0
        compAfterNetMetering = 0


        for building in self.profiles:
            costsBefore += building.gridCostsBeforeCom
            compBefore += building.gridCompFeedInBeforeCom
            costsAfter += building.gridCostsAfterCom
            compAfter += building.gridCompFeedInAfterCom
            costsAfterNetMetering += building.gridCostsNetMetering
            compAfterNetMetering += building.gridFeedInNetMetering
        #print(f"==================================================================")
        #print(f"======== Effects of Energy Community ============")
        #print(f"Costs for Griddemand before Energy Community: {costsBefore}")
        #print(f"Costs for Griddemand after Energy Community: {costsAfter}")
        #print(f"Difference: {costsBefore-costsAfter}")
        #print(f"Compensation for GridFeedin before Energy Community: {compBefore}")
        #print(f"Compensation for GridFeedin after Energy Community: {compAfter}")
        #print(f"Difference: {compAfter-compBefore}")
        #print(f"Final Gain from Community: {(costsBefore-costsAfter)+(compAfter-compBefore)}")
        #print(f"==================================================================")
        #print(f"======== Effects of Net Metering ============")
        
        #print(f"Gridcosts with Net Metering: {costsAfterNetMetering}")
        #print(f"Compensation with Net Metering: {compAfterNetMetering}")

        return 

    def TestFlows(self):
        """Testet die Energieflüsse auf Gemeinschaftsebene. Summe der Energieflüsse müssen 0 ergeben.
        Return:
            Hat keinen Returnwert"""
        demand = 0
        production = 0
        for building in self.profiles:
            demand += sum(building.demand)# + sum(building.demandEV) + sum(building.demandHP)
            production += sum(building.production)

        #Positive Energieflüsse von Außen (Netzbezug, Batterieentladung, PV-Produktion)
        flowsIn = production + abs(sum(self.gridDemand)) + abs(sum(self.battery.entladeEnergie))

        #Negative Energieflüsse nach Außen
        flowsOut = demand + abs(sum(self.gridFeedIn)) + abs(sum(self.battery.ladeEnergie)) + abs(sum(self.battery.verluste))

        #Energieflüsse testen
        Test = flowsIn - flowsOut
        if round(abs(Test),3) != 0:
           raise ValueError(f"ENERGIEBILANZ STIMMT NICHT!: {Test}")

    def TestFlowsHourly(self, timestep):
        """Testet die Energieflüsse auf Gemeinschaftsebene auf Stundenbasis. Summe der Energieflüsse müssen 0 ergeben.
        timestep:
            Zeitschritt der getestet wird
        Return:
            Hat keinen Returnwert"""
        demand = 0
        production = 0
        for building in self.profiles:
            demand += building.demand[timestep]# + building.demandEV[timestep] + building.demandHP[timestep]
            production += building.production[timestep]

        #Positive Energieflüsse von Außen (Netzbezug, Batterieentladung, PV-Produktion)
        gridDem = abs(self.gridDemand[timestep])
        batEntlade = abs(self.battery.entladeEnergie[timestep])
        flowsIn = production + abs(self.gridDemand[timestep]) + abs(self.battery.entladeEnergie[timestep])

        #Negative Energieflüsse nach Außen
        gridFeed = abs(self.gridFeedIn[timestep])
        batLade = abs(self.battery.ladeEnergie[timestep])
        batVerl = abs(self.battery.verluste[timestep])
        flowsOut = demand + abs(self.gridFeedIn[timestep]) + abs(self.battery.ladeEnergie[timestep]) + abs(self.battery.verluste[timestep])

        #Energieflüsse testen
        Test = flowsIn - flowsOut
        if round(abs(Test),1) != 0:
           raise ValueError(f"ENERGIEBILANZ STIMMT NICHT!: {Test} Zeitschritt: {timestep}")


    def ExportResults(self, typ):
        investKosten = 0
        ersparnisseProsumer = 0
        ersparnisseConsumer = 0
        förderkosten = 0
        kWhperkWp = 1000

        verbrauch = 0
        erzeugung = 0
        eigenverbrauch = 0
        netzbezug = 0
        netzeinspeisung = 0

        if typ == "Peer-to-Peer":
            for building in self.profiles:
                verbrauch += sum(building.demand)
                erzeugung += sum(building.production)
                eigenverbrauch += sum(building.selfConsumptionAfterCom)
                netzbezug += sum(building.gridDemandAfterCom)
                netzeinspeisung += sum(building.gridFeedInAfterCom)

                if building.type == "Consumer":
                    ersparnisseConsumer += (building.gridCostsBeforeCom - building.gridCostsAfterCom) + (building.gridCompFeedInAfterCom - building.gridCompFeedInBeforeCom)
                else:
                    investKosten += sum(building.production) / kWhperkWp * self.econParameters["Kosten Photovoltaik"] 
                    ersparnisOhneMitPV = building.CalcGridDemand(building.demand, mode= "Normal") - building.gridCostsAfterCom
                    ersparnisseProsumer += ersparnisOhneMitPV + building.gridCompFeedInAfterCom
            förderkosten += investKosten * self.econParameters["Förderrate Photovoltaik"] 
            investKosten += self.battery.kapazitätMAX * self.econParameters["Kosten Stromspeicher"] 
            förderkosten += self.battery.kapazitätMAX * self.econParameters["Kosten Stromspeicher"] * self.econParameters["Förderrate Stromspeicher"]

        elif typ == "netMetering":
            for building in self.profiles:
                verbrauch += sum(building.demand)
                erzeugung += sum(building.production)
                eigenverbrauch += sum(building.selfConsumptionBeforeCom)
                netzbezug += sum(building.gridDemandBeforeCom)
                netzeinspeisung += sum(building.gridFeedInBeforeCom)

                if building.type == "Consumer":
                    ersparnisseConsumer += 0
                else:
                    investKosten += sum(building.production) / kWhperkWp * self.econParameters["Kosten Photovoltaik"] 
                    ersparnisOhneMitPV = building.CalcGridDemand(building.demand, mode= "Normal") - building.gridCostsBeforeCom
                    ersparnisseProsumer += ersparnisOhneMitPV + building.gridFeedInNetMetering
            förderkosten += investKosten * self.econParameters["Förderrate Photovoltaik"] 
            investKosten += self.battery.kapazitätMAX * self.econParameters["Kosten Stromspeicher"] 
            förderkosten += self.battery.kapazitätMAX * self.econParameters["Kosten Stromspeicher"] * self.econParameters["Förderrate Stromspeicher"]
        
        elif typ == "sharedGeneration":
            for building in self.profiles:
                verbrauch += sum(building.demand)
                erzeugung += sum(building.production)
                eigenverbrauch += sum(building.selfConsumptionAfterCom)
                netzbezug += sum(building.gridDemandAfterCom)
                netzeinspeisung += sum(building.gridFeedInAfterCom)

                investKosten += sum(building.production) / kWhperkWp * self.econParameters["Kosten Photovoltaik"]
                if building.type == "Consumer":
                    ersparnisOhneMitPV = building.CalcGridDemand(building.demand, mode= "Normal") - building.gridCostsAfterCom
                    ersparnisseConsumer += ersparnisOhneMitPV + building.gridCompFeedInAfterCom
                else:
                    ersparnisOhneMitPV = building.CalcGridDemand(building.demand, mode= "Normal") - building.gridCostsAfterCom
                    ersparnisseProsumer += ersparnisOhneMitPV + building.gridCompFeedInAfterCom
            förderkosten += investKosten * self.econParameters["Förderrate Photovoltaik"] 
            investKosten += self.battery.kapazitätMAX * self.econParameters["Kosten Stromspeicher"] 
            förderkosten += self.battery.kapazitätMAX * self.econParameters["Kosten Stromspeicher"] * self.econParameters["Förderrate Stromspeicher"]
            
        results = {
            "Verbrauch" : verbrauch,
            "Erzeugung" : erzeugung,
            "Eigenverbrauch" : eigenverbrauch,
            "Netzbezug" : netzbezug,
            "Netzeinspeisung" : netzeinspeisung,
            "Investkosten" : investKosten,
            "Ersparnisse Prosumer" : ersparnisseProsumer,
            "Ersparnisse Consumer" : ersparnisseConsumer,
            "Förderkosten" : förderkosten,
            }
        
        return results

profileSim = CreateProfiles(startConditions)

#sim = Simulation(profileSim,econParameters= econParameters, var_kapMAX= 100, sharedGenerationkWp= 0, peerToPeer= True)

#sim.Simulate()
#sim.TestFlows()
#print(sim.ExportResults())

econParametersMain = {
    "antEnergie" : [0.6, 0.6, 0.6],
    "antAbgabe" : [0.2, 0.2, 0.2],
    "antSteuer" : [0.2, 0.2, 0.2],
    "priceDemand" : [0.17 , 0.6, 0.3],
    "priceFeedIn" : [0.05, 0.286, 0.11],    
    "Kosten Photovoltaik" : [1300, 1800, 1500],
    "Kosten Stromspeicher" : [1000, 1500, 1300],
    "Förderrate Photovoltaik" : [0.3, 0.3, 0.4],
    "Förderrate Stromspeicher" : [0.2, 0.2, 0.3]
    }

mainSzens = {
    "netMetering" : [True, False, False],
    "Peer-to-Peer" : [True, True, True],
    "sharedGeneration" : [False, False, True],    
    }


data = pd.DataFrame({"Investkosten" : np.nan, "Ersparnisse Prosumer" : np.nan, "Ersparnisse Consumer" : np.nan, "Förderkosten" : np.nan}, index = [0])
if True:
    for szen in tqdm(range(3)):
        for kostenSzen in range(3):        
            econParameters = {
                "antEnergie" : econParametersMain["antEnergie"][kostenSzen],
                "antAbgabe" : econParametersMain["antAbgabe"][kostenSzen],
                "antSteuer" : econParametersMain["antSteuer"][kostenSzen],
                "priceDemand" : econParametersMain["priceDemand"][kostenSzen],
                "priceFeedIn" : econParametersMain["priceFeedIn"][kostenSzen], 
                "Kosten Photovoltaik" : econParametersMain["Kosten Photovoltaik"][kostenSzen],
                "Kosten Stromspeicher" : econParametersMain["Kosten Stromspeicher"][kostenSzen],
                "Förderrate Photovoltaik" : econParametersMain["Förderrate Photovoltaik"][kostenSzen],
                "Förderrate Stromspeicher" : econParametersMain["Förderrate Stromspeicher"][kostenSzen],
                }
            profileSim = CreateProfiles(startConditions)
            sim = Simulation(profileSim,econParameters= econParameters, var_kapMAX= 0, sharedGenerationkWp= 100, peerToPeer= mainSzens["Peer-to-Peer"][szen], netMetering= mainSzens["netMetering"][szen], sharedGeneration=mainSzens["sharedGeneration"][szen])
            sim.Simulate()
            results = sim.ExportResults(typ= list(mainSzens.keys())[szen])
            data = data.append(results, ignore_index = True)
    #data.to_csv("Wirtschaftliche_Bewertung.csv", sep=";", decimal = ",", encoding= "cp1252")


    book = load_workbook("Wirtschaftliche_Bewertung.xlsx")
    writer = pd.ExcelWriter("Wirtschaftliche_Bewertung.xlsx", engine='openpyxl')

    writer.book = book
    writer.sheets = dict((ws.title, ws) for ws in book.worksheets)
    data.to_excel(writer, sheet_name= "Wirtschaftliche_Bewertung", header= True,index= True,
                         startcol= 1, startrow= 0)
    data.to_csv("Wirtschaftliche_Bewertung.csv", sep=";", decimal=",", encoding="cp1252")
    writer.save()
    writer.close()


if False:
    for szen in tqdm(range(3)):
        for kostenSzen in range(3): 

            econParameters = {
                "antEnergie" : econParametersMain["antEnergie"][kostenSzen],
                "antAbgabe" : econParametersMain["antAbgabe"][kostenSzen],
                "antSteuer" : econParametersMain["antSteuer"][kostenSzen],
                "priceDemand" : econParametersMain["priceDemand"][kostenSzen],
                "priceFeedIn" : econParametersMain["priceFeedIn"][kostenSzen], 
                "Kosten Photovoltaik" : econParametersMain["Kosten Photovoltaik"][kostenSzen],
                "Kosten Stromspeicher" : econParametersMain["Kosten Stromspeicher"][kostenSzen],
                "Förderrate Photovoltaik" : econParametersMain["Förderrate Photovoltaik"][kostenSzen],
                "Förderrate Stromspeicher" : econParametersMain["Förderrate Stromspeicher"][kostenSzen],
                }
            if szen == 0:
                #Net-Metering
                dataNet = pd.DataFrame({"Investkosten" : np.nan, "Ersparnisse Prosumer" : np.nan, "Ersparnisse Consumer" : np.nan, "Förderkosten" : np.nan}, index = [0])
            
                profileSim = CreateProfiles(startConditions)
                sim = Simulation(profileSim,econParameters= econParameters, var_kapMAX= 0, sharedGenerationkWp= 0, peerToPeer= mainSzens["Peer-to-Peer"][szen], netMetering= mainSzens["netMetering"][szen], sharedGeneration=mainSzens["sharedGeneration"][szen])
                sim.Simulate()
                results = sim.ExportResults(typ= list(mainSzens.keys())[szen])
                dataNet = dataNet.append(results, ignore_index = True)
                dataNet.to_csv(f"./Output/Ergebnis_NetMetering_{kostenSzen}.csv", sep= ";", decimal= ",", encoding= "cp1252")

            if szen == 1:
                #Peer-to-Peer
                dataPeer = pd.DataFrame({"Investkosten" : np.nan, "Ersparnisse Prosumer" : np.nan, "Ersparnisse Consumer" : np.nan, "Förderkosten" : np.nan}, index = [0])
                for batGröße in np.linspace(0,1000,11):
                    profileSim = CreateProfiles(startConditions)
                    sim = Simulation(profileSim,econParameters= econParameters, var_kapMAX= batGröße, sharedGenerationkWp= 0, peerToPeer= mainSzens["Peer-to-Peer"][szen], netMetering= mainSzens["netMetering"][szen], sharedGeneration=mainSzens["sharedGeneration"][szen])
                    sim.Simulate()
                    results = sim.ExportResults(typ= list(mainSzens.keys())[szen])
                    dataPeer = dataPeer.append(results, ignore_index = True)
                dataPeer.to_csv(f"./Output/Ergebnis_PeertpPeer_{kostenSzen}.csv", sep= ";", decimal= ",", encoding= "cp1252")

            if szen == 2:
                #Shared Generation
                dataShared = pd.DataFrame({"Investkosten" : np.nan, "Ersparnisse Prosumer" : np.nan, "Ersparnisse Consumer" : np.nan, "Förderkosten" : np.nan}, index = [0])    
                for batGröße in np.linspace(0,1000,11):
                    print(batGröße)
                    for sharedGröße in np.linspace(0,500,11):
                        profileSim = CreateProfiles(startConditions)
                        sim = Simulation(profileSim,econParameters= econParameters, var_kapMAX= batGröße, sharedGenerationkWp= sharedGröße, peerToPeer= mainSzens["Peer-to-Peer"][szen], netMetering= mainSzens["netMetering"][szen], sharedGeneration=mainSzens["sharedGeneration"][szen])
                        sim.Simulate()
                        results = sim.ExportResults(typ= list(mainSzens.keys())[szen])
                        dataShared = dataShared.append(results, ignore_index = True)        
                dataShared.to_csv(f"./Output/Ergebnis_SharedGen_{kostenSzen}.csv", sep= ";", decimal= ",", encoding= "cp1252")     

        



































