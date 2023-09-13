import pandas as pd
import urllib
import requests

# gets latitude and longitude from address using GSI API
def get_coordinates(address, latitude, longitude, isNan):
    if not isNan:
        return latitude, longitude
    
    make_url = "https://msearch.gsi.go.jp/address-search/AddressSearch?q="
    s_quote = urllib.parse.quote(address)
    response = requests.get(make_url + s_quote)
    return response.json()[0]["geometry"]["coordinates"][1], response.json()[0]["geometry"]["coordinates"][0]

def main():
    hotels_df = pd.read_csv("data/hotels/KNT_hotels.csv")
    
    # if latitude and longitude are not given, get them from address
    hotels_df[["Latitude", "Longitude"]] = hotels_df.apply(lambda x: get_coordinates(x["Address"], x["Latitude"], x["Longitude"], pd.isnull(x["Latitude"])), axis=1, result_type='expand')
    

    hotels_df.to_csv("data/hotels/KNT_hotels.csv", index=False)
    
if __name__ == "__main__":
    main()