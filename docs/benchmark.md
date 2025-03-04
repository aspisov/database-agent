
## Simple queries

1. Show me all bookings where the total amount exceeds 500.00.
```sql
SELECT *
FROM bookings
WHERE total_amount > 500.00;
```

2. Retrieve the names of passengers along with their flight numbers for all flights departing from the airport with code 'JFK'.
```sql
SELECT t.passenger_name, f.flight_no
FROM tickets AS t
JOIN ticket_flights AS tf ON t.ticket_no = tf.ticket_no
JOIN flights AS f ON tf.flight_id = f.flight_id
WHERE f.departure_airport = 'JFK';
```

3. List all flights scheduled to depart in the next 7 days.
```sql
SELECT *
FROM flights
WHERE scheduled_departure BETWEEN NOW() AND NOW() + INTERVAL '7 days';
```

4. How many tickets are associated with each booking reference?
```sql
SELECT book_ref, COUNT(*) AS ticket_count
FROM tickets
GROUP BY book_ref;
```

5. Show the average fare for all ticket flights that have the fare condition set to 'Economy'.
```sql
SELECT AVG(amount) AS avg_fare
FROM ticket_flights
WHERE fare_conditions = 'Economy';
```

6. Retrieve all airport details for airports in the city of Los Angeles.
```sql
SELECT *
FROM airports
WHERE city = 'Los Angeles';
```

7. List flight numbers, scheduled departure/arrival times, and the aircraft model for flights with a status of 'Delayed'.
```sql
SELECT f.flight_no, f.scheduled_departure, f.scheduled_arrival, a.model
FROM flights AS f
JOIN aircrafts AS a ON f.aircraft_code = a.aircraft_code
WHERE f.status = 'Delayed';
```

8. Get all seat numbers and their fare conditions for the aircraft with code 'A32'.
```sql
SELECT seat_no, fare_conditions
FROM seats
WHERE aircraft_code = 'A32';
```

9. Show all boarding passes with their ticket numbers, flight IDs, boarding numbers, and seat numbers, ordered by the boarding number.
```sql
SELECT ticket_no, flight_id, boarding_no, seat_no
FROM boarding_passes
ORDER BY boarding_no;
```

10. What is the total booking amount for bookings made on January 15, 2025?
```sql
SELECT SUM(total_amount) AS total_bookings_amount
FROM bookings
WHERE DATE(book_date) = '2025-01-15';
```

## Hard queries

1. List the top 3 airports with the highest number of departing flights in the last month along with their names and the count of flights.
```sql
SELECT f.departure_airport, a.airport_name, COUNT(*) AS departing_flights
FROM flights AS f
JOIN airports AS a ON f.departure_airport = a.airport_code
WHERE f.scheduled_departure >= NOW() - INTERVAL '1 month'
GROUP BY f.departure_airport, a.airport_name
ORDER BY departing_flights DESC
LIMIT 3;
```

2. Retrieve the names of passengers who have booked more than one flight, along with the total number of flights and the total fare they have paid.
```sql
SELECT t.passenger_name, COUNT(tf.flight_id) AS flight_count, SUM(tf.amount) AS total_fare
FROM tickets AS t
JOIN ticket_flights AS tf ON t.ticket_no = tf.ticket_no
GROUP BY t.passenger_name
HAVING COUNT(tf.flight_id) > 1;
```

3. For each flight, show the flight number, scheduled departure/arrival times, the total number of seats available on the assigned aircraft, and the number of boarding passes issued.
```sql
SELECT f.flight_no,
       f.scheduled_departure,
       f.scheduled_arrival,
       (SELECT COUNT(*) FROM seats s WHERE s.aircraft_code = f.aircraft_code) AS total_seats,
       (SELECT COUNT(*) FROM boarding_passes bp WHERE bp.flight_id = f.flight_id) AS issued_boarding_passes
FROM flights AS f;
```

4. For each booking, calculate the sum of the fare amounts from all its associated ticket flights, then show the booking’s total amount and the difference between the booking total and the summed fare amounts.
```sql
SELECT b.book_ref,
       b.total_amount,
       COALESCE(SUM(tf.amount), 0) AS total_fare_amount,
       b.total_amount - COALESCE(SUM(tf.amount), 0) AS difference
FROM bookings AS b
LEFT JOIN tickets AS t ON b.book_ref = t.book_ref
LEFT JOIN ticket_flights AS tf ON t.ticket_no = tf.ticket_no
GROUP BY b.book_ref, b.total_amount;
```

