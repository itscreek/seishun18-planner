import requests
import datetime


# convert datetime to string
def datetime_to_str(dt):
    return dt.strftime("%Y-%m-%dT%H:%M:%S")


def str_to_datetime(str):
    return datetime.datetime.strptime(str, "%Y-%m-%dT%H:%M:%S+09:00")


class StopOptionsLister:
    def __init__(
        self, start, goal, start_time, max_travel_time=60 * 6, latest_stop_time=19
    ):
        # convert station name to id
        url = "https://navitime-transport.p.rapidapi.com/transport_node"
        querystring = {"word": start}
        headers = {
            "X-RapidAPI-Key": "4d46e4ed49msha7517f29d7a002cp197a84jsnb631db197b9a",
            "X-RapidAPI-Host": "navitime-transport.p.rapidapi.com",
        }
        response = requests.get(url, headers=headers, params=querystring)
        self.start_station = response.json()["items"][0]["id"]

        querystring["word"] = goal
        response = requests.get(url, headers=headers, params=querystring)
        self.goal_station = response.json()["items"][0]["id"]

        self.trip_start_time = start_time
        self.max_travel_time = max_travel_time  # max travel time in minutes
        self.latest_stop_time = latest_stop_time  # must stop before latest_stop_time
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

        return self.stop_options_lists

    # returns a list of stations options to stop at.
    # returns empty list if you don't need to stop
    def next_stop_stations(self, start, goal, start_time):
        res = self.search_route(start, goal, start_time)
        route = res["items"][0]
        stop_options = []

        travel_time = 0
        last_section_id = None
        terminal_station = None
        previous_start_time = start_time
        for section_id, section in enumerate(route["sections"]):
            if section["type"] == "move":
                section_to_time = str_to_datetime(section["to_time"])
                duration = (section_to_time - previous_start_time).total_seconds() // 60
                travel_time += duration
                previous_start_time = section_to_time

                if (
                    travel_time > self.max_travel_time
                    or section_to_time.hour > self.latest_stop_time
                ):
                    stop_options.append(
                        {
                            "name": route["sections"][section_id - 1]["name"],
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
            if "to_time" not in station:
                continue
            to_time = str_to_datetime(station["to_time"])
            terminal_to_time = str_to_datetime(
                route["sections"][last_section_id]["to_time"]
            )
            # if the previous stop is within 30 minutes, add it to the list
            if (terminal_to_time - to_time).total_seconds() < 30 * 60:
                stop_options.append(
                    {
                        "name": station["name"],
                        "node_id": station["node_id"],
                        "coord": station["coord"],
                    }
                )

        return stop_options, terminal_station


def main():
    lister = StopOptionsLister(
        "京都", "博多", datetime.datetime(2020, 1, 1, 9, 0, 0)
    )
    print(len(lister.list_stop_stations()))


if __name__ == "__main__":
    main()
