#!/usr/bin/env python3
"""
Roommatch.nl API Module
Fetches available room listings from the Roommatch API.

Can be used as a standalone script or imported as a module.

Usage as script:
    python listings.py

Usage as module:
    from listings import fetch_listings
    rooms = fetch_listings()
"""

import requests
import json
from typing import Optional

REGION_ID = "3"


def fetch_listings(region_id: str = REGION_ID, limit: int = 100) -> list[dict]:
    """
    Fetch room listings from the Roommatch API.

    Args:
        region_id: The region ID to filter by (default: "3" for Amsterdam area)
        limit: Maximum number of listings to fetch

    Returns:
        List of room dictionaries with normalized fields
    """
    session = requests.Session()
    session.headers.update({
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "nl-NL,nl;q=0.9,en;q=0.8",
        "Accept-Encoding": "gzip, deflate, br",
        "Content-Type": "application/json;charset=UTF-8",
        "Referer": "https://www.roommatch.nl/aanbod/studentenwoningen",
        "Origin": "https://www.roommatch.nl"
    })

    api_url = "https://roommatching-aanbodapi.zig365.nl/api/v1/actueel-aanbod"

    params = {
        "limit": limit,
        "locale": "nl_NL",
        "page": 0,
        "sort": "!reactionData.zoekprofielMatchOrder,-reactionData.zoekprofielMatchOrder,%2BreactionData.aangepasteTotaleHuurprijs",
    }

    post_data = {
        "filters": {
            "$and": [
                {
                    "$and": [
                        {
                            "regio.id": {"$eq": region_id}
                        }
                    ]
                }
            ]
        },
        "hidden-filters": {
            "$and": [
                {"dwellingType.categorie": {"$eq": "woning"}},
                {"rentBuy": {"$eq": "Huur"}},
                {"isExtraAanbod": {"$eq": ""}},
                {"isWoningruil": {"$eq": ""}},
                {
                    "$and": [
                        {
                            "$or": [
                                {"street": {"$like": ""}},
                                {"houseNumber": {"$like": ""}},
                                {"houseNumberAddition": {"$like": ""}}
                            ]
                        },
                        {
                            "$or": [
                                {"street": {"$like": ""}},
                                {"houseNumber": {"$like": ""}},
                                {"houseNumberAddition": {"$like": ""}}
                            ]
                        }
                    ]
                },
                {
                    "$and": [
                        {"reactionData.isPassend": {"$eq": "1"}}
                    ]
                }
            ]
        },
        "woningzoekende": {
            "heeftToegangTotExtraAanbod": False,
            "neemtDeelAanHaastrij": False,
            "huurperiodeVanStartdatum": None,
            "huurperiodeVanEinddatum": None,
            "isRechtspersoon": False,
            "isStudent": True,
            "isAlleenAccomodate": False,
            "heeftBlokkade": False,
            "blokkadeVoorCorporatieIds": None,
            "huishoudgrootte": 1,
            "aantalMeeverhuizendeKinderen": 0,
            "aantalMeeverhuizendeKinderenOnder18": 0,
            "verzamelinkomen": 0,
            "heeftEenTMin2Inkomen": False,
            "heeftElkHuishoudLidOnderbouwdInkomen": False,
            "leeftijdA1": 23,
            "heeftA2": False,
            "leeftijdA2": None,
            "aowLeeftijdBereiktA1": False,
            "aowLeeftijdBereiktA2": None,
            "genderIdA1": "1",
            "genderIdA2": None,
            "startDatumStudieLigtInVoorrangsPeriode": False,
            "studeertBijOnderwijsinstellingInRegioHaaglanden": False,
            "woontVerderVanStudieVoorRegioHaaglanden": False,
            "woontInNederland": True,
            "studeertBijOnderwijsinstellingVU": True,
            "studeertBijOnderwijsinstellingACTA": False,
            "studeertBijOnderwijsinstellingRocAirport": False,
            "studeertBijOnderwijsinstellingHaagseHogeschool": False,
            "studeertBijOnderwijsinstellingUniversiteitLeiden": False,
            "onderwijsinstellingBrincode": "21PL",
            "studieRegioId": 3,
            "stageRegioId": 0,
            "startdatumStudie": "2022-09-01",
            "startdatumStage": None,
            "inschrijvingTypes": [{"inCode": "student", "id": "2"}],
            "subtypeInschrijvingId": None,
            "opleidingstypeId": 5,
            "woontVerderVanOnderwijsinstelling": False,
            "gemeenteGeoLocatieNaamA1": "Amsterdam",
            "gemeenteIdA1": 16,
            "soortWoningzoekendeStarterDoorstromer": None,
            "regioIdA1": 3,
            "regioIdA2": None,
            "huisnummerA1": "367",
            "huisnummertoevoegingA1": None,
            "postcodeA1": "1069 RR",
            "huisnummerA2": None,
            "huisnummertoevoegingA2": None,
            "postcodeA2": None,
            "latitudeA1": 52.3502,
            "latitudeA2": None,
            "longitudeA1": 4.80072,
            "longitudeA2": None,
            "landIdA1": 524,
            "landIdA2": None,
            "voorrangen": [],
            "heeftVermogen": False,
            "huidigeWoonsituatieId": None,
            "heeftUitstaandeBetaling": False,
            "achterlatendeWoningen": [],
            "vestigingsDatum": None,
            "eigenaarId": None,
            "maximaleInschrijftijdEinddatum": None,
            "minimaleHuurprijs": None,
            "maximaleHuurprijs": None,
            "isScheefhuurder": False,
            "bijzondereDoelgroepId": 0,
            "extraInschrijfduurCorporatieId": None,
            "extraInschrijfduurGemeente": None,
            "actieveExtraInschrijfduur": False,
            "meetDatum": "2024-03-24",
            "wachttijdRegulierDatum": "2024-03-24",
            "eigenWoningId": None,
            "projecten": None
        },
        "zoekprofiel": {
            "locatie": {
                "regio": [],
                "municipality": [],
                "city": [],
                "neighborhood": []
            }
        }
    }

    try:
        response = session.post(api_url, params=params, json=post_data, timeout=30)

        if response.status_code != 200:
            print(f"[Listings] API returned status {response.status_code}")
            return []

        data = response.json()

        # Extract listings from response
        offers = []
        if isinstance(data, dict):
            for key in ["content", "items", "data", "result", "results", "objects",
                        "woningen", "dwellings", "advertenties", "aanbod"]:
                if key in data and isinstance(data[key], list):
                    offers = data[key]
                    break
        elif isinstance(data, list):
            offers = data

        # Normalize each room to a consistent format
        return sorted([normalize_room(room) for room in offers], key=lambda x: x['total_rent'])

    except requests.RequestException as e:
        print(f"[Listings] Request error: {e}")
        return []
    except json.JSONDecodeError as e:
        print(f"[Listings] JSON decode error: {e}")
        return []


