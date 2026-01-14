"""
Seed database with sample data for testing and development.
"""
import asyncio
import sys
from pathlib import Path
from datetime import datetime, timedelta
from decimal import Decimal
import random
import secrets

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import structlog

from models.database import AsyncSessionLocal, engine, Base
from models.customer import Customer, APIKey, OrganizationType, SubscriptionTier
from models.flight import Flight, FlightStatus, AircraftSize
from models.turnaround import Turnaround, TurnaroundActivity, TurnaroundStatus, ActivityType
from models.alert import Alert, AlertType, AlertSeverity
from api.auth import generate_api_key

logger = structlog.get_logger()


async def create_customers(db: AsyncSession) -> dict:
    """Create sample customers/organizations."""
    logger.info("creating_customers")

    customers = []

    # Turkish Airlines (Design Partner)
    turkish_airlines = Customer(
        id="cust_turkish_airlines",
        name="Turkish Airlines",
        legal_name="Türk Hava Yolları A.O.",
        organization_type=OrganizationType.AIRLINE,
        email="ops@turkishairlines.com",
        phone="+90-212-463-6363",
        address_line1="Türk Hava Yolları Genel Müdürlüğü",
        city="Istanbul",
        country="Turkey",
        postal_code="34149",
        subscription_tier=SubscriptionTier.ENTERPRISE,
        monthly_fee=Decimal("55000.00"),
        monthly_api_call_limit=None,  # Unlimited
        predict_api_rate=Decimal("0.025"),
        parse_api_rate=Decimal("0.04"),
        benchmark_api_rate=Decimal("0.015"),
        enabled_connectors=["SITA", "Amadeus"],
        connector_annual_fees={"SITA": 15000, "Amadeus": 20000},
        contributes_data=True,
        is_design_partner=True,
        is_active=True,
    )
    customers.append(turkish_airlines)

    # Lufthansa (Enterprise)
    lufthansa = Customer(
        id="cust_lufthansa",
        name="Lufthansa",
        legal_name="Deutsche Lufthansa AG",
        organization_type=OrganizationType.AIRLINE,
        email="operations@lufthansa.com",
        phone="+49-69-696-0",
        address_line1="Lufthansa Aviation Center",
        city="Frankfurt",
        country="Germany",
        postal_code="60546",
        subscription_tier=SubscriptionTier.ENTERPRISE,
        monthly_fee=Decimal("50000.00"),
        monthly_api_call_limit=None,
        predict_api_rate=Decimal("0.03"),
        parse_api_rate=Decimal("0.05"),
        benchmark_api_rate=Decimal("0.02"),
        enabled_connectors=["Amadeus"],
        connector_annual_fees={"Amadeus": 20000},
        contributes_data=True,
        is_active=True,
    )
    customers.append(lufthansa)

    # Swissport (Ground Handler - Professional)
    swissport = Customer(
        id="cust_swissport_ist",
        name="Swissport Istanbul",
        legal_name="Swissport International Ltd.",
        organization_type=OrganizationType.GROUND_HANDLER,
        email="ops.istanbul@swissport.com",
        phone="+90-212-465-4000",
        city="Istanbul",
        country="Turkey",
        subscription_tier=SubscriptionTier.PROFESSIONAL,
        monthly_fee=Decimal("20000.00"),
        monthly_api_call_limit=50000,
        predict_api_rate=Decimal("0.03"),
        parse_api_rate=Decimal("0.05"),
        benchmark_api_rate=Decimal("0.02"),
        enabled_connectors=["Swissport"],
        connector_annual_fees={"Swissport": 15000},
        contributes_data=True,
        is_active=True,
    )
    customers.append(swissport)

    # Istanbul Airport (Airport Authority - Starter)
    istanbul_airport = Customer(
        id="cust_istanbul_airport",
        name="Istanbul Airport",
        legal_name="İGA Havalimanı İşletmesi A.Ş.",
        organization_type=OrganizationType.AIRPORT,
        email="operations@istairport.com",
        phone="+90-212-444-1442",
        city="Istanbul",
        country="Turkey",
        subscription_tier=SubscriptionTier.STARTER,
        monthly_fee=Decimal("5000.00"),
        monthly_api_call_limit=10000,
        predict_api_rate=Decimal("0.04"),
        parse_api_rate=Decimal("0.06"),
        benchmark_api_rate=Decimal("0.03"),
        contributes_data=False,
        is_active=True,
    )
    customers.append(istanbul_airport)

    # Demo Customer (Free Tier)
    demo = Customer(
        id="cust_demo",
        name="Demo Company",
        legal_name="Demo Company Inc.",
        organization_type=OrganizationType.AIRLINE,
        email="demo@example.com",
        subscription_tier=SubscriptionTier.FREE,
        monthly_api_call_limit=1000,
        predict_api_rate=Decimal("0.05"),
        parse_api_rate=Decimal("0.07"),
        benchmark_api_rate=Decimal("0.04"),
        is_active=True,
    )
    customers.append(demo)

    for customer in customers:
        db.add(customer)

    await db.commit()

    logger.info("customers_created", count=len(customers))

    return {c.id: c for c in customers}


