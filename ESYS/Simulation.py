# -*- coding: cp1252 -*-

import numpy as np

from profileInitializer import CreateProfiles
from Batterie import Batterie

startConditions = {
    "A0" : 16,
    "B0" : 12,
    "C0" : 7,
    "A1" : 4,
    "A2" : 6,
    "A3" : 2,
    "B1" : 2,
    "B2" : 5,
    "B3" : 3,
    "C1" : 0,
    "C2" : 1,
    "C3" : 0,
    "D1" : 5,
    "D2" : 0,
    "D3" : 0,
    "Sport-30" : 0,
    "Sport-100" : 10,
    "Sport-200" : 10}



class Simulation():

    def __init__(self, profiles) -> None:
        self.profiles = profiles
        self.battery = Batterie(var_EntTiefe = 0.2, var_Effizienz = 0.95,var_kapMAX = 10000, infoAmount= 35036)
        self.gridDemand = np.zeros(35036)
        self.gridFeedIn = np.zeros(35036)

        self.selfConsumptionBeforeCom = np.zeros(35036)
        self.selfConsumptionAfterCom = np.zeros(35036)


    def Simulate(self,verbose = False):

        for timestep in range(35036):
            for building in self.profiles:
                #Residuallast der einzelnen Gebäude ermitteln
                demand = building.demand[timestep] + building.demandEV[timestep] + building.demandHP[timestep]
                building.residualLoad[timestep] = demand - building.production[timestep]
                building.selfConsumptionBeforeCom[timestep] = min(demand, building.production[timestep]) #Eigenverbrauch vor E-Gemeinschaft
                building.gridDemandBeforeCom[timestep] = demand - building.selfConsumptionBeforeCom[timestep] #Netzbezug vor E-Gemeinschaft
                building.gridFeedInBeforeCom[timestep] = building.production[timestep] - building.selfConsumptionBeforeCom[timestep] #Netzeinspeisung vor E-Gemeinschaft


            #Summe der gesamten Residuallast der Gemeinschaft ermitteln
            residualDemandSum = sum([building.residualLoad[timestep] for building in self.profiles if building.residualLoad[timestep] > 0])
            residualProductionSum = sum([building.residualLoad[timestep] for building in self.profiles if building.residualLoad[timestep] < 0])
            print(f"Timestep: {timestep}")
            if verbose == True:
                
                print(f"residualDemandSum: {residualDemandSum}")
                print(f"residualProductionSum: {residualProductionSum}")
                print("----------------------------------------------------")

            #Direktzuweisung für andere Gebäude
            SumEnergytoAllocate = min(abs(residualProductionSum),residualDemandSum)
            checkResidualProdSum = 0
            allocatedEnergy =  0
            if residualProductionSum < 0: #Nur wenn Energie übrig ist
                
                for building in self.profiles:
                    if building.residualLoad[timestep] < 0: #Wenn ResLast negativ ist dürfen wir die Residuallast nicht verändern
                        continue
                    #Einspeisung dynamisch aufteilen
                    allocatedEnergy = SumEnergytoAllocate / residualDemandSum * building.residualLoad[timestep]
                    building.residualLoad[timestep] -= allocatedEnergy
                    checkResidualProdSum += allocatedEnergy
                    demand = building.demand[timestep] + building.demandEV[timestep] + building.demandHP[timestep]
                    building.selfConsumptionAfterCom[timestep] = min(demand, (building.production[timestep]+allocatedEnergy)) #Eigenverbrauch vor E-Gemeinschaft
                    building.gridDemandAfterCom[timestep] = demand - building.selfConsumptionAfterCom[timestep] #Netzbezug vor E-Gemeinschaft
                    building.gridFeedInAfterCom[timestep] = building.production[timestep] - building.selfConsumptionAfterCom[timestep] #Netzeinspeisung vor E-Gemeinschaft
                    

                #Kontrolle ob die gesamte Verfügbare Energie verteilt woren ist (Auf 6 Kommastellen)
                if round(checkResidualProdSum,6) != round(min(abs(residualProductionSum),residualDemandSum),6):                
                    raise ValueError(f"Allocated Energy must be 0. It is {allocatedEnergy - min(abs(residualProductionSum),residualDemandSum)}")
                if round(residualDemandSum,6) < 0:
                    raise ValueError(f"Demand Energy must be grater than 0. It is {round(residualDemandSum,6)}")
            #negative Residuallast updaten
            residualProductionSum += round(checkResidualProdSum,6)
            residualDemandSum -= round(checkResidualProdSum,6)
            if timestep == 36:
                print("")
            #Falls nach der direktzuweisung noch Energie übrig ist, wird der gemeinschaftsspeicher befüllt
            if residualProductionSum < 0:
                residualProductionSum = abs(residualProductionSum)
                #Batterie Laden
                residualProductionSum = self.battery.Laden(qtoLoad= residualProductionSum, timestep= timestep)
                #restliche Energie in das Netz einspeisen
                self.gridFeedIn[timestep] = residualProductionSum

            if round(residualDemandSum,6) > 0:
                #Batterie entladen
                residualDemandSum = self.battery.Entladen(qtoTake= residualDemandSum, timestep= timestep)
                #restliche Energie aus dem Netz beziehen
                self.gridDemand[timestep] = residualDemandSum

            #self.battery.Entladen(qttoTake= 5, )
            self.battery.TestBattery(timestep= timestep)
            self.TestFlowsHourly(timestep= timestep)

        for building in self.profiles:
            building.SetAttributes(antEnergie= 0.32, antAbgabe= 0.34, antSteuer= 0.34, priceDemand= 0.3, priceFeedIn= 0.1)
            building.gridCostsBeforeCom = building.CalcGridDemand(building.gridDemandBeforeCom)
            building.gridCompFeedInBeforeCom = building.CalcGridFeedIn(building.gridFeedInBeforeCom)

            building.gridCostsAfterCom = building.CalcGridDemand(building.gridDemandAfterCom)
            building.gridCompFeedInAfterCom = building.CalcGridFeedIn(building.gridFeedInAfterCom)

        costsBefore = 0
        compBefore = 0
        
        costsAfter = 0
        compAfter = 0
        for building in self.profiles:
            costsBefore += building.gridCostsBeforeCom
            compBefore += building.gridCompFeedInBeforeCom
            costsAfter += building.gridCostsAfterCom
            compAfter += building.gridCompFeedInAfterCom

        print(f"Costs before Energy Community: {costsBefore}")
        print(f"Costs after Energy Community: {costsAfter}")
        print(f"Difference: {costsBefore-costsAfter}")
        print(f"Compensation before Energy Community: {compBefore}")
        print(f"Compensation after Energy Community: {compAfter}")
        print(f"Difference: {compAfter-compBefore}")
        print(f"Final Gain from Community: {(costsBefore-costsAfter)-(compAfter-compBefore)}")


        return 

    def TestFlows(self):
        """Testet die Energieflüsse auf Gemeinschaftsebene. Summe der Energieflüsse müssen 0 ergeben.
        Return:
            Hat keinen Returnwert"""
        demand = 0
        production = 0
        for building in self.profiles:
            demand += sum(building.demand) + sum(building.demandEV) + sum(building.demandHP)
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
            demand += building.demand[timestep] + building.demandEV[timestep] + building.demandHP[timestep]
            production += building.production[timestep]

        #Positive Energieflüsse von Außen (Netzbezug, Batterieentladung, PV-Produktion)
        gridDemand = abs(self.gridDemand[timestep])
        entladung = abs(self.battery.entladeEnergie[timestep])

        flowsIn = production + abs(self.gridDemand[timestep]) + abs(self.battery.entladeEnergie[timestep])

        #Negative Energieflüsse nach Außen
        feedIn = abs(self.gridFeedIn[timestep])
        ladung = abs(self.battery.ladeEnergie[timestep])
        verluste = abs(self.battery.verluste[timestep])

        flowsOut = demand + abs(self.gridFeedIn[timestep]) + abs(self.battery.ladeEnergie[timestep]) + abs(self.battery.verluste[timestep])

        #Energieflüsse testen
        Test = flowsIn - flowsOut
        if round(abs(Test),3) != 0:
           raise ValueError(f"ENERGIEBILANZ STIMMT NICHT!: {Test} Zeitschritt: {timestep}")

profileSim = CreateProfiles(startConditions)

sim = Simulation(profileSim)

sim.Simulate()
sim.TestFlows()
















































