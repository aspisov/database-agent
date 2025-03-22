-- Table storing booking information
CREATE TABLE IF NOT EXISTS bookings (
    book_ref CHAR(6) PRIMARY KEY,  -- Unique booking reference number
    book_date TIMESTAMPTZ NOT NULL,  -- Date and time when the booking was made
    total_amount NUMERIC(10, 2) NOT NULL  -- Total price of the booking
);

-- Table storing ticket details for passengers
CREATE TABLE IF NOT EXISTS tickets (
    ticket_no CHAR(13) PRIMARY KEY,  -- Unique ticket number
    book_ref CHAR(6) NOT NULL REFERENCES bookings (book_ref),  -- Booking reference associated with the ticket
    passenger_id VARCHAR(20) NOT NULL,  -- Unique identifier of the passenger
    passenger_name TEXT NOT NULL,  -- Full name of the passenger
    contact_data JSONB  -- JSON structure containing passenger contact details
);


-- Table storing airport details
CREATE TABLE IF NOT EXISTS airports (
    airport_code CHAR(3) PRIMARY KEY,  -- IATA airport code
    airport_name TEXT NOT NULL,  -- Full name of the airport
    city TEXT NOT NULL,  -- City where the airport is located
    coordinates_lon DOUBLE PRECISION NOT NULL,  -- Longitude coordinate of the airport
    coordinates_lat DOUBLE PRECISION NOT NULL,  -- Latitude coordinate of the airport
    timezone TEXT NOT NULL  -- Time zone in which the airport operates
);

-- Table storing aircraft details
CREATE TABLE IF NOT EXISTS aircrafts (
    aircraft_code CHAR(3) PRIMARY KEY,  -- Unique aircraft model code
    model JSONB NOT NULL,  -- JSON structure containing aircraft model details
    range INT NOT NULL  -- Maximum range of the aircraft in kilometers
);

-- Table storing flight schedules
CREATE TABLE IF NOT EXISTS flights (
    flight_id SERIAL PRIMARY KEY,  -- Unique identifier for the flight
    flight_no CHAR(6) NOT NULL,  -- Flight number assigned to the flight
    scheduled_departure TIMESTAMPTZ NOT NULL,  -- Scheduled departure time
    scheduled_arrival TIMESTAMPTZ NOT NULL,  -- Scheduled arrival time
    departure_airport CHAR(3) NOT NULL REFERENCES airports (airport_code),  -- Airport code of departure location
    arrival_airport CHAR(3) NOT NULL REFERENCES airports (airport_code),  -- Airport code of arrival location
    status VARCHAR(20) NOT NULL,  -- Current flight status (e.g., 'Scheduled', 'Cancelled', 'Departed')
    aircraft_code CHAR(3) NOT NULL REFERENCES aircrafts (aircraft_code),  -- Aircraft model used for the flight
    actual_departure TIMESTAMPTZ,  -- Actual departure time (if available)
    actual_arrival TIMESTAMPTZ  -- Actual arrival time (if available)
);

-- Table storing ticket details for individual flights
CREATE TABLE IF NOT EXISTS ticket_flights (
    ticket_no CHAR(13) NOT NULL REFERENCES tickets (ticket_no),  -- Ticket number associated with the flight
    flight_id INT NOT NULL REFERENCES flights (flight_id),  -- Flight ID linked to the ticket
    fare_conditions VARCHAR(10) NOT NULL,  -- Fare category (e.g., 'Economy', 'Business', 'First Class')
    amount NUMERIC(10, 2) NOT NULL,  -- Ticket price for the flight
    PRIMARY KEY (ticket_no, flight_id)
);

-- Table storing seat availability per aircraft model
CREATE TABLE IF NOT EXISTS seats (
    aircraft_code CHAR(3) NOT NULL REFERENCES aircrafts (aircraft_code),  -- Aircraft model associated with the seat
    seat_no VARCHAR(4) NOT NULL,  -- Seat number within the aircraft
    fare_conditions VARCHAR(10) NOT NULL,  -- Fare conditions applicable to the seat
    PRIMARY KEY (aircraft_code, seat_no)
);

-- Table storing boarding passes issued to passengers
CREATE TABLE IF NOT EXISTS boarding_passes (
    ticket_no CHAR(13) NOT NULL REFERENCES tickets (ticket_no),  -- Ticket number associated with the boarding pass
    flight_id INT NOT NULL REFERENCES flights (flight_id),  -- Flight ID linked to the boarding pass
    boarding_no INT NOT NULL,  -- Sequential boarding number assigned to the passenger
    seat_no VARCHAR(4) NOT NULL,  -- Assigned seat number on the flight
    PRIMARY KEY (ticket_no, flight_id)
);