async def create_api_keys(db: AsyncSession, customers: dict) -> dict:
    """Create API keys for customers."""
    logger.info("creating_api_keys")

    api_keys = {}

    for customer_id, customer in customers.items():
        # Create production key
        full_key, key_hash, key_prefix = generate_api_key("gs_live")

        api_key = APIKey(
            id=f"key_{customer_id}_prod",
            customer_id=customer_id,
            key_hash=key_hash,
            key_prefix=key_prefix,
            name="Production API Key",
            environment="production",
            scopes=["predict:read", "parse:read", "benchmark:read"],
            rate_limit_per_minute=1000 if customer.subscription_tier == SubscriptionTier.ENTERPRISE else 100,
            is_active=True,
        )

        db.add(api_key)
        api_keys[customer_id] = full_key

        logger.info("api_key_created", customer_id=customer_id, key_prefix=key_prefix, full_key=full_key)

    await db.commit()

    logger.info("api_keys_created", count=len(api_keys))

    return api_keys


async def create_flights(db: AsyncSession, count: int = 50) -> list:
    """Create sample flights."""
    logger.info("creating_flights", count=count)

    flights = []
    airlines = ["TK", "LH", "BA", "AF", "KL", "EK", "QR"]
    aircraft_types = ["B737", "A320", "B777", "A350", "A321", "B787"]
    origins = ["FRA", "LHR", "CDG", "AMS", "DXB", "DOH", "JFK"]

    now = datetime.utcnow()

    for i in range(count):
        airline = random.choice(airlines)
        flight_number = f"{airline}{random.randint(1000, 9999)}"

        # Random time within next 24 hours
        scheduled_arrival = now + timedelta(minutes=random.randint(-60, 1440))
        scheduled_departure = scheduled_arrival + timedelta(minutes=random.randint(45, 120))

        flight = Flight(
            id=f"flight_{i+1}",
            flight_number=flight_number,
            airline_code=airline,
            aircraft_type=random.choice(aircraft_types),
            aircraft_size=random.choice(list(AircraftSize)),
            registration=f"{airline}-{random.randint(1000, 9999)}",
            origin=random.choice(origins),
            destination="IST",
            scheduled_arrival_time=scheduled_arrival,
            scheduled_departure_time=scheduled_departure,
            status=random.choice([FlightStatus.SCHEDULED, FlightStatus.AIRBORNE, FlightStatus.LANDED]),
            gate=f"{random.choice(['A', 'B', 'C', 'D'])}{random.randint(1, 99)}",
            terminal="International",
            passenger_count=random.randint(80, 350),
            cargo_weight=random.randint(1000, 15000),
            weather_impact_score=random.uniform(0.1, 0.9),
            arrival_delay_minutes=random.randint(-10, 30) if random.random() > 0.7 else 0,
        )

        flights.append(flight)
        db.add(flight)

    await db.commit()

    logger.info("flights_created", count=len(flights))

    return flights


