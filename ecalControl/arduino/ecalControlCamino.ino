
#include "Camino4809.h"
#include "arduino.h"

#define Pin_ECalD0 9
#define Pin_ECalD1 14
#define Pin_ECalD2 8
#define Pin_ECalD3 15
#define Pin_ECalD4 7
#define Pin_ECalD5 16
#define Pin_ECalD6 6
#define Pin_ECalD7 17

#define Pin_ECalA0 5
#define Pin_ECalA1 18
#define Pin_ECalA2 4

#define Pin_ECalOEn 3
#define Pin_ECalMRn 2

#define Pin_ECalENn 19
#define Pin_ECalWEn 20


#define Pin_MUX_Flash_ADR_0_7 2
#define Pin_MUX_Flash_ADR_8_15 3
#define Pin_MUX_Flash_ADR_16_17 4

#define Pin_MUX_Gates_1_8 0
#define Pin_MUX_Gates_9_16 1

#define Pin_MUX_Flash_CEn 7

#define Pin_Prsnt_Relay 21
#define Pin_5V_detect 1
#define Pin_Pulldown 0

bool pins_enabled;

void enable_pins()
{
  pins_enabled = true;

  set_data(0);
  set_mux_address(0);
  latch();
  clear_flash_OE();
  pulse_latch_clear();
  disable_presence_detect();

  pinMode(Pin_ECalD0,OUTPUT);
  pinMode(Pin_ECalD1,OUTPUT);
  pinMode(Pin_ECalD2,OUTPUT);
  pinMode(Pin_ECalD3,OUTPUT);
  pinMode(Pin_ECalD4,OUTPUT);
  pinMode(Pin_ECalD5,OUTPUT);
  pinMode(Pin_ECalD6,OUTPUT);
  pinMode(Pin_ECalD7,OUTPUT);

  pinMode(Pin_ECalA0,OUTPUT);
  pinMode(Pin_ECalA1,OUTPUT);
  pinMode(Pin_ECalA2,OUTPUT);
  pinMode(Pin_ECalENn,OUTPUT);
  pinMode(Pin_ECalOEn,OUTPUT);
  pinMode(Pin_ECalMRn,OUTPUT);

}

void disable_pins()
{
  pinMode(Pin_ECalD0,INPUT);
  pinMode(Pin_ECalD1,INPUT);
  pinMode(Pin_ECalD2,INPUT);
  pinMode(Pin_ECalD3,INPUT);
  pinMode(Pin_ECalD4,INPUT);
  pinMode(Pin_ECalD5,INPUT);
  pinMode(Pin_ECalD6,INPUT);
  pinMode(Pin_ECalD7,INPUT);

  pinMode(Pin_ECalA0,INPUT);
  pinMode(Pin_ECalA1,INPUT);
  pinMode(Pin_ECalA2,INPUT);
  pinMode(Pin_ECalENn,INPUT);
  pinMode(Pin_ECalOEn,INPUT);
  pinMode(Pin_ECalMRn,INPUT);

  pins_enabled = false;
}

void reset()
{
  digitalWrite(Pin_ECalMRn, LOW);
  delayMicroseconds(10);
  digitalWrite(Pin_ECalMRn, HIGH); 
  delayMicroseconds(10);
}

void latch()
{
  digitalWrite(Pin_ECalENn, LOW);
  delayMicroseconds(1);
  digitalWrite(Pin_ECalENn, HIGH); 
  delayMicroseconds(1);
}

void set_mux_address(byte addr)
{
  digitalWrite(Pin_ECalA0, addr & 1 ? HIGH : LOW);
  digitalWrite(Pin_ECalA1, addr & 2 ? HIGH : LOW);
  digitalWrite(Pin_ECalA2, addr & 4 ? HIGH : LOW);
}

void set_data(byte data)
{
  digitalWrite(Pin_ECalD0, data & 1 ? HIGH : LOW);
  digitalWrite(Pin_ECalD1, data & 2 ? HIGH : LOW);
  digitalWrite(Pin_ECalD2, data & 4 ? HIGH : LOW);
  digitalWrite(Pin_ECalD3, data & 8 ? HIGH : LOW);
  digitalWrite(Pin_ECalD4, data & 16 ? HIGH : LOW);
  digitalWrite(Pin_ECalD5, data & 32 ? HIGH : LOW);
  digitalWrite(Pin_ECalD6, data & 64 ? HIGH : LOW);
  digitalWrite(Pin_ECalD7, data & 128 ? HIGH : LOW);
}

byte get_data()
{
  byte data = 0;

  if (digitalRead(Pin_ECalD0) == HIGH) { data += 1; }
  if (digitalRead(Pin_ECalD1) == HIGH) { data += 2; }
  if (digitalRead(Pin_ECalD2) == HIGH) { data += 4; }
  if (digitalRead(Pin_ECalD3) == HIGH) { data += 8; }
  if (digitalRead(Pin_ECalD4) == HIGH) { data += 16; }
  if (digitalRead(Pin_ECalD5) == HIGH) { data += 32; }
  if (digitalRead(Pin_ECalD6) == HIGH) { data += 64; }
  if (digitalRead(Pin_ECalD7) == HIGH) { data += 128; }

  return data;
}

