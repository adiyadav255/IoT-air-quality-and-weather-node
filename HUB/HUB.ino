#include<WiFi.h>
#include<esp_wifi.h>
#include<esp_now.h>
#include "tinyNN_int8.h"
#include<tflm_esp32.h>
#include<eloquent_tinyml.h>
#define TENSOR_ARENA_SIZE 16384
Eloquent::TF::Sequential<2, TENSOR_ARENA_SIZE> tf;
#define WINDOW_SIZE 8
#define NUM_FEATURES 4
float inputWindow[WINDOW_SIZE][NUM_FEATURES];
int8_t modelInput[WINDOW_SIZE * NUM_FEATURES];
uint8_t samplesCollected = 0;
const float X_MEAN[4] =
{
    197.25513906f,
    227.17230955f,
    26.34304716f,
    45.83494559f
};
const float X_STD[4] =
{
    50.92380164f,
    60.14131832f,
    1.08786175f,
    5.58391736f
};
const float Y_MEAN = 349.86281917f;
const float Y_STD  = 54.75528965f;
typedef struct __attribute__((packed)) {
    uint32_t sequence;
    float pm25;
    float pm10;
    float temperature;
    float humidity;
    float mq135;
    float mq7;
} SensorPacket;
SensorPacket receivedPacket;
inline float standardize(float value, uint8_t feature)
{
  return (value - X_MEAN[feature] / X_STD[feature]);
}
//WIFI CONFIG
#define WIFI_CHANNEL 11
static uint8_t S3_MAC[] = {
    0x1A, 0x00, 0x00,
    0x00, 0x00, 0x02
};
static uint8_t AQMS_MAC[] = {
    0x1A, 0x00, 0x00,
    0x00, 0x00, 0x01
};
volatile bool newPacketAvailable = false;
uint32_t lastSequence = 0;
bool firstPacket = true;
//Receiver Function
void onDataReceived(
    const esp_now_recv_info_t *info,
    const uint8_t *data,
    int len)
{
  if(memcpy(info->src_addr, AQMS_MAC, 6)!=0)
  {
    return;
  }
  // Make sure we received exactly one SensorPacket
  if (len != sizeof(SensorPacket)) {
    return;
  }
  memcpy(
    &receivedPacket,
    data,
    sizeof(SensorPacket)
  );
  newPacketAvailable = true;
}
//Append data to window
void updateInputWindow(const SensorPacket &packet)
{
  for(int t=0; t<WINDOW_SIZE -1; t++)
  {
    for(int f=0; f<NUM_FEATURES; f++)
    {
      inputWindow[t][f]=inputWindow[t+1][f];
    }
  }
  inputWindow[WINDOW_SIZE - 1][0] = packet.pm25;
  inputWindow[WINDOW_SIZE - 1][1] = packet.pm10;
  inputWindow[WINDOW_SIZE - 1][2] = packet.temperature;
  inputWindow[WINDOW_SIZE - 1][3] = packet.humidity;
  if (samplesCollected<WINDOW_SIZE)
  {
    samplesCollected++;
  }
}
//ESP-NOW configuration
bool setupESPNow()
{
  WiFi.mode(WIFI_STA);
  esp_err_t result=esp_wifi_set_mac(WIFI_IF_STA, S3_MAC);
  if (result!=ESP_OK){
    Serial.printf("Failed to set MAC Address(S3):%d",result);
    return false;
  }
  result=esp_wifi_set_channel(WIFI_CHANNEL, WIFI_SECOND_CHAN_NONE);
  if (result!=ESP_OK){
    Serial.printf("Failed to set Wifi channel:%d",result);
    return false;
  }
  esp_wifi_set_ps(WIFI_PS_NONE);
  result=esp_now_init();
  if(result!=ESP_OK){
    Serial.printf("ESP-NOW Initialization failed:%d",result);
  return false;
  }
  result=esp_now_register_recv_cb(onDataReceived);
  if (result!=ESP_OK){
    Serial.printf("Failed to Receive Callback:%d",result);
  return false;
  }
  return true;
}
//Prepare Window
void prepareModelInput()
{
  int index = 0;
  const float inputScale = tf.in->params.scale;
  const int32_t inputZeroPoint = tf.in->params.zero_point;
  for (int t = 0; t < WINDOW_SIZE; t++)
  {
    for (int f = 0; f < NUM_FEATURES; f++)
    {
    float x = standardize(inputWindow[t][f],f);
    int32_t q = (int32_t)roundf(x / inputScale) + inputZeroPoint;
    if (q > 127)
        q = 127;
    else if (q < -128)
        q = -128;
    modelInput[index++] = (int8_t)q;
    }
  }
}
bool setupTensorFlow()
{
  tf.setNumInputs(32);
  tf.setNumOutputs(1);
  tf.resolver.AddFullyConnected();
  tf.resolver.AddReshape();
  if (!tf.begin(tinyNN_int8_tflite).isOk())
  {
    Serial.println("TensorFlow initialization failed:");
    Serial.println(tf.exception.toString());
    return false;
  }
  Serial.println("TensorFlow initialized successfully.");
  return true;
}
void setup() {
  Serial.begin(115200);
  delay(1000); 
  if(!setupESPNow()){
    Serial.println("ESP-NOW setup failed");
    while (true){
      delay(1000);
    }
  }
  Serial.print("S3 MAC: ");
  Serial.println(WiFi.macAddress());
  Serial.print("Wi-Fi Channel: ");
  Serial.println(WIFI_CHANNEL);
  Serial.println("Waiting for AQMS packets...");
  if (!setupTensorFlow())
  {
      while (true);
      {delay(100);}
  }
}
void loop() {
  if(!newPacketAvailable)
  {return;}
  newPacketAvailable=false;
  if(!firstPacket){
    uint32_t expected = lastSequence+1;
    if(receivedPacket.sequence!=expected)
    {
      Serial.printf("Invalid sequence: %lu",receivedPacket.sequence);
    }
  }
  firstPacket=false;
  lastSequence=receivedPacket.sequence;
  Serial.println();
  Serial.println("------------------------------");
  Serial.printf("Packet:      %lu\n",receivedPacket.sequence);
  Serial.printf("PM2.5      : %.2f ug/m3\n", receivedPacket.pm25);
  Serial.printf("PM10       : %.2f ug/m3\n", receivedPacket.pm10);
  Serial.printf("Temperature: %.2f C\n", receivedPacket.temperature);
  Serial.printf("Humidity   : %.2f %%\n", receivedPacket.humidity);
  Serial.printf("MQ135      : %.2f\n", receivedPacket.mq135);
  Serial.printf("MQ7        : %.2f\n", receivedPacket.mq7);
  updateInputWindow(receivedPacket);
  Serial.printf("\nWindow Status: %d%d samples\n",samplesCollected,WINDOW_SIZE);
  if(samplesCollected < WINDOW_SIZE)
  {
    Serial.println("\nCollecting Samples...");
    return;
  }
  prepareModelInput();
  if (!tf.predict(modelInput).isOk())
  {
    Serial.println("Inference Failed");
    Serial.println(tf.exception.toString());
    return;
  }
  int8_t quantizedOutput = tf.out->data.int8[0];
  float yScaled =(quantizedOutput - tf.out->params.zero_point) * tf.out->params.scale;
  float predictedAQI =yScaled * Y_STD + Y_MEAN;
  Serial.printf("Predicted AQI: %.2f\n", predictedAQI);
}
