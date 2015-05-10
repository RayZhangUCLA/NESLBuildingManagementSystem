#include <RFduinoBLE.h>
//This is a simple RFduino sketch that will allow RFduino reads
//analog readings from a Temperature Sensor, and send this reading 
//to Beaglebone Black through BLE after conversion.

//TMP36 Pin Variables
int sensorPin = 6;
//
//void RFduinoBLE_onConnect(){
//  Serial.println("BLE connected");
//}
// 
void setup()
{
//  Serial.begin(9600); 
  RFduinoBLE.advertisementInterval = 500;
  RFduinoBLE.deviceName = "RFduino-Temp";
  RFduinoBLE.txPowerLevel = -16;
//  Serial.println("RFduino BLE Advertising interval is 500ms");
  RFduinoBLE.begin(); //start BLE
//  Serial.println("RFduino BLE stack started");
}
 
void loop()
{
 //getting the voltage reading from the temperature sensor
 int reading = analogRead(sensorPin);  
 //Find the corrosponding temperature
 float voltage = reading * 3.3;
 voltage /= 1024.0; 
// Serial.print(voltage);Serial.print("\n");
 float temp = (voltage - 0.5) * 100 ;  //formula from Product Specs
 RFduinoBLE.sendFloat(temp);
// Serial.print(temp); Serial.println(" degrees C");
 RFduino_ULPDelay( SECONDS(120) );//waiting two minutes
}
