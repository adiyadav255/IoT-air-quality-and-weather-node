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
//DHT, MQ135, PMS//
DHT dht(DHTPIN, DHTTYPE);
MQUnifiedsensor coSensor(BOARD, VOLT_RES, ADC_BIT_RES, MQ7_PIN);
MQUnifiedsensor co2Sensor(BOARD, VOLT_RES, ADC_BIT_RES, MQ135_PIN);
PMS pms(Serial2);
PMS::DATA data;
void setup() {
  Serial.begin(115200);
  Serial.println("Power ON");
  dht.begin();
  Serial.println("DHT init");
  Serial2.begin(9600,SERIAL_8N1, RXD2, TXD2);
  Serial.println("PMS init");
  // --- MQ-7 Initialization ---
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
    calcR0 += coSensor.calibrate(22.00);
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
  Serial.println("Time(ms),Temp(°C),Humidity(%),PM2.5,PM10,CO2/VOC(ppm),CO(ppm)");
}
void loop() {
  //PMS//
  if(pms.read(data)){
  //DHT11//
  float t=dht.readTemperature();
  float rh=dht.readHumidity();
  //MQ7//
  coSensor.update(); 
  float ppm1=co2Sensor.readSensor();
  //MQ135//
  co2Sensor.update();
  float ppm2=coSensor.readSensor();
  //csv output//
  Serial.print(millis()/1000.0); Serial.print(",");
  Serial.print(t); Serial.print(",");
  Serial.print(rh); Serial.print(",");
  Serial.print(data.PM_AE_UG_2_5); Serial.print(",");
  Serial.print(data.PM_AE_UG_10_0); Serial.print(",");
  if(isnan(ppm1))
  {
    ppm1=0.00;
  }
  if(isnan(ppm2))
  {
    ppm2=0.00;
  }
  Serial.print(ppm1,2); Serial.print(",");
  Serial.println(ppm2,2);
  delay(5000);
  }
}