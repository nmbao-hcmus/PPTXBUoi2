/* Tap lenh SCPI thuc hanh cho Arduino Uno.
   A0 doc dien ap 0-5 V; cac dai luong khac chi la so lieu minh hoa.
   Cau hinh buoi hoc: 9600 baud, 8N1, khong flow control; phan hoi ket thuc CR. */
#include <Arduino.h>
#include <stdlib.h>
#include <stdio.h>

const byte MAX_LINE = 96;
const byte ERROR_CAPACITY = 5;
char inputLine[MAX_LINE];
byte inputLength = 0;

String errorQueue[ERROR_CAPACITY];
byte errorHead = 0;
byte errorCount = 0;

String activeFunction = "VOLT:DC";
float dcRange = 10.0;
bool autoRange = true;
float nplc = 1.0;
float lastReading = 0.0;
bool hasReading = false;

void sendResponse(const String &text);
void sendResponse(float value, byte decimals);

void addError(int code, const char *message) {
  if (errorCount >= ERROR_CAPACITY) return;
  byte slot = (errorHead + errorCount) % ERROR_CAPACITY;
  errorQueue[slot] = String(code) + "," + message;
  errorCount++;
}

void printNextError() {
  if (errorCount == 0) {
    sendResponse("0,No error");
    return;
  }
  sendResponse(errorQueue[errorHead]);
  errorHead = (errorHead + 1) % ERROR_CAPACITY;
  errorCount--;
}

String normalizeCommand(String command) {
  command.trim();
  command.toUpperCase();
  if (command.startsWith(":")) command.remove(0, 1);
  command.replace("CONFIGURE", "CONF");
  command.replace("FRESISTANCE", "FRES");
  command.replace("VOLTAGE", "VOLT");
  command.replace("CURRENT", "CURR");
  command.replace("RESISTANCE", "RES");
  command.replace("SENSE", "SENS");
  command.replace("SYSTEM", "SYST");
  command.replace("RANGE", "RANG");
  command.replace("MEASURE", "MEAS");
  command.replace("FETCH", "FETC");
  command.replace("FUNCTION", "FUNC");
  command.replace("ERROR", "ERR");
  command.replace("VERSION", "VERS");
  command.replace("NPLCYCLES", "NPLC");
  return command;
}

void resetSettings() {
  activeFunction = "VOLT:DC";
  dcRange = 10.0;
  autoRange = true;
  nplc = 1.0;
  hasReading = false;
}

float readMeasurementValue(const String &functionName) {
  float v = analogRead(A0) * (5.0 / 1023.0);
  if (functionName == "VOLT:DC") return v;
  if (functionName == "VOLT:AC") return v * 0.707;     // So lieu minh hoa
  if (functionName == "CURR:DC") return v / 1000.0;   // So lieu minh hoa
  if (functionName == "RES") return 1000.0 + v * 1000.0;
  if (functionName == "FRES") return 1000.0 + v * 999.0;
  return v;
}

void sendResponse(const String &text) {
  Serial.print(text);
  Serial.write('\r');
}

void sendResponse(float value, byte decimals) {
  Serial.print(value, decimals);
  Serial.write('\r');
}

void printReading(const String &functionName) {
  lastReading = readMeasurementValue(functionName);
  hasReading = true;
  sendResponse(lastReading, 6);
}

bool parseNumber(const String &text, float &value) {
  char *endPointer;
  value = strtof(text.c_str(), &endPointer);
  return endPointer != text.c_str() && *endPointer == '\0';
}

void setFunction(const String &functionName) {
  activeFunction = functionName;
  dcRange = 10.0;
  autoRange = true;
  nplc = 1.0;
  hasReading = false;
}

