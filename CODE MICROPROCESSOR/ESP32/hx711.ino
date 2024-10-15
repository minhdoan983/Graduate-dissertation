#include <LiquidCrystal_I2C.h>
#include "HX711.h"
#include <Wire.h>
#define DEBUG_HX711
// Calibration factors for each load cell
#define CALIBRATION_FACTOR_1 458000.0 // Calibration factor for load cell 1
#define CALIBRATION_FACTOR_2 470000.0 // Calibration factor for load cell 2
//HC-SR04
int trigPin = 2;
int echoPin = 4;
long khoangthoigian; //micro second
int khoangcach;
// Create the LCD object, address 0x27, 16 columns x 2 rows 
LiquidCrystal_I2C lcd(0x27, 16, 2);

// Pins for the first load cell
byte pinData1 = 18;
byte pinClk1 = 19;

// Pins for the second load cell
byte pinData2 = 33; // Change to the appropriate pin for load cell 2
byte pinClk2 = 32; // Change to the appropriate pin for load cell 2
// Define HX711 instances for each load cell
HX711 scale1;
HX711 scale2;

void setup() {
  // Initialize LCD
  lcd.init();
  lcd.backlight();
  // lcd.print("Trong luong");
  lcd.setCursor(0, 0);
  lcd.print("DO AN TOT NGHIEP");
  pinMode(trigPin,OUTPUT); // chan trig phat tin hieu
  pinMode(echoPin,INPUT); // chan echo nhan tin hieu
#ifdef DEBUG_HX711
  // Initialize serial communication
  Serial.begin(9600);
#endif

  // Initialize first scale
  scale1.begin(pinData1, pinClk1);
  scale1.set_scale(CALIBRATION_FACTOR_1);
  scale1.tare();

  // Initialize second scale
  scale2.begin(pinData2, pinClk2);
  scale2.set_scale(CALIBRATION_FACTOR_2);
  scale2.tare();
}

void loop() {
digitalWrite(trigPin, LOW); // tat chan trig
delayMicroseconds(2);
digitalWrite(trigPin, HIGH); // phat xung tu chan trig
delayMicroseconds(10);
digitalWrite(trigPin, LOW);
khoangthoigian = pulseIn(echoPin, HIGH);
khoangcach= khoangthoigian*0.0343/2;
// Serial.print("Khoangcach: ");
// Serial.println(khoangcach);
#ifdef DEBUG_HX711
if (khoangcach<=40&&khoangcach>15)
{
  // Read and print weight from first load cell
  // Serial.print("Load cell 2: ");
  Serial.print(abs(scale2.get_units()), 3);
  Serial.print("\n");}
else
{  // Read and print weight from second load cell
  // Serial.print("Load cell 1: ");
  Serial.print(abs(scale1.get_units()), 3);
  Serial.print("\n");}
#endif
if (khoangcach<=40&&khoangcach>15)
 { // Display weight from first load cell on LCD
  lcd.setCursor(0, 1);
  lcd.print("Weight: ");
  lcd.print(abs(scale2.get_units()), 3);
  lcd.print(" Kg");}
else {
  // Display weight from second load cell on LCD
  lcd.setCursor(0, 1);
  lcd.print("Weight: ");
  lcd.print(abs(scale1.get_units()), 3);
  lcd.print(" Kg");}
}
