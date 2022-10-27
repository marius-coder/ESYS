# -*- coding: cp1252 -*-
import numpy as np

class Batterie():
    
    def __init__(self, var_EntTiefe, var_Effizienz, var_kapMAX, var_LadeEntladeLeistung = 0, infoAmount= 0):
        self.minLadung = var_kapMAX * var_EntTiefe  #%
        self.effizienz = var_Effizienz # Einheit %/100
        self.kapazit�t = self.minLadung #kWh
        self.maxLadung = var_kapMAX #kWh
        self.Leistung = var_LadeEntladeLeistung #kW
        self.kapazit�tMAX = var_kapMAX# * 0.5 #kW
        self.verlust = 0 #kW

        self.ladeEnergie = np.zeros(infoAmount)
        self.entladeEnergie = np.zeros(infoAmount)
        self.verluste = np.zeros(infoAmount)
        
    def Entladen(self, qtoTake, timestep):
        """Entladet die Batterie mit einer gegebenen Ladung
        qtoTake: float,  
        Ladung mit dem die Batterie entladen wird in kWh
        Return:
        qtoTake: float,
        gibt den Input zuruck. Falls alles entladen werden konnte, ist der return 0"""
        self.leistung = 0
        self.verlust = 0

        if qtoTake > self.kapazit�tMAX:
            #Wenn ja wird gekappt
            self.verlust = self.kapazit�tMAX * (1-self.effizienz)
            self.leistung = self.kapazit�tMAX * self.effizienz 
        else:
            #Wenn nein, g2g
            self.verlust = qtoTake * (1-self.effizienz) 
            self.leistung = qtoTake 

        #Kontrolle der Leistung
        if self.leistung + self.verlust > self.kapazit�t:
            #Wenn nicht genugend Kapazitat vorhanden ist wird die Leistung gekappt
            self.verlust = self.kapazit�t * (1-self.effizienz)
            self.leistung = self.kapazit�t - self.verlust

        if self.kapazit�t - (self.leistung + self.verlust) < self.minLadung:
            #Wenn die mindestladung unterschritten wird die Leistung gekappt
            self.verlust = (self.kapazit�t - self.minLadung) * (1-self.effizienz)
            self.leistung = (self.kapazit�t - self.minLadung) - self.verlust

        #Ausfuhren des Entladevorgangs
        self.kapazit�t -= self.leistung + self.verlust
        qtoTake -= self.leistung 

        #Tracken der relevanten Daten
        self.entladeEnergie[timestep] = self.leistung
        self.verluste[timestep] = self.verlust

        return qtoTake + self.verlust
    
    def Laden(self, qtoLoad, timestep):
        """Ladet die Batterie mit einer gegebenen Ladung
        qtoLoad: float,  
	        Ladung mit dem die Batterie geladen wird in kWh
        Return:
        qtoLoad: float,
	        gibt den Input zuruck. Falls alles geladen werden konnte, ist der return 0"""
        self.leistung = 0
        self.verlust = 0


        if qtoLoad > self.kapazit�tMAX:
        #Wenn ja wird gekappt
            self.verlust = self.kapazit�tMAX * (1-self.effizienz)
            self.leistung = self.kapazit�tMAX * self.effizienz            
        else:
        #Wenn nein, g2g
            self.verlust = qtoLoad * (1-self.effizienz)
            self.leistung = qtoLoad * self.effizienz 
            
        #Kontrolle ob die Batterie uber die Maximale Kapazitat geladen werden wurde
        if self.kapazit�t + self.leistung > self.maxLadung:
            self.verlust = (self.maxLadung - self.kapazit�t) * (1-self.effizienz)
            self.leistung = (self.maxLadung - self.kapazit�t) * self.effizienz
            
        #Ausfuhren des Ladevorgangs
        self.kapazit�t += self.leistung
        qtoLoad -= (self.leistung + self.verlust)

        #Tracken der relevanten Daten
        self.ladeEnergie[timestep] = self.leistung
        self.verluste[timestep] = self.verlust
        
        return qtoLoad

    def TestBattery(self, timestep):

        if self.kapazit�t < 0:
            raise ValueError("Batterie hat eine negative Ladung. Ladung: {self.kapazit�t}. Zeitpunkt: {timestep}")
        if self.kapazit�t > self.kapazit�tMAX:
            raise ValueError("Batterie ist �ber die maximale Ladung beladen. Ladung: {self.kapazit�t}, Maximale Ladung: {self.kapazit�tMAX}, Zeitpunkt: {timestep}")


