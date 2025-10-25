#include<PMS.h>
#include<DHT.h>
#include<MQ135.h>
#define DHTTYPE DHT11
#define DHTPIN 4
#define RXD2 16
#define TXD2 17
#define MQ135_PIN 36
#define RZERO 78
DHT dht(DHTPIN, DHTTYPE);
MQ135 co2sensor(MQ135_PIN, RZERO);
PMS pms(Serial2);
PMS::DATA data;
void setup() {
  Serial.begin(115200);
  Serial.println("Power ON");
  dht.begin();
  Serial.println("DHT init");
  Serial2.begin(9600,SERIAL_8N1, RXD2, TXD2);
  Serial.println("PMS init");
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
  //float ppm=co2sensor.getCorrectedPPM(t,rh);//
  //csv output//
  Serial.print(millis()/1000.0); Serial.print(",");
  Serial.print(t); Serial.print(",");
  Serial.print(rh); Serial.print(",");
  Serial.print(data.PM_AE_UG_2_5); Serial.print(",");
  Serial.println(data.PM_AE_UG_10_0);
  //Serial.println(ppm,2); Serial.print(",");//
  delay(5000);
  }
}