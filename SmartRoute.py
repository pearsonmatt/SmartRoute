"""
SmartRoute.py

Second Project:
App for finding Cheap gas on route, needs better name.

→Name Options: 
SmartRoute - built with this name for now.

→Current Tasks:
1. Expanding # notation throughout code to reinforce Python learning.
2. Fix the UI since it's still showing longitude after I switched to using Address and it's not selectable. 
    ♦ Maybe limit to start/destination fields, condense at the top and make the map area more square instead of the current rectangular shape. 
3. Fix the Map UI since it's not centering correctly and otherwise displays awkwardly. 

→Currently the Route is a straight line "as the bird flies" type. 
Once the above tasks are complete, I'll look into mapping it by actual road. 
"""

#Importing kivy since it should make this usable for both 
#computer program and android app. 
import kivy
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.label import Label
from kivy.uix.spinner import Spinner
from kivy.clock import Clock
from kivy_garden.mapview import MapView, MapMarker, MapLayer
from kivy.graphics import Color, Line
import requests
from bs4 import BeautifulSoup
import threading
import math

# Set your OpenRouteService API key here
ORS_API_KEY = "YOUR_OPENROUTESERVICE_API_KEY"

def geocode_address(address):
    url = "https://nominatim.openstreetmap.org/search"
    params = {"q": address, "format": "json"}
    headers = {'User-Agent': 'SmartRouteApp'}
    try:
        resp = requests.get(url, params=params, headers=headers, timeout=7)
        data = resp.json()
        if data:
            return float(data[0]['lat']), float(data[0]['lon'])
    except Exception as e:
        print(f"Geocoding error: {e}")
    return None

def get_route_coords(start, end):
    url = "https://api.openrouteservice.org/v2/directions/driving-car"
    headers = {'Authorization': ORS_API_KEY}
    params = {
        "start": f"{start[1]},{start[0]}",
        "end": f"{end[1]},{end[0]}"
    }
    resp = requests.get(url, params=params, headers=headers, timeout=10)
    if resp.status_code == 200:
        data = resp.json()
        coords = data["features"][0]["geometry"]["coordinates"]
        # Convert from [lon, lat] to [lat, lon]
        return [(lat, lon) for lon, lat in coords]
    else:
        print(f"OpenRouteService error: {resp.text}")
        return [start, end]

