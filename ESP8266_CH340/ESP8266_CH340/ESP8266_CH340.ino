void setup() 
{
Serial.begin(9600);
}
void loop() 
{
if (Serial.available() > 0) {
String message = Serial.readStringUntil('\n');
message += " - Modified by server";
Serial.println(message);
}
}