async def create_turnarounds(db: AsyncSession, flights: list) -> list:
    """Create turnaround records for flights."""
    logger.info("creating_turnarounds")

    turnarounds = []

    for flight in flights[:30]:  # Create turnarounds for first 30 flights
        turnaround = Turnaround(
            id=f"turn_{flight.id}",
            flight_id=flight.id,
            status=random.choice([
                TurnaroundStatus.SCHEDULED,
                TurnaroundStatus.IN_PROGRESS,
                TurnaroundStatus.ON_TIME,
                TurnaroundStatus.AT_RISK,
            ]),
            scheduled_start=flight.scheduled_arrival_time,
            scheduled_end=flight.scheduled_departure_time,
            actual_start=flight.scheduled_arrival_time if flight.status != FlightStatus.SCHEDULED else None,
            risk_score=random.uniform(0.1, 0.9),
            predicted_delay_minutes=random.randint(0, 45),
            prediction_confidence=random.uniform(0.6, 0.95),
        )

        turnarounds.append(turnaround)
        db.add(turnaround)

        # Create activities
        activities = [
            ("deboarding", timedelta(minutes=15)),
            ("cleaning", timedelta(minutes=25)),
            ("catering", timedelta(minutes=30)),
            ("refueling", timedelta(minutes=35)),
            ("boarding", timedelta(minutes=25)),
        ]

        for activity_name, duration in activities:
            activity = TurnaroundActivity(
                id=f"act_{turnaround.id}_{activity_name}",
                turnaround_id=turnaround.id,
                activity_type=ActivityType[activity_name.upper()],
                scheduled_start=turnaround.scheduled_start + timedelta(minutes=random.randint(0, 20)),
                scheduled_duration_minutes=int(duration.total_seconds() / 60),
                status="completed" if random.random() > 0.3 else "in_progress",
            )
            db.add(activity)

    await db.commit()

    logger.info("turnarounds_created", count=len(turnarounds))

    return turnarounds


async def create_alerts(db: AsyncSession, turnarounds: list) -> list:
    """Create sample alerts."""
    logger.info("creating_alerts")

    alerts = []

    for turnaround in turnarounds[:15]:  # Create alerts for first 15 turnarounds
        alert = Alert(
            id=f"alert_{turnaround.id}",
            turnaround_id=turnaround.id,
            alert_type=random.choice(list(AlertType)),
            severity=random.choice(list(AlertSeverity)),
            title=f"Delay risk detected for {turnaround.flight_id}",
            message=f"Turnaround at risk with {turnaround.predicted_delay_minutes} min predicted delay",
            status="active" if random.random() > 0.5 else "acknowledged",
            metadata={"risk_score": turnaround.risk_score},
        )

        alerts.append(alert)
        db.add(alert)

    await db.commit()

    logger.info("alerts_created", count=len(alerts))

    return alerts


async def main():
    """Main seed data function."""
    logger.info("starting_database_seed")

    # Create tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    logger.info("database_tables_created")

    # Create session
    async with AsyncSessionLocal() as db:
        # Create seed data
        customers = await create_customers(db)
        api_keys = await create_api_keys(db, customers)
        flights = await create_flights(db, count=50)
        turnarounds = await create_turnarounds(db, flights)
        alerts = await create_alerts(db, turnarounds)

    logger.info("database_seed_completed")

    # Print API keys for testing
    print("\n" + "=" * 80)
    print("DATABASE SEEDED SUCCESSFULLY")
    print("=" * 80)
    print("\nAPI Keys for Testing:")
    print("-" * 80)
    for customer_id, api_key in api_keys.items():
        print(f"{customer_id:30s} : {api_key}")
    print("=" * 80)
    print("\nUse these API keys in the 'X-API-Key' header to test the API.")
    print("=" * 80 + "\n")


if __name__ == "__main__":
    asyncio.run(main())
