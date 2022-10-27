# -*- coding: cp1252 -*-

#import required modules
import pandas as pd
import numpy as np
import os
import time

class cla_Gebäude():
    def __init__(self, var_BGF, var_EV):
        self.BGF = var_BGF   #m²
        self.EV = var_EV

        
class cla_PV_Anlage():
    def __init__(self,PV_kWp,var_PV_EK):
        faktor = PV_kWp/250
        self.PV_EK = [i * faktor for i in var_PV_EK]#kW
   
class cla_Batterie():
    
    def __init__(self, var_EntTiefe, var_Effizienz, var_kapMAX, var_LadeEntladeLeistung = 0):
        self.minLadung = var_kapMAX * var_EntTiefe/100  #%
        self.effizienz = var_Effizienz # Einheit %/100
        self.kapazitat = self.minLadung #kWh
        self.maxLadung = var_kapMAX #kWh
        self.Leistung = var_LadeEntladeLeistung #kW
        self.leistung_MAX = var_kapMAX# * 0.5 #kW
        self.verlust = 0 #kW


    def Entladen(self, qtoTake):
        """Entladet das Auto mit einer gegebenen Ladung
        qtoTake: float,  
        Ladung mit dem das Auto entladen wird in kWh
        Return:
        qtoTake: float,
        gibt den Input zuruck. Falls alles entladen werden konnte, ist der return 0"""

        if qtoTake > self.leistung_MAX:
            #Wenn ja wird gekappt
            self.verlust = self.leistung_MAX * (1-self.effizienz)
            self.leistung = self.leistung_MAX * self.effizienz 
        else:
            #Wenn nein, g2g
            self.verlust = qtoTake * (1-self.effizienz) 
            self.leistung = qtoTake 

        #Kontrolle der Leistung
        if self.leistung + self.verlust > self.kapazitat:
            #Wenn nicht genugend Kapazitat vorhanden ist wird die Leistung gekappt
            self.verlust = self.kapazitat * (1-self.effizienz)
            self.leistung = self.kapazitat - self.verlust

        if self.kapazitat - (self.leistung + self.verlust) < self.minLadung:
            #Wenn die mindestladung unterschritten wird die Leistung gekappt
            self.verlust = (self.kapazitat - self.minLadung) * (1-self.effizienz)
            self.leistung = (self.kapazitat - self.minLadung) - self.verlust

        #Ausfuhren des Entladevorgangs
        self.kapazitat -= self.leistung + self.verlust
        qtoTake -= self.leistung 
        return qtoTake
    
    def Laden(self, qtoLoad):
        """Ladet das Auto mit einer gegebenen Ladung
        qtoLoad: float,  
	        Ladung mit dem das Auto geladen wird in kWh
        Return:
        qtoLoad: float,
	        gibt den Input zuruck. Falls alles geladen werden konnte, ist der return 0"""
        if qtoLoad > self.leistung_MAX:
        #Wenn ja wird gekappt
            self.verlust = self.leistung_MAX * (1-self.effizienz)
            self.leistung = self.leistung_MAX * self.effizienz            
        else:
        #Wenn nein, g2g
            self.verlust = qtoLoad * (1-self.effizienz)
            self.leistung = qtoLoad * self.effizienz 
            
        #Kontrolle ob die Batterie uber die Maximale Kapazitat geladen werden wurde
        if self.kapazitat + self.leistung > self.maxLadung:
            self.verlust = (self.maxLadung - self.kapazitat) * (1-self.effizienz)
            self.leistung = (self.maxLadung - self.kapazitat) * self.effizienz
            
        #Ausfuhren des Ladevorgangs
        self.kapazitat += self.leistung
        qtoLoad -= (self.leistung + self.verlust)
        
        return qtoLoad
    
class cla_Data_Tracking():    
    def __init__(self,arg_PV_Anlage,arg_Gebäude,arg_Battery,PV_kWp):
        self.Bat_kWh = arg_Battery.maxLadung
        self.PV_kWp = PV_kWp
        self.PV_Erzeugung = arg_PV_Anlage.PV_EK
        self.Gebäudeverbrauch = arg_Gebäude.EV
        self.PV_Direktverbrauch = np.zeros(8760)
        self.Batteriekapazität = np.zeros(8760)
        self.Batterieeinspeisung = np.zeros(8760)
        self.Batterieentladung = np.zeros(8760)
        self.Batterieverluste = np.zeros(8760)
        self.Netzeinspeisung = np.zeros(8760)
        self.Netzbezug = np.zeros(8760)    
        self.EigenverbrauchDavor = np.zeros(8760)
        self.EigenverbrauchDanach = np.zeros(8760)


    #CleanData sorgt dafür dass alle Datenpunkte positiv sind
    def CleanData(self):
        for attr,val in self.__dict__.items():
            #Kontrolle ob unsere Variable iterierbar ist
            try:
                iter(val)
                if any(val < 0):
                    setattr(self, attr, abs(val))
            except TypeError:
                continue


