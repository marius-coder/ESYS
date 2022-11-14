# -*- coding: cp1252 -*-

import numpy as np

from profileInitializer import CreateProfiles
from Batterie import Batterie

startConditions = {
    "A0" : 1,
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
    "C3" : 1,
    "D1" : 1,
    "D2" : 0,
    "D3" : 0,
    "Sport-30" : 0,
    "Sport-100" : 0,
    "Sport-200" : 0}



class Simulation():

    def __init__(self, profiles) -> None:
        self.profiles = profiles
        self.battery = Batterie(var_EntTiefe = 0.2, var_Effizienz = 0.95,var_kapMAX = 10000, infoAmount= 35036)
        self.gridDemand = np.zeros(35036)
        self.gridFeedIn = np.zeros(35036)

        self.selfConsumptionBeforeCom = np.zeros(35036)
        self.selfConsumptionAfterCom = np.zeros(35036)


    def Simulate(self, peerToPeer= False, sharedGeneration = False,verbose = False):

        for timestep in range(35036):
            for building in self.profiles:
                #Residuallast der einzelnen Gebäude ermitteln
                demand = building.demand[timestep] + building.demandEV[timestep] + building.demandHP[timestep]
                building.residualLoad[timestep] = demand - building.production[timestep]
                building.selfConsumptionBeforeCom[timestep] = min(demand, building.production[timestep]) #Eigenverbrauch vor E-Gemeinschaft
                building.gridDemandBeforeCom[timestep] = demand - building.selfConsumptionBeforeCom[timestep] #Netzbezug vor E-Gemeinschaft
                building.gridFeedInBeforeCom[timestep] = abs(building.production[timestep] - building.selfConsumptionBeforeCom[timestep]) #Netzeinspeisung vor E-Gemeinschaft


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
            for building in self.profiles:
                if building.residualLoad[timestep] > 0:
                    #Einspeisung dynamisch aufteilen
                    allocatedEnergy = SumEnergytoAllocate / residualDemandSum * building.residualLoad[timestep]
                    building.residualLoad[timestep] -= allocatedEnergy
                    checkResidualProdSum += allocatedEnergy
                    #Daten loggen                
                    demand = building.demand[timestep] + building.demandEV[timestep] + building.demandHP[timestep]
                    building.selfConsumptionAfterCom[timestep] = building.selfConsumptionBeforeCom[timestep] #Eigenverbrauch nach E-Gemeinschaft
                    building.gridDemandAfterCom[timestep] = demand - (building.selfConsumptionAfterCom[timestep] + allocatedEnergy) #Netzbezug nach E-Gemeinschaft
                    building.gridFeedInAfterCom[timestep] = building.gridFeedInBeforeCom[timestep] #Netzeinspeisung nach E-Gemeinschaft   
                
                elif building.residualLoad[timestep] < 0:
                    #Residuallast dynamisch aufteilen
                    allocatedEnergy = abs(SumEnergytoAllocate / residualProductionSum * building.residualLoad[timestep])
                    building.residualLoad[timestep] -= allocatedEnergy
                    #checkResidualProdSum += allocatedEnergy
                    #Daten loggen
                    demand = building.demand[timestep] + building.demandEV[timestep] + building.demandHP[timestep]
                    building.selfConsumptionAfterCom[timestep] = building.selfConsumptionBeforeCom[timestep]
                    building.gridDemandAfterCom[timestep] = building.gridDemandBeforeCom[timestep]
                    building.gridFeedInAfterCom[timestep] = abs(building.production[timestep] - building.selfConsumptionAfterCom[timestep]) - allocatedEnergy

            #Kontrolle ob die gesamte Verfügbare Energie verteilt woren ist (Auf 6 Kommastellen)
            if round(checkResidualProdSum,6) != round(min(abs(residualProductionSum),residualDemandSum),6):                
                raise ValueError(f"Allocated Energy must be 0. It is {allocatedEnergy - min(abs(residualProductionSum),residualDemandSum)}")
            if round(residualDemandSum,6) < 0:
                raise ValueError(f"Demand Energy must be grater than 0. It is {round(residualDemandSum,6)}")
            #negative Residuallast updaten
            residualProductionSum += round(checkResidualProdSum,6)
            residualDemandSum -= round(checkResidualProdSum,6)

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

            print(f"Gebäude: {building.name}")
            print(f"Gebäudebezug Davor: {sum(building.gridDemandBeforeCom)}")
            print(f"Gebäudebezug Danach: {sum(building.gridDemandAfterCom)}")
            print(f"Gebäudeeinspeisung Davor: {sum(building.gridFeedInBeforeCom)}")
            print(f"Gebäudeeinspeisung Danach: {sum(building.gridFeedInAfterCom)}")

        costsBefore = 0
        compBefore = 0
        
        costsAfter = 0
        compAfter = 0
        for building in self.profiles:
            costsBefore += building.gridCostsBeforeCom
            compBefore += building.gridCompFeedInBeforeCom
            costsAfter += building.gridCostsAfterCom
            compAfter += building.gridCompFeedInAfterCom

        print(f"Costs for Griddemand before Energy Community: {costsBefore}")
        print(f"Costs for Griddemand after Energy Community: {costsAfter}")
        print(f"Difference: {costsBefore-costsAfter}")
        print(f"Compensation for GridFeedin before Energy Community: {compBefore}")
        print(f"Compensation for GridFeedin after Energy Community: {compAfter}")
        print(f"Difference: {compBefore-compAfter}")
        print(f"Final Gain from Community: {(costsBefore-costsAfter)-(compBefore-compAfter)}")


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
        flowsIn = production + abs(self.gridDemand[timestep]) + abs(self.battery.entladeEnergie[timestep])

        #Negative Energieflüsse nach Außen
        flowsOut = demand + abs(self.gridFeedIn[timestep]) + abs(self.battery.ladeEnergie[timestep]) + abs(self.battery.verluste[timestep])

        #Energieflüsse testen
        Test = flowsIn - flowsOut
        if round(abs(Test),3) != 0:
           raise ValueError(f"ENERGIEBILANZ STIMMT NICHT!: {Test} Zeitschritt: {timestep}")

profileSim = CreateProfiles(startConditions)

sim = Simulation(profileSim)

sim.Simulate()
sim.TestFlows()
















































