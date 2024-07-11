from typing import Annotated
from pydantic import BaseModel, Field, model_validator
from datetime import date, datetime
import pandas as pd

from src.db_utils import get_flight_details


class FlightBookingInputs(BaseModel):
    source_city: Annotated[str, Field(description="Source Station for the flight booking.")]
    destination_city: Annotated[str, Field(description="Destination station for the flight booking.")]
    travel_date: Annotated[date, Field(description="Date for which flight to be booked")]

    @model_validator(mode="before")
    def check(cls, values):
        print(values)
        missing_data_list = []
        if not values.get("source_city"):
            missing_data_list.append("source city")

        if not values.get("destination_city"):
            missing_data_list.append("destination city")

        if not values.get("travel_date"):
            missing_data_list.append("travel date")

        if missing_data_list:
            raise ValueError(f"Please provide {','.join(missing_data_list)}")

        return values


def flight_list(inputs: Annotated[FlightBookingInputs, "Inputs for flight list extraction"]) -> str:
    print(inputs)

    source = inputs.source_city.lower()
    destination = inputs.destination_city.lower()
    travel_date = datetime.strftime(inputs.travel_date, "%Y-%m-%d")
    print(travel_date, source, destination)

    df = get_flight_details(source, destination, travel_date)
    df["departure_time"] = df["departure_time"].astype(str)
    df = df.to_dict(orient="records")
    print(df)
    return f"The list of flights available are {df}"


class FlightConfirmationInputs(BaseModel):
    flight_id: Annotated[int, Field(description="The flight id to book a seat eg. 1001, 2003 ")]

    @model_validator(mode="before")
    def check(cls, values):
        if not values.get('flight_id'):
            raise ValueError("Please provide valid flight id from the above list")

        return values


def flight_booking(inputs: Annotated[FlightConfirmationInputs, "Inputs for flight confirmation"]) -> str:
    flight_id = inputs.flight_id

    return f"Please provide Name and Age to confirm your booking for flight {flight_id}"


class PassengerDetails(BaseModel):
    passenger_name: Annotated[str, Field(description="name of the passenger")]
    passenger_age: Annotated[int, Field(description="age of the passenger")]

    @model_validator(mode="before")
    def check(cls, values):
        missing_inputs = []
        if not values.get("passenger_name"):
            missing_inputs.append("name")
        if not values.get("passenger_age"):
            missing_inputs.append("age")

        if missing_inputs:
            raise ValueError(f"Please provide {','.join(missing_inputs)}")

        return values

def booking_confirmation(inputs: Annotated[PassengerDetails, "Passenger details for Ticket booking"]) -> str:
    pass