class cla_Costs():

    def __init__(self, obj_Datatracker, price_grid,price_einspeisung,price_battery,PV_kWp=250):
        self.obj_Datatracker = obj_Datatracker
        self.PV_kWp = PV_kWp
        self.Bat_kWh = obj_Datatracker.Bat_kWh
        self.PV_cost = 1200 # €/kWp
        self.battery_cost = price_battery    # €/kWh
        self.strompreiserhöhung = 0.01 #2% Strompreiserhöhung pro Jahr
        self.Cost_Operation_Percent = 1 # % der Investmestkosten pro Jahr
        self.price_feed_in = price_einspeisung  # €/kWh
        self.price_grid = price_grid  # €/kWh 
        self.price_feed_in_OLD = price_einspeisung  # €/kWh
        self.price_grid_OLD = price_grid  # €/kWh
        self.Life = 20 #Years
        self.Investment_costs = self.Bat_kWh * self.battery_cost
        self.total_costs = self.Get_Costs()

    def CalcNewGridPrice(self, year):
        factor = (1+self.strompreiserhöhung)**year
        self.price_feed_in = (1+self.strompreiserhöhung) * self.price_feed_in
        self.price_grid =  (1+self.strompreiserhöhung) * self.price_grid
    def Get_Costs(self):
        totalOperationalCosts = 0
        for year in range(self.Life):
            self.CalcNewGridPrice(year)

            kosten = 0 # sum(self.obj_Datatracker.Netzbezug) * self.price_grid
            #PV_Direktverbrauch = sum(self.obj_Datatracker.PV_Direktverbrauch) * self.price_grid
            #Netzeinspeisung = sum(self.obj_Datatracker.Netzeinspeisung) * self.price_feed_in
            Batterieentladung = sum(self.obj_Datatracker.Batterieentladung) * self.price_grid
            Batterieeinspeisung = sum(self.obj_Datatracker.Batterieeinspeisung) * self.price_feed_in
            vergütung = Batterieentladung - Batterieeinspeisung
            totalOperationalCosts += vergütung

        return -self.Investment_costs + totalOperationalCosts 


           
 
