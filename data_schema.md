# Data Schema for SmartRoute Gas Finder

Below are the core data structures used internally by the app.

---

## 1. **Route Coordinates**

A driving route is a list of (latitude, longitude) tuples, e.g.:

```python
route_coords = [
    (lat1, lon1),
    (lat2, lon2),
    ...,
    (latN, lonN)
]
```

- Used for plotting the polyline (route) and for gas station sampling.

---

## 2. **Gas Station**

Each gas station is a dictionary with:
- `name`: (str) Station name or `"Gas Station"` if not named.
- `lat`: (float) Latitude.
- `lon`: (float) Longitude.

Example:
```python
{
    "name": "Shell",
    "lat": 39.12345,
    "lon": -97.54321
}
```
The full list:
```python
gas_stations = [station1, station2, ...]
```

---

## 3. **Average Price**

A float, representing the average gas price for the current state (from AAA), e.g.:

```python
avg_price = 3.89
```

If unavailable, `avg_price` is `None`.

---

## 4. **State**

A string, the U.S. state name (from reverse geocoding), e.g.:

```python
state = "Kansas"
```

---

## 5. **Start and End Locations**

Each is a tuple:
```python
start_location = (lat, lon)
end_location = (lat, lon)
```
Obtained from geocoding or manual entry.

---

## 6. **Markers and Layers**

- `map_markers`: list of Kivy `MapMarker` objects (for start, end, and stations).
- `route_layer`: a `RouteLineLayer` object for the blue route polyline.

---

## 7. **Sample Data Object (for saving/exporting)**

If you want to persist a trip, you can structure it as:

```python
trip_data = {
    "start_location": (lat1, lon1),
    "end_location": (lat2, lon2),
    "route_coords": [...],
    "gas_stations": [...],
    "avg_price": 3.99,
    "state": "Missouri"
}
```

---

*You can extend this schema for advanced features such as per-station price, trip stats, or exporting to JSON.*
