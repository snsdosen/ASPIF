//ASPIF - Arduino SPI Flasher
//snsdosen 2019
//This project is used to read and write data to various SPI flash chips

#include <SPI.h>

//Hardware specific setup
#define WP_PIN      4       //Write Protect
#define HOLD_PIN    5       //Hold
#define CS_PIN      6       //Select
#define PAGE_SIZE   256     //Default page size, change if needed

//Commands
#define CMD_IDENTIFIER  'X'   //Get identifier
#define CMD_VERSION     'V'   //Get firmware version
#define CMD_READ        'R'   //Read from flash
#define CMD_WRITE       'W'   //Write to flash
#define CMD_ERASE       'E'   //Erase flash
#define CMD_INFO        'I'   //Info of the connected flash
#define CMD_BUFF_PUSH   'H'   //Push data from client to buffer
#define CMD_BUFF_PULL   'L'   //Pull data from buffer to client

//Info subcommands
#define INFO_JEDEC      'J'   //Get JEDEC ID
#define INFO_MAN_ID     'M'   //Get Manufacturer ID
#define INFO_CAPACITY   'C'   //Get flash capacity

//Responses
#define RES_OK          'K'   //Positive response
#define RES_ERR         'E'   //Negative response
#define RES_CONTINUE    'C'   //Continue feeding the input buffer
#define RES_BUSY        'B'   //Busy keep alive

//Info
#define IDENTIFIER      "ASPIF"       //Arduino SPI (Flash) Flasher
#define VERSION         "0.1 beta"

//SPI opcodes
#define WRITE_ENABLE                0x06
#define VOLATILE_SR_WRITE_ENABLE    0x50
#define WRITE_DISABLE               0x04
#define READ_STATUS_REGISTER_1      0x05
#define READ_STATUS_REGISTER_2      0x35
#define WRITE_STATUS_REGISTER       0x01
#define PAGE_PROGRAM                0x02
#define SECTOR_ERASE_4KB            0x20
#define SECTOR_ERASE_32KB           0x52
#define SECTOR_ERASE_64KB           0xD8
#define CHIP_ERASE_1                0xC7
#define CHIP_ERASE_2                0x60
#define ERASE_PROGRAM_SUSPEND       0x75
#define ERASE_PROGRAM_RESUME        0x7A
#define POWER_DOWN                  0xB9
#define READ_DATA                   0x03
#define FAST_READ                   0x0B
#define RELEASE_POWERDOWN_ID        0xAB
#define MANUFACTURER_ID             0x90
#define JEDEC_ID                    0x9F
#define READ_UNIQUE_ID              0x4B
#define READ_SFDP_REGISTER          0x5A
#define ERASE_SECURITY_REGISTERS    0x44
#define PROGRAM_SECURITY_REGISTERS  0x42
#define READ_SECURITY_REGISTERS     0x48
#define ENABLE_QPI                  0x38
#define ENABLE_RESET                0x66
#define RESET                       0x99

byte cmd = 0;
byte subCmd = 0;

uint32_t currentAddress = 0;   //Current read or write address
byte buffer[PAGE_SIZE];

//Function defines
void waitSerial(int bytesToWait);
void selectLine();
void deselectLine();
uint16_t getManID();
uint32_t getJEDECID();
uint32_t getCapacity();
void readByteArray(uint32_t dataAddress, byte* dataBuffer);
void writeByteArray(uint32_t dataAddress, byte* dataBuffer);
void waitWriteEnable();
void eraseChip();

//Activate flash chip
void selectLine(){
  digitalWrite(CS_PIN, LOW);
}

//Deactivate flash chip
void deselectLine(){
  digitalWrite(CS_PIN, HIGH);
}

uint16_t getManID(){
  uint16_t ManufacturerID = 0;
  selectLine();

  SPI.transfer(MANUFACTURER_ID);
  SPI.transfer(0xFF);
  SPI.transfer(0xFF);
  SPI.transfer(0x0);
  ManufacturerID = SPI.transfer(0xFF) << 8 | SPI.transfer(0xFF);
  
  deselectLine();
  return ManufacturerID;
}

uint32_t getJEDECID(){
  uint32_t jedecID = 0;
  selectLine();

  SPI.transfer(JEDEC_ID);

  jedecID = ((uint32_t) SPI.transfer(0)) << 16;
  jedecID |= ((uint32_t)(SPI.transfer(0)) << 8);
  jedecID |= (SPI.transfer(0));
  
  SPI.transfer(0);
  SPI.transfer(0);

  
  deselectLine();
  return jedecID;
}


uint32_t getCapacity(){
  uint32_t capacity = 0;
  selectLine();

  //Capacity is contained in the JEDEC ID
  SPI.transfer(JEDEC_ID);

  SPI.transfer(0);
  SPI.transfer(0);
  capacity = ((uint32_t) 1) << SPI.transfer(0);
  
  SPI.transfer(0);
  SPI.transfer(0);

  deselectLine();
  return capacity;
}

