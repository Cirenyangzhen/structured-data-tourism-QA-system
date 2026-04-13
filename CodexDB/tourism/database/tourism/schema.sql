PRAGMA foreign_keys = ON;
CREATE TABLE attractions (
  attraction_id INTEGER PRIMARY KEY,
  name TEXT,
  rating DECIMAL(3,2),
  address TEXT,
  opening_hours TEXT,
  description TEXT
);
CREATE TABLE hotels (
  hotel_id INTEGER PRIMARY KEY AUTOINCREMENT,
  name TEXT NOT NULL,
  rating REAL DEFAULT NULL,
  address TEXT DEFAULT NULL,
  contact TEXT DEFAULT NULL
);
CREATE TABLE reviews (
  review_id INTEGER PRIMARY KEY,
  attraction_id INTEGER,
  review_text TEXT,
  rating VARCHAR(10),
  date DATE,
  FOREIGN KEY (attraction_id) REFERENCES attractions(attraction_id)
);
CREATE TABLE nearby_food (
  food_id INTEGER PRIMARY KEY,
  attraction_id INTEGER,
  name TEXT,
  score DECIMAL(3,2),
  distance DECIMAL(5,2),
  FOREIGN KEY (attraction_id) REFERENCES attractions(attraction_id)
);