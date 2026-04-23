# Local development

## Running locally

## Configuring the hardware

## Send/read arbitrary data to the hardware

The streaming control board accepts reads and writes. 

The format for reading is a 32 bit integer of the address to read, then a 16 bit integer of the block size. 
it will return a 32 bit address, 16 bit block size and 32 bit data

It's worth noting that the 16 bit block size is the number of 32 bit "words" you are reading from or writing to - _not_ the number of bytes. 

The format for writing is a 32 bit integer of the address to read, a 16 bit integer of the block size, and then a 32 bit integer containing the data to write. 
