CREATE DATABASE IF NOT EXISTS car_rental_db;
USE car_rental_db;


CREATE TABLE Tbl_client (
    client_id INT AUTO_INCREMENT PRIMARY KEY,
    client_name VARCHAR(100),
    client_address TEXT,
    client_email VARCHAR(100),
    client_mobnum VARCHAR(20)
);


CREATE TABLE Tbl_booking (
    booking_id INT AUTO_INCREMENT PRIMARY KEY,
    client_id INT,
    pickup_data DATETIME,
    return_data DATETIME,
    destination TEXT,
    FOREIGN KEY (client_id) REFERENCES Tbl_client(client_id)
);


CREATE TABLE Tbl_brand (
    brand_id INT AUTO_INCREMENT PRIMARY KEY,
    booking INT,
    brand VARCHAR(100),
    FOREIGN KEY (booking) REFERENCES Tbl_booking(booking_id)
);


CREATE TABLE Tbl_carinfo (
    car_id INT AUTO_INCREMENT PRIMARY KEY,
    brand_id INT,
    car_modelyear VARCHAR(10),
    car_platenumber VARCHAR(20),
    FOREIGN KEY (brand_id) REFERENCES Tbl_brand(brand_id)
);


CREATE TABLE Tbl_payment (
    payment_id INT AUTO_INCREMENT PRIMARY KEY,
    gcash VARCHAR(50),
    paypal VARCHAR(50)
);


CREATE TABLE Tbl_transaction (
    transaction_id INT AUTO_INCREMENT PRIMARY KEY,
    payment_id INT,
    car_id INT,
    booking_id INT,
    transaction_status VARCHAR(50),
    transaction_timestop DATETIME,
    FOREIGN KEY (payment_id) REFERENCES Tbl_payment(payment_id),
    FOREIGN KEY (car_id) REFERENCES Tbl_carinfo(car_id),
    FOREIGN KEY (booking_id) REFERENCES Tbl_booking(booking_id)
);


CREATE TABLE Tbl_location_turnover (
    location_id INT AUTO_INCREMENT PRIMARY KEY,
    transaction INT,
    location VARCHAR(100),
    timestop DATETIME,
    FOREIGN KEY (transaction) REFERENCES Tbl_transaction(transaction_id)
);


CREATE TABLE Tbl_admin (
    admin_id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50),
    password VARCHAR(255)
);


CREATE TABLE Tbl_testimonial (
    testimonial_id INT AUTO_INCREMENT PRIMARY KEY,
    car_id INT,
    car_comment TEXT,
    time_stop DATETIME,
    FOREIGN KEY (car_id) REFERENCES Tbl_carinfo(car_id)
);
