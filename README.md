## 🚗 Smart & Effective Real-Time Management of Street Parking

A Django-based smart parking management system designed to simplify parking discovery, slot booking, digital payments, check-in/check-out, and parking-time monitoring.

The system combines **real-time parking management with machine-learning-based availability prediction**, helping users identify suitable parking slots while giving administrators visibility into occupancy, bookings, payments, and parking activity.

---

## 📌 Overview

Finding an available parking space can be time-consuming, especially in busy areas such as campuses, commercial zones, and city streets.

This project provides a centralized parking management platform where users can:

- View available parking slots
- Select and reserve a suitable slot
- Book parking for a specified time
- Make digital payments
- Receive an electronic parking ticket
- Use QR codes for check-in and check-out
- Monitor active parking sessions
- Receive booking, payment, and parking alerts
- Track booking and payment history

The platform also includes an **ML-based parking availability prediction module** that estimates occupancy and availability based on factors such as:

- Time of day
- Day of week
- Parking zone
- Vehicle type
- Priority level

---

## ✨ Key Features

### 🅿️ Parking Slot Management

The system maintains parking lots and individual parking slots with information such as:

- Slot number
- Location coordinates
- Occupancy status
- Supported vehicle types
- EV charging availability
- Slot type
- Booking status

Available slots can be retrieved dynamically and assigned to users during the booking process.

---

### 📅 Parking Reservation & Booking

Users can reserve parking slots by providing:

- Vehicle number
- Vehicle type
- Parking slot
- Start time
- End time

The application supports a structured booking lifecycle:

```text
Pending
   ↓
Reserved
   ↓
Payment
   ↓
Confirmed
   ↓
Checked-In
   ↓
Active
   ↓
Checked-Out
   ↓
Completed
```

Bookings can also be:

- Cancelled
- Expired
- Released when payment is not completed within the reservation window

---

### 🗺️ Parking Map & Live Slot Status

The application provides parking-related map views and APIs for displaying:

- Parking locations
- Parking zones
- Slot availability
- Occupied slots
- Live parking status
- Nearest parking locations

---

### 🤖 ML-Based Parking Availability Prediction

A major component of the project is the parking availability prediction system.

The advanced predictor uses **Random Forest models** for:

1. Availability classification
2. Occupancy-rate regression


---

### 🎫 QR-Based E-Tickets

After booking, the system can generate digital parking tickets containing QR codes.

QR functionality supports:

- Booking QR generation
- Check-in QR generation
- Check-out QR generation
- QR parsing and validation
- Electronic ticket status management

Ticket states include:

```text
Valid
Used
Invalid
Expired
```

QR data is generated programmatically using the `qrcode` library.

---

### 🚪 QR Check-In & Check-Out

Parking sessions can be managed through QR-based workflows.

#### Check-In

The system records:

- Reservation/booking
- Slot number
- Vehicle
- Check-in time

#### Check-Out

The system records:

- Actual checkout time
- Parking duration
- Final parking charge
- Additional over-parking charges

This allows the system to distinguish between the scheduled parking duration and the actual parking duration.

---

### ⚠️ Over-Parking Detection

The system includes monitoring for vehicles that stay beyond their scheduled end time.

The monitoring workflow can:

- Detect over-parking
- Calculate additional charges
- Mark a reservation as over-parked
- Create notifications
- Send alerts to the user
- Track monitoring status

Additional charges are calculated using the reservation's over-parking duration and a congestion-adjusted rate.

---


### 👤 Authentication & User Profiles

The application uses Django authentication and provides:

- User registration
- Login
- Logout
- Password change
- Profile management
- Phone number management
- Profile image upload

Each user has an associated profile containing account and wallet information.

---

### 📊 Analytics & Admin Features

The application contains administrative and analytical views for monitoring the parking system.

These views are designed to provide information about:

- Parking usage
- Reservations
- Occupancy
- Overbooking
- Parking activity
- System-level statistics

---

## 🧠 Machine Learning Workflow

The advanced prediction component follows this workflow:

```text
Parking Dataset
      ↓
Data Loading
      ↓
Synthetic Time-Series Generation
      ↓
Feature Engineering
      ↓
Categorical Encoding
      ↓
Random Forest Classifier
      +
Random Forest Regressor
      ↓
Model Serialization
      ↓
Availability Prediction
      ↓
24-Hour Forecast
      ↓
Parking Analytics
```

### Models Used

**RandomForestClassifier**

Used to predict whether parking availability is expected.

**RandomForestRegressor**

Used to estimate parking occupancy rate.

---

## 🏗️ System Architecture

```text
                    ┌───────────────────────┐
                    │       User            │
                    │ Web Interface         │
                    └───────────┬───────────┘
                                │
                                ▼
                    ┌───────────────────────┐
                    │      Django           │
                    │    Web Application    │
                    └───────────┬───────────┘
                                │
             ┌──────────────────┼──────────────────┐
             │                  │                  │
             ▼                  ▼                  ▼
      Parking & Booking      Payments         Notifications
             │                  │                  │
             │          ┌───────┴───────┐      ┌───┴────┐
             │          │ Razorpay       │      │ Email  │
             │          │ PayPal         │      │ SMS    │
             │          │ Wallet         │      │ FCM    │
             │          └───────────────┘      └────────┘
             │
             ▼
      ┌────────────────┐
      │ SQLite / DB    │
      └────────────────┘
             │
             ▼
      ┌────────────────┐
      │ ML Prediction  │
      │ Random Forest  │
      └────────────────┘
             │
             ▼
      Availability &
      Occupancy Forecast
             
             ┌────────────────┐
             │ Redis + Celery │
             └───────┬────────┘
                     ▼
              Background Jobs
```

