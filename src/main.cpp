#include <Arduino.h>
#include <ArduinoJson.h>
#include "ADS119X.h"
#ifdef ARDUINO_ARCH_ESP8266
#include <ESP8266WiFi.h>
#else
#include <WiFi.h>
#endif

#include <WiFiUdp.h>

// Set WiFi credentials
#define WIFI_SSID ***REMOVED***
#define WIFI_PASS ***REMOVED***

// UDP
#define UDP_PORT 4210
WiFiUDP UDP;
char packet[2048];

StaticJsonDocument<1024> packetJson;

#ifdef ARDUINO_ARCH_ESP8266
byte dataReady_Pin = D2;
byte reset_pin = D1;
byte cs_pin = D0;
#else
byte dataReady_Pin = 34;
byte reset_pin = 35;
byte cs_pin = 32;
#endif

#define MEAS_PER_MSG 5

uint8_t sendBuffer[8 * MEAS_PER_MSG];

char currentCycle = 0;

boolean sendUdp = false;

IPAddress remoteIp;
unsigned int remotePort;

// #ifdef ARDUINO_ARCH_ESP8266
// SPIClass SPI1();
// #else
// SPIClass SPI1(VSPI);
// #endif

// ADS119X adc(SPI1, dataReady_Pin, reset_pin, cs_pin);
ADS119X adc(dataReady_Pin, reset_pin, cs_pin);

// variables
bool dataReady = 0;
bool prev_dataReady = 0;
byte received;
boolean verbosity = 1;
byte numberOfChannels;

// Serial comm
const byte numChars = 32;
char receivedChars[numChars];
char tempChars[numChars]; // temporary array for use when parsing
int command[2];
boolean newData = false;

byte state = 0;

int elapsed = 0;
long prevMicros = 0;

void print8bits(int var)
{
  for (unsigned int bitpos = 0x80; bitpos; bitpos >>= 1)
  {
    Serial.write(var & bitpos ? '1' : '0');
  }
  Serial.println();
}

void printStatus()
{
  Serial.print(adc.getStatus(), HEX);
  Serial.print(", ");
}

void printData()
{
  for (int ch = 0; ch < numberOfChannels; ch++) //adc.getNumberOfChannels()
  {
    Serial.print(adc.getChannelData(ch));
    if (ch < numberOfChannels - 1)
    {
      Serial.print(",");
    }
  }
  Serial.println("");
}

void displayRegs()
{
  Serial.println("REGISTERS: ");
  for (int i = 0; i < adc.getRegisterSize(); i++)
  {
    if (i < 0x10)
    {
      Serial.print(" ");
    }
    Serial.print("0x");
    Serial.print(i, HEX);
    Serial.print(": ");
    print8bits(adc.getRegister(i));
  }
}

void fillSendBuffer()
{
  for (int ch = 0; ch < numberOfChannels; ch++)
  {
    short channelData = adc.getChannelData(ch);
    // Serial.printf("cycle: %d, channelData: %d (%#04x)\n", currentCycle, channelData, channelData);
    sendBuffer[8 * currentCycle + 2 * ch] = (char)(channelData >> 8);
    sendBuffer[8 * currentCycle + 2 * ch + 1] = (char)(channelData & 0xFF);
  }
}

void sendData()
{
  if (currentCycle >= MEAS_PER_MSG - 1)
  {
    // Serial.println("Send");
    UDP.beginPacket(UDP.remoteIP(), UDP.remotePort());
    UDP.write(sendBuffer, 8 * MEAS_PER_MSG);
    UDP.endPacket();
    currentCycle = 0;
  }
  else
  {
    currentCycle++;
  }
}

void handleData()
{
  fillSendBuffer();
  sendData();
}

