#define BLYNK_TEMPLATE_ID "TMPL3rQGiyUze"
#define BLYNK_TEMPLATE_NAME "ESP32 AQI Node"
#include<WiFi.h>
#include<WiFiUdp.h>
#include<BlynkSimpleEsp32.h>
#include<PMS.h>
#include<DHT.h>
#include<MQUnifiedsensor.h>
#define DHTTYPE DHT11
#define DHTPIN 4
#define RXD2 16
#define TXD2 17
#define MQ135_PIN 36
#define MQ7_PIN 39     
#define BOARD "ESP-32" 
#define VOLT_RES 3.3  
#define ADC_BIT_RES 12 
#define RL 1.0
#define RZERO_135 60.00
#define RZERO_7 18.00
DHT dht(DHTPIN, DHTTYPE);
PMS pms(Serial2);
MQUnifiedsensor coSensor(BOARD, VOLT_RES, ADC_BIT_RES, MQ7_PIN);
MQUnifiedsensor co2Sensor(BOARD, VOLT_RES, ADC_BIT_RES, MQ135_PIN);
int pm25=0;
int pm10=0;
PMS::DATA data;
char auth[] = "H5OXKNaNL93W1dLbRS6qvOvidInfoSJv";
char ssid[] = "Connected, no internet";
char pass[] = "Aditya@12345";
const char* pc_ip="10.96.51.48";
const int pc_port=9000;
WiFiUDP udp;
BlynkTimer timer;
void sendSensorData()
{
  //DHT11
  float t=dht.readTemperature();
  float rh=dht.readHumidity();
  if (isnan(t) || isnan(rh)) {
    Serial.println("DHT11: Failed to read!");
    return;
  }
  //MQ SENSORS//
  coSensor.update(); 
  float ppm1=co2Sensor.readSensor();
  co2Sensor.update();
  float ppm2=coSensor.readSensor();
  if(isnan(ppm2))
  {
    ppm2=0.00;
  }
  //SEND TO BLYNK//
  Blynk.virtualWrite(V1, rh);
  Blynk.virtualWrite(V2, pm25);
  Blynk.virtualWrite(V3, pm10);
  Blynk.virtualWrite(V4, ppm2);
  Blynk.virtualWrite(V5, ppm1);
  //UDP packet//
  char buffer[128];
  snprintf(buffer, sizeof(buffer), "%.2f,%.2f,%.2f,%d,%d,%.2f,%.2f\n",millis()/1000.0, t, rh, pm25, pm10, ppm1, ppm2);
  udp.beginPacket(pc_ip, pc_port);
  udp.print(buffer);
  udp.endPacket();
  Serial.println("Packet Sent");
}
void setup() {
  Serial.begin(115200);
  Serial.println("Power ON");
  dht.begin();
  Serial.println("DHT init");
  Serial2.begin(9600,SERIAL_8N1, RXD2, TXD2);
  Serial.println("PMS init");
  coSensor.init(); 
  coSensor.setR0(RZERO_7);
  coSensor.setRL(RL);
  coSensor.setA(99.042); 
  coSensor.setB(-1.518);
  coSensor.setRegressionMethod(1);  
  // MQ-7 Calibration routine, optional after first run
  Serial.print("Calibrating MQ7");
  float calcR0 = 0;
  for(int i = 1; i<=10; i ++) {
    coSensor.update();
    calcR0 += coSensor.calibrate(18.00);
    delay(500);
  }
  coSensor.setR0(calcR0/10);
  Serial.print("R0_MQ7 = "); Serial.println(calcR0 / 10);
  coSensor.serialDebug(true);
  // --- MQ135 Initialization ---
  co2Sensor.init();
  co2Sensor.setR0(RZERO_135);
  co2Sensor.setRL(RL);
  co2Sensor.setRegressionMethod(1);
  co2Sensor.setA(110.47); // Empirical constants for CO2 from MQ135 datasheet
  co2Sensor.setB(-2.862);
  Serial.print("Calibrating MQ135... ");
  float calcR0_CO2 = 0;
  for (int i = 0; i < 10; i++) {
    co2Sensor.update();
    calcR0_CO2 += co2Sensor.calibrate(0.6);
    delay(500);
  }
  co2Sensor.setR0(calcR0_CO2 / 10);
  Serial.print("R0_MQ135 = "); Serial.println(calcR0_CO2 / 10);
  Serial.println("---------------------------------");
  Blynk.begin(auth,ssid,pass);
  Serial.print("Connected Successfully");
  timer.setInterval(15000L,sendSensorData);
}
void loop() {
  Blynk.run();
  timer.run();
  if (pms.read(data)) {
    pm25=data.PM_AE_UG_2_5;
    pm10=data.PM_AE_UG_10_0;
  }
}
