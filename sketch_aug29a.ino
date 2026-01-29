#include <Servo.h>

Servo myServo;

int targetAngle = 90;
int currentAngle = 90;
int moveDelay = 10;
bool isRunning = false;
unsigned long lastMove = 0;
unsigned long lastSend = 0;

void setup() {
  Serial.begin(9600);
  myServo.attach(9);
  currentAngle = 90;
  myServo.write(currentAngle);
  delay(1000);
  Serial.println("Servo initialized at 90 degrees");
}

void loop() {
  // Handle serial commands (non-blocking)
  if (Serial.available()) {
    String input = Serial.readStringUntil('\n');
    input.trim();
    Serial.println("Received: " + input);

    if (input.startsWith("START")) {
      // Parse: START,angle,speed
      int firstComma = input.indexOf(',');
      int secondComma = input.indexOf(',', firstComma + 1);

      if (firstComma > 0 && secondComma > firstComma) {
        int newTarget = input.substring(firstComma + 1, secondComma).toInt();
        int speed = input.substring(secondComma + 1).toInt();

        // Constrain values
        newTarget = constrain(newTarget, 0, 180);
        speed = constrain(speed, 1, 5);
        moveDelay = map(speed, 1, 5, 20, 100); // Slower timing for non-blocking
        
        targetAngle = newTarget;
        isRunning = true;
        lastMove = millis(); // Initialize movement timer
        
        Serial.println("START - Target: " + String(targetAngle) + 
                      ", Current: " + String(currentAngle) + 
                      ", Speed: " + String(speed));
      }
    }
    else if (input.startsWith("STOP")) {
      isRunning = false;
      Serial.println("STOPPED at angle: " + String(currentAngle));
    }
    else if (input.startsWith("RESET")) {
      // Parse: RESET,angle
      int commaIndex = input.indexOf(',');
      if (commaIndex > 0) {
        int angle = input.substring(commaIndex + 1).toInt();
        angle = constrain(angle, 0, 180);
        targetAngle = angle;
        currentAngle = angle;
        myServo.write(currentAngle);
        isRunning = false;
        Serial.println("RESET to: " + String(angle));
      }
    }
  }

  // Non-blocking movement logic
  if (isRunning && (millis() - lastMove >= moveDelay)) {
    if (currentAngle != targetAngle) {
      // Move one step towards target
      if (currentAngle < targetAngle) {
        currentAngle++;
      } else {
        currentAngle--;
      }
      
      myServo.write(currentAngle);
      lastMove = millis(); // Update movement timer
      
      // Optional: print movement progress
      // Serial.println("Moving to: " + String(currentAngle));
    } else {
      // Target reached
      isRunning = false;
      Serial.println("TARGET_REACHED at " + String(currentAngle));
    }
  }

  // Send periodic feedback (non-blocking)
  if (millis() - lastSend >= 100) { // More frequent updates
    Serial.println("Angle:" + String(currentAngle));
    lastSend = millis();
  }
}