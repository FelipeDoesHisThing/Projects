#include "Light.h"

void Light::Init(int LightPin, int SwitchPin)
{
  pinLight = LightPin;
  pinSwitch = SwitchPin;
  
  pinMode(pinLight, OUTPUT);
  pinMode(pinSwitch, INPUT);
}

void Light::Blink()
{
  State before = CheckState();

  delay(200);

  if(CheckState() != before)
  {
    digitalWrite(pinLight, HIGH);
    delay(200);
    digitalWrite(pinLight, LOW);
    delay(500);
    digitalWrite(pinLight, HIGH);
    delay(500);
    digitalWrite(pinLight, LOW);

    return;
  }

  return;
}

Light::State Light::CheckState()
{
  if(pinSwitch == HIGH) switchState = ON;
  else switchState = OFF;
  
  return switchState;
}