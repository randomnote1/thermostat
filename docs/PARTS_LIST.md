# Raspberry Pi Thermostat - Parts Shopping List

## Where to Buy

Most parts available from:
- Amazon
- DigiKey
- Mouser
- Adafruit
- SparkFun
- AliExpress (cheaper, longer shipping)

## Core Components

### Raspberry Pi & Storage
- [ ] **Raspberry Pi 3B** (already owned)
- [ ] **SanDisk Ultra 16GB microSD** (~$8)
  - Amazon: B073JYVKNX
  - Alternative: Any Class 10 microSD, 16GB+

**Connecting Thermostat Wire to Pi:**

You need to connect the 22/3 thermostat wire to GPIO pins. Two options:

**Option 1: GPIO Screw Terminal Board (RECOMMENDED - Most Secure)**
- [ ] **GPIO Screw Terminal Breakout** (~$10-15) **REQUIRED**
  - Amazon: Search "Raspberry Pi GPIO screw terminal"
  - Look for boards with **stackable/extra-tall headers** (allows e-ink HAT on top)
  - Example: "Raspberry Pi Screw Terminal Breakout Board" or "GPIO Terminal Block Shield"
  - Provides secure screw terminals for solid thermostat wire
  - Professional, permanent connection
  
**Stacking with E-ink Display HAT:**
Two ways to use both:
1. **Buy GPIO board with stackable headers** - E-ink HAT mounts on top
2. **Use ribbon cable breakout** - GPIO board sits beside Pi instead of on top
   - Example: Adafruit GPIO Reference Board with ribbon cable (~$10)

**Wiring at screw terminals:**
- Red wire → 3.3V terminal
- White wire → GPIO 4 terminal
- Blue wire → GND terminal
- 4.7kΩ resistor → Between 3.3V and GPIO 4 terminals

**Option 2: Use Wago Connectors + Jumper Wires (Alternative)**
- Use 3 Wago connectors (in parts list below)
- Connect thermostat wire to female-to-female jumper wires (in parts list below)
- Plug jumpers onto GPIO header (or top of e-ink HAT)
- ✅ No HAT stacking issues
- ⚠️ Less secure connection (may need hot glue)

### Display
- [ ] **Waveshare 2.13" E-Ink Display HAT** (~$20)
  - Amazon: B07P6NPZGN (2.13inch e-Paper HAT)
  - Alternative: Waveshare 2.7" for larger display (~$25)
  - Must be HAT version (fits directly on GPIO)

