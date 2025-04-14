import requests

BASE_URL = "https://services.odata.org/V4/TripPinServiceRW"

def get_people_with_trips_and_planitems():
    """
    Retrieves people who have at least one trip, including their plan items.
    """
    url = f"{BASE_URL}/People?$filter=Trips/any(t: true)&$expand=Trips($expand=PlanItems)&$select=UserName,Trips"
    response = requests.get(url)
    if response.status_code != 200:
        raise Exception(f"Request failed: {response.status_code}")
    data = response.json()

    people_with_trips = []
    for person in data.get('value', []):
        trips = person.get('Trips', [])
        if trips:
            people_with_trips.append({
                "UserName": person["UserName"],
                "Trips": trips
            })
    return people_with_trips

def filter_people_with_multiple_airline_prefixes(people):
    """
    Filters people who have flown with at least two different airline prefixes
    based on the first two letters of FlightNumber.
    """
    valid_people = []
    for person in people:
        prefixes = set()
        for trip in person['Trips']:
            for item in trip.get('PlanItems', []):
                flight_number = item.get('FlightNumber')
                if flight_number and len(flight_number) >= 2:
                    prefixes.add(flight_number[:2].upper())
        if len(prefixes) >= 2:
            valid_people.append({
                "UserName": person["UserName"],
                "AirlinePrefixes": list(prefixes),
                "Trips": person["Trips"]
            })
    return valid_people

def find_person_with_longest_flight(people):
    """
    Identifies the person who has taken the single longest flight by distance.
    """
    longest = None
    for person in people:
        for trip in person['Trips']:
            for item in trip.get('PlanItems', []):
                if 'Distance' in item and item['Distance'] is not None:
                    if not longest or item['Distance'] > longest['Distance']:
                        longest = {
                            "UserName": person["UserName"],
                            "Distance": item['Distance'],
                            "Airlines": person["AirlinePrefixes"]
                        }
    return longest

people = get_people_with_trips_and_planitems()
eligible_people = filter_people_with_multiple_airline_prefixes(people)
longest_flight_person = find_person_with_longest_flight(eligible_people)

print(f"Eligible People: {len(eligible_people)}")
print("Usernames with multiple airline prefixes:")
for person in eligible_people:
    print(f" - {person['UserName']} | Airlines: {', '.join(person['AirlinePrefixes'])}")

if longest_flight_person:
    print(f"Longest Flight Taken By: {longest_flight_person['UserName']}")
    print(f"Distance: {longest_flight_person['Distance']} km")
    print(f"Airlines: {', '.join(longest_flight_person['Airlines'])}")
else:
    print("No flights with distance found among eligible people.")
