"""
IATA delay codes reference.

Standard IATA delay codes used in aviation industry to categorize delays.
"""

IATA_DELAY_CODES = {
    # Passenger and Baggage (codes 11-19)
    "11": {
        "code": "11",
        "category": "Passenger and Baggage",
        "description": "Late crew or cabin crew",
        "responsible_party": "airline",
        "typical_minutes": "5-30",
    },
    "12": {
        "code": "12",
        "category": "Passenger and Baggage",
        "description": "Late pax boarding",
        "responsible_party": "passengers",
        "typical_minutes": "5-15",
    },
    "13": {
        "code": "13",
        "category": "Passenger and Baggage",
        "description": "Late captain",
        "responsible_party": "airline",
        "typical_minutes": "10-30",
    },
    "14": {
        "code": "14",
        "category": "Passenger and Baggage",
        "description": "Pax documentation/visa check",
        "responsible_party": "airline",
        "typical_minutes": "5-20",
    },
    "15": {
        "code": "15",
        "category": "Passenger and Baggage",
        "description": "Special pax handling",
        "responsible_party": "handler",
        "typical_minutes": "5-15",
    },
    "16": {
        "code": "16",
        "category": "Operations",
        "description": "De-icing",
        "responsible_party": "weather",
        "typical_minutes": "10-30",
    },
    "17": {
        "code": "17",
        "category": "Passenger and Baggage",
        "description": "Pax missing at gate",
        "responsible_party": "passengers",
        "typical_minutes": "10-20",
    },
    "18": {
        "code": "18",
        "category": "Passenger and Baggage",
        "description": "Baggage reconciliation",
        "responsible_party": "airline",
        "typical_minutes": "10-30",
    },

    # Technical (codes 31-39)
    "31": {
        "code": "31",
        "category": "Technical",
        "description": "Flight deck technical defect",
        "responsible_party": "airline",
        "typical_minutes": "30-120",
    },
    "32": {
        "code": "32",
        "category": "Aircraft Services",
        "description": "Catering",
        "responsible_party": "vendor_catering",
        "typical_minutes": "10-30",
    },
    "33": {
        "code": "33",
        "category": "Aircraft Services",
        "description": "Cleaning",
        "responsible_party": "handler",
        "typical_minutes": "10-20",
    },
    "34": {
        "code": "34",
        "category": "Aircraft Services",
        "description": "Fueling/defueling",
        "responsible_party": "vendor_fuel",
        "typical_minutes": "10-30",
    },
    "35": {
        "code": "35",
        "category": "Technical",
        "description": "Cabin technical defect",
        "responsible_party": "airline",
        "typical_minutes": "20-60",
    },
    "36": {
        "code": "36",
        "category": "Technical",
        "description": "Engine/APU",
        "responsible_party": "airline",
        "typical_minutes": "30-120",
    },
    "37": {
        "code": "37",
        "category": "Technical",
        "description": "Component change",
        "responsible_party": "airline",
        "typical_minutes": "60-180",
    },
    "38": {
        "code": "38",
        "category": "Operations",
        "description": "Aircraft weight check",
        "responsible_party": "airline",
        "typical_minutes": "5-15",
    },

    # Documentation (codes 41-49)
    "41": {
        "code": "41",
        "category": "Documentation",
        "description": "Late loadsheet/trim sheet",
        "responsible_party": "handler",
        "typical_minutes": "5-15",
    },
    "42": {
        "code": "42",
        "category": "Documentation",
        "description": "Late flight plan",
        "responsible_party": "airline",
        "typical_minutes": "5-20",
    },
    "43": {
        "code": "43",
        "category": "Documentation",
        "description": "Flight documentation late",
        "responsible_party": "airline",
        "typical_minutes": "5-15",
    },

    # Airport Services (codes 61-69)
    "61": {
        "code": "61",
        "category": "Airport Services",
        "description": "Runway closed",
        "responsible_party": "airport_atc",
        "typical_minutes": "10-60",
    },
    "62": {
        "code": "62",
        "category": "Airport Services",
        "description": "No ramp/towing equipment",
        "responsible_party": "airport_atc",
        "typical_minutes": "10-30",
    },
    "63": {
        "code": "63",
        "category": "Airport Services",
        "description": "Airport facilities",
        "responsible_party": "airport_atc",
        "typical_minutes": "10-45",
    },
    "64": {
        "code": "64",
        "category": "Airport Services",
        "description": "Restrictions at airport",
        "responsible_party": "airport_atc",
        "typical_minutes": "10-60",
    },
    "65": {
        "code": "65",
        "category": "Airport Services",
        "description": "ATC delays",
        "responsible_party": "airport_atc",
        "typical_minutes": "10-90",
    },
    "66": {
        "code": "66",
        "category": "Airport Services",
        "description": "Slot allocation",
        "responsible_party": "airport_atc",
        "typical_minutes": "20-120",
    },
    "67": {
        "code": "67",
        "category": "Airport Services",
        "description": "Stand allocation",
        "responsible_party": "airport_atc",
        "typical_minutes": "10-30",
    },
    "68": {
        "code": "68",
        "category": "Airport Services",
        "description": "Late gate opening",
        "responsible_party": "airport_atc",
        "typical_minutes": "5-20",
    },
    "69": {
        "code": "69",
        "category": "Airport Services",
        "description": "Airport services",
        "responsible_party": "airport_atc",
        "typical_minutes": "10-30",
    },

    # Weather (codes 71-77)
    "71": {
        "code": "71",
        "category": "Weather",
        "description": "Weather at origin",
        "responsible_party": "weather",
        "typical_minutes": "30-180",
    },
    "72": {
        "code": "72",
        "category": "Weather",
        "description": "Weather at destination",
        "responsible_party": "weather",
        "typical_minutes": "30-180",
    },
    "73": {
        "code": "73",
        "category": "Weather",
        "description": "Weather en-route",
        "responsible_party": "weather",
        "typical_minutes": "20-120",
    },
    "75": {
        "code": "75",
        "category": "Weather",
        "description": "De-icing (weather)",
        "responsible_party": "weather",
        "typical_minutes": "15-45",
    },
    "76": {
        "code": "76",
        "category": "Weather",
        "description": "Snow removal",
        "responsible_party": "weather",
        "typical_minutes": "20-90",
    },
    "77": {
        "code": "77",
        "category": "Weather",
        "description": "Lightning/storms",
        "responsible_party": "weather",
        "typical_minutes": "30-120",
    },

    # Load (codes 81-89)
    "81": {
        "code": "81",
        "category": "Load",
        "description": "Load connection",
        "responsible_party": "handler",
        "typical_minutes": "10-30",
    },
    "82": {
        "code": "82",
        "category": "Load",
        "description": "Baggage late",
        "responsible_party": "handler",
        "typical_minutes": "10-25",
    },
    "83": {
        "code": "83",
        "category": "Load",
        "description": "Cargo late",
        "responsible_party": "handler",
        "typical_minutes": "10-30",
    },
    "84": {
        "code": "84",
        "category": "Load",
        "description": "Mail late",
        "responsible_party": "handler",
        "typical_minutes": "5-20",
    },
    "85": {
        "code": "85",
        "category": "Load",
        "description": "ULD/container shortage",
        "responsible_party": "airline",
        "typical_minutes": "15-45",
    },
    "86": {
        "code": "86",
        "category": "Load",
        "description": "Load planning error",
        "responsible_party": "handler",
        "typical_minutes": "10-30",
    },
    "87": {
        "code": "87",
        "category": "Load",
        "description": "Loading/offloading delayed",
        "responsible_party": "handler",
        "typical_minutes": "10-30",
    },
    "88": {
        "code": "88",
        "category": "Load",
        "description": "Cargo documentation",
        "responsible_party": "handler",
        "typical_minutes": "5-20",
    },

    # Aircraft Arrival (codes 91-99)
    "91": {
        "code": "91",
        "category": "Aircraft Arrival",
        "description": "Late aircraft arrival",
        "responsible_party": "airline",
        "typical_minutes": "10-180",
    },
    "92": {
        "code": "92",
        "category": "Aircraft Arrival",
        "description": "Aircraft rotation",
        "responsible_party": "airline",
        "typical_minutes": "15-120",
    },
    "93": {
        "code": "93",
        "category": "Aircraft Arrival",
        "description": "Late inbound connection",
        "responsible_party": "airline",
        "typical_minutes": "20-180",
    },
    "94": {
        "code": "94",
        "category": "Aircraft Arrival",
        "description": "Aircraft change",
        "responsible_party": "airline",
        "typical_minutes": "30-120",
    },
    "95": {
        "code": "95",
        "category": "Operations",
        "description": "Aircraft diversion",
        "responsible_party": "other",
        "typical_minutes": "60-240",
    },
    "96": {
        "code": "96",
        "category": "Operations",
        "description": "Aircraft rescheduled",
        "responsible_party": "airline",
        "typical_minutes": "30-180",
    },
}


