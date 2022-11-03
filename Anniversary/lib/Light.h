#ifndef BLINK_H
#define BLINK_H

#include <Arduino.h>

class Light
{
  typedef enum
  {
    OFF = 0,
    ON = 1
  }State;

  public:
    void Init(int LightPin, int SwitchPin);
    void Blink();

  private:
    int CheckState();

    int pinLight;
    int pinSwitch;
    State switchState;
};





#endif