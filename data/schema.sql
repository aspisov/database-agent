-- Table storing booking information
CREATE TABLE IF NOT EXISTS bookings (
    book_ref CHAR(6) PRIMARY KEY,  -- Unique booking reference number
    book_date TIMESTAMPTZ NOT NULL,  -- Date and time when the booking was made
    total_amount NUMERIC(10, 2) NOT NULL  -- Total price of the booking
);
COMMENT ON TABLE bookings IS 'Stores information about flight bookings.';
COMMENT ON COLUMN bookings.book_ref IS 'Unique reference number for the booking.';
COMMENT ON COLUMN bookings.book_date IS 'Timestamp indicating when the booking was made.';
COMMENT ON COLUMN bookings.total_amount IS 'Total cost of the booking in currency units.';

-- Table storing ticket details for passengers
CREATE TABLE IF NOT EXISTS tickets (
    ticket_no CHAR(13) PRIMARY KEY,  -- Unique ticket number
    book_ref CHAR(6) NOT NULL REFERENCES bookings (book_ref),  -- Booking reference associated with the ticket
    passenger_id VARCHAR(20) NOT NULL,  -- Unique identifier of the passenger
    passenger_name TEXT NOT NULL,  -- Full name of the passenger
    contact_data JSONB  -- JSON structure containing passenger contact details
);
COMMENT ON TABLE tickets IS 'Stores ticket details associated with bookings.';
COMMENT ON COLUMN tickets.ticket_no IS 'Unique ticket number assigned to a passenger.';
COMMENT ON COLUMN tickets.book_ref IS 'Booking reference associated with this ticket.';
COMMENT ON COLUMN tickets.passenger_id IS 'Unique identifier of the passenger.';
COMMENT ON COLUMN tickets.passenger_name IS 'Full name of the passenger.';
COMMENT ON COLUMN tickets.contact_data IS 'Passenger contact information stored in JSON format.';

-- Table storing airport details
CREATE TABLE IF NOT EXISTS airports (
    airport_code CHAR(3) PRIMARY KEY,  -- IATA airport code
    airport_name TEXT NOT NULL,  -- Full name of the airport
    city TEXT NOT NULL,  -- City where the airport is located
    coordinates_lon DOUBLE PRECISION NOT NULL,  -- Longitude coordinate of the airport
    coordinates_lat DOUBLE PRECISION NOT NULL,  -- Latitude coordinate of the airport
    timezone TEXT NOT NULL  -- Time zone in which the airport operates
);
COMMENT ON TABLE airports IS 'Stores information about airports.';
COMMENT ON COLUMN airports.airport_code IS 'Three-letter IATA airport code.';
COMMENT ON COLUMN airports.airport_name IS 'Official name of the airport.';
COMMENT ON COLUMN airports.city IS 'City where the airport is located.';
COMMENT ON COLUMN airports.coordinates_lon IS 'Longitude coordinate of the airport.';
COMMENT ON COLUMN airports.coordinates_lat IS 'Latitude coordinate of the airport.';
COMMENT ON COLUMN airports.timezone IS 'Time zone in which the airport operates.';

-- Table storing aircraft details
CREATE TABLE IF NOT EXISTS aircrafts (
    aircraft_code CHAR(3) PRIMARY KEY,  -- Unique aircraft model code
    model JSONB NOT NULL,  -- JSON structure containing aircraft model details
    range INT NOT NULL  -- Maximum range of the aircraft in kilometers
);
COMMENT ON TABLE aircrafts IS 'Stores details about aircraft models.';
COMMENT ON COLUMN aircrafts.aircraft_code IS 'Unique aircraft model identifier.';
COMMENT ON COLUMN aircrafts.model IS 'JSON structure containing aircraft model details.';
COMMENT ON COLUMN aircrafts.range IS 'Maximum flight range of the aircraft in kilometers.';

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
COMMENT ON TABLE flights IS 'Stores information about scheduled flights.';
COMMENT ON COLUMN flights.flight_id IS 'Unique identifier for each flight.';
COMMENT ON COLUMN flights.flight_no IS 'Flight number assigned to the flight.';
COMMENT ON COLUMN flights.scheduled_departure IS 'Scheduled departure time of the flight.';
COMMENT ON COLUMN flights.scheduled_arrival IS 'Scheduled arrival time of the flight.';
COMMENT ON COLUMN flights.departure_airport IS 'IATA code of the departure airport.';
COMMENT ON COLUMN flights.arrival_airport IS 'IATA code of the arrival airport.';
COMMENT ON COLUMN flights.status IS 'Current status of the flight (e.g., Scheduled, Cancelled, Delayed).';
COMMENT ON COLUMN flights.aircraft_code IS 'Code of the aircraft model used for the flight.';
COMMENT ON COLUMN flights.actual_departure IS 'Actual departure time, if available.';
COMMENT ON COLUMN flights.actual_arrival IS 'Actual arrival time, if available.';

-- Table storing ticket details for individual flights
CREATE TABLE IF NOT EXISTS ticket_flights (
    ticket_no CHAR(13) NOT NULL REFERENCES tickets (ticket_no),  -- Ticket number associated with the flight
    flight_id INT NOT NULL REFERENCES flights (flight_id),  -- Flight ID linked to the ticket
    fare_conditions VARCHAR(10) NOT NULL,  -- Fare category (e.g., 'Economy', 'Business', 'First Class')
    amount NUMERIC(10, 2) NOT NULL,  -- Ticket price for the flight
    PRIMARY KEY (ticket_no, flight_id)
);
COMMENT ON TABLE ticket_flights IS 'Stores ticket information related to specific flights.';
COMMENT ON COLUMN ticket_flights.ticket_no IS 'Ticket number associated with the flight.';
COMMENT ON COLUMN ticket_flights.flight_id IS 'Flight ID linked to the ticket.';
COMMENT ON COLUMN ticket_flights.fare_conditions IS 'Fare category for the ticket (e.g., Economy, Business, First Class).';
COMMENT ON COLUMN ticket_flights.amount IS 'Price of the ticket for the flight.';

-- Table storing seat availability per aircraft model
CREATE TABLE IF NOT EXISTS seats (
    aircraft_code CHAR(3) NOT NULL REFERENCES aircrafts (aircraft_code),  -- Aircraft model associated with the seat
    seat_no VARCHAR(4) NOT NULL,  -- Seat number within the aircraft
    fare_conditions VARCHAR(10) NOT NULL,  -- Fare conditions applicable to the seat
    PRIMARY KEY (aircraft_code, seat_no)
);
COMMENT ON TABLE seats IS 'Stores seat details for aircraft models.';
COMMENT ON COLUMN seats.aircraft_code IS 'Aircraft model code associated with the seat.';
COMMENT ON COLUMN seats.seat_no IS 'Seat number within the aircraft.';
COMMENT ON COLUMN seats.fare_conditions IS 'Fare category for the seat (e.g., Economy, Business, First Class).';

-- Table storing boarding passes issued to passengers
CREATE TABLE IF NOT EXISTS boarding_passes (
    ticket_no CHAR(13) NOT NULL REFERENCES tickets (ticket_no),  -- Ticket number associated with the boarding pass
    flight_id INT NOT NULL REFERENCES flights (flight_id),  -- Flight ID linked to the boarding pass
    boarding_no INT NOT NULL,  -- Sequential boarding number assigned to the passenger
    seat_no VARCHAR(4) NOT NULL,  -- Assigned seat number on the flight
    PRIMARY KEY (ticket_no, flight_id)
);
COMMENT ON TABLE boarding_passes IS 'Stores boarding pass details for passengers.';
COMMENT ON COLUMN boarding_passes.ticket_no IS 'Ticket number associated with the boarding pass.';
COMMENT ON COLUMN boarding_passes.flight_id IS 'Flight ID linked to the boarding pass.';
COMMENT ON COLUMN boarding_passes.boarding_no IS 'Sequential boarding number assigned to the passenger.';
COMMENT ON COLUMN boarding_passes.seat_no IS 'Assigned seat number on the flight.';
