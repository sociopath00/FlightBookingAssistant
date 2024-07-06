from typing import Annotated
from pydantic import BaseModel, Field, model_validator
from datetime import date, datetime
import pandas as pd


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


def flight_list(inputs: Annotated[FlightBookingInputs, "Inputs for flight list extraction"]) -> dict:
    print(inputs)
    df = pd.read_csv("flights.csv")

    source = inputs.source_city.lower()
    destination = inputs.destination_city.lower()
    travel_date = datetime.strftime(inputs.travel_date, "%Y-%m-%d")
    print(travel_date, source, destination)

    df = df[(df["source"] == source) & (df["destination"] == destination) & (df["date"] == travel_date)]
    df = df.to_dict(orient="records")
    print(df)
    return {"message": "The list of flights ", "data": df}