//Read page from flash to byte array
void readByteArray(uint32_t dataAddress, byte* dataBuffer){
  uint16_t bufferIndex = 0;
  dataAddress *= PAGE_SIZE;

  selectLine();

  SPI.transfer(READ_DATA);
  SPI.transfer((dataAddress >> 16) & 0xFF);
  SPI.transfer((dataAddress >> 8) & 0xFF);
  SPI.transfer(dataAddress & 0xFF);

  for(bufferIndex = 0; bufferIndex < PAGE_SIZE; bufferIndex++) {
    dataBuffer[bufferIndex] = SPI.transfer(0xff);
  }

  deselectLine();
}

//Write page to flash from byte array
void writeByteArray(uint32_t dataAddress, byte* dataBuffer){
  uint16_t bufferIndex = 0;
  dataAddress *= PAGE_SIZE;

  //Enable write
  selectLine();
  SPI.transfer(WRITE_ENABLE);
  deselectLine();

  delay(10);

  selectLine();

  SPI.transfer(PAGE_PROGRAM);
  SPI.transfer((dataAddress >> 16) & 0xFF);
  SPI.transfer((dataAddress >> 8) & 0xFF);
  SPI.transfer(dataAddress & 0xFF);

  for(bufferIndex = 0; bufferIndex < PAGE_SIZE; bufferIndex++) {
     SPI.transfer(dataBuffer[bufferIndex]);
  }

  deselectLine();

  delay(1);

  waitWriteEnable();
}

void waitWriteEnable(){
  uint8_t statreg = 0x1;

  while((statreg & 0x1) == 0x1) {
    // Wait for the chip
    selectLine();
    SPI.transfer(READ_STATUS_REGISTER_1);
    statreg = SPI.transfer(READ_STATUS_REGISTER_1);
    deselectLine();
  }
}

//Wait for serial buffer to fill with expected data
void waitSerial(int bytesToWait){
  while(Serial.available() < bytesToWait);
}

//Erase entire flash chip
void eraseChip(){
  uint8_t statreg = 0x1;

  //Enable write
  selectLine();
  SPI.transfer(WRITE_ENABLE);
  deselectLine();

  delay(10);
  
  selectLine();
  SPI.transfer(CHIP_ERASE_2);
  deselectLine();

  while((statreg & 0x1) == 0x1) {
    selectLine();
    SPI.transfer(READ_STATUS_REGISTER_1);
    statreg = SPI.transfer(READ_STATUS_REGISTER_1);
    deselectLine();
    delay(1000);
    Serial.println(RES_BUSY);
  }
  
}

void setup() {
  Serial.begin(115200);
  while(!Serial);

  SPISettings spiSettings(F_CPU / 4, MSBFIRST, SPI_MODE0);
  SPI.begin();
  SPI.beginTransaction(spiSettings);
  pinMode(CS_PIN, OUTPUT);
  digitalWrite(CS_PIN, HIGH); // disable flash device

  pinMode(WP_PIN, OUTPUT);
  digitalWrite(WP_PIN, HIGH);

  pinMode(HOLD_PIN, OUTPUT);
  digitalWrite(HOLD_PIN, HIGH);
  
  delay(10);
}

void loop() {
  if(Serial.available() > 0){
    cmd = Serial.read();

    switch(cmd){
      case CMD_IDENTIFIER:
        Serial.println(IDENTIFIER);
        break;

      case CMD_VERSION:
        Serial.println(VERSION);
        break;

      case CMD_READ:
        waitSerial(2);
        currentAddress = Serial.read() << 8 | Serial.read();
        readByteArray(currentAddress, buffer);
        Serial.println(CMD_READ);   //Acknowledge
        break;

      case CMD_WRITE:
        waitSerial(2);
        currentAddress = Serial.read() << 8 | Serial.read();

        //Write data
        writeByteArray(currentAddress, buffer);
        Serial.println(CMD_WRITE);   //Acknowledge
        break;

      case CMD_ERASE:
          eraseChip();
          Serial.println(CMD_ERASE);   //Acknowledge
        break;

      case CMD_BUFF_PUSH:
        for(int i = 0; i < 8; i++){
            for(int j = 0; j < 32; j++)
            {
              waitSerial(1);
              buffer[(i * 32) + j] = Serial.read();
            }
            Serial.println(RES_CONTINUE);   //Clear to send rest of the data
        }
        break;

      case CMD_BUFF_PULL:
        for(int i = 0; i < PAGE_SIZE; i++){
          Serial.write(buffer[i]);
        }
        break;

      case CMD_INFO:
        waitSerial(1);
        subCmd = Serial.read();

        switch(subCmd){
          case INFO_JEDEC:
            Serial.print("0x");
            Serial.println(getJEDECID(), HEX);
            break;

          case INFO_MAN_ID:
            Serial.print("0x");
            Serial.println(getManID(), HEX);
            break;

          case INFO_CAPACITY:
            Serial.println(getCapacity());
            break;
        }
        
        break;
    }
    
  }
}
