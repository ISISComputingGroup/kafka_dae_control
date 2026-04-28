# Local development

To develop locally, set up a venv using `uv`:

`uv pip install -e .[dev]`

## Running locally

In the same virtual environment configured above, set these environment variables: 
- `EPICS_PVAS_INTF_ADDR_LIST` to the IP you want to bind to for the PVA server
- `EPICS_CA_ADDR_LIST` (and probably `EPICS_CA_AUTO_ADDR_LIST=NO`) to the instrument's CA gateway - this is used for picking up the block names

```kdaectrl --confg config.toml --log-level DEBUG```

An example `config.toml` is provided in the root of this repository; this will need to be modified for your machine.

## Configuring the hardware

TODO - need input from DSG to get this correct really. 

## Send/read arbitrary data to the hardware

The streaming control board accepts reads and writes. 

The format for reading is a 32 bit integer of the address to read, then a 16 bit integer of the block size. 
it will return a 32 bit address, 16 bit block size and 32 bit data

It's worth noting that the 16 bit block size is the number of 32 bit "words" you are reading from or writing to - _not_ the number of bytes. 

The format for writing is a 32 bit integer of the address to read, a 16 bit integer of the block size, and then a 32 bit integer containing the data to write. 
