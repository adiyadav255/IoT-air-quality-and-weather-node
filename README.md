#  AI Enhanced IoT Node for Air Quality Monitoring

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Platform: ESP32](https://img.shields.io/badge/Hardware-ESP32-red.svg)](https://www.espressif.com/en/products/socs/esp32)
[![Framework: Arduino / C++](https://img.shields.io/badge/Framework-Arduino%20C%2B%2B-00979D.svg)](https://www.arduino.cc/)
[![Python: 3.8+](https://img.shields.io/badge/Python-3.8%2B-blue.svg)](https://www.python.org/)

An edge IoT sensing node designed for real-time ambient air quality measurement and microclimate monitoring. The system samples particulate matter ( PM2.5, PM10), gaseous pollutants (CO, NO2), and environmental metrics (temperature and relative humidity), publishing sensor data, real-time AQI and future AQI prediction (on-chip inference) over Wi-Fi UDP, displayed on a custom dashboard

---

## 📌 Features

- **Multi-Pollutant Sampling**:
  - Laser scattering particulate detection for **PM2.5**, and **PM10**
  - Electrochemical/semiconductor gas sensing for **CO** and **NO2**
- **Other Parameters**: Real-time ambient temperature and relative humidity monitoring
- **Robust Calibration & Baseline Correction**: Clean-air baseline resistance ($R_0$) estimation and logarithmic curve approximation for gas concentration derivation
- **ML Based Prediction**: Linear Regression and a lightweight, windowed Neural Network (TinyNN) predict the AQI for the next 2 minute window

---

## 🛠️ Hardware Stack & Wiring

### Components
| Component | Function | Interface | Operating Voltage |
| :--- | :--- | :--- | :--- |
| **ESP32 DevKit** | Microcontroller | 3.3V / 5V |
| **PMS7003 / PMS5003** | Particulate Matter ($PM_{2.5}, PM_{10}$) | UART (Serial2) | 5V (VCC), 3.3V (Logic) |
| **MQ-135** | Air Quality / Hazardous Gases ($NO_2$) | Analog (ADC) | 5V |
| **MQ-7** | Carbon Monoxide ($CO$) | Analog (ADC) | 5V |
| **DHT22** | Temperature, Relative Humidity & Pressure | GPIO / $I^2C$ | 3.3V |
