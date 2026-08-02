#include<PMS.h>
#include<DHT.h>
#include<MQUnifiedsensor.h>
#include<WiFi.h>
#include<esp_wifi.h>
#include<esp_now.h>
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
#define RZERO_135 40.00
#define RZERO_7 18.00
#define WIFI_CHANNEL 11       
//DHT, MQ135, PMS//
DHT dht(DHTPIN, DHTTYPE);
MQUnifiedsensor coSensor(BOARD, VOLT_RES, ADC_BIT_RES, MQ7_PIN);
MQUnifiedsensor co2Sensor(BOARD, VOLT_RES, ADC_BIT_RES, MQ135_PIN);
PMS pms(Serial2);
PMS::DATA data;
typedef struct __attribute__((packed)) {
    uint32_t sequence;
    float temperature;
    float humidity;
    float pm25;
    float pm10;
    float mq135;
    float mq7;
} SensorPacket;
SensorPacket packet;
uint8_t AQMS_MAC[] = {
    0x1A, 0x00, 0x00,
    0x00, 0x00, 0x01
};
uint8_t S3_MAC[] = {
    0x1A, 0x00, 0x00,
    0x00, 0x00, 0x02
};
void setup() {
  Serial.begin(115200);
  Serial.println("Power ON");
  dht.begin();
  Serial.println("DHT init");
  Serial2.begin(9600,SERIAL_8N1, RXD2, TXD2);
  Serial.println("PMS init");
  //WIFI INIT
  WiFi.mode(WIFI_STA);
  ESP_ERROR_CHECK(esp_wifi_set_mac(WIFI_IF_STA, AQMS_MAC));
  ESP_ERROR_CHECK(esp_wifi_set_channel(WIFI_CHANNEL, WIFI_SECOND_CHAN_NONE));
  if(esp_now_init()!=ESP_OK){
    Serial.println("ESP-NOW Initialization Failed");
    return;
  }
  esp_now_peer_info_t peer={};
  memcpy(peer.peer_addr, S3_MAC, 6);
  peer.channel=WIFI_CHANNEL;
  peer.encrypt = false;
  if(esp_now_add_peer(&peer)!=ESP_OK){
    Serial.println("Failed to Add Receiver");
    return;
  }
  Serial.println("Ready to Send Data");

  // --- MQ-7 Initialization ---
  coSensor.init(); 
  coSensor.setR0(RZERO_7);
  coSensor.setRL(RL);
  coSensor.setA(99.042); 
  coSensor.setB(-1.518);
  coSensor.setRegressionMethod(1);  
  Serial.print("Calibrating MQ7");
  float calcR0 = 0;
  for(int i = 1; i<=10; i ++) {
    coSensor.update();
    calcR0 += coSensor.calibrate(22.0);
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
  co2Sensor.setA(110.47); 
  co2Sensor.setB(-2.862);
  Serial.print("Calibrating MQ135... ");
  float calcR0_CO2 = 0;
  for (int i = 0; i < 10; i++) {
    co2Sensor.update();
    calcR0_CO2 += co2Sensor.calibrate(5.5);
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
  if(isnan(ppm1))
  {
    ppm1=0.00;
  }
  if(isnan(ppm2))
  {
    ppm2=0.00;
  }
  //Serial output//
  Serial.print(millis()/1000.0); Serial.print(",");
  Serial.print(t); Serial.print(",");
  Serial.print(rh); Serial.print(",");
  Serial.print(data.PM_AE_UG_2_5); Serial.print(",");
  Serial.print(data.PM_AE_UG_10_0); Serial.print(",");
  Serial.print(ppm1,2); Serial.print(",");
  Serial.print(ppm2,2); Serial.print(",");
  //UDP Packet//
  packet.sequence++;
  packet.temperature = t;
  packet.humidity = rh;
  packet.pm25 = data.PM_AE_UG_2_5;
  packet.pm10 = data.PM_AE_UG_10_0;
  packet.mq135 = ppm2;
  packet.mq7 = ppm1;
  esp_err_t result = esp_now_send(
      S3_MAC,
      reinterpret_cast<uint8_t *>(&packet),
      sizeof(packet)
  );

  if (result == ESP_OK)
      Serial.println("Packet queued");
  else
      Serial.printf("ESP-NOW error: %d\n", result);
  }
}
