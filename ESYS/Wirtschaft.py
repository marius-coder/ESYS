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


	def GetMonth(self, timestep):
		if 0 <= timestep <= 2976:
			return 1
		if 2976 <= timestep <= 5664:
			return 2
		if 5664 <= timestep <= 8640:
			return 3
		if 8640 <= timestep <= 11520:
			return 4
		if 11520 <= timestep <= 14496:
			return 5
		if 14496 <= timestep <= 17376:
			return 6
		if 17376 <= timestep <= 20352:
			return 7
		if 20352 <= timestep <= 23328:
			return 8
		if 23328 <= timestep <= 26208:
			return 9
		if 26208 <= timestep <= 29184:
			return 10
		if 29184 <= timestep <= 32064:
			return 11
		if 32064 <= timestep <= 35040:
			return 12


    
	def CalcNetMetering(self, gridDemand, gridFeedIn):

		monthBorders = [[0,2976],[2976,5664],[5664,8640],[8640,11520],[11520,14496],[14496,17376],[17376,20352],[20352,23328],[23328,26208],[26208,29184],[29184,32064],[32064,35040]]

		residualFeedIn = 0 #Restliche Einspeisevergütung nach NetMetering
		netMeterFeedIn = 0 #Erhöhte Einspeisevergütung durch NetMetering
		for month in range(12):
			gridDemandMonthly = sum(gridDemand[monthBorders[month][0]:monthBorders[month][1]])
			gridFeedInMonthly = sum(gridFeedIn[monthBorders[month][0]:monthBorders[month][1]])
			difference = min(gridFeedInMonthly, gridDemandMonthly)


			netMeterFeedIn += difference * self.antEnergie * self.priceDemand
			if gridFeedInMonthly > gridDemandMonthly:
				residualFeedIn += (gridFeedInMonthly - difference) * self.priceFeedIn

		gridDemandCosts = self.CalcGridDemand(gridDemand)

		energycosts = gridDemandCosts - (netMeterFeedIn + residualFeedIn)

		return energycosts



















