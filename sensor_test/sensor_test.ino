#include<MQ135.h>
#include<MQUnifiedsensor.h>
#define MQ135_PIN 36
#define MQ7_PIN 39     
void setup() {
  Serial.begin(115200);
  Serial.println("Power ON");
}

void loop() {
    int raw_mq135 = analogRead(MQ135_PIN);
    int raw_mq7 = analogRead(MQ7_PIN);
    Serial.print("MQ-135 (GPIO39) ADC: ");
    Serial.print(raw_mq135);
    Serial.print(" | MQ-7 (GPIO36) ADC: ");
    Serial.println(raw_mq7);
    delay(5000);

}
