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
- **Environmental Data**: Real-time ambient temperature and relative humidity monitoring
- **Robust Calibration & Baseline Correction**: Clean-air baseline resistance ($R_0$) estimation and logarithmic curve approximation for gas concentration derivation
- **ML Based Prediction**: Linear Regression and a lightweight, windowed Neural Network (TinyNN) predict the AQI for the next 2 minute window

---

## 🛠️ Hardware Stack & Wiring

### Components
| Component | Function | Interface | Operating Voltage |
| :--- | :--- | :--- | :--- |
| **ESP32 DevKit** | Microcontroller | 3.3V / 5V |
| **PMS7003** | Particulate Matter ($PM_{2.5}, PM_{10}$) | UART (Serial2) | 5V (VCC), 3.3V (Logic) |
| **MQ-135** | Air Quality / Hazardous Gases ($NO_2$) | Analog (ADC) | 5V |
| **MQ-7** | Carbon Monoxide ($CO$) | Analog (ADC) | 5V |
| **DHT11** | Temperature, Relative Humidity & Pressure | GPIO / $I^2C$ | 3.3V |

<img width="600" height="380" alt="Hardware" src="https://github.com/user-attachments/assets/159d8905-beba-4c06-988b-6ede42538b20" />
<img width="600" height="380" alt="Schematic" src="https://github.com/user-attachments/assets/0d90e8f2-080c-4956-b06b-f4c9eb6763d6" />

---

## Dependencies

- **[MQSensorsLib](https://github.com/miguel5612/MQSensorsLib)** : Gas sensor calibration and concentration
- **[PMSLibrary](https://github.com/fu-hsi/PMS)** : PMS7003 interfacing
- **[DHT-sensor-library](https://github.com/adafruit/DHT-sensor-library)** : Temperature and Humidity values from DHT11

---

## Machine Learning
To enable real-time Air Quality Index (AQI) forecasting on the resource-constrained ESP32 (~320 KB SRAM) without relying on memory-heavy cloud APIs, two edge-deployable regression models were evaluated: a **Linear Regression** baseline and a compact **Windowed Multi-Layer Perceptron (TinyNN)**. Sensor telemetry is aggregated chronologically, removing duplicate timestamps and packet anomalies.
### 1. Linear Regression

Models AQI via a direct linear combination of standardized particulate levels:
$$AQI = w_1 \cdot PM_{2.5}' + w_2 \cdot PM_{10}' + b$$
- **Deployment**: Executed as a closed-form algebraic formula in firmware with $\mathcal{O}(1)$ time complexity, requiring zero external ML runtime.

**MODEL PERFORMANCE**

<img width="420" height="280" alt="image" src="https://github.com/user-attachments/assets/1f89cd38-03f7-4dcf-ad60-38eca0537be7" />

### 2. TinyNN (Windowed Multi-Layer Perceptron)
To capture short-term temporal dynamics and sharp AQI spikes without the computational weight of recurrent models (e.g., LSTM), a feedforward TinyNN is trained with the Adam optimizer over Mean Squared Error (MSE) loss for 40 epochs.

<img width="483" height="185" alt="image" src="https://github.com/user-attachments/assets/f1e8eff6-bd6b-40d6-a6bc-fbd7d1854c91" />

- **Input Layer**: Flatten Layer ($32\text{ inputs}$ from $8\text{ time steps} \times 4\text{ features}$).
- **Hidden Layer 1**: Dense ($16\text{ Neurons}$, $\text{ReLU}$).
- **Hidden Layer 2**: Dense ($8\text{ Neurons}$, $\text{ReLU}$).
- **Output Layer**: Dense ($1\text{ Neuron}$, $\text{Linear Activation}$).

**MODEL PERFORMANCE**

<img width="420" height="280" alt="image" src="https://github.com/user-attachments/assets/f79eddfd-60af-4881-a0cc-31dc3abdf894" />


### Experimental Results & Benchmarks

Models were evaluated on a chronological 20% test holdout using Mean Absolute Error (MAE) and Root Mean Squared Error (RMSE):

| Model | MAE | RMSE | Parameters | Hardware Deployment Complexity |
| :--- | :--- | :--- | :--- | :--- |
| **Linear Regression** | 19.70 | 26.51 | 3 | **Very Low** (Direct C++ expression) |
| **Windowed TinyNN (MLP)** | **13.06** | **19.33** | ~600 | **Moderate** (Tensor Arena / Quantization) |

> **Key Finding**: The windowed TinyNN reduces average prediction error by **~34%** compared to the linear baseline, significantly improving trend-following and peak tracking during high-AQI spikes (350–450 AQI range) by leveraging the 2-minute temporal history.

---

## Real-Time UDP Telemetry & Custom Dashboard

To bypass memory-heavy cloud APIs and minimize runtime computational overhead on the ESP32, the system utilizes a connectionless **UDP broadcast pipeline** paired with a lightweight local monitoring dashboard.

* **Packet Structure**: Telemetry metrics are packed into a compact comma-separated string buffer containing:
  *Temperature*, *Humidity*, *PM2.5*, *PM10*, *NO2*, *CO*, *Predicted_AQI*

<img width="400" height="400" alt="image" src="https://github.com/user-attachments/assets/1561714d-9732-451f-b932-7b88df488ff3" />
<img width="400" height="400" alt="image" src="https://github.com/user-attachments/assets/949fdb31-bf87-4464-896c-077e910ecfca" />