def normalize_room(room: dict) -> dict:
    """
    Normalize room data to a consistent format.

    Returns a dictionary with standardized keys.
    """
    # Extract ID
    room_id = (room.get("id") or room.get("dwellingId") or
               room.get("objectId") or room.get("advertisementId") or
               room.get("advertentieId"))

    # Address components
    street = (room.get("street") or room.get("straat") or
              room.get("adres") or "")
    house_num = (room.get("houseNumber") or room.get("huisnummer") or
                 room.get("number") or "")
    addition = (room.get("houseNumberAddition") or
                room.get("huisnummerToevoeging") or "")

    # City
    city = room.get("city") or room.get("plaats") or room.get("stad") or {}
    if isinstance(city, dict):
        city_name = city.get("name") or city.get("naam") or ""
    else:
        city_name = str(city)

    # Build address string
    address_parts = [street, house_num, addition]
    address = " ".join(filter(None, [str(p) for p in address_parts])).strip()

    # Price information
    total_rent = (room.get("totalRent") or room.get("totaleHuur") or
                  room.get("totalPrice") or room.get("huurprijs") or
                  room.get("huurprijsTotaal"))

    # Convert to float if possible
    if total_rent is not None:
        try:
            total_rent = float(total_rent)
        except (ValueError, TypeError):
            total_rent = None

    # Area
    area = (room.get("areaDwelling") or room.get("oppervlakte") or
            room.get("area") or room.get("woonoppervlakte") or
            room.get("oppervlakteWoning"))

    # Number of rooms
    rooms = (room.get("numberOfRooms") or room.get("aantalKamers") or
             room.get("rooms") or room.get("kamers") or
             room.get("aantalSlaapkamers"))

    # Room type
    dwelling_type = room.get("dwellingType") or room.get("woningType") or {}
    if isinstance(dwelling_type, dict):
        type_name = (dwelling_type.get("name") or
                     dwelling_type.get("localizedName") or
                     dwelling_type.get("naam") or "")
    else:
        type_name = str(dwelling_type) if dwelling_type else ""

    # Available from date
    available_from = (room.get("availableFromDate") or room.get("beschikbaarPer") or
                      room.get("availableFrom") or room.get("availableDate") or
                      room.get("ingangsdatum"))

    # Application deadline
    deadline = (room.get("closingDate") or room.get("sluitingsdatum") or
                room.get("deadline") or room.get("reactDeadline") or
                room.get("reageerDeadline"))

    # URL key (used for applying)
    url_key = room.get("urlKey") or room.get("url_key") or ""

    return {
        "id": room_id,
        "url_key": url_key,
        "street": street,
        "house_number": house_num,
        "addition": addition,
        "address": address,
        "city": city_name,
        "total_rent": total_rent,
        "area": area,
        "rooms": rooms,
        "type": type_name,
        "available_from": available_from,
        "deadline": deadline,
        "url": f"https://www.roommatch.nl/aanbod/studentenwoningen/details/{url_key}" if url_key else None,
        "_raw": room  # Keep raw data for debugging
    }