#%%
class Model():

    def Simulate(self,var_BGF, var_battery_kWh, price_grid, price_battery, PV_kWp, price_einspeisung,verbose = False, plotting = False):
        self.price_grid = price_grid
        self.price_battery = price_battery
        Test_hourly = []
        obj_Gebäude = cla_Gebäude(var_BGF,pd.read_csv(".\Data\Verbrauch.csv", sep=";", decimal=",")["Verbrauch "].values.tolist())
        obj_PV_Anlage = cla_PV_Anlage(PV_kWp,pd.read_csv(".\Data\PV.csv", sep=";", decimal=",")["PV-Energie (DC) "].values.tolist())
        obj_Batterie = cla_Batterie(var_EntTiefe = 20, var_Effizienz = 0.95,var_kapMAX = var_battery_kWh)
        obj_Datatracker = cla_Data_Tracking(arg_PV_Anlage = obj_PV_Anlage, arg_Gebäude = obj_Gebäude, arg_Battery = obj_Batterie,PV_kWp=PV_kWp)
        
        wohnhaus = pd.read_csv(".\Data\PV_Wohnen.csv", sep=";", decimal=",")["PV-Energie (DC) "].values.tolist()

        t0 = time.time() #Timekeeping
        for it_hour in range(8760):
            #Residuallast
            if obj_PV_Anlage.PV_EK[it_hour] < 0: obj_PV_Anlage.PV_EK[it_hour]=0
            if wohnhaus[it_hour] < 0: wohnhaus[it_hour]=0
            #obj_PV_Anlage.PV_EK[it_hour] += wohnhaus[it_hour]
            var_ResLast = obj_PV_Anlage.PV_EK[it_hour] - obj_Gebäude.EV[it_hour]
            #Tracking des Direktverbrauches
            obj_Datatracker.PV_Direktverbrauch[it_hour] = min(obj_PV_Anlage.PV_EK[it_hour], obj_Gebäude.EV[it_hour])

            #Debug Prints
            if verbose == True:
                print("PV_Ertrag: ", obj_PV_Anlage.PV_EK[it_hour])
                print("Gebäude_Bezug: ", obj_Gebäude.EV[it_hour])
                print("ResLast_Davor: ", var_ResLast)

            obj_Batterie.verlust = 0
            obj_Batterie.leistung = 0
            if var_ResLast > 0: 
                obj_Datatracker.EigenverbrauchDavor[it_hour] = var_ResLast
                #Einspeisefall
                var_ResLast = obj_Batterie.Laden(var_ResLast)
                obj_Datatracker.Batterieeinspeisung[it_hour] = obj_Batterie.leistung
                #Restverwertung via Netz + Tracking
                obj_Datatracker.Netzeinspeisung[it_hour] = var_ResLast
                obj_Datatracker.EigenverbrauchDanach[it_hour] = var_ResLast

            elif var_ResLast < 0:
                #Entladefall
                var_ResLast = abs(var_ResLast) #Die späteren Funktionen gehen immer von einer Positiven Zahl aus.
                var_ResLast = obj_Batterie.Entladen(var_ResLast)
                obj_Datatracker.Batterieentladung[it_hour] = obj_Batterie.leistung + obj_Batterie.verlust
                #Restverwertung via Netz + Tracking
                obj_Datatracker.Netzbezug[it_hour] = var_ResLast
        
            #Tracking der allgemeinen Daten
            obj_Datatracker.Batterieverluste[it_hour] = obj_Batterie.verlust
            obj_Datatracker.Batteriekapazität[it_hour] = obj_Batterie.kapazitat
        
            #Debug Prints
            if verbose == True:
                print("ResLast_Danach: ", var_ResLast)
                print("Bat_Kapazität: ", obj_Batterie.kapazitat)
                print("Bat_Ladeleistung: ", obj_Batterie.Leistung)
                print("Bat_Verlust: ", obj_Batterie.verlust)
                print("Netzbezug: ", obj_Datatracker.Netzbezug[it_hour])
                print("NetzEinspeisung: ", obj_Datatracker.Netzeinspeisung[it_hour]) 
                print("Verbrauch: ", obj_Datatracker.Gebäudeverbrauch[it_hour])
                print("PV: ", obj_Datatracker.PV_Erzeugung[it_hour])
                print("BatLadung: ", obj_Datatracker.Batterieeinspeisung[it_hour])
                print("BatEntladung: ", obj_Datatracker.Batterieentladung[it_hour])
                print("BatVerlust: ", obj_Datatracker.Batterieverluste[it_hour])
                
                
                print(it_hour)
            flows_in_hour = abs(obj_Datatracker.Netzbezug[it_hour]) + abs(obj_Datatracker.Batterieentladung[it_hour]) + abs(obj_Datatracker.PV_Erzeugung[it_hour])
            flows_out_hour = abs(obj_Datatracker.Netzeinspeisung[it_hour]) + abs(obj_Datatracker.Batterieeinspeisung[it_hour]) + \
                            abs(obj_Datatracker.Batterieverluste[it_hour]) + abs(obj_Datatracker.Gebäudeverbrauch[it_hour])
            if abs(flows_in_hour - flows_out_hour) > 0.00001:
                raise ValueError(f"ENERGIEBILANZ STIMMT NICHT! Stunde: {it_hour} Differenz: {flows_in_hour - flows_out_hour}  Bat: {obj_Datatracker.Bat_kWh}, PV: {obj_Datatracker.PV_kWp}")
            Test_hourly.append(flows_in_hour - flows_out_hour)

        #Test ob die Energiebilanz stimmt
        obj_Datatracker.CleanData()
        flows_in = [sum(obj_Datatracker.Netzbezug),sum(obj_Datatracker.Batterieentladung), sum(obj_Datatracker.PV_Erzeugung)]
        flows_out = [sum(obj_Datatracker.Netzeinspeisung),sum(obj_Datatracker.Batterieeinspeisung), 
                            sum(obj_Datatracker.Batterieverluste),sum(obj_Datatracker.Gebäudeverbrauch)]
        Test = sum(flows_in) - sum(flows_out)
        if abs(Test) > 0.00001:
           raise ValueError(f"ENERGIEBILANZ STIMMT NICHT!: {Test} Bat: {obj_Datatracker.Bat_kWh}")



        objCosts= cla_Costs(obj_Datatracker, self.price_grid, price_einspeisung, self.price_battery)
        self.result = {
            #"Gesamtkosten" : obj_Costs.total_costs,
            #"Investmentkosten" : obj_Batterie.maxLadung * self.price_battery,
            #"Operationskosten" : self.CalcOperationalCosts(obj_Datatracker),
            "Netzeinspeisung" : sum(obj_Datatracker.Netzeinspeisung),
            "Netzbezug" : sum(obj_Datatracker.Netzbezug),
            "PV_Erzeugung" : sum(obj_Datatracker.PV_Erzeugung),
            "Gebäudeverbrauch" : sum(obj_Datatracker.Gebäudeverbrauch),
            "Batterieeinspeisung" : sum(obj_Datatracker.Batterieeinspeisung),
            "Batterieentladung" : sum(obj_Datatracker.Batterieentladung),
            "Batterieverluste" : sum(obj_Datatracker.Batterieverluste)
            }
        self.eigVerbrauchDavor = sum(obj_Datatracker.EigenverbrauchDavor)
        self.eigVerbrauchDanach = sum(obj_Datatracker.EigenverbrauchDanach)
        self.total_costs = objCosts.total_costs
        return self.result
#%%





def main():
    #this should work
    model = Model()
    
    result = model.Simulate(var_BGF=100, var_battery_kWh = 500,price_grid=0.2, price_battery=1500, PV_kWp=250, price_einspeisung= 0.05, verbose = False, plotting = True)
    
    print(f"Gebäudeverbrauch: {result['Gebäudeverbrauch']:.2f} kWh")
    print(f"PV_Erzeugung: {result['PV_Erzeugung']:.2f} kWh")
    print(f"Netzeinspeisung: {result['Netzeinspeisung']:.2f} kWh")
    print(f"Netzbezug: {result['Netzbezug']:.2f} kWh")
    

if __name__ == "__main__":  # https://www.youtube.com/watch?v=sugvnHA7ElY
    main() 