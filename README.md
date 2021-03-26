# ASPIF
### Arduino SPI (Flash) Flasher

This project came to fruition because I needed a quick way to revive a couple of bricked PC motherboards with corrupted BIOSes.

#### Features:
- Read information from a connected flash chip (JEDEC ID, Manufacturer ID, Capacity).
- Dump data to PC
- Flash new data
- Erase entire chip (required before flashing new data)

ASPIF consists of Arduino sketch and a client application written in python.

#### Rationale behind writing yet another flasher "suite":
Other projects weren't working on my Itead Leonardo compatible board and debugging those issues did not seem appealing to me so I decided to have some fun on my own.

## Hardware:
As of now the only Arduino board I tested this on is **Itead Leonardo**,<br>
an **Arduino Leonardo** compatible board containing ATmega32u4 microcontroller.

It should work on other Arduino boards with little or no modification.

Make sure to use **3.3V logic** microcontrollers as flash chips are **NOT 5V compatible**.

##### Connection diagram:
| SPI flash  | Arduino|
| ------------ | ------------ |
|1. CS  | 6 |
|2. SO  | MISO |
|3. WP | 4 |
|4. VSS | GND |
|5. SI  | MOSI |
|6. SCLK | SCK |
|7. HOLD | 5 |
|8. VCC | 3.3V |

##### Compatible chips:
As of now I tested this suite with **Winbond 25Q64FVSIG** and **GD25Q32C** chips.

## Software:
#### Microcontroller:
Use a provided "ASPIF.ino" sketch and upload it to your Arduino devboard.

#### PC:
To use ASPIF PC client you need to have python 3 installed.<br>
Windows, Linux and macOS operating systems are supported.

You also need pyserial which can be installed using the following command:<br>
`python3 -m pip install pyserial`

After installation run `python3 ASPIF.py --help` to see help screen.