---

## 🛠️ Technology Stack

### Backend

- Python
- Django 5.0.1
- Django REST Framework
- Django CORS Headers

### Database

- SQLite
- PostgreSQL support through `psycopg2-binary`

### Machine Learning

- Pandas
- Scikit-learn
- Joblib
- NumPy

### Background Processing

- Celery
- Redis
- Django Channels
- Channels Redis

### Other Technologies

- QR Code
- Pillow
- Requests
- Python Decouple

---

## 🗃️ Core Database Models

The application contains several models supporting the complete parking lifecycle.

### Profile

Stores user-related information such as:

- Phone number
- Wallet balance
- Profile image
- Two-factor authentication state

### ParkingLot

Stores parking lot information including:

- Name
- Latitude
- Longitude
- Total slots

### ParkingSlot

Stores individual parking slot information including:

- Slot number
- Geographic coordinates
- Occupancy
- Vehicle compatibility
- EV charging support
- Slot type
- Booking status

### Reservation

Stores parking reservation information.

### Booking

Represents the newer booking workflow with:

- Time range
- Slot
- Vehicle details
- Booking status
- QR codes
- Payment-related timestamps

### Transaction

Tracks digital payment transactions.

### Payment

Stores payment records associated with reservations.

### ETicket

Stores generated digital parking tickets.

### ParkingMonitor

Tracks parking sessions and over-parking conditions.

---

## ⚙️ Installation & Setup

### 1. Clone the repository

```bash
git clone https://github.com/Sanika-Gajarishi/Smart-Effective-Real-Time-Management-of-Street-Parking-.git
cd Smart-Effective-Real-Time-Management-of-Street-Parking-
```

---

### 2. Create a virtual environment

#### Windows

```bash
python -m venv venv
venv\Scripts\activate
```

#### macOS / Linux

```bash
python3 -m venv venv
source venv/bin/activate
```

---

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

---

### 4. Configure environment variables

Create a `.env` file using `.env.template` as a reference.

Example:

```env
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1,0.0.0.0

DATABASE_NAME=db.sqlite3
DATABASE_ENGINE=django.db.backends.sqlite3

EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_HOST_USER=your_email@gmail.com
EMAIL_HOST_PASSWORD=your_app_password
DEFAULT_FROM_EMAIL=your_email@gmail.com

```

Never commit real API keys, passwords, or payment credentials.

---

### 5. Apply migrations

```bash
python manage.py makemigrations
python manage.py migrate
```

---

### 6. Create an admin user

```bash
python manage.py createsuperuser
```

Follow the prompts to create the Django administrator account.

---

### 7. Start the Django server

```bash
python manage.py runserver
```

The application will normally be available at:

```text
http://127.0.0.1:8000/
```

---

## 🔄 Running Background Services

The application includes Celery and Redis configuration for scheduled/background processing.

### Start Redis

Make sure Redis is running locally:

```text
redis://localhost:6379/0
```

### Start Celery Worker

```bash
celery -A ParkingSystem worker -l info
```

### Start Celery Beat

```bash
celery -A ParkingSystem beat -l info
```

Celery Beat is configured for periodic monitoring tasks such as booking reminders and over-parking checks.

---

## 🤖 Training the Advanced Parking Models

The advanced predictor expects a parking dataset under:

```text
data/adypu_parking_users.csv
```

The training workflow generates synthetic time-series observations from the parking data and trains Random Forest models.

The training process includes:

```text
Dataset
→ Synthetic Time-Series Generation
→ Feature Engineering
→ Encoding
→ Random Forest Classification
→ Random Forest Regression
→ Model Serialization
```

---

## 📈 What This Project Demonstrates

This project demonstrates practical experience with:

**Backend Development**

- Django architecture
- Models and relationships
- Authentication
- Views and URL routing
- Form handling
- Database-backed workflows

**Machine Learning**

- Feature engineering
- Classification
- Regression
- Random Forest
- Availability prediction
- Occupancy forecasting
- Model persistence with Joblib

**System Design**

- Booking lifecycle management
- Payment lifecycle management
- Background processing
- Notification workflows
- Parking monitoring
- Analytics

---

## 📚 Learning Outcomes

Building this project provides hands-on experience in combining a traditional web backend with machine learning and external services.

Key concepts covered include:

```text
Django
   +
Database Design
   +
Parking & Booking Management
   +
Machine Learning
   +
Payment Integration
   +
QR Code Workflows
   +
Notifications
   +
Celery / Redis
   =
Smart Parking Management Platform
```

---

## 👩‍💻 Author

**Sanika Gajarishi**

B.Tech — Artificial Intelligence & Data Science

GitHub: [Sanika-Gajarishi](https://github.com/Sanika-Gajarishi)

---

## ⭐ Support

If you find this project useful, consider giving the repository a ⭐ on GitHub.

---

## 📄 License

This project is intended for educational and portfolio purposes. Add an explicit open-source license such as MIT before presenting it as a reusable open-source project.