bool handleStartMessage(int len)
{
  DeserializationError error = deserializeJson(packetJson, &packet[1]);

  if (error)
  {
    Serial.println("Received invalid JSON!");
    return false;
  }

  int dataRate = packetJson["data_rate"] | -1;
  int rldSensP = packetJson["rld_sens_p"] | -1;
  int rldSensN = packetJson["rld_sens_n"] | -1;
  JsonArray channelArray = packetJson["channels"].as<JsonArray>();

  if (dataRate >= 0)
  {
    if (dataRate < 0b111)
    {
      adc.setDataRate(dataRate & 0b111);
    }
    else
    {
      Serial.println("Received invalid data rate!");
      return false;
    }
  }

  if (rldSensP >= 0)
  {
    adc.WREG(ADS119X_ADD_RLD_SENSP, rldSensP & 0xFF);
  }

  if (rldSensN >= 0)
  {
    adc.WREG(ADS119X_ADD_RLD_SENSN, rldSensN & 0xFF);
  }

  if (rldSensP >= 0 || rldSensN >= 0)
  {
    adc.WREG(ADS119X_ADD_CONFIG3, adc.getRegister(ADS119X_ADD_CONFIG3) | ADS119X_NOT_PD_RLD_MASK | ADS119X_RLD_MEAS_MASK | ADS119X_RLDREF_INT_MASK);
  }
  else
  {
    adc.WREG(ADS119X_ADD_CONFIG3, adc.getRegister(ADS119X_ADD_CONFIG3) & ~(ADS119X_NOT_PD_RLD_MASK | ADS119X_RLD_MEAS_MASK | ADS119X_RLDREF_INT_MASK));
  }

  byte currentChannel = 0;

  for (JsonObject channel : channelArray)
  {
    if (currentChannel >= numberOfChannels)
    {
      Serial.println("Too many channels specified!");
      return false;
    }

    byte channelAddress = ADS119X_ADD_CH1SET + currentChannel;

    int powerDown = channel["power_down"] | -1;
    int gain = channel["gain"] | -1;
    int mux = channel["mux"] | -1;

    Serial.println(gain);

    if (powerDown != 1)
    {
      if (gain >= 0 && gain <= 0b111 && mux >= 0 && mux <= 0b111)
      {
        adc.setChannelSettings(channelAddress, 0, (gain & 0b111) << 4, mux & 0b111);
      }
      else
      {
        Serial.println("You have to specify mux and gain!");
        return false;
      }
    }
    else
    {
      adc.setChannelSettings(channelAddress, ADS119X_CHnSET_PD_MASK, 0 << 4, 1);
    }

    currentChannel++;
  }

  return true;
}

void setup()
{
  Serial.begin(1000000);
  Serial.println("Init");
  SPI.beginTransaction(SPISettings(2000000, MSBFIRST, SPI_MODE1));

  // Begin WiFi
  WiFi.begin(WIFI_SSID, WIFI_PASS);

  // Connecting to WiFi...
  Serial.print("Connecting to ");
  Serial.print(WIFI_SSID);
  // Loop continuously while WiFi is not connected
  while (WiFi.status() != WL_CONNECTED)
  {
    delay(100);
    Serial.print(".");
  }

  // Connected to WiFi
  Serial.println();
  Serial.print("Connected! IP address: ");
  Serial.println(WiFi.localIP());

  UDP.begin(UDP_PORT);
  Serial.print("Listening on UDP port ");
  Serial.println(UDP_PORT);

  // adc begin() puts the ADS in a datasheet state, if verbosity is true it will print the ADS's register values
  if (adc.begin())
  {
    numberOfChannels = adc.getNumberOfChannels();
    if (verbosity)
    {
      Serial.print("ADS119X Conected");
      Serial.println("");
      displayRegs();
      Serial.print("Num Channels: ");
      Serial.print(numberOfChannels);
      Serial.println();
    }
  }
  else
  {
    Serial.print("ADS119X not started");
  }

  // Stop continuous conversion, and send commands to configure
  adc.sendCommand(ADS119X_CMD_SDATAC);
  adc.setAllChannelGain(ADS119X_CHnSET_GAIN_12);
  adc.setAllChannelMux(ADS119X_CHnSET_MUX_NORMAL);
  adc.setDataRate(ADS119X_DRATE_1000SPS);

  // RLD --> RLD1P, RLD1N, RLD2P
  adc.WREG(ADS119X_ADD_RLD_SENSP, 0x03);
  adc.WREG(ADS119X_ADD_RLD_SENSN, 0x01);
  adc.WREG(ADS119X_ADD_CONFIG3, adc.getRegister(ADS119X_ADD_CONFIG3) | ADS119X_NOT_PD_RLD_MASK | ADS119X_RLDREF_INT_MASK);

  displayRegs();
}

void loop()
{
  // If packet received...
  int packetSize = UDP.parsePacket();
  if (packetSize)
  {
    memset(&packet, 0, sizeof(packet));
    int len = UDP.read(packet, 255);
    if (len > 0)
    {
      switch (packet[0])
      {
      case 's':
        Serial.printf("Received message: %s\n", packet);
        sendUdp = true;
        currentCycle = 0;
        remoteIp = UDP.remoteIP();
        remotePort = UDP.remotePort();
        adc.sendCommand(ADS119X_CMD_SDATAC);
        if (len == 1 || handleStartMessage(len))
        {
          Serial.println("Start sending");
          displayRegs();
          adc.sendCommand(ADS119X_CMD_RDATAC);
        }
        else
        {
          Serial.println("Packet invalid!");
        }
        break;
      case 'f':
        Serial.println("Stop sending");
        sendUdp = false;
        adc.sendCommand(ADS119X_CMD_SDATAC);
        break;
      default:
        break;
      }
    }
  }

  // Check if the ADC conversion data is ready
  if (sendUdp)
  {
    dataReady = adc.isDRDY();

    if (!prev_dataReady && dataReady)
    {
      elapsed = micros() - elapsed;
      // if (elapsed > 2500)
      // {
      //   Serial.println(elapsed);
      // }
      elapsed = micros();
      adc.readChannelData();
      // printStatus();
      // printData();
      handleData();
    }
    prev_dataReady = dataReady;
  }
}
