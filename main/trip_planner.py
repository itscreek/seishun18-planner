import pandas as pd
import datetime
import stop_options
from geopy.distance import geodesic


class TripPlanner:
    def __init__(self):
        self.nearest_station_df = pd.read_csv("data/hotels/nearest_station.csv")
        self.hotels_scores_df = pd.read_csv("data/hotels/hotels_scores.csv")

    # returns a list of hotel codes which nearest station is the given station
    def search_hotels_from_station(
        self, station_name, station_latitude, station_longitude
    ):
        result = self.nearest_station_df[
            self.nearest_station_df["nearest_station_name"] == station_name
        ]["hotelcode"].tolist()
        # if there is no station with the given name, search hotels within 100 meters from the given latitude and longitude
        if not result:
            distance = self.nearest_station_df.apply(
                lambda row: geodesic(
                    (row["nearest_station_latitude"], row["nearest_station_longitude"]),
                    (station_latitude, station_longitude),
                ).m
                if not row.isnull().any()
                else 1000,
                axis=1,
            )
            result = self.nearest_station_df[distance <= 100]["hotelcode"].tolist()
        return result

    # returns a dataframe of hotels with scores
    def get_hotels_scores(self, hotels_list):
        return self.hotels_scores_df[
            self.hotels_scores_df["hotelcode"].isin(hotels_list)
        ]

    # returns a tuple of station score and a dataframe of top 5 hotels with scores
    def get_station_score(self, station_name, station_latitude, station_longitude):
        hotels_list = self.search_hotels_from_station(
            station_name, station_latitude, station_longitude
        )
        nearby_hotels_with_scores_df = self.get_hotels_scores(hotels_list)
        sorted_hotels_with_scores_df = nearby_hotels_with_scores_df.sort_values(
            "score", ascending=False
        )
        # station score is the average of the top 5 hotels' scores
        if len(sorted_hotels_with_scores_df) < 5:
            data = [["none", 0] for x in range(5)]
            indices = [
                i
                for i in range(
                    len(sorted_hotels_with_scores_df),
                    len(sorted_hotels_with_scores_df) + 5,
                )
            ]
            df = pd.DataFrame(data, columns=["hotelcode", "score"], index=indices)
            sorted_hotels_with_scores_df = pd.concat([sorted_hotels_with_scores_df, df])

        station_score = sorted_hotels_with_scores_df["score"].head(5).mean()
        return station_score, sorted_hotels_with_scores_df["hotelcode"].head(5).tolist()

    # returns a tuple of best station name and top 5 hotels near the station
    def get_best_station(self, stations_names, latitudes, longitudes):
        best_score = 0
        best_station_name = None
        best_hotels = None
        for station_name, latitude, longitude in zip(
            stations_names, latitudes, longitudes
        ):
            station_score, hotels = self.get_station_score(
                station_name, latitude, longitude
            )
            if station_score > best_score:
                best_score = station_score
                best_station_name = station_name
                best_hotels = hotels
        return best_station_name, best_hotels

    # return a list of stops
    # each stop is a tuple of station name and top 5 hotels near the station
    def plan_trip(self, start, goal, start_time):
        stops_lister = stop_options.StopOptionsLister(start, goal, start_time)
        stops_options_list = stops_lister.list_stop_stations()
        suggest_stops = []
        for stops_options in stops_options_list:
            station_names = [stop["name"] for stop in stops_options]
            station_latitudes = [stop["coord"]["lat"] for stop in stops_options]
            station_longitudes = [stop["coord"]["lon"] for stop in stops_options]
            suggest_stops.append(
                self.get_best_station(
                    station_names, station_latitudes, station_longitudes
                )
            )

        return suggest_stops


def test():
    start = input("出発地: ")
    goal = input("目的地: ")
    start_time = input("出発時刻(YYYY/MM/DD HH:MM): ")
    start_time = datetime.datetime.strptime(start_time, "%Y/%m/%d %H:%M")
    planner = TripPlanner()
    suggests = planner.plan_trip(start, goal, start_time)
  
    hotel_df = pd.read_csv("data/hotels/KNT_hotels.csv")
    # prints suggested stops
    for i, suggest in enumerate(suggests):
        print("{}泊目".format(i + 1))
        print(" 駅名: {}".format(suggest[0]))
        print(" ホテル")
        for hotelcode in suggest[1]:
            if hotelcode == "none":
                continue
            print(
                "  {}".format(
                    hotel_df[hotel_df["hotelcode"] == hotelcode]["name"].values[0]
                )
            )
           
        print("*************************************")

if __name__ == "__main__":
    test()
