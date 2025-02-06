import json

scenario = [
    {
        "type": "polygon",
        "waypoints": [
            {"lat": 41.2764214, "lon": 1.9882317},
            {"lat": 41.2761916, "lon": 1.9883283},
            {"lat": 41.2763750, "lon": 1.9891195},
            {"lat": 41.2766119, "lon": 1.9890162},
            {"lat": 41.2764214, "lon": 1.9882317}
        ]
    }
]


json_data = json.dumps(scenario, indent=4)

with open("GeoFenceScenario.json", "w", encoding="utf-8") as file:
    file.write(json_data)

print("JSON Creado")