5. List flight numbers, departure and arrival cities, and the delay in minutes (actual departure minus scheduled departure) for flights that departed more than 30 minutes late.
```sql
SELECT f.flight_no,
       a_dep.city AS departure_city,
       a_arr.city AS arrival_city,
       EXTRACT(EPOCH FROM (f.actual_departure - f.scheduled_departure)) / 60 AS delay_minutes
FROM flights AS f
JOIN airports AS a_dep ON f.departure_airport = a_dep.airport_code
JOIN airports AS a_arr ON f.arrival_airport = a_arr.airport_code
WHERE f.actual_departure IS NOT NULL
  AND EXTRACT(EPOCH FROM (f.actual_departure - f.scheduled_departure)) / 60 > 30;
```

6. For each aircraft model, list the aircraft code, model name (extracted from the JSON field), the total number of flights it has operated, and the average flight duration (in minutes) computed from scheduled departure and arrival times.
```sql
SELECT a.aircraft_code,
       a.model ->> 'name' AS model_name,
       COUNT(f.flight_id) AS flight_count,
       AVG(EXTRACT(EPOCH FROM (f.scheduled_arrival - f.scheduled_departure))) / 60 AS avg_duration_minutes
FROM aircrafts AS a
LEFT JOIN flights AS f ON a.aircraft_code = f.aircraft_code
GROUP BY a.aircraft_code, a.model;
```

7. Identify the top 5 passengers who have traveled the farthest total distance. Compute each flight’s distance using the departure and arrival airports’ coordinates (using an approximate Haversine formula), then sum the distances per passenger.
```sql
SELECT t.passenger_id,
       t.passenger_name,
       SUM(2 * 6371 * ASIN(SQRT(
             POWER(SIN(RADIANS((a_dep.coordinates_lat - a_arr.coordinates_lat) / 2)), 2) +
             COS(RADIANS(a_dep.coordinates_lat)) * COS(RADIANS(a_arr.coordinates_lat)) *
             POWER(SIN(RADIANS((a_dep.coordinates_lon - a_arr.coordinates_lon) / 2)), 2)
           ))) AS total_distance_km
FROM tickets AS t
JOIN ticket_flights AS tf ON t.ticket_no = tf.ticket_no
JOIN flights AS f ON tf.flight_id = f.flight_id
JOIN airports AS a_dep ON f.departure_airport = a_dep.airport_code
JOIN airports AS a_arr ON f.arrival_airport = a_arr.airport_code
GROUP BY t.passenger_id, t.passenger_name
ORDER BY total_distance_km DESC
LIMIT 5;
```

8. Find bookings where every associated flight has departed (i.e. actual departure exists and is later than scheduled) and the booking’s total amount exactly matches the sum of the fare amounts from its ticket flights.
```sql
SELECT b.book_ref, b.book_date, b.total_amount, SUM(tf.amount) AS total_fare
FROM bookings AS b
JOIN tickets AS t ON b.book_ref = t.book_ref
JOIN ticket_flights AS tf ON t.ticket_no = tf.ticket_no
WHERE NOT EXISTS (
    SELECT 1
    FROM ticket_flights AS tf2
    JOIN flights AS f ON tf2.flight_id = f.flight_id
    JOIN tickets AS t2 ON tf2.ticket_no = t2.ticket_no
    WHERE t2.book_ref = b.book_ref
      AND (f.actual_departure IS NULL OR f.actual_departure <= f.scheduled_departure)
)
GROUP BY b.book_ref, b.book_date, b.total_amount
HAVING b.total_amount = SUM(tf.amount);
```

9. Determine which fare condition is used most frequently across all ticket flights, and report both the total count and the average fare amount for that condition.
```sql
SELECT fare_conditions, COUNT(*) AS usage_count, AVG(amount) AS avg_fare
FROM ticket_flights
GROUP BY fare_conditions
ORDER BY usage_count DESC
LIMIT 1;
```

10. Produce a summary for each city with an airport that shows the number of flights departing from that city, the number of flights arriving into that city, and the difference between these counts.
```sql
SELECT a.city,
       COALESCE(dep.departure_count, 0) AS departing_flights,
       COALESCE(arr.arrival_count, 0) AS arriving_flights,
       COALESCE(dep.departure_count, 0) - COALESCE(arr.arrival_count, 0) AS difference
FROM airports AS a
LEFT JOIN (
    SELECT departure_airport, COUNT(*) AS departure_count
    FROM flights
    GROUP BY departure_airport
) AS dep ON a.airport_code = dep.departure_airport
LEFT JOIN (
    SELECT arrival_airport, COUNT(*) AS arrival_count
    FROM flights
    GROUP BY arrival_airport
) AS arr ON a.airport_code = arr.arrival_airport;
```
