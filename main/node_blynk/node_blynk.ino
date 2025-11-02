#define BLYNK_TEMPLATE_ID "TMPL3rQGiyUze"
#define BLYNK_TEMPLATE_NAME "ESP32 AQI Node"
#include<WiFi.h>
#include<WiFiUdp.h>
#include<BlynkSimpleEsp32.h>
#include<PMS.h>
#include<DHT.h>
#define LED 2
#define DHTTYPE DHT11
#define DHTPIN 4
#define RXD2 16
#define TXD2 17
#define MQ135_PIN 36
DHT dht(DHTPIN, DHTTYPE);
PMS pms(Serial2);
int pm25=0;//Global var//
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
  //Sending to Blynk//
  Blynk.virtualWrite(V0, t);
  Blynk.virtualWrite(V1, rh);
  Blynk.virtualWrite(V2, pm25);
  Blynk.virtualWrite(V3, pm10);
  //UDP packet//
  char buffer[128];
  snprintf(buffer, sizeof(buffer), "%.2f,%.2f,%.2f,%d,%d\n",millis()/1000.0, t, rh, pm25, pm10);
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
  Blynk.begin(auth,ssid,pass);
  Serial.println("Connected Successfully"); Serial.println("------------------------");
  timer.setInterval(15000L,sendSensorData);
}
void loop() {
  Blynk.run();
  timer.run();
  //PMS//
  if (pms.read(data)) {
    pm25=data.PM_AE_UG_2_5;
    pm10=data.PM_AE_UG_10_0;
  }
}