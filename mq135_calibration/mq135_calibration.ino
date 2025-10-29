#include<MQ135.h>
#define MQ135_PIN 36
MQ135 mq135_sensor(MQ135_PIN);
void setup() {
  Serial.begin(115200);
  Serial.println("Power ON");
  Serial.println("-----------------------");
}
void loop() {
  float rzero = mq135_sensor.getRZero();
  Serial.print("Value: ");
  Serial.println(rzero);
  delay(3000);
}
