import requests
import pandas as pd
import logging


cache = {}

def get_cached(url: str) -> dict:
    """Fetch and cache responses from the API."""
    if url in cache:
        return cache[url]
    try:
        res = requests.get(url)
        if res.status_code == 200:
            cache[url] = res.json()
            return cache[url]
    except Exception as e:
        logging.warning(f"Failed to fetch {url}: {e}")
    return None

def get_grievous_data() -> list[str]:
    """Search for General Grievous and return his data."""
    logging.info("Searching for General Grievous...")
    url = "https://swapi.dev/api/people/?search=grievous"
    response = get_cached(url)
    if response and response.get("count", 0) > 0:
        return response["results"][0]
    logging.warning("General Grievous not found.")
    return None

def get_related_character_urls(grievous: dict) -> list:
    """Get all character URLs from the same films as Grievous."""
    character_urls = set()
    for film_url in grievous.get("films", []):
        film_data = get_cached(film_url)
        if film_data:
            character_urls.update(film_data.get("characters", []))
    return list(character_urls)

def fetch_species_name(species_urls: list[str]) -> str:
    """Get species name from the first URL in the list (if exists)."""
    if not species_urls:
        return None
    species_data = get_cached(species_urls[0])
    return species_data.get("name") if species_data else None

def fetch_film_titles(film_urls):
    """Return list of film titles from a list of URLs."""
    return [get_cached(url).get("title") for url in film_urls if get_cached(url)]

def get_enriched_characters_df(character_urls: list[str])-> pd.DataFrame:
    """Fetch and enrich character data, return as a pandas DataFrame."""
    data = []

    for url in character_urls:
        char_data = get_cached(url)
        if not char_data:
            continue

        name = char_data.get("name")
        species = fetch_species_name(char_data.get("species", []))
        edited = char_data.get("edited")
        film_titles = fetch_film_titles(char_data.get("films", []))

        data.append({
            "name": name,
            "species": species,
            "edited": edited,
            "films": film_titles,
            "film_count": len(film_titles)
        })

    df = pd.DataFrame(data)
    return df

def main() -> None:
    grievous = get_grievous_data()
    if not grievous:
        logging.error("General Grievous not found.")
        

    related_character_urls = get_related_character_urls(grievous)
    logging.info(f"Characters found: {len(related_character_urls)}")

    df = get_enriched_characters_df(related_character_urls)

    filtered_df = df[
        (df["species"].str.lower() != "droid") &
        (df["film_count"] >= 2)
    ]

    if filtered_df.empty:
        logging.info("No valid characters found.")
    else:
        logging.info("Filtered characters:")
        logging.info(filtered_df.to_dict(orient="records"))

    df = df.drop('films', axis=1)
    df.to_csv("/tmp/second_question_general_grievous.csv", index=False)
    logging.info("Data saved to /tmp/second_question_general_grievous.csv")

if __name__ == "__main__":
    main()
