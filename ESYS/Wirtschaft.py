# -*- coding: cp1252 -*-


class Econ():


	def __init__(self, antEnergie, antAbgabe, antSteuer, priceDemand, priceFeedIn) -> None:
		self.antEnergie = antEnergie
		self.antAbgabe = antAbgabe
		self.antSteuer = antSteuer
		self.priceDemand = priceDemand
		self.priceFeedIn = priceFeedIn


	def SetAttributes(self, antEnergie= None, antAbgabe= None, antSteuer= None, priceDemand= None, priceFeedIn= None):
		if antEnergie != None:
			self.antEnergie = antEnergie
		if antAbgabe != None:
			self.antAbgabe = antAbgabe
		if antSteuer != None:
			self.antSteuer = antSteuer
		if priceDemand != None:
			self.priceDemand = priceDemand
		if priceFeedIn != None:
			self.priceFeedIn = priceFeedIn


	def CalcGridDemand(self, gridDemand):
		return sum(gridDemand) * self.priceDemand

	def CalcGridFeedIn(self, gridFeedIn):
		return sum(gridFeedIn) * self.priceFeedIn

	def CalcEconFlows(self, profile, selfConsumption, demand, production, gridDemand, gridFeedIn):
		"""Berechnet die monetären Flüsse. Diese Funktion geht von kWh aus"""

		





		pass




    




