void enable_presence_detect()
{
  digitalWrite(Pin_Prsnt_Relay, HIGH);
}
void disable_presence_detect()
{
  digitalWrite(Pin_Prsnt_Relay, LOW);
}

void set_flash_OE()
{
  digitalWrite(Pin_ECalOEn, LOW);
}
void clear_flash_OE()
{
  digitalWrite(Pin_ECalOEn, HIGH);
}

void pulse_latch_clear()
{
  digitalWrite(Pin_ECalMRn, LOW);
  digitalWrite(Pin_ECalMRn, HIGH);
}

bool is_5V_supply_present()
{
  return digitalRead(Pin_5V_detect) == HIGH;
}

void set_gates(word gates)
{
  set_data(0x00FF & gates);
  set_mux_address(Pin_MUX_Gates_1_8);
  latch();

  set_data((0xFF00 & gates) >> 8);
  set_mux_address(Pin_MUX_Gates_9_16);
  latch();
}

byte read_Flash(unsigned long address)
{
  byte data = 0;

  set_data((0x000000FF & address) >> 0);
  set_mux_address(Pin_MUX_Flash_ADR_0_7);
  latch();

  set_data((0x0000FF00 & address) >> 8);
  set_mux_address(Pin_MUX_Flash_ADR_8_15);
  latch();

  set_data((0x00030000 & address) >> 16);
  set_mux_address(Pin_MUX_Flash_ADR_16_17);
  latch();

  pinMode(Pin_ECalD0,INPUT);
  pinMode(Pin_ECalD1,INPUT);
  pinMode(Pin_ECalD2,INPUT);
  pinMode(Pin_ECalD3,INPUT);
  pinMode(Pin_ECalD4,INPUT);
  pinMode(Pin_ECalD5,INPUT);
  pinMode(Pin_ECalD6,INPUT);
  pinMode(Pin_ECalD7,INPUT);

  set_mux_address(Pin_MUX_Flash_CEn);
  digitalWrite(Pin_ECalENn, LOW);
  set_flash_OE();
  delayMicroseconds(1);

  data = get_data();

  clear_flash_OE();
  digitalWrite(Pin_ECalENn, HIGH);

  if (pins_enabled)
  {
    pinMode(Pin_ECalD0,OUTPUT);
    pinMode(Pin_ECalD1,OUTPUT);
    pinMode(Pin_ECalD2,OUTPUT);
    pinMode(Pin_ECalD3,OUTPUT);
    pinMode(Pin_ECalD4,OUTPUT);
    pinMode(Pin_ECalD5,OUTPUT);
    pinMode(Pin_ECalD6,OUTPUT);
    pinMode(Pin_ECalD7,OUTPUT);
  }

  return data;
}

word read_FlashW(unsigned long address)
{
  word data;
  data = ((word)(read_Flash(address+1))) << 8;
  data += read_Flash(address);
  return data;
}

unsigned long read_FlashL(unsigned long address)
{
  unsigned long data;
  data = ((unsigned long)read_Flash(address));
  data += ((unsigned long)read_Flash(address+1) << 8);
  data += ((unsigned long)read_Flash(address+2) << 16);
  data += ((unsigned long)read_Flash(address+3) << 24);
  return data;
}

byte read_FlashS(unsigned long address, char* buffer, byte maxLen)
{
  byte data;
  for (byte i = 0; i < maxLen; i++)
  {

    buffer[i] = (char)read_Flash(address + i);
    if (buffer[i] == 255) buffer[i] = 0;
    if (buffer[i] == 0) 
    {
      return i+1;
    }
  }
  buffer[maxLen-1] = 0;
  return maxLen;
}



void setup() {
  // put your setup code here, to run once:


  pins_enabled = false;
  disable_pins();

  //pinMode(Pin_Prsnt_Relay,OUTPUT);
  pinMode(Pin_Pulldown,OUTPUT);
  digitalWrite(Pin_Pulldown,LOW);

  camino.begin(115200);


  //enable_presence_detect();

}

unsigned long lastEepromAddress = 0;

void loop() 
{
}


void resetECal(byte dataLength, byte *dataArray) {
  
  enable_pins();
  reset();

}

void writeByte(byte dataLength, byte *dataArray) {
  if (dataLength =! 2) return; //need 1 bytes MUX address, 1 byte data
    set_data(dataArray[1]);
    set_mux_address(dataArray[0]);
    latch();
}

void readByteFromFlash(byte dataLength, byte *dataArray) {
  if (dataLength =! 3) return; //need 3 bytes address

  unsigned long address = 0;
  memcpy((byte*)&address, dataArray, 3);
  lastEepromAddress = address;
  returns(read_Flash(address));
}


void readNextByteFromFlash(byte dataLength, byte *dataArray) {
  lastEepromAddress++;
  returns(read_Flash(lastEepromAddress));
}



BEGIN_CALLABLES {
  {"resetECal", resetECal},
  {"writeByte", writeByte},
  {"readByteFromFlash", readByteFromFlash},
  {"readNextByteFromFlash", readNextByteFromFlash},
} END_CALLABLES;