def get_gas_stations_along_route(route_coords, buffer_km=2):
    # For demo: sample every 10th point along the route for querying Overpass (to stay within API limits)
    sample_points = route_coords[::max(1, len(route_coords)//10)]
    stations = []
    for lat, lon in sample_points:
        # Overpass QL: find all stations within buffer_km (2000 meters)
        overpass_url = "https://overpass-api.de/api/interpreter"
        query = f"""
        [out:json][timeout:25];
        (
          node["amenity"="fuel"](around:{int(buffer_km*1000)},{lat},{lon});
        );
        out center;
        """
        try:
            r = requests.post(overpass_url, data=query, timeout=15)
            elements = r.json().get("elements", [])
            for elem in elements:
                station = {
                    "name": elem.get("tags", {}).get("name", "Gas Station"),
                    "lat": elem["lat"],
                    "lon": elem["lon"]
                }
                stations.append(station)
        except Exception as e:
            print(f"Overpass error: {e}")
    # Remove duplicates by lat/lon (some overlap due to buffer)
    unique = {(s["lat"], s["lon"]): s for s in stations}
    return list(unique.values())

def get_state_from_coords(lat, lon):
    # Reverse geocode to get state
    url = "https://nominatim.openstreetmap.org/reverse"
    params = {"lat": lat, "lon": lon, "format": "json", "zoom": 5, "addressdetails": 1}
    headers = {'User-Agent': 'SmartRouteApp'}
    try:
        resp = requests.get(url, params=params, headers=headers, timeout=7)
        data = resp.json()
        return data.get("address", {}).get("state", "")
    except Exception as e:
        print(f"Reverse geocode error: {e}")
        return ""

def scrape_aaa_gas_price(state):
    # Scrape https://gasprices.aaa.com/state-gas-price-averages/
    url = "https://gasprices.aaa.com/state-gas-price-averages/"
    try:
        resp = requests.get(url, timeout=10)
        soup = BeautifulSoup(resp.text, "html.parser")
        table = soup.find("table", {"id": "sortable"})
        for row in table.find_all("tr")[1:]:
            cols = row.find_all("td")
            if len(cols) >= 2 and cols[0].text.strip().lower() == state.lower():
                price = cols[1].text.strip().replace("$", "")
                return float(price)
    except Exception as e:
        print(f"AAA scrape error: {e}")
    return None

def midpoint(coords):
    # Returns the geographic midpoint as (lat, lon)
    if not coords:
        return 0, 0
    # Convert lat/lon to radians and cartesian
    x, y, z = 0, 0, 0
    for lat, lon in coords:
        lat_rad = math.radians(lat)
        lon_rad = math.radians(lon)
        x += math.cos(lat_rad) * math.cos(lon_rad)
        y += math.cos(lat_rad) * math.sin(lon_rad)
        z += math.sin(lat_rad)
    total = len(coords)
    x /= total
    y /= total
    z /= total
    lon_mid = math.atan2(y, x)
    hyp = math.sqrt(x * x + y * y)
    lat_mid = math.atan2(z, hyp)
    return math.degrees(lat_mid), math.degrees(lon_mid)

def bounding_box(coords):
    """Returns (min_lat, min_lon, max_lat, max_lon) of the list of (lat, lon)"""
    lats = [lat for lat, lon in coords]
    lons = [lon for lat, lon in coords]
    return min(lats), min(lons), max(lats), max(lons)

def optimal_zoom(min_lat, min_lon, max_lat, max_lon, map_width_px=800, map_height_px=600):
    # This is a rough approximation for OpenStreetMap Web Mercator
    WORLD_DIM = {"height": 256, "width": 256}
    ZOOM_MAX = 19

    def lat_rad(lat):
        sin = math.sin(lat * math.pi / 180)
        rad_x2 = math.log((1 + sin) / (1 - sin)) / 2
        return max(min(rad_x2, math.pi), -math.pi) / 2

    def zoom(map_px, world_px, fraction):
        return math.floor(math.log(map_px / world_px / fraction) / math.log(2))

    lat_fraction = (lat_rad(max_lat) - lat_rad(min_lat)) / math.pi
    lon_fraction = (max_lon - min_lon) / 360.0
    lat_zoom = zoom(map_height_px, WORLD_DIM["height"], lat_fraction)
    lon_zoom = zoom(map_width_px, WORLD_DIM["width"], lon_fraction)
    return min(lat_zoom, lon_zoom, ZOOM_MAX)

# Route polyline layer for MapView
class RouteLineLayer(MapLayer):
    def __init__(self, route_coords, **kwargs):
        super().__init__(**kwargs)
        self.route_coords = route_coords

    def reposition(self):
        self.canvas.clear()
        if not self.route_coords or not self.parent:
            return
        # Convert geo-coordinates to screen coordinates
        points = []
        for lat, lon in self.route_coords:
            x, y = self.parent.get_window_xy_from(lat, lon, self.parent.zoom)
            points.extend([x, y])
        if len(points) >= 4:
            with self.canvas:
                Color(0, 0, 1, 1)  # Blue
                Line(points=points, width=2)

class LocationInput(BoxLayout):
    def __init__(self, label_text, on_location_selected, **kwargs):
        super().__init__(orientation="vertical", **kwargs)
        self.on_location_selected = on_location_selected
        self.label = Label(text=label_text)
        self.add_widget(self.label)
        self.spinner = Spinner(
            text="Enter Address",
            values=["Enter Address", "Enter Lat/Lon"],
        )
        self.spinner.bind(text=self.update_input_fields)
        self.add_widget(self.spinner)
        self.input1 = TextInput(hint_text="Address or Latitude")
        self.input2 = TextInput(hint_text="Longitude (if manual)")
        self.ok_btn = Button(text="Set Location", on_press=self.get_location)
        self.add_widget(self.input1)
        self.add_widget(self.input2)
        self.add_widget(self.ok_btn)
        self.input1.disabled = False
        self.input2.disabled = True

    def update_input_fields(self, spinner, text):
        if text == "Enter Address":
            self.input1.hint_text = "Enter address"
            self.input1.text = ""
            self.input2.text = ""
            self.input1.disabled = False
            self.input2.disabled = True
        elif text == "Enter Lat/Lon":
            self.input1.hint_text = "Latitude"
            self.input1.text = ""
            self.input2.text = ""
            self.input1.disabled = False
            self.input2.disabled = False

    def get_location(self, instance):
        method = self.spinner.text
        if method == "Enter Address":
            address = self.input1.text
            if address.strip():
                latlon = geocode_address(address)
                if latlon:
                    self.on_location_selected(latlon)
                    self.label.text = f"Location set: {latlon}"
                else:
                    self.label.text = "Address not found."
            else:
                self.label.text = "Please enter an address."
        elif method == "Enter Lat/Lon":
            try:
                lat = float(self.input1.text)
                lon = float(self.input2.text)
                self.on_location_selected((lat, lon))
                self.label.text = f"Location set: ({lat}, {lon})"
            except:
                self.label.text = "Invalid latitude or longitude."
        else:
            self.label.text = "Please choose a location method."

class SmartRouteRoot(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(orientation="vertical", **kwargs)
        self.start_location = None
        self.end_location = None
        self.route_coords = []
        self.gas_stations = []
        self.avg_price = None
        self.state = ""
        self.map_view = MapView(zoom=6, lat=39.5, lon=-98.35)  # Approx US center
        self.map_markers = []  # Track our own markers!
        self.route_layer = None
        self.add_widget(Label(text="SmartRoute: Gas Stations Along Route", font_size=22, size_hint_y=None, height=40))
        self.start_input = LocationInput("Start Location:", self.set_start_location)
        self.add_widget(self.start_input)
        self.end_input = LocationInput("End Location:", self.set_end_location)
        self.add_widget(self.end_input)
        self.route_btn = Button(text="Find Route & Gas Stations", size_hint_y=None, height=40)
        self.route_btn.bind(on_press=self.process_route)
        self.add_widget(self.route_btn)
        self.add_widget(self.map_view)
        self.status_label = Label(text="", size_hint_y=None, height=30)
        self.add_widget(self.status_label)

    def set_start_location(self, latlon):
        self.start_location = latlon
        self.status_label.text = f"Start set: {latlon}"

    def set_end_location(self, latlon):
        self.end_location = latlon
        self.status_label.text = f"End set: {latlon}"

    def process_route(self, instance):
        if self.start_location and self.end_location:
            self.status_label.text = "Getting route, gas stations, and average price..."
            threading.Thread(target=self.background_process).start()
        else:
            self.status_label.text = "Please set both start and end locations."

    def background_process(self):
        try:
            # 1. Get route
            self.route_coords = get_route_coords(self.start_location, self.end_location)
            # 2. Get state (from start point)
            self.state = get_state_from_coords(self.start_location[0], self.start_location[1])
            # 3. Scrape AAA for average price
            self.avg_price = scrape_aaa_gas_price(self.state) if self.state else None
            # 4. Get gas stations along route
            self.gas_stations = get_gas_stations_along_route(self.route_coords)
            # 5. Update map on main thread
            Clock.schedule_once(lambda dt: self.display_results())
        except Exception as e:
            Clock.schedule_once(lambda dt: self.show_error(str(e)))

    def show_error(self, msg):
        self.status_label.text = f"Error: {msg}"

    def display_results(self):
        # Remove old markers
        for marker in self.map_markers:
            self.map_view.remove_marker(marker)
        self.map_markers.clear()
        # Remove old route layer if any
        if self.route_layer:
            self.map_view.remove_layer(self.route_layer)
            self.route_layer = None

        # Center and zoom map to midpoint and fit route
        if self.route_coords:
            min_lat, min_lon, max_lat, max_lon = bounding_box(self.route_coords)
            mid_lat, mid_lon = midpoint([self.route_coords[0], self.route_coords[-1]])
            zoom = optimal_zoom(min_lat, min_lon, max_lat, max_lon, map_width_px=800, map_height_px=600)
            self.map_view.set_zoom_at(zoom, mid_lat, mid_lon)
        # Draw route polyline
        if self.route_coords:
            self.route_layer = RouteLineLayer(self.route_coords)
            self.map_view.add_layer(self.route_layer)
        # Draw route start/end markers
        if self.route_coords:
            start_marker = MapMarker(lat=self.route_coords[0][0], lon=self.route_coords[0][1], source="start.png", size=(32,32))
            end_marker = MapMarker(lat=self.route_coords[-1][0], lon=self.route_coords[-1][1], source="end.png", size=(32,32))
            self.map_view.add_marker(start_marker)
            self.map_view.add_marker(end_marker)
            self.map_markers.extend([start_marker, end_marker])
        # Add gas stations
        for station in self.gas_stations:
            price_text = f"Avg price: ${self.avg_price:.2f}" if self.avg_price else "No price"
            marker = MapMarker(lat=station["lat"], lon=station["lon"], source="gas.png", size=(32,32))
            self.map_view.add_marker(marker)
            self.map_markers.append(marker)
        self.status_label.text = (
            f"Route and {len(self.gas_stations)} stations shown. (AAA avg: ${self.avg_price:.2f} in {self.state})"
            if self.avg_price else
            "Stations shown (price not available)."
        )

class SmartRouteApp(App):
    def build(self):
        return SmartRouteRoot()

if __name__ == "__main__":
    SmartRouteApp().run()
