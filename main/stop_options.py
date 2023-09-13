import requests
import datetime


# convert datetime to string
def datetime_to_str(dt):
    return dt.strftime("%Y-%m-%dT%H:%M:%S")


def str_to_datetime(str):
    return datetime.datetime.strptime(str, "%Y-%m-%dT%H:%M:%S+09:00")


class StopOptionsLister:
    def __init__(self, start, goal, start_time):
        self.start_station = start
        self.goal_station = goal
        self.trip_start_time = start_time
        self.max_travel_time = 60 * 6  # 6 hours
        self.latest_stop_time = 19  # must stop before 6pm
        self.stop_options_lists = []
        
    def get_stop_options_lists(self):
        return self.stop_options_lists

    # search route using Navitime API
    def search_route(self, start, goal, start_time):
        url = "https://navitime-route-totalnavi.p.rapidapi.com/route_transit"

        headers = {
            "X-RapidAPI-Key": "4d46e4ed49msha7517f29d7a002cp197a84jsnb631db197b9a",
            "X-RapidAPI-Host": "navitime-route-totalnavi.p.rapidapi.com",
        }

        querystring = {
            "unuse": "domestic_flight.superexpress_train.sleeper_ultraexpress.ultraexpress_train.express_train.semiexpress_train.shuttle_bus",
            "options": "railway_calling_at",
        }
        querystring["start"] = start
        querystring["goal"] = goal
        querystring["start_time"] = datetime_to_str(start_time)

        response = requests.get(url, headers=headers, params=querystring)

        return response.json()

    # makes a list of stations to stop at during the trip
    def list_stop_stations(self):
        start = self.start_station
        start_time = self.trip_start_time

        while True:
            stop_options, terminal_station = self.next_stop_stations(
                start, self.goal_station, start_time
            )
            if not stop_options:
                break
            self.stop_options_lists.append(stop_options)
            start = terminal_station
            start_time = start_time + datetime.timedelta(days=1)
            start_time.replace(hour=9, minute=0, second=0)

    # returns a list of stations options to stop at.
    # returns empty list if you don't need to stop
    def next_stop_stations(self, start, goal, start_time):
        res = self.search_route(start, goal, start_time)
        route = res["items"][0]
        stop_options = []

        travel_time = 0
        last_section_id = None
        terminal_station = None
        for section_id, section in enumerate(route["sections"]):
            if section["type"] == "move":
                to_time = str_to_datetime(section["to_time"])
                duration = (to_time - start_time).total_seconds() // 60
                travel_time += duration

                if (
                    travel_time > self.max_travel_time
                    or to_time.hour > self.latest_stop_time
                ):
                    stop_options.append(
                        {
                            "node_id": route["sections"][section_id - 1]["node_id"],
                            "coord": route["sections"][section_id - 1]["coord"],
                        }
                    )
                    last_section_id = section_id - 2
                    terminal_station = route["sections"][section_id - 1]["node_id"]
                    break

        if last_section_id is None:
            return [], terminal_station

        for station in route["sections"][last_section_id]["transport"]["calling_at"]:
            to_time = str_to_datetime(station["to_time"])
            terminal_to_time = str_to_datetime(
                route["sections"][last_section_id]["to_time"]
            )
            # if the previous stop is within 15 minutes, add it to the list
            if (terminal_to_time - to_time).total_seconds() < 15 * 60:
                stop_options.append(
                    {"node_id": station["node_id"], "coord": station["coord"]}
                )

        return stop_options, terminal_station

def main():
    lister = StopOptionsLister("00001756", "00007420", datetime.datetime(2020, 1, 1, 9, 0, 0))
    lister.list_stop_stations()
    print(lister.get_stop_options_lists())

if __name__ == "__main__":
    main()
