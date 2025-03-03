CREATE TABLE IF NOT EXISTS bookings (
    book_ref CHAR(6) PRIMARY KEY,
    book_date TIMESTAMPTZ NOT NULL,
    total_amount NUMERIC(10, 2) NOT NULL
);
CREATE TABLE IF NOT EXISTS tickets (
    ticket_no CHAR(13) PRIMARY KEY,
    book_ref CHAR(6) NOT NULL REFERENCES bookings (book_ref),
    passenger_id VARCHAR(20) NOT NULL,
    passenger_name TEXT NOT NULL,
    contact_data JSONB
);
CREATE TABLE IF NOT EXISTS airports (
    airport_code CHAR(3) PRIMARY KEY,
    airport_name TEXT NOT NULL,
    city TEXT NOT NULL,
    coordinates_lon DOUBLE PRECISION NOT NULL,
    coordinates_lat DOUBLE PRECISION NOT NULL,
    timezone TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS aircrafts (
    aircraft_code CHAR(3) PRIMARY KEY,
    model JSONB NOT NULL,
    range INT NOT NULL
);
CREATE TABLE IF NOT EXISTS flights (
    flight_id SERIAL PRIMARY KEY,
    flight_no CHAR(6) NOT NULL,
    scheduled_departure TIMESTAMPTZ NOT NULL,
    scheduled_arrival TIMESTAMPTZ NOT NULL,
    departure_airport CHAR(3) NOT NULL REFERENCES airports (airport_code),
    arrival_airport CHAR(3) NOT NULL REFERENCES airports (airport_code),
    status VARCHAR(20) NOT NULL,
    aircraft_code CHAR(3) NOT NULL REFERENCES aircrafts (aircraft_code),
    actual_departure TIMESTAMPTZ,
    actual_arrival TIMESTAMPTZ
);
CREATE TABLE IF NOT EXISTS ticket_flights (
    ticket_no CHAR(13) NOT NULL REFERENCES tickets (ticket_no),
    flight_id INT NOT NULL REFERENCES flights (flight_id),
    fare_conditions VARCHAR(10) NOT NULL,
    amount NUMERIC(10, 2) NOT NULL,
    PRIMARY KEY (ticket_no, flight_id)
);
CREATE TABLE IF NOT EXISTS seats (
    aircraft_code CHAR(3) NOT NULL REFERENCES aircrafts (aircraft_code),
    seat_no VARCHAR(4) NOT NULL,
    fare_conditions VARCHAR(10) NOT NULL,
    PRIMARY KEY (aircraft_code, seat_no)
);
CREATE TABLE IF NOT EXISTS boarding_passes (
    ticket_no CHAR(13) NOT NULL REFERENCES tickets (ticket_no),
    flight_id INT NOT NULL REFERENCES flights (flight_id),
    boarding_no INT NOT NULL,
    seat_no VARCHAR(4) NOT NULL,
    PRIMARY KEY (ticket_no, flight_id)
);