#include<PMS.h>
#include<DHT.h>
#include<MQ135.h>
#include<MQUnifiedsensor.h>
#define DHTTYPE DHT11
#define DHTPIN 4
#define RXD2 16
#define TXD2 17
#define MQ135_PIN 36
#define RZERO_135 0.00 //IN CLEAN AIR
#define MQ7_PIN 39     
#define BOARD "ESP-32" 
#define VOLT_RES 3.3  
#define ADC_BIT_RES 12 
#define RL 10.0       
#define RZERO_7 10.00 //IN CLEAN AIR
#define GAS "CO"
//DHT, MQ135, PMS//
DHT dht(DHTPIN, DHTTYPE);
MQ135 co2sensor(MQ135_PIN, RZERO_135);
MQUnifiedsensor coSensor(BOARD, VOLT_RES, ADC_BIT_RES, MQ7_PIN, GAS);
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
  // MQ-7 Calibration routine 
  Serial.print("Calibrating MQ7 please wait.");
  float calcR0 = 0;
  for(int i = 1; i<=10; i ++) {
    coSensor.update();
    calcR0 += coSensor.calibrate(27.5); 
    Serial.print(".");
  }
  coSensor.setR0(calcR0/10);
  Serial.println(" done!.");
  coSensor.serialDebug(true);
  Serial.println("---------------------------------");
  Serial.println("Time(ms),Temp(°C),Humidity(%),PM2.5,PM10,CO2/VOC(ppm)");
}
void loop() {
  //PMS//
  if(pms.read(data)){
  //DHT11//
  float t=dht.readTemperature();
  float rh=dht.readHumidity();
  //MQ135//
  float ppm1=co2sensor.getPPM();
  //MQ7//
  coSensor.update(); 
  float ppm2=coSensor.readSensor(false, 0.0);
  //csv output//
  Serial.print(millis()/1000.0); Serial.print(",");
  Serial.print(t); Serial.print(",");
  Serial.print(rh); Serial.print(",");
  Serial.print(data.PM_AE_UG_2_5); Serial.print(",");
  Serial.print(data.PM_AE_UG_10_0); Serial.print(",");
  if(isnan(ppm2))
  {
    ppm2=0.00;
  }
  Serial.print(ppm1,2); Serial.print(",");
  Serial.println(ppm2,2);
  delay(5000);
  }
}