### Temperature Sensors (Option A - RECOMMENDED)
- [ ] **DS18B20 Digital Temperature Sensors**
  
  **Option A1: Non-Waterproof TO-92 Package (Best for indoor wall mounting)**
  - **Amazon**: Search "DS18B20 TO-92" or "DS18B20 transistor"
    - Example listings: Look for "10pcs DS18B20" or "DS18B20 Temperature Sensor TO-92"
    - Price: ~$8-15 for pack of 10
  - **DigiKey**: DS18B20+ (Part #: DS18B20+-ND) - $4.26 each, more reliable
  - **Mouser**: DS18B20+ (Part #: 700-DS18B20+) - $4.15 each
  - **AliExpress**: Search "DS18B20 TO-92" - $5-8 for 10pcs (2-4 week shipping)
  - Small transistor-like component with 3 wire leads
  - Perfect for mounting behind wall plates
  - Smaller and cheaper than waterproof version
  - Easier to run wires through walls
  - **Recommended for this project**
  - **Note**: Verify you're getting genuine Maxim/Dallas chips (many counterfeits exist)
  
  **Option A2: Waterproof Sensors (Overkill for indoor use)**
  - Amazon: B012C597T0 (Pack of 5-6) (~$25)
  - Stainless steel probe with 3m cable
  - Unnecessary for dry indoor environments
  - Bulkier and harder to mount
  - More expensive
  - Good if you need outdoor/moisture sensing
  
  **Quantity needed:** 6 sensors (one per room)
  
  **Wiring for TO-92 sensors:**
  - Sensors connect to shared 3-wire bus (1-Wire protocol)
  - All sensors share same wires - no home runs needed!
  - Use CAT5e cable for bus wiring (recommended)
  - **Connection options at each sensor:**
    - **Wago lever connectors** (RECOMMENDED - no soldering!)
    - Solder connections with heat shrink tubing
    - Screw terminal blocks

### Temperature Sensors (Option B - Advanced)
- [ ] **BME280 I2C Sensors (Pack of 5)** (~$30)
  - Amazon: B07KR24P6P
- [ ] **TCA9548A I2C Multiplexer** (~$8)
  - Amazon: B07Y8J8P1J

### Sensor Mounting Hardware
- [ ] **Wall Plates - Choose One Option:**
  
  **Option 1: Vented Wall Plates (BEST - Solves air circulation issue!)**
  - Amazon: Search "vented wall plate" or "ventilated outlet cover"
  - Example: "Cable wall plate with brush insert" - has natural gaps
  - Example: "Louvered wall plate" - has vent slots
  - Price: ~$3-5 each
  - Perfect for temperature sensors - allows air circulation
  - Professional appearance
  - No drilling needed
  - **Recommended choice**
  
  **Option 2: Blank Wall Plates (Traditional)**
  - Amazon: B07VQKZG9K (white) or B07VQKQJXC (almond) - Pack of 5-10 (~$10)
  - Match your existing switch plates
  - Will need to add vent holes if air circulation is concern
  
- [ ] **Keystone Jack Wall Plates** (~$8)
  - Amazon: B0744KXM72 (1-port keystone)
  - Alternative: Professional looking sensor outlets
- [ ] **Cable Entry Grommets (3/8" or 1/2")** (~$6)
  - Amazon: B07VFC4QQT
  - For drilling holes in wall plates for sensor wires
- [ ] **Old Work Electrical Boxes (Single Gang, Pack of 5)** (~$15)
  - Amazon: B000BQS3KA (Carlon B114R)
  - Optional: For recessed mounting in drywall
- [ ] **Surface Mount Boxes (Single Gang, Pack of 5)** (~$12)
  - Amazon: B000HEL3QK
  - For mounting on wall surface without cutting drywall
- [ ] **Cable Staples or Clips** (~$5)
  - Amazon: B07DFKR2S7 (cable clips)
  - For securing sensor wires along baseboards/walls

### HVAC Control
- [ ] **4-Channel Relay Module (5V, optocoupler isolated)** (~$10)
  - Amazon: B00KTEN3TM (SainSmart)
  - Must support 24VAC @ 1A minimum
  - **IMPORTANT**: Must be optocoupler isolated for safety

### Power Supply
- [ ] **24VAC to 5VDC Converter** (~$12)
  - Option 1: MEAN WELL IRM-03-5 (DigiKey: 1866-3169-ND)
  - Option 2: Hi-Link HLK-PM01 (~$3 on AliExpress)
  - Must be isolated, 2.5A+ recommended

### Electronics Components
- [ ] **4.7kΩ Resistor (1/4W, pack of 10)** (~$2)
  - Any electronics supplier
  - Only ONE needed for all DS18B20 sensors (at Raspberry Pi)
- [ ] **Wago 221-413 Lever Connectors (50-pack)** (~$25) **RECOMMENDED**
  - Amazon: B08XXWW46C
  - 3-port lever wire connectors
  - For connecting sensors to bus WITHOUT SOLDERING
  - Need 3 per sensor location (18 total for 6 sensors)
  - Professional grade, removable, transparent housing
  - Works with 22-24 AWG solid or stranded wire
  - **Alternative**: 3-position screw terminal blocks (~$8 for 10)
- [ ] **Terminal Blocks (2-position and 3-position)** (~$8)
  - Amazon: B07C69M2KW (pack)
  - For secure HVAC wire connections
- [ ] **Jumper Wires Female-to-Female (40 pieces)** (~$5)
  - Amazon: B07GD2BWPY
  - For prototyping connections

### Enclosure & Mounting
- [ ] **Project Box/Enclosure** (~$15)
  - Amazon: B07Q14K7YZ (Hammond 1591XXBK)
  - Must fit: Pi (85x56mm), relay board, power supply
  - Recommended: 150x100x60mm or larger
- [ ] **Standoffs/Spacers for Pi** (~$5)
  - Amazon: B07CLDGFQT
  - M2.5 size for Raspberry Pi

### Wiring
- [ ] **22/3 Thermostat Wire (100-250ft)** (~$15-25) **RECOMMENDED**
  - Amazon: Search "22/3 thermostat wire"
  - Home Depot/Lowe's: Coleman or Southwire brand
  - Example: Southwire 64169644 (250ft) - ~$25
  - 22 AWG, 3-conductor (Red, White, Blue/Green)
  - Perfect for DS18B20 1-Wire bus
  - Solid copper core (better than stranded for 1-Wire)
  - Less bulk than CAT5e, easier to fish through walls
  - **Alternative**: CAT5e cable (~$15 for 100ft) - use 3 of 8 conductors
  - **Alternative**: 18/3 low voltage cable (~$25) - heavier gauge for long runs

### Optional but Recommended
- [ ] **Heat Shrink Tubing** (~$8)
  - Amazon: B084GDLSCK
  - Only needed if soldering connections (skip if using Wago connectors)
- [ ] **Electrical Tape** (~$5)
  - For labeling wires and sensors
- [ ] **Wire Labels/Tape** (~$6)
  - For identifying sensor IDs

## Tools You'll Need

### Required Tools
- [ ] Phillips screwdriver
- [ ] Wire strippers
- [ ] **Multimeter** (~$15-25) **ESSENTIAL for safety!**
  - Amazon: B00TLB9KQ0 (Klein Tools)
  - For testing voltages and continuity
- [ ] Drill (if mounting to wall)

### Nice to Have
- [ ] Soldering iron (only if not using Wago connectors)
- [ ] Heat gun (for heat shrink if soldering)
- [ ] Label maker
- [ ] Voltage tester

## Part Alternatives by Budget

### Budget Build (~$65)
- Skip enclosure (use cardboard box temporarily)
- Use cheaper DS18B20 sensors from AliExpress (~$10 for 5)
- Simple sensor mounting: tape or small adhesive hooks
- Screw terminal blocks instead of Wago connectors (~$8)
- Generic relay board from AliExpress (~$3)
- Hi-Link power supply (~$3)
- Generic microSD card

### Standard Build (~$145)
Prices listed above

### Premium Build (~$220)
- Waveshare 2.7" or 4.2" display ($25-40)
- BME280 sensors for humidity monitoring
- High-quality MEAN WELL power supply
- Professional enclosure with DIN rail mounts
- Backup battery (UPS HAT) for Pi (~$25)

## Where to Save Money

1. **Buy sensor packs**: 5-10 pack cheaper per sensor
2. **AliExpress**: Save 50%+ but wait 2-4 weeks shipping
3. **Use existing parts**:
   - Old Ethernet cable for sensor wiring
   - Scrap project boxes
   - Resistors/jumper wires from old electronics
4. **Skip the enclosure initially**: Test everything first

## What NOT to Cheap Out On

1. **Power supply**: MUST be isolated and rated for HVAC voltage
2. **Relay board**: MUST be optocoupler isolated for safety
3. **Multimeter**: Essential for safe HVAC testing
4. **MicroSD card**: Use reputable brand (SanDisk, Samsung)

## Shipping & Availability Notes

- **Amazon Prime**: Most parts, 1-2 day shipping
- **DigiKey/Mouser**: Professional components, fast shipping, no free shipping under $50
- **AliExpress**: Cheapest but 2-4 weeks from China
- **Local electronics store**: Resistors, wire, basic components

## Purchase Priority

### Order First (longest lead time)
1. E-ink display (sometimes out of stock)
2. DS18B20 sensors (if ordering from overseas)
3. Relay board

### Order Second
4. Power supply
5. MicroSD card
6. Enclosure

### Buy Locally (when ready to assemble)
7. Wire, terminal blocks
8. Resistors, jumper wires

## Total Cost Summary

| Component Category | Budget | Standard | Premium |
|-------------------|--------|----------|---------|
| Display           | $15    | $20      | $35     |
| Sensors           | $10    | $25      | $35     |
| Sensor Mounting   | $5     | $25      | $40     |
| Relay Board       | $3     | $10      | $15     |
| Power Supply      | $3     | $12      | $15     |
| Storage           | $6     | $8       | $12     |
| GPIO Breakout     | $0     | $12      | $15     |
| Electronics       | $10    | $40      | $45     |
| Enclosure         | $0     | $15      | $25     |
| Wiring/Misc       | $10    | $15      | $20     |
| **TOTAL**         | **$62**| **$182** | **$257**|

*Excludes Raspberry Pi 3B (already owned)*

## Notes

- Prices are approximate (as of Dec 2024)
- Add 10-20% for shipping if not using Prime
- Buy extra sensors (one spare) in case of failure
- Consider buying a second SD card as backup
- Save all receipts for warranty purposes

## Pre-Purchase Checklist

Before ordering, verify:
- [ ] Your HVAC system voltage (should be 24VAC, check with multimeter)
- [ ] Available HVAC wires (need at least R, C, W, Y, G)
- [ ] Number of rooms to monitor (= number of sensors needed)
- [ ] Distance from thermostat location to furthest room
- [ ] Wall mounting location (near existing thermostat for easy wiring)
