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


	def CalcGridDemand(self, gridDemand, mode, gridDemandEC=[]):
		if mode == "Normal":
			return sum(gridDemand) * self.priceDemand
		if mode == "EC":
			difference = sum(gridDemand) - sum(gridDemandEC)
			return (sum(gridDemand)-difference) * self.priceDemand + difference * ((self.priceDemand + self.priceFeedIn)/2)

	def CalcGridFeedIn(self, gridFeedIn, mode, gridFeedInEC=[]):
		sumgridFeedIn = sum(gridFeedIn)
		sumgridFeedInEC = sum(gridFeedInEC)
		if mode == "Normal":
			return sumgridFeedIn * self.priceFeedIn
		if mode == "EC":
			difference = sumgridFeedIn - sumgridFeedInEC
			return (sumgridFeedIn-difference) * self.priceDemand + difference * ((self.priceDemand + self.priceFeedIn)/2)

    
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

		gridDemandCosts = self.CalcGridDemand(gridDemand, mode= "Normal") 
		vergleichFeedIn = self.CalcGridFeedIn(gridFeedIn, mode= "Normal")


		energycosts = gridDemandCosts - (netMeterFeedIn + residualFeedIn)

		self.gridCostsNetMetering = self.CalcGridDemand(self.demand, mode= "Normal") - gridDemandCosts
		self.gridFeedInNetMetering = netMeterFeedIn + residualFeedIn

		return energycosts



