def get_code_info(code: str) -> dict:
    """Get information about an IATA delay code."""
    return IATA_DELAY_CODES.get(code, {
        "code": code,
        "category": "Unknown",
        "description": "Unknown code",
        "responsible_party": "other",
        "typical_minutes": "Unknown",
    })


def get_codes_by_category(category: str) -> list:
    """Get all codes in a specific category."""
    return [
        info for code, info in IATA_DELAY_CODES.items()
        if info["category"] == category
    ]


def get_codes_by_responsible_party(party: str) -> list:
    """Get all codes for a specific responsible party."""
    return [
        info for code, info in IATA_DELAY_CODES.items()
        if info["responsible_party"] == party
    ]


STANDARD_TURNAROUND_TIMES = {
    "narrow_body": {  # A320, B737
        "deboarding": {"min": 8, "max": 15},
        "cleaning": {"min": 12, "max": 20},
        "catering": {"min": 10, "max": 20},
        "fueling": {"min": 15, "max": 30},
        "boarding": {"min": 15, "max": 30},
        "pushback": {"min": 3, "max": 5},
    },
    "wide_body": {  # A330, B777, A350
        "deboarding": {"min": 15, "max": 25},
        "cleaning": {"min": 20, "max": 35},
        "catering": {"min": 15, "max": 30},
        "fueling": {"min": 20, "max": 40},
        "boarding": {"min": 25, "max": 40},
        "pushback": {"min": 5, "max": 8},
    },
}


def get_standard_time(aircraft_size: str, activity_type: str) -> dict:
    """
    Get standard turnaround time for an activity.

    Args:
        aircraft_size: "narrow_body" or "wide_body"
        activity_type: Activity type (deboarding, cleaning, etc.)

    Returns:
        Dict with min and max standard times in minutes
    """
    size = aircraft_size.lower()
    activity = activity_type.lower()

    if size not in STANDARD_TURNAROUND_TIMES:
        size = "narrow_body"  # Default to narrow body

    if activity not in STANDARD_TURNAROUND_TIMES[size]:
        return {"min": 0, "max": 999}  # Unknown activity

    return STANDARD_TURNAROUND_TIMES[size][activity]


def is_within_standard(aircraft_size: str, activity_type: str, actual_minutes: int) -> bool:
    """Check if an activity duration was within industry standard."""
    standard = get_standard_time(aircraft_size, activity_type)
    return standard["min"] <= actual_minutes <= standard["max"]