def display_rooms(rooms: list[dict], max_display: int = 15):
    """Display room listings in a readable format"""
    print("\n" + "=" * 70)
    print(f"AVAILABLE ROOMS ({len(rooms)} found)")
    print("=" * 70)

    if len(rooms) == 0:
        print("\n    No rooms currently available")
        return

    for i, room in enumerate(rooms[:max_display], 1):
        print(f"\n[{i}] {room['address']}, {room['city']}")
        print("-" * 70)

        if room['total_rent']:
            print(f"    💰 Total rent: €{room['total_rent']:,.2f}/month")
        if room['area']:
            print(f"    📐 Area: {room['area']} m²")
        if room['rooms']:
            print(f"    🚪 Rooms: {room['rooms']}")
        if room['type']:
            print(f"    🏠 Type: {room['type']}")
        if room['available_from']:
            print(f"    📅 Available from: {room['available_from']}")
        if room['deadline']:
            print(f"    ⏰ Deadline: {room['deadline']}")
        if room['url']:
            print(f"    🔗 URL: {room['url']}")
        if room.get('url_key'):
            print(f"    🔑 URL Key: {room['url_key']}")

    if len(rooms) > max_display:
        print(f"\n... and {len(rooms) - max_display} more rooms")


def main():
    """Run as standalone script"""
    print("=" * 70)
    print("Roommatch.nl Room Listings")
    print("=" * 70)

    print("\n[1] Fetching room listings from API...")
    rooms = fetch_listings()

    if rooms:
        print(f"    ✓ Found {len(rooms)} rooms")

        # Save to JSON file
        with open("roommatch_listings.json", "w", encoding="utf-8") as f:
            json.dump(rooms, f, indent=2, ensure_ascii=False, default=str)
        print("    ✓ Saved to: roommatch_listings.json")

        display_rooms(rooms)
    else:
        print("    ✗ No rooms found or error occurred")

    print("\n" + "=" * 70)


if __name__ == "__main__":
    main()
