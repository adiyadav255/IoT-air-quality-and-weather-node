#include<MQ135.h>
#include<MQUnifiedsensor.h>
#define MQ135_PIN 36
#define RZERO_135 62.00 //IN CLEAN AIR
#define MQ7_PIN 39     
#define BOARD "ESP-32" 
#define VOLT_RES 3.3  
#define ADC_BIT_RES 12 
#define RL 10.0       
#define RZERO_7 10.00 //IN CLEAN AIR
#define GAS "CO"
MQ135 co2sensor(MQ135_PIN, RZERO_135);
MQUnifiedsensor coSensor(BOARD, VOLT_RES, ADC_BIT_RES, MQ7_PIN, GAS);
void setup() {
  Serial.begin(115200);
  Serial.println("Power ON");
  // --- MQ-7 Initialization ---
  coSensor.init(); 

}

void loop() {
  // Read raw 12-bit ADC values (0 to 4095 on ESP32)
    int raw_mq135 = analogRead(MQ135_PIN);
    int raw_mq7 = analogRead(MQ7_PIN);

    Serial.print("MQ-135 (GPIO39) ADC: ");
    Serial.print(raw_mq135);
    Serial.print(" | MQ-7 (GPIO36) ADC: ");
    Serial.println(raw_mq7);
    
    // Delay is mandatory to see the output
    delay(5000);

}
