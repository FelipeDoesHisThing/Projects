#include <Arduino.h>
#include "../lib/Light/Light.h"

const int HeartPin = 4;
const int SwitchPin = A5;

Light light;

void setup() 
{
  Serial.begin(9600);

  light.Init(HeartPin, SwitchPin); //Initialize Values
}

void loop() 
{
  light.Blink(); //Check if the device has been shaken
}

