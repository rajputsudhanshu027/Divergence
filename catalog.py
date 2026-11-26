"""Shared World Bank indicator and country catalog for the app and refresh job."""

INDICATORS = {
    "GDP per capita (constant 2015 US$)": "NY.GDP.PCAP.KD",
    "Life expectancy at birth (years)": "SP.DYN.LE00.IN",
    "Access to electricity (% of population)": "EG.ELC.ACCS.ZS",
    "School enrollment, secondary (% gross)": "SE.SEC.ENRR",
    "CO₂ emissions excluding LULUCF (t CO₂e per capita)": "EN.GHG.CO2.PC.CE.AR5",
    "Poverty headcount ($2.15/day, 2017 PPP, %)": "SI.POV.DDAY",
    "Labor force participation (% ages 15+)": "SL.TLF.CACT.ZS",
    "Access to clean fuels and technologies for cooking (%)": "EG.CFT.ACCS.ZS",
}

FEATURES = {
    "GDP per capita": "NY.GDP.PCAP.KD",
    "Population": "SP.POP.TOTL",
    "Urban population (% total)": "SP.URB.TOTL.IN.ZS",
    "Age dependency ratio (% working-age)": "SP.POP.DPND",
    "Agriculture (% GDP)": "NV.AGR.TOTL.ZS",
    "Trade (% GDP)": "NE.TRD.GNFS.ZS",
}

COUNTRIES = {
    "India": "IND", "Bangladesh": "BGD", "Nepal": "NPL", "Pakistan": "PAK",
    "Sri Lanka": "LKA", "Vietnam": "VNM", "Indonesia": "IDN", "Philippines": "PHL",
    "Cambodia": "KHM", "Lao PDR": "LAO", "Malaysia": "MYS", "Thailand": "THA",
    "Mongolia": "MNG", "China": "CHN", "Brazil": "BRA", "Mexico": "MEX",
    "Colombia": "COL", "Peru": "PER", "Ecuador": "ECU", "Bolivia": "BOL",
    "Paraguay": "PRY", "Argentina": "ARG", "South Africa": "ZAF", "Ghana": "GHA",
    "Kenya": "KEN", "Ethiopia": "ETH", "Nigeria": "NGA", "Egypt, Arab Rep.": "EGY",
    "Morocco": "MAR", "Tunisia": "TUN", "Türkiye": "TUR", "Jordan": "JOR",
}

SYNTHETIC = "Synthetic demo data"
