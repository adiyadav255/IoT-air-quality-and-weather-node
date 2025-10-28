#include<PMS.h>
#include<DHT.h>
#include<MQ135.h>
#define DHTTYPE DHT11
#define DHTPIN 4
#define RXD2 16
#define TXD2 17
#define MQ135_PIN 36
#define RZERO 5804
DHT dht(DHTPIN, DHTTYPE);
MQ135 co2sensor(MQ135_PIN, RZERO);
PMS pms(Serial2);
PMS::DATA data;
void setup() {
  Serial.begin(115200);
  Serial.println("Power ON");
  dht.begin();
  Serial.println("DHT init")
  Serial2.begin(9600,SERIAL_8N1, RXD2, TXD2);
  Serial.print("PMS init");
}
void loop() {
  //PMS//
  if(pms.read(data)){
    Serial.println("---------SENSOR READINGS----------");
    Serial.print("PM 1.0:"); Serial.println(data.PM_AE_UG_1_0);//Atmospheric Environment reading//
    Serial.print("PM 2.5: "); Serial.println(data.PM_AE_UG_2_5);
    Serial.print("PM 10: "); Serial.println(data.PM_AE_UG_10_0);
    delay(5000);
  }
  //DHT11//
  float t=dht.readTemperature();
  float rh=dht.readHumidity();
  if (!isnan(t) && !isnan(h)) {
    Serial.print("Temperature: "); Serial.print(t); Serial.print(" °C  ");
    Serial.print("Humidity: "); Serial.print(h); Serial.println(" %");
  } else {
    Serial.println("DHT11: Failed to read");
  }
  //MQ135//
  float ppm=co2sensor.getCorrectedPPM(t,h);
  Serial.print("CO2 Corrected:");Serial.println(ppm,2);
  Serial.println("-------------------------------------------");
}