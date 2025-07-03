# Automated-Building-Management-System
Here’s a summarized and polished version of your report turned into a professional and informative GitHub `README.md` file:

---

# Smart HVAC & Security Control System

A Python-based embedded system project that integrates HVAC control, security mechanisms, ambient lighting, fire alarms, and weather-based automation. It utilizes hardware interfaces such as PIR sensors, buttons, DHT11 sensors, and an LCD display to create an intelligent home/office environment monitor and controller.

---

## Features

* **Door Security System**: Detects door open/close state and halts HVAC operations for safety.
* **Feels-Like Temperature Calculation**: Combines real-time DHT11 sensor data and CIMIS web data for accurate temperature and humidity assessments.
* **Fire Alarm System**: Activates red LED flashing alarm when temperature exceeds safety threshold.
* **HVAC Automation**: Automatically enables AC or heater based on feels-like temperature differential.
* **Ambient Light Control**: Turns on LED lighting when motion is detected using a PIR sensor.
* **LCD Display**: Displays real-time system status, including temperature, door state, and HVAC activity.
* **Weather Data API Integration**: Pulls live humidity data from the CIMIS (California Irrigation Management Information System) API.

---

## Software Architecture

### `setup()`

Initializes all hardware components:

* Buttons: Configured as input with pull-up resistors.
* LEDs: Set as output, initially off.
* PIR Sensor: Configured as input.

---

### `pirLight()`

Controls the ambient lighting:

* When motion is detected by the PIR sensor, a green LED is activated.
* A 10-second timer checks for continued motion; the LED turns off if no motion is detected.

---

### `doorSecurity()`

* Triggered by pressing the green button.
* Displays “HVAC Halted” when the door opens.
* Locks system operations for 3 seconds, then resumes after confirming door closure.

---

### `calcTemp()`

Calculates the “feels-like” temperature:

1. Averages the 3 most recent DHT11 temperature readings.

2. Converts to Fahrenheit.

3. Fetches the last hour's humidity from CIMIS.

4. Uses the formula:

   ```
   feels_like = avg_temp + (avg_humidity * 0.05)
   ```

5. If temperature exceeds 95°F, triggers the fire alarm.

---

### `fireAlarm()`

* Locks the system and flashes the red LED once per second.
* Displays “Fire Alarm” on screen.
* Automatically deactivates once the temperature falls below 95°F.

---

### `acControl()` / `heaterControl()`

* Triggered by corresponding button presses.
* Checks that the door is closed.
* AC activates if `feels_like` is 3°F above target temp.
* Heater activates if `feels_like` is 3°F below target temp.
* Displays current HVAC state on LCD and via LEDs.

---

### `lcdOutput()`

* Continuously displays:

  * Ambient light status
  * Door status
  * Current/target temperature
  * HVAC system state

---

## Weather Data Retrieval

### `WeatherData` class

Stores:

* Hour of the day
* Timestamp
* Humidity

---

### `fetchWeatherDataForHour()`

* Determines if the data should be retrieved for today or yesterday.
* Constructs the datetime object accordingly.
* Passes time to the API request function to fetch humidity data.

---

### `retrieveDataFromURL()`

* Opens the URL
* Parses and decodes the JSON response.

---

### `requestWeatherData()`

* Uses CIMIS API with authentication key.
* Constructs a query URL.
* Extracts humidity data needed for temperature calculation.

---

## Hardware Used

* Raspberry Pi / Microcontroller
* DHT11 Temperature & Humidity Sensor
* PIR Motion Sensor
* Push Buttons
* Red and Green LEDs
* LCD Display
* Internet access for API communication

---

