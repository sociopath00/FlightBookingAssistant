import os
from datetime import date

import dotenv
import pandas as pd
import psycopg2
from psycopg2 import pool
import redis

dotenv.load_dotenv('../config/.env')


# Create a connection pool
def postgres_connection_pool():
    connection_pool = psycopg2.pool.SimpleConnectionPool(
        1,  # minimum number of connections
        10,  # maximum number of connections
        user=os.environ["PG_USER"],
        password=os.environ["PG_PWD"],
        host=os.environ["PG_HOST"],
        port=os.environ["PG_PORT"],
        database=os.environ["PG_DB"]
    )

    # Get a connection from the pool
    connection = connection_pool.getconn()
    return connection


def get_flight_details(source: str, destination: str, travel_date: date) -> pd.DataFrame:
    """
    Function to get the flights from source city to destination city on a given travel date
    :param source: source city
    :param destination: destination city
    :param travel_date: travel date
    :return: list of flight details as a DataFrame
    """
    conn = postgres_connection_pool()

    query = f"""
    SELECT a.flight_id, b.airlines, b.departure_time, b.ticket_price, a.seats_available
    FROM daily_flights a LEFT JOIN flight_details b
    ON a.flight_id = b.flight_id
    WHERE a.flight_date='{travel_date}' AND b.source_city='{source}' AND b.destination_city='{destination}'
    """

    print(query)

    df = pd.read_sql(query, conn)
    df = df[df["seats_available"] > 0]
    # df["departure_time"] = df["departure_time"].dt.strftime("%H:%M:%s")
    print(df)
    return df


def update_available_seats(flight_id: int, travel_date: str):
    conn = postgres_connection_pool()
    query = f"""
    UPDATE daily_flights 
        SET seats_available = seats_available-1
    WHERE flight_id = {flight_id} AND
          flight_date = '{travel_date}'
    """

    cursor = conn.cursor()
    cursor.execute(query)
    conn.commit()

    return


def add_passenger_details(name: str, age: str, flight_id: int, travel_date: str, PNR):
    conn = postgres_connection_pool()

    query = f"""
    INSERT INTO booked_tickets VALUES(
    '{PNR}', {flight_id}, '{name}', {age}, '{travel_date}')
    """

    cursor = conn.cursor()
    cursor.execute(query)
    conn.commit()

    return


def redis_connection_pool():
    conn = redis.from_url(os.environ["REDIS_CONN_STRING"])
    return conn


if __name__ == "__main__":
    get_flight_details("mumbai", "new delhi", "2024-07-15")
