#define BLYNK_TEMPLATE_ID "TMPL3rQGiyUze"
#define BLYNK_TEMPLATE_NAME "ESP32 AQI Node"
#include<WiFi.h>
#include<BlynkSimpleEsp32.h>
#include<PMS.h>
#include<DHT.h>
#define DHTTYPE DHT11
#define DHTPIN 4
#define RXD2 16
#define TXD2 17
#define MQ135_PIN 36
DHT dht(DHTPIN, DHTTYPE);
PMS pms(Serial2);
PMS::DATA data;
char auth[] = "H5OXKNaNL93W1dLbRS6qvOvidInfoSJv";
char ssid[] = "Aditya";
char pass[] = "adi@12345";
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
  //PMS7003//
   //if(pms.read(data)){
    Serial.println("---------SENSOR READINGS----------");
    Serial.print("PM 1.0:"); Serial.println(data.PM_AE_UG_1_0);//Atmospheric Environment reading//
    Serial.print("PM 2.5: "); Serial.println(data.PM_AE_UG_2_5);
    Serial.print("PM 10: "); Serial.println(data.PM_AE_UG_10_0);
    //Send to Blynk//
    Blynk.virtualWrite(V0,t); 
    Blynk.virtualWrite(V1,rh); 
    Blynk.virtualWrite(V2,data.PM_AE_UG_2_5); 
    Blynk.virtualWrite(V3,data.PM_AE_UG_10_0);
}
void setup() {
  Serial.begin(115200);
  Serial.println("Power ON");
  dht.begin();
  Serial.println("DHT init");
  Serial2.begin(9600,SERIAL_8N1, RXD2, TXD2);
  Serial.print("PMS init");
  WiFi.begin(ssid, pass);
  Blynk.config(auth);
  Blynk.connect();
  Serial.print("Connected");
  timer.setInterval(15000L,sendSensorData);
}
void loop() {
  Blynk.run();
  timer.run();
}