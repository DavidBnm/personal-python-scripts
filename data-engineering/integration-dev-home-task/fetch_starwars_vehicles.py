import requests
import json

BASE_URL = "https://swapi.dev/api"
VEHICLES_ENDPOINT = f"{BASE_URL}/vehicles/"

# === Helpers ===

def fetch_field(url, field):
    """Fetches a single field from a resource URL."""
    try:
        res = requests.get(url)
        if res.status_code == 200:
            return res.json().get(field)
    except:
        return None

def fetch_list_field(urls, field):
    """Fetches a list of field values from resource URLs."""
    return [fetch_field(url, field) for url in urls]

def get_pilot_data(pilot_urls):
    """Returns a list of enriched pilot data dictionaries."""
    enriched_pilots = []

    for url in pilot_urls:
        try:
            res = requests.get(url)
            if res.status_code != 200:
                continue

            pilot = res.json()
            enriched = {
                "name": pilot.get("name"),
                "species": fetch_field(pilot["species"][0], "name") if pilot.get("species") else None,
                "homeworld": fetch_field(pilot["homeworld"], "name") if pilot.get("homeworld") else None,
                "films": fetch_list_field(pilot.get("films", []), "title"),
                "edited": pilot.get("edited")
            }

            enriched_pilots.append(enriched)

        except Exception as e:
            print(f"Error fetching pilot data: {e}")
            continue

    return enriched_pilots

# === Main Fetch Function ===

def get_vehicles_basic_info():
    url = VEHICLES_ENDPOINT
    vehicles = []

    while url:
        response = requests.get(url)
        if response.status_code != 200:
            raise Exception(f"Failed to get vehicles: {response.status_code}")

        data = response.json()
        for v in data['results']:
            vehicle_info = {
                "name": v.get("name"),
                "model": v.get("model"),
                "class": v.get("vehicle_class"),
                "edited": v.get("edited"),
                "pilots": v.get("pilots")  # list of pilot URLs
            }
            vehicles.append(vehicle_info)

        url = data.get("next")

    return vehicles

def enrich_vehicle_pilots(vehicles):
    enriched_vehicles = []

    for vehicle in vehicles:
        vehicle_copy = vehicle.copy()

        if vehicle_copy.get("pilots"):
            print(f"Enriching pilots for vehicle: {vehicle_copy['name']}")
            enriched_pilots = get_pilot_data(vehicle_copy["pilots"])
            vehicle_copy["pilots"] = enriched_pilots
        else:
            vehicle_copy["pilots"] = []

        enriched_vehicles.append(vehicle_copy)

    return enriched_vehicles

# === Run Everything ===

if __name__ == "__main__":
    print("Fetching vehicles...")
    vehicles = get_vehicles_basic_info()

    print("Enriching pilots...")
    enriched_vehicles = enrich_vehicle_pilots(vehicles)

    print("Saving to JSON file...")
    with open("/Users/davidbenami/Downloads/question_one_sw_vehicles.json", "w") as f:
        json.dump(enriched_vehicles, f, indent=2)

    print("Done! 🚀 Check 'vehicles_enriched.json'")
