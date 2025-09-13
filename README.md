# SmartRoute Gas Finder

**SmartRoute** is a Python/Kivy desktop/mobile app to help you plan driving routes, find gas stations along the way, and see average gas prices in each state.  
It uses OpenRouteService for routing, OpenStreetMap/Overpass for gas stations, AAA for average prices, and Kivy Garden MapView for mapping.

## Features

- Enter start/end locations as addresses or lat/lon.
- Route is plotted as a blue line between start and end.
- Map auto-centers and zooms to fit your route.
- Gas stations along the route are marked.
- Station marker size is consistent and customizable.
- Start/end and gas station icons.
- Displays average state gas price (scraped from AAA).

## Installation

1. **Clone or download this repo.**

2. **Install dependencies:**
    ```sh
    pip install kivy kivy-garden kivy-garden.mapview requests beautifulsoup4
    ```
    If `garden` command is needed:
    ```sh
    pip install kivy-garden
    garden install mapview
    ```

3. **Obtain an OpenRouteService API key:**
    - Sign up at [openrouteservice.org](https://openrouteservice.org/sign-up/)
    - Put your API key in `main.py`:
      ```python
      ORS_API_KEY = "YOUR_OPENROUTESERVICE_API_KEY"
      ```

4. **(Optional) Replace or remove marker icons:**
    - Place `start.png`, `end.png`, and `gas.png` in the project directory, or remove `source="..."` from the code to use default pins.

## Usage

```sh
python main.py
```
- Enter a start and end address or lat/lon.
- Click "Find Route & Gas Stations".
- The map will show your route, gas stations along the route, and display the average gas price in the relevant state.

## Data Flow

- Geocoding is performed using OpenStreetMap Nominatim.
- Route is requested from OpenRouteService.
- Gas stations are found by querying Overpass API at sampled points along the route.
- AAA gas prices are scraped for the state where the route starts.
- Markers and polylines are drawn on the map.
- The map centers and zooms to the area of interest.

## Troubleshooting

- If icons are too large/small, edit the `size=(32,32)` parameter in code.
- If the AAA price scrape fails, check their site for layout changes.
- All network operations require an internet connection.

## License

MIT, see LICENSE file.

---

```
kivy
kivy-garden
kivy-garden.mapview
requests
beautifulsoup4
```
---

## Screenshots

*(Add screenshots here if desired)*
