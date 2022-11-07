#include "Light.h"

/**
 * @brief Initializer Function for Light Object
 * 
 * @param LightPin Output Pin for Light
 * @param SwitchPin Input Pin for Switch
 */
void Light::Init(int LightPin, int SwitchPin)
{
  pinLight = LightPin;
  pinSwitch = SwitchPin;
  
  pinMode(pinLight, OUTPUT);
  pinMode(pinSwitch, INPUT);
}

/**
 * @brief Function for Blinking when Device is Shaken
 * 
 */
void Light::Blink()
{
  State before = CheckState();


  delay(500);

  if(CheckState() != before)
  {
    digitalWrite(pinLight, HIGH);
    delay(200);
    digitalWrite(pinLight, LOW);
    delay(200);
    digitalWrite(pinLight, HIGH);
    delay(400);
    digitalWrite(pinLight, LOW);

    delay(400);

    digitalWrite(pinLight, HIGH);
    delay(200);
    digitalWrite(pinLight, LOW);
    delay(200);
    digitalWrite(pinLight, HIGH);
    delay(400);
    digitalWrite(pinLight, LOW);

    return;
  }

  // Serial.println("Not ON");
  return;
}

/**
 * @brief Check the Current State of Switch
 * 
 * @return State of the Switch
 */
Light::State Light::CheckState()
{
  if(digitalRead(pinSwitch)) switchState = ON;
  else switchState = OFF;
  
  return switchState;
}