void handleCommand(String command) {
  command = normalizeCommand(command);
  if (command.length() == 0) return;

  if (command == "*IDN?") {
    sendResponse("KEITHLEY INSTRUMENTS INC., MODEL 2000, 1234567, 1.0/1.0");
  } else if (command == "*RST") {
    resetSettings();
  } else if (command == "*CLS") {
    errorHead = 0;
    errorCount = 0;
  } else if (command == "*TST?") {
    sendResponse("0");
  } else if (command == "*OPC?") {
    sendResponse("1");
  } else if (command == "SYST:VERS?") {
    sendResponse("1991.0");
  } else if (command == "SYST:ERR?") {
    printNextError();
  } else if (command == "CONF?") {
    sendResponse(activeFunction);
  } else if (command == "SENS:FUNC?") {
    sendResponse(activeFunction);
  } else if (command == "CONF:VOLT:DC") {
    setFunction("VOLT:DC");
  } else if (command == "CONF:VOLT:AC") {
    setFunction("VOLT:AC");
  } else if (command == "CONF:CURR:DC") {
    setFunction("CURR:DC");
  } else if (command == "CONF:RES") {
    setFunction("RES");
  } else if (command == "CONF:FRES") {
    setFunction("FRES");
  } else if (command == "READ?") {
    printReading(activeFunction);
  } else if (command == "FETC?") {
    if (hasReading) sendResponse(lastReading, 6);
    else addError(-230, "Data corrupt or stale");
  } else if (command == "MEAS:VOLT:DC?") {
    setFunction("VOLT:DC"); printReading(activeFunction);
  } else if (command == "MEAS:VOLT:AC?") {
    setFunction("VOLT:AC"); printReading(activeFunction);
  } else if (command == "MEAS:CURR:DC?") {
    setFunction("CURR:DC"); printReading(activeFunction);
  } else if (command == "MEAS:RES?") {
    setFunction("RES"); printReading(activeFunction);
  } else if (command == "MEAS:FRES?") {
    setFunction("FRES"); printReading(activeFunction);
  } else if (command.startsWith("SENS:VOLT:DC:RANG:AUTO")) {
    const String header = "SENS:VOLT:DC:RANG:AUTO";
    String arg = command.substring(header.length());
    arg.trim();
    if (arg == "?") {
      sendResponse(autoRange ? "1" : "0");
    } else if (arg == "ON" || arg == "1") {
      autoRange = true;
    } else if (arg == "OFF" || arg == "0") {
      autoRange = false;
    } else if (arg.length() == 0) {
      addError(-109, "Missing parameter");
    } else {
      addError(-104, "Data type error");
    }
  } else if (command.startsWith("SENS:VOLT:DC:RANG")) {
    const String header = "SENS:VOLT:DC:RANG";
    String arg = command.substring(header.length());
    arg.trim();
    if (arg == "?") {
      sendResponse(dcRange, 3);
    } else {
      float requestedRange;
      if (arg.length() == 0) {
        addError(-109, "Missing parameter");
      } else if (!parseNumber(arg, requestedRange)) {
        addError(-104, "Data type error");
      } else if (requestedRange != 0.1 && requestedRange != 1.0 &&
                 requestedRange != 10.0 && requestedRange != 100.0 &&
                 requestedRange != 1000.0) {
        addError(-222, "Parameter data out of range");
      } else {
        dcRange = requestedRange;
        autoRange = false;
      }
    }
  } else if (command.startsWith("SENS:VOLT:DC:NPLC")) {
    const String header = "SENS:VOLT:DC:NPLC";
    String arg = command.substring(header.length());
    arg.trim();
    if (arg == "?") {
      sendResponse(nplc, 2);
    } else {
      float requestedNplc;
      if (arg.length() == 0) {
        addError(-109, "Missing parameter");
      } else if (!parseNumber(arg, requestedNplc)) {
        addError(-104, "Data type error");
      } else if (requestedNplc < 0.01 || requestedNplc > 10.0) {
        addError(-222, "Parameter data out of range");
      } else {
        nplc = requestedNplc;
      }
    }
  } else {
    addError(-113, "Undefined header");
  }
}

void setup() {
  Serial.begin(9600);
  resetSettings();
}

void loop() {
  while (Serial.available() > 0) {
    char incoming = (char)Serial.read();
    if (incoming == '\r' || incoming == '\n') {
      if (inputLength > 0) {
        inputLine[inputLength] = '\0';
        handleCommand(String(inputLine));
        inputLength = 0;
      }
    } else if (inputLength < MAX_LINE - 1) {
      inputLine[inputLength++] = incoming;
    } else {
      inputLength = 0;
      addError(-363, "Input buffer overrun");
    }
  }
}
