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

    def __init__(self, profiles, econParameters, sharedGenerationkWp = 0,peerToPeer= False, sharedGeneration= False, netMetering= False) -> None:
        self.profiles = profiles
        self.battery = Batterie(var_EntTiefe = 0.2, var_Effizienz = 0.95,var_kapMAX = 10000, infoAmount= 35036)

        self.sharedGenerationkWp = sharedGenerationkWp
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


    def CalcEEG(self, timestep, residualProductionSum, residualDemandSum, checkResidualProdSum):
        SumEnergytoAllocate = min(abs(residualProductionSum),residualDemandSum)
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
        return checkResidualProdSum

    def Simulate(self,verbose = False):

        for timestep in range(35036):
            for building in self.profiles:
                #Residuallast der einzelnen Geb?ude ermitteln
                building.production[timestep] += self.sharedGenerationProfile[timestep]/len(self.profiles) #Shared Generation hinzuf?gen zu Produktion. Hier w?re auch eine nicht Gleichm??ige Aufteilung zu machen
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

            #Direktzuweisung f?r andere Geb?ude
            
            checkResidualProdSum = 0
            allocatedEnergy =  0
            if self.peerToPeer == True:
                checkResidualProdSum = self.CalcEEG(timestep= timestep, residualProductionSum= residualProductionSum, residualDemandSum= residualDemandSum, checkResidualProdSum= checkResidualProdSum)
                #Kontrolle ob die gesamte Verf?gbare Energie verteilt woren ist (Auf 6 Kommastellen)
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

            #Falls nach der direktzuweisung noch Energie ?brig ist, wird der gemeinschaftsspeicher bef?llt
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
            building.SetAttributes(antEnergie= self.econParameters["antEnergie"], antAbgabe= self.econParameters["antAbgabe"]
                                   , antSteuer= self.econParameters["antSteuer"], priceDemand= self.econParameters["priceDemand"], 
                                   priceFeedIn= self.econParameters["priceFeedIn"])
            building.gridCostsBeforeCom = building.CalcGridDemand(building.gridDemandBeforeCom, mode= "Normal")
            building.gridCompFeedInBeforeCom = building.CalcGridFeedIn(building.gridFeedInBeforeCom, mode= "Normal")

            building.gridCostsAfterCom = building.CalcGridDemand(gridDemand= building.gridDemandBeforeCom, mode= "EC", gridDemandEC= building.gridDemandAfterCom)
            building.gridCompFeedInAfterCom = building.CalcGridFeedIn(gridFeedIn= building.gridFeedInBeforeCom, mode= "EC", gridFeedInEC= building.gridFeedInAfterCom)

            building.CalcNetMetering(gridDemand= building.gridDemandBeforeCom, gridFeedIn= building.gridFeedInBeforeCom)
            if verbose == True:
                print(f"Geb?ude: {building.name}")
                print(f"Geb?udebezug Davor: {sum(building.gridDemandBeforeCom)}")
                print(f"Geb?udebezug Danach: {sum(building.gridDemandAfterCom)}")
                print(f"Geb?udeeinspeisung Davor: {sum(building.gridFeedInBeforeCom)}")
                print(f"Geb?udeeinspeisung Danach: {sum(building.gridFeedInAfterCom)}")

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
        print(f"==================================================================")
        print(f"======== Effects of Energy Community ============")
        print(f"Costs for Griddemand before Energy Community: {costsBefore}")
        print(f"Costs for Griddemand after Energy Community: {costsAfter}")
        print(f"Difference: {costsBefore-costsAfter}")
        print(f"Compensation for GridFeedin before Energy Community: {compBefore}")
        print(f"Compensation for GridFeedin after Energy Community: {compAfter}")
        print(f"Difference: {compAfter-compBefore}")
        print(f"Final Gain from Community: {(costsBefore-costsAfter)+(compAfter-compBefore)}")
        print(f"==================================================================")
        print(f"======== Effects of Net Metering ============")
        
        print(f"Gridcosts with Net Metering: {costsAfterNetMetering}")
        print(f"Compensation with Net Metering: {compAfterNetMetering}")

        return 

    def TestFlows(self):
        """Testet die Energiefl?sse auf Gemeinschaftsebene. Summe der Energiefl?sse m?ssen 0 ergeben.
        Return:
            Hat keinen Returnwert"""
        demand = 0
        production = 0
        for building in self.profiles:
            demand += sum(building.demand) + sum(building.demandEV) + sum(building.demandHP)
            production += sum(building.production)

        #Positive Energiefl?sse von Au?en (Netzbezug, Batterieentladung, PV-Produktion)
        flowsIn = production + abs(sum(self.gridDemand)) + abs(sum(self.battery.entladeEnergie))

        #Negative Energiefl?sse nach Au?en
        flowsOut = demand + abs(sum(self.gridFeedIn)) + abs(sum(self.battery.ladeEnergie)) + abs(sum(self.battery.verluste))

        #Energiefl?sse testen
        Test = flowsIn - flowsOut
        if round(abs(Test),3) != 0:
           raise ValueError(f"ENERGIEBILANZ STIMMT NICHT!: {Test}")

    def TestFlowsHourly(self, timestep):
        """Testet die Energiefl?sse auf Gemeinschaftsebene auf Stundenbasis. Summe der Energiefl?sse m?ssen 0 ergeben.
        timestep:
            Zeitschritt der getestet wird
        Return:
            Hat keinen Returnwert"""
        demand = 0
        production = 0
        for building in self.profiles:
            demand += building.demand[timestep] + building.demandEV[timestep] + building.demandHP[timestep]
            production += building.production[timestep]

        #Positive Energiefl?sse von Au?en (Netzbezug, Batterieentladung, PV-Produktion)
        flowsIn = production + abs(self.gridDemand[timestep]) + abs(self.battery.entladeEnergie[timestep])

        #Negative Energiefl?sse nach Au?en
        flowsOut = demand + abs(self.gridFeedIn[timestep]) + abs(self.battery.ladeEnergie[timestep]) + abs(self.battery.verluste[timestep])

        #Energiefl?sse testen
        Test = flowsIn - flowsOut
        if timestep == 442:
            print("")

        if round(abs(Test),1) != 0:
           raise ValueError(f"ENERGIEBILANZ STIMMT NICHT!: {Test} Zeitschritt: {timestep}")

profileSim = CreateProfiles(startConditions)

econParameters = {
    "antEnergie" : 0.6,
    "antAbgabe" : 0.2,
    "antSteuer" : 0.2,
    "priceDemand" : 0.3,
    "priceFeedIn" : 0.1,    
    }
sim = Simulation(profileSim,econParameters= econParameters, sharedGenerationkWp= 1000, peerToPeer= True)

sim.Simulate()
sim.TestFlows()
















































