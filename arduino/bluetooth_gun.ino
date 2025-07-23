#include <SoftwareSerial.h>
SoftwareSerial BTserial(2, 3); // RX | TX

const long baudRate = 38400;
char c = ' ';
boolean NL = true;

void setup()
{
   Serial.begin(38400);
   Serial.print("Sketch:   ");   Serial.println(__FILE__);
   Serial.print("Uploaded: ");   Serial.println(__DATE__);
   Serial.println(" ");

   BTserial.begin(baudRate);
   Serial.print("BTserial started at "); 
   Serial.println(baudRate);
   Serial.println(" ");
   pinMode(LED_BUILTIN, OUTPUT);
   pinMode(6, OUTPUT);

}

void loop()
{
   // Read from the Bluetooth module and shoot if 'F' letter came
   if (BTserial.available())
   {
      c = BTserial.read();
      Serial.write(c);
      if(c=='F')
      {
        c='0';
        Serial.println(c);
        digitalWrite(LED_BUILTIN, 1);   
        digitalWrite(6, 1);   
        delay(75);                      
        digitalWrite(LED_BUILTIN, 0); 
        digitalWrite(6, 0); 
        delay(1000);
      }
      
   }

}
