-- 1. Insert sample airports
INSERT INTO airports (airport_code, airport_name, city, coordinates_lon, coordinates_lat, timezone)
VALUES
  ('JFK', 'John F. Kennedy International Airport', 'New York', -73.7781, 40.6413, 'America/New_York'),
  ('LAX', 'Los Angeles International Airport', 'Los Angeles', -118.4085, 33.9416, 'America/Los_Angeles'),
  ('ORD', 'O Hare International Airport', 'Chicago', -87.9048, 41.9742, 'America/Chicago'),
  ('ATL', 'Hartsfield-Jackson Atlanta International Airport', 'Atlanta', -84.4277, 33.6407, 'America/New_York');

-- 2. Insert sample aircrafts
INSERT INTO aircrafts (aircraft_code, model, range)
VALUES
  ('A01', '{"name": "Boeing 737"}', 3000);

-- 3. Insert sample bookings (one per passenger)
INSERT INTO bookings (book_ref, book_date, total_amount) VALUES
  ('B00001', '2025-01-01 07:00:00+00', 700.00),
  ('B00002', '2025-01-03 07:00:00+00', 600.00),
  ('B00003', '2025-01-06 07:00:00+00', 500.00),
  ('B00004', '2025-01-07 07:00:00+00', 300.00),
  ('B00005', '2025-01-09 07:00:00+00', 400.00),
  ('B00006', '2025-01-13 07:00:00+00', 700.00);

-- 4. Insert sample tickets (one per passenger)
INSERT INTO tickets (ticket_no, book_ref, passenger_id, passenger_name, contact_data) VALUES
  ('T000000000001', 'B00001', 'P1', 'Alice', '{"email": "alice@example.com"}'),
  ('T000000000002', 'B00002', 'P2', 'Bob', '{"email": "bob@example.com"}'),
  ('T000000000003', 'B00003', 'P3', 'Charlie', '{"email": "charlie@example.com"}'),
  ('T000000000004', 'B00004', 'P4', 'Diana', '{"email": "diana@example.com"}'),
  ('T000000000005', 'B00005', 'P5', 'Ethan', '{"email": "ethan@example.com"}'),
  ('T000000000006', 'B00006', 'P6', 'Frank', '{"email": "frank@example.com"}');

-- 5. Insert sample flights
-- Passenger 1: Alice
INSERT INTO flights (flight_id, flight_no, scheduled_departure, scheduled_arrival, departure_airport, arrival_airport, status, aircraft_code, actual_departure, actual_arrival)
VALUES
  (1, 'FL001', '2025-01-01 08:00:00+00', '2025-01-01 10:00:00+00', 'JFK', 'LAX', 'on time', 'A01', '2025-01-01 08:00:00+00', '2025-01-01 10:00:00+00'),
  (2, 'FL002', '2025-01-02 08:00:00+00', '2025-01-02 11:00:00+00', 'JFK', 'ORD', 'on time', 'A01', '2025-01-02 08:00:00+00', '2025-01-02 11:00:00+00');
  
-- Passenger 2: Bob
INSERT INTO flights (flight_id, flight_no, scheduled_departure, scheduled_arrival, departure_airport, arrival_airport, status, aircraft_code, actual_departure, actual_arrival)
VALUES
  (3, 'FL003', '2025-01-03 08:00:00+00', '2025-01-03 10:00:00+00', 'LAX', 'JFK', 'on time', 'A01', '2025-01-03 08:00:00+00', '2025-01-03 10:00:00+00'),
  (4, 'FL004', '2025-01-04 08:00:00+00', '2025-01-04 10:30:00+00', 'LAX', 'ORD', 'on time', 'A01', '2025-01-04 08:00:00+00', '2025-01-04 10:30:00+00'),
  (5, 'FL005', '2025-01-05 08:00:00+00', '2025-01-05 09:45:00+00', 'ORD', 'LAX', 'on time', 'A01', '2025-01-05 08:00:00+00', '2025-01-05 09:45:00+00');
  
-- Passenger 3: Charlie
INSERT INTO flights (flight_id, flight_no, scheduled_departure, scheduled_arrival, departure_airport, arrival_airport, status, aircraft_code, actual_departure, actual_arrival)
VALUES
  (6, 'FL006', '2025-01-06 08:00:00+00', '2025-01-06 09:30:00+00', 'ATL', 'ORD', 'on time', 'A01', '2025-01-06 08:00:00+00', '2025-01-06 09:30:00+00');

-- Passenger 4: Diana
INSERT INTO flights (flight_id, flight_no, scheduled_departure, scheduled_arrival, departure_airport, arrival_airport, status, aircraft_code, actual_departure, actual_arrival)
VALUES
  (7, 'FL007', '2025-01-07 08:00:00+00', '2025-01-07 09:30:00+00', 'JFK', 'LAX', 'on time', 'A01', '2025-01-07 08:00:00+00', '2025-01-07 09:30:00+00'),
  (8, 'FL008', '2025-01-08 08:00:00+00', '2025-01-08 09:30:00+00', 'LAX', 'JFK', 'on time', 'A01', '2025-01-08 08:00:00+00', '2025-01-08 09:30:00+00');
  
-- Passenger 5: Ethan
INSERT INTO flights (flight_id, flight_no, scheduled_departure, scheduled_arrival, departure_airport, arrival_airport, status, aircraft_code, actual_departure, actual_arrival)
VALUES
  (9,  'FL009', '2025-01-09 08:00:00+00', '2025-01-09 09:00:00+00', 'ORD', 'ATL', 'on time', 'A01', '2025-01-09 08:00:00+00', '2025-01-09 09:00:00+00'),
  (10, 'FL010', '2025-01-10 08:00:00+00', '2025-01-10 09:00:00+00', 'ATL', 'ORD', 'on time', 'A01', '2025-01-10 08:00:00+00', '2025-01-10 09:00:00+00'),
  (11, 'FL011', '2025-01-11 08:00:00+00', '2025-01-11 09:00:00+00', 'ORD', 'ATL', 'on time', 'A01', '2025-01-11 08:00:00+00', '2025-01-11 09:00:00+00'),
  (12, 'FL012', '2025-01-12 08:00:00+00', '2025-01-12 09:00:00+00', 'ORD', 'LAX', 'on time', 'A01', '2025-01-12 08:00:00+00', '2025-01-12 09:00:00+00');

-- Passenger 6: Frank (extra flights for testing aggregation on same day)
INSERT INTO flights (flight_id, flight_no, scheduled_departure, scheduled_arrival, departure_airport, arrival_airport, status, aircraft_code, actual_departure, actual_arrival)
VALUES
  (13, 'FL013', '2025-01-01 12:00:00+00', '2025-01-01 14:00:00+00', 'JFK', 'LAX', 'on time', 'A01', '2025-01-01 12:00:00+00', '2025-01-01 14:00:00+00'),
  (14, 'FL014', '2025-01-02 12:00:00+00', '2025-01-02 14:00:00+00', 'LAX', 'JFK', 'on time', 'A01', '2025-01-02 12:00:00+00', '2025-01-02 14:00:00+00');

-- 6. Insert sample ticket_flights linking tickets to flights
-- Alice (P1)
INSERT INTO ticket_flights (ticket_no, flight_id, fare_conditions, amount) VALUES
  ('T000000000001', 1, 'Economy', 300.00),
  ('T000000000001', 2, 'Economy', 400.00);
  
-- Bob (P2)
INSERT INTO ticket_flights (ticket_no, flight_id, fare_conditions, amount) VALUES
  ('T000000000002', 3, 'Economy', 200.00),
  ('T000000000002', 4, 'Economy', 200.00),
  ('T000000000002', 5, 'Economy', 200.00);
  
-- Charlie (P3)
INSERT INTO ticket_flights (ticket_no, flight_id, fare_conditions, amount) VALUES
  ('T000000000003', 6, 'Economy', 500.00);
  
-- Diana (P4)
INSERT INTO ticket_flights (ticket_no, flight_id, fare_conditions, amount) VALUES
  ('T000000000004', 7, 'Economy', 150.00),
  ('T000000000004', 8, 'Economy', 150.00);
  
-- Ethan (P5)
INSERT INTO ticket_flights (ticket_no, flight_id, fare_conditions, amount) VALUES
  ('T000000000005', 9,  'Economy', 100.00),
  ('T000000000005', 10, 'Economy', 100.00),
  ('T000000000005', 11, 'Economy', 100.00),
  ('T000000000005', 12, 'Economy', 100.00);

-- Frank (P6)
INSERT INTO ticket_flights (ticket_no, flight_id, fare_conditions, amount) VALUES
  ('T000000000006', 13, 'Economy', 350.00),
  ('T000000000006', 14, 'Economy', 350.00);