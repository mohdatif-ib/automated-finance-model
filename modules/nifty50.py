from __future__ import annotations

from collections import OrderedDict


# Constituents from the Nifty 50 index constituent sheet dated 13.05.2026.
# Yahoo Finance uses NSE symbols with the ".NS" suffix.
NIFTY_50_COMPANIES = OrderedDict(
    [
        ("Adani Enterprises", "ADANIENT.NS"),
        ("Adani Ports and SEZ", "ADANIPORTS.NS"),
        ("Apollo Hospitals", "APOLLOHOSP.NS"),
        ("Asian Paints", "ASIANPAINT.NS"),
        ("Axis Bank", "AXISBANK.NS"),
        ("Bajaj Auto", "BAJAJ-AUTO.NS"),
        ("Bajaj Finserv", "BAJAJFINSV.NS"),
        ("Bajaj Finance", "BAJFINANCE.NS"),
        ("Bharat Electronics", "BEL.NS"),
        ("Bharti Airtel", "BHARTIARTL.NS"),
        ("Cipla", "CIPLA.NS"),
        ("Coal India", "COALINDIA.NS"),
        ("Dr. Reddy's Laboratories", "DRREDDY.NS"),
        ("Eicher Motors", "EICHERMOT.NS"),
        ("Eternal", "ETERNAL.NS"),
        ("Grasim Industries", "GRASIM.NS"),
        ("HCL Technologies", "HCLTECH.NS"),
        ("HDFC Bank", "HDFCBANK.NS"),
        ("HDFC Life Insurance", "HDFCLIFE.NS"),
        ("Hindalco Industries", "HINDALCO.NS"),
        ("Hindustan Unilever", "HINDUNILVR.NS"),
        ("ICICI Bank", "ICICIBANK.NS"),
        ("InterGlobe Aviation", "INDIGO.NS"),
        ("Infosys", "INFY.NS"),
        ("ITC", "ITC.NS"),
        ("Jio Financial Services", "JIOFIN.NS"),
        ("JSW Steel", "JSWSTEEL.NS"),
        ("Kotak Mahindra Bank", "KOTAKBANK.NS"),
        ("Larsen & Toubro", "LT.NS"),
        ("Mahindra & Mahindra", "M&M.NS"),
        ("Maruti Suzuki India", "MARUTI.NS"),
        ("Max Healthcare Institute", "MAXHEALTH.NS"),
        ("Nestle India", "NESTLEIND.NS"),
        ("NTPC", "NTPC.NS"),
        ("Oil & Natural Gas Corp.", "ONGC.NS"),
        ("Power Grid Corp. of India", "POWERGRID.NS"),
        ("Reliance Industries", "RELIANCE.NS"),
        ("SBI Life Insurance", "SBILIFE.NS"),
        ("State Bank of India", "SBIN.NS"),
        ("Shriram Finance", "SHRIRAMFIN.NS"),
        ("Sun Pharmaceutical", "SUNPHARMA.NS"),
        ("Tata Consumer Products", "TATACONSUM.NS"),
        ("Tata Motors Passenger Vehicles", "TATAMOTORS.NS"),
        ("Tata Steel", "TATASTEEL.NS"),
        ("Tata Consultancy Services", "TCS.NS"),
        ("Tech Mahindra", "TECHM.NS"),
        ("Titan Company", "TITAN.NS"),
        ("Trent", "TRENT.NS"),
        ("UltraTech Cement", "ULTRACEMCO.NS"),
        ("Wipro", "WIPRO.NS"),
    ]
)


NIFTY_50_INDEX = OrderedDict([("NIFTY 50 Index", "^NSEI")])


def nifty_50_company_options(include_index: bool = False) -> OrderedDict[str, str]:
    options = OrderedDict(NIFTY_50_COMPANIES)
    if include_index:
        options.update(NIFTY_50_INDEX)
    return options
