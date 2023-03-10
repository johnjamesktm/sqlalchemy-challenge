import datetime as dt

import sqlalchemy
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import Session
from sqlalchemy import create_engine, inspect, func

from flask import Flask, jsonify

engine = create_engine("sqlite:///Resources/hawaii.sqlite")

Base = automap_base()
Base.prepare(autoload_with=engine) 

Station = Base.classes.station
Measurement = Base.classes.measurement

session = Session(engine)

def populate_precipitation():
    recent_date_str = session.query(Measurement.date).order_by(Measurement.date.desc()).first()[0]
    recent_date = dt.datetime.strptime(recent_date_str, "%Y-%m-%d").date()

    # Calculate the date one year from the last date in data set.
    past_date = dt.datetime(year=recent_date.year - 1, month=recent_date.month, day=recent_date.day).date()

    # Perform a query to retrieve the date and precipitation scores
    sel = [Measurement.date, Measurement.prcp]
    last_year_data = session.query(*sel)\
        .filter(Measurement.date >= past_date)\
        .filter(Measurement.date <= recent_date)\
        .order_by(Measurement.date.desc())\
        .all()

    return [{"date": result[0], "prcp": result[1]} for result in last_year_data]

last_year_prcp_data = populate_precipitation()

# Find all stations
stations_data = session.query(Station).all()
stations_result = [{"station": result.station,\
    "name": result.name,\
    "latitude": result.latitude,\
    "longitude": result.longitude,\
    "elevation": result.elevation\
} for result in stations_data]

# Find the most active station
sel = [Measurement.station, func.count()]
stations_count = session.query(*sel)\
    .group_by(Measurement.station)\
    .order_by(func.count().desc())\
    .all()
most_active_station = stations_count[0][0]

def populate_tempratures():
    recent_date_str = session.query(Measurement.date)\
        .filter(Measurement.station == most_active_station)\
        .order_by(Measurement.date.desc())\
        .first()[0]
    recent_date = dt.datetime.strptime(recent_date_str, "%Y-%m-%d").date()
    past_date = dt.datetime(year=recent_date.year - 1, month=recent_date.month, day=recent_date.day).date()
    sel = [Measurement.date, Measurement.tobs]
    last_year_data = session.query(*sel)\
        .filter(Measurement.station == most_active_station)\
        .filter(Measurement.date >= past_date)\
        .filter(Measurement.date <= recent_date)\
        .order_by(Measurement.date)\
        .all()
    return last_year_data

last_year_tobs_data = [{"date": result[0], "tobs": result[1]} for result in populate_tempratures()]

session.close()

app = Flask(__name__)

@app.route("/")
def home():
    print("Server received request for 'Home' page...")
    return (
        f"Welcome to the Climate App API!<br/>"
        f"Available Routes:<br/>"
        f"/api/v1.0/precipitation<br/>"
        f"/api/v1.0/stations<br/>"
        f"/api/v1.0/tobs<br/>"
        f"/api/v1.0/&lt;start&gt;<br/>"
        f"/api/v1.0/&lt;start&gt;/&lt;end&gt;"
    )


@app.route("/api/v1.0/precipitation")
def precipitation():
    return jsonify(last_year_prcp_data)

@app.route("/api/v1.0/stations")
def stations():
    return jsonify(stations_result)

@app.route("/api/v1.0/tobs")
def tempratures():
    return jsonify(last_year_tobs_data)

@app.route("/api/v1.0/<start>")
def dynamic_route_start(start):
    session = Session(engine)
    
    result_data = session.query(func.min(Measurement.tobs), func.max(Measurement.tobs), func.avg(Measurement.tobs))\
        .filter(Measurement.date >= start)\
        .all()
    
    result = {
        "TMIN": result_data[0][0],
        "TMAX": result_data[0][1],
        "TAVG": result_data[0][2]
    }

    session.close()
    return jsonify(result)

@app.route("/api/v1.0/<start>/<end>")
def dynamic_route_start_end(start, end):
    session = Session(engine)
    
    result_data = session.query(func.min(Measurement.tobs), func.max(Measurement.tobs), func.avg(Measurement.tobs))\
        .filter(Measurement.date >= start)\
        .filter(Measurement.date <= end)\
        .all()
    
    result = {
        "TMIN": result_data[0][0],
        "TMAX": result_data[0][1],
        "TAVG": result_data[0][2]
    }

    session.close()
    return jsonify(result)

if __name__ == "__main__":
    app.run(debug=True)
