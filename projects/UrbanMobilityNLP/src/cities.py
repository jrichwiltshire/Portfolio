"""
City Name list and regex-based extraction for urban mobility NLP pipeline.

Uses curated matching (not NER model) for interpretability and precision.
Sortec by length descending so "New York City" matches before "York".
"""

import re

CITY_NAMES: list[str] = [
    # Multi-word US cities (must come before their substrings)
      "New York City", "Los Angeles", "San Francisco", "San Jose", "San Diego",                                              
      "San Antonio", "Las Vegas", "New Orleans", "Salt Lake City", 
      "Kansas City", "Oklahoma City", "Virginia Beach", "Colorado Springs", 
      "Fort Worth", "Long Beach", "Santa Ana", "Corpus Christi", "St. Louis", 
      "St. Paul", "Washington DC", "Washington D.C.", "Fort Collins", "Fort Lauderdale",                                                           
      "Grand Rapids", "El Paso", "Mesa",               
      # US cities                                                        
      "Chicago", "Houston", "Phoenix", "Philadelphia", "Dallas", "Jacksonville",                                                        
      "Austin", "Columbus", "Charlotte", "Indianapolis", "Seattle", "Denver",                                                              
      "Nashville", "Baltimore", "Louisville", "Portland", "Milwaukee",
      "Albuquerque", "Tucson", "Fresno", "Sacramento", "Atlanta", "Omaha",                                             
      "Minneapolis", "Tulsa", "Tampa", "Arlington", "Raleigh", "Buffalo",
      "Rochester", "Syracuse", "Albany", "Cleveland", "Cincinnati", "Akron",                                                               
      "Toledo", "Pittsburgh", "Detroit", "Memphis", "Knoxville", "Chattanooga",                                                         
      "Miami", "Orlando", "Tallahassee", "Durham", "Greensboro", "Richmond",                                                            
      "Norfolk", "Alexandria", "Newark", "Madison", "Wichita", "Boise",  
      "Spokane", "Tacoma", "Bellevue", "Anchorage", "Honolulu", "Riverside",                                                           
      "Stockton", "Bakersfield", "Anaheim", "Irvine", "Fremont", "Modesto",                                              
      "Glendale", "Scottsdale", "Henderson", "Aurora", "Lakewood", "Thornton",                                             
      "Boulder", "Provo", "Ogden", "Cheyenne", "Billings", "Missoula",   
      "Bozeman", "Fargo", "Bismarck", "Lincoln", "Topeka", "Springfield",
      "Columbia", "Savannah", "Augusta", "Macon", "Greenville", "Charleston",                                                          
      "Roanoke", "Charlottesville", "Annapolis", "Wilmington", "Providence",                                                          
      "Manchester", "Burlington",                      
      # Canadian cities                                                  
      "Toronto", "Vancouver", "Montreal", "Calgary", "Edmonton", "Ottawa",                                                              
      "Winnipeg", "Quebec City", "Hamilton", "Kitchener", "Halifax", "Victoria",                                                            
      "Saskatoon", "Regina",                           
      # European cities (prominent in urbanism discourse)                
      "Amsterdam", "Copenhagen", "Stockholm", "Oslo", "Helsinki", "Gothenburg",                                                          
      "Zurich", "Geneva", "Basel", "Vienna", "Berlin", "Munich", "Hamburg",                                                             
      "Frankfurt", "Cologne", "Stuttgart", "Leipzig", "Dresden", "Paris",
      "Lyon", "Marseille", "Bordeaux", "Toulouse", "Strasbourg", "Nantes",                                                              
      "Lille", "Barcelona", "Madrid", "Valencia", "Seville", "Bilbao",
      "Lisbon", "Porto", "Brussels", "Ghent", "Bruges", "Antwerp", "Rotterdam",                                                           
      "Utrecht", "London", "Birmingham", "Manchester", "Leeds", "Glasgow",                                                             
      "Edinburgh", "Bristol", "Liverpool", "Dublin", "Cork", "Milan", "Rome",                                                                
      "Florence", "Bologna", "Turin", "Naples", "Venice", "Prague", "Budapest",                                                            
      "Warsaw", "Krakow", "Bucharest", "Sofia", "Athens", "Bern", "Lausanne",                                                            
      "Reykjavik", "Tallinn", "Riga", "Vilnius", "Ljubljana", "Zagreb",
      "Belgrade",                                                        
      # Asia-Pacific                                   
      "Tokyo", "Osaka", "Kyoto", "Nagoya", "Sapporo", "Fukuoka", "Seoul",
      "Busan", "Incheon", "Beijing", "Shanghai", "Shenzhen", "Guangzhou",
      "Chengdu", "Hangzhou", "Singapore", "Hong Kong", "Taipei", "Bangkok",                                              
      "Kuala Lumpur", "Jakarta", "Manila", "Ho Chi Minh City", "Hanoi",  
      "Mumbai", "Delhi", "Bangalore", "Chennai", "Hyderabad", "Kolkata",
      "Sydney", "Melbourne", "Brisbane", "Perth", "Adelaide", "Auckland",
      "Wellington", "Christchurch",                                      
      # Latin America                                                    
      "Mexico City", "Guadalajara", "Monterrey", "Bogota", "Medellin",   
      "Lima", "Quito", "Santiago", "Buenos Aires", "Montevideo", "Curitiba",                                                            
      "Porto Alegre", "Recife", "Sao Paulo", "Rio de Janeiro", "Brasilia",                                                            
      "Caracas", "Havana",                                               
      # Africa & Middle East                                             
      "Cairo", "Nairobi", "Lagos", "Accra", "Johannesburg", "Cape Town", 
      "Durban", "Casablanca", "Dubai", "Abu Dhabi", "Riyadh", "Doha",    
      "Amman", "Beirut", "Tel Aviv", "Jerusalem", "Istanbul", "Ankara",  
      "Tehran",
]

# Deduplicate while preserving order
_seen: set[str] = set()
CITY_NAMES_DEDUP: list[str] = []
for _c in CITY_NAMES:
    if _c.lower() not in _seen:
        _seen.add(_c.lower())
        CITY_NAMES_DEDUP.append(_c)

CITY_SET: set[str] = {c. lower() for c in CITY_NAMES_DEDUP}

# Compile once at import time - sorted longest-first to avoid partial matches
_sorted = sorted(CITY_NAMES_DEDUP, key=len, reverse=True)
_escaped = [re.escape(c) for c in _sorted]
CITY_PATTERN: re.Pattern = re.compile(
    r"\b(" + "|".join(_escaped) + r")\b", re.IGNORECASE
)

def extract_city_mentions(text: str) -> list[str]:
    """Return a deduplicated list of city names found in text (title-cased)."""
    matches = CITY_PATTERN.findall(text)
    seen: set[str] = set()
    result: list[str] = []
    for m in matches:
        key = m.lower()
        if key not in seen:
            seen.add(key)
            result.append(m.title())
    return result