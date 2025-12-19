# Sensor Mounting Guide

## Overview

DS18B20 temperature sensors need to be mounted in each room for accurate readings. This guide covers several mounting options from simple to professional.

## Understanding DS18B20 Sensors

**Two Types Available:**

### Type 1: TO-92 Package (Recommended for Indoor Wall Mounting)

The bare DS18B20 looks like a small transistor:
- **Size**: 5mm wide × 3mm thick × 7mm tall (tiny!)
- **Form**: Black plastic component with 3 metal pins
- **Pins**: GND, Data, VDD (typically flat side facing you, left to right)
- **Wires**: You attach your own (22-24 AWG)
- **Cost**: ~$1-2 per sensor

```
    TO-92 Package (front view):
    
         Flat side
    ┌───────────┐
    │ DS18B20   │ ← Black plastic housing
    │           │    ~5mm wide
    └──┬──┬──┬──┘
       │  │  │
       │  │  │  ← Three metal pins
       1  2  3
     GND Data VDD
     
    Side view (actual size):
    ┌───┐
    │  │ ← ~7mm tall
    └┬┬┬┘
     │││
```

**Advantages for wall mounting:**
- ✅ Very small - fits anywhere
- ✅ Can solder directly to thin wires
- ✅ Easy to run through walls (just wires, no bulky probe)
- ✅ Multiple mounting options (tape, hot glue, 3D print holder)
- ✅ Cheaper (~$1 vs ~$5 per sensor)
- ✅ Perfect for dry indoor environments

### Type 2: Waterproof Probe (Original Guide Assumption)

Waterproof sensors have:
- **Stainless steel probe**: 6mm diameter × 30-50mm long cylinder
- **Cable**: Pre-wired 3-conductor cable, 1-10 meters long
- **Heat shrink**: Seals cable to probe
- **Cost**: ~$4-6 per sensor

**Use waterproof ONLY if:**
- Mounting outdoors
- Moisture/humidity present
- Need long pre-made cable runs
- Don't want to solder connections

The waterproof probe needs to be positioned where it can sense room air temperature, while the cable runs back to the Raspberry Pi.

## Important: Cable Routing

**The cable runs THROUGH THE WALL, not through the front of the wall plate!**

**Standard Installation (Using Wall Box):**
```
    Cross-section view:
    
    Room Air              Wall              Inside Wall
    ─────────            ─────              ───────────
    
                    ┌──────────┐
                    │ Wall     │ ← Plate covers box
                    │ Plate    │   (usually NO hole needed)
                    └────┬─────┘
    ─────────────────────┼─────────────────
                    ┌────┴─────┐
                    │  ╭──○──╮ │ ← Probe inside box
                    │  │     │ │   sensing room air
                    │  ╰─────╯ │
                    │          │ ← Wall box
                    │    ║     │
    ─────────────────────║─────────────────
                         ║
                    Cable runs through
                    wall to Pi
```

**How It Actually Works:**

1. **Cable enters wall box** through knockout hole (from inside wall cavity)
2. **Probe sits inside wall box** in room air
3. **Wall plate covers the box** - no hole needed in most cases!
4. **Air circulates naturally** through gaps around plate edges and box knockouts

**When DO You Need a Hole in the Wall Plate?**

Only in these specific cases:

**Case 1: No Wall Box (Direct Surface Mount)**
- Mounting plate directly to wall surface
- Need hole for cable to exit through plate
- Probe hangs behind plate in ~1/4" gap

**Case 2: Probe Protrusion for Better Sensing**
- Want probe to stick through plate into room
- Better air exposure and faster response
- Drill hole sized for probe (1/4")
- Cable still comes through wall box normally

**Case 3: Decorative/Aesthetic Choice**
- Want visible probe for "tech" look
- Intentional design choice

## Wall Box Types Explained

### Low-Voltage Mounting Bracket (Recommended)

**What it is:**
- Plastic frame that mounts in drywall
- NO back or sides (just a frame)
- Wall plate screws to frame
- Open back allows easy cable routing

```
    Side view of low-voltage bracket:
    
    Drywall            Frame mounted in wall
    │                  ┌──────────┐
    │  ┌───────────┼──Tab locks  │
    ├──┤ Frame      │  into drywall │
    │  └───────────┼──────────┘
    │               │
    │               │ ← Open back, no enclosure
    │            ╭──○─╮ ← Probe hangs in wall cavity
                   │    │
                   ╰────╯
                      ║
                   Cable in wall
```

**Advantages:**
- ✅ Perfect for low-voltage applications (sensors, data cables)
- ✅ Very shallow - only 1/2" deep
- ✅ Easy installation (cut hole, push in, tabs grip drywall)
- ✅ Cheap (~$1-2 each)
- ✅ Open back = easy cable access
- ✅ Probe has entire wall cavity for air circulation
- ✅ Code-compliant for low-voltage
- ✅ Looks identical to electrical box when plate installed

**Important Consideration:**
- ⚠️ **Air circulation concern**: With wall plate covering the opening, room air must circulate through gaps around plate edges to reach the sensor
- ⚠️ Sensor measures wall cavity temperature, which may differ slightly from room temperature
- ⚠️ Best for interior walls (not exterior walls with insulation)

**Solutions if air circulation is insufficient:**
1. **Add small ventilation holes** in wall plate (drill 2-4 small 1/8" holes)
2. **Use probe protrusion method** (Method B) - probe sticks through plate into room
3. **Use shallow electrical box instead** - provides defined air space that equalizes better
4. **Leave slight gap** at bottom of wall plate (1/16" shim)

**Installation Steps:**
1. Mark location on wall
2. Cut rectangular hole (use bracket as template)
3. Feed cable through wall to hole location
4. Push bracket into hole
5. Tighten mounting screws (tabs bite into drywall)
6. Coil sensor probe in wall cavity behind bracket
7. Attach standard wall plate to bracket

### Full Electrical Box (Alternative)

**What it is:**
- Complete enclosed box with back and sides
- Designed for electrical outlets/switches
- More protection but unnecessary for sensors

```
    Side view of electrical box:
    
    Drywall       Enclosed box
    │             ┌──────────┐
    │  ┌────────┼──────────┤
    ├──┤          │          │
    │  │  ╭──○─╮ │ Enclosed │ ← Probe contained
    │  │  │    │ │   box    │    in box
    │  │  ╰────╯ │          │
    │  │     ║    │          │
    │  └─────┼────┴──────────┘
              ║
           Cable through knockout
```

**When to use:**
- Need structural protection for probe
- Matching existing electrical boxes nearby
- Want more enclosed space
- Mounting in harsh environment (basement, garage)

### Comparison

| Feature | Low-Voltage Bracket | Full Electrical Box |
|---------|-------------------|---------------------|
| **Depth** | 1/2" | 2-3" |
| **Cost** | $1-2 | $2-5 |
| **Installation** | Very easy | Easy |
| **Cutting required** | Small hole | Larger hole |
| **Protection** | Minimal | Full enclosure |
| **Air space** | Wall cavity | Defined box volume |
| **Room air access** | ⚠️ Through plate gaps only | ✅ Better circulation |
| **Best for sensors** | ✅ With ventilation | ✅ Ideal for accuracy |
| **Code compliant** | Low-voltage only | Any use |

**Recommendation for accurate room temperature:**

**Best Option: Full electrical box (old-work style) with blank wall plate**
- Creates defined air space that equalizes with room temperature
- Natural convection through plate edge gaps
- More reliable temperature sensing
- Only slightly more work to install

**Alternative: Low-voltage bracket + ventilation holes in plate**
- Drill 2-4 small holes (1/8") in wall plate for air circulation
- Less professional appearance but functional
- Good for areas where aesthetics less important

**Best for accuracy: Probe protrusion through plate (Method B)**
- Drill hole for probe to stick through into room
- Direct exposure to room air
- Works with either bracket or box

## Wiring TO-92 Sensors

### Materials Needed

- DS18B20 TO-92 sensors (bare component)
- 22 or 24 AWG solid core wire (or stranded)
- Heat shrink tubing (1/8" and 1/4")
- Soldering iron and solder
- Wire strippers
- Multimeter (for testing)

### Wiring Options

**Option 1: Individual Wires (Simple)**
```
    DS18B20 Pins          Wire Colors (suggested)
    ┌───────────┐
    │ DS18B20   │
    └──┬──┬──┬──┘
       │  │  │
       1  2  3
      GND Data VDD
       │  │  │
     Black Yellow Red  ← Run 3 separate wires
                          through wall to Pi
```

**Option 2: CAT5e Cable (Multiple Sensors)**
```
    Using one CAT5e cable for 2 sensors:
    
    Sensor 1:                Sensor 2:
    Pin 1 → Blue/White      Pin 1 → Brown/White
    Pin 2 → Blue            Pin 2 → Brown
    Pin 3 → Orange          Pin 3 → Green
    
    All Data wires (Pin 2) connect to GPIO 4 at Pi
    All GND wires (Pin 1) connect to Ground at Pi
    All VDD wires (Pin 3) connect to 3.3V at Pi
    
    One CAT5e cable = 8 wires = 2 full sensors + 2 wires spare
```

### Soldering Instructions

1. **Prepare wires**
   - Cut wires to needed length (measure wall route)
   - Strip 1/4" (6mm) from one end
   - Tin wire ends with solder

2. **Prepare sensor**
   - Bend pins slightly apart for easier soldering
   - Tin each pin with small amount of solder

3. **Solder connections**
   - Hold wire to pin
   - Touch with soldering iron (~2 seconds)
   - Remove iron, let cool
   - Connection should be shiny, not blobby

4. **Add heat shrink**
   - Slide small heat shrink over each pin connection
   - Heat with heat gun or lighter (carefully)
   - Slide larger heat shrink over entire sensor body
   - Heat to seal

5. **Test before installation**
   ```bash
   # On Raspberry Pi
   ls /sys/bus/w1/devices/
   # Should see: 28-xxxxxxxxxxxx
   
   cat /sys/bus/w1/devices/28-xxxxxxxxxxxx/w1_slave
   # Should show temperature reading
   ```

### Connector Options (No Soldering)

If you don't want to solder:

**Option 1: Screw Terminal Blocks**
- Small 3-position terminal block
- Insert sensor pins and tighten screws
- Attach wires to other side
- More bulky than soldering

**Option 2: Breadboard for Testing**
- Use breadboard and jumper wires
- Test sensor before permanent installation
- Then solder for permanent mount

**Option 3: Pre-wired Sensors**
- Buy TO-92 sensors with wires already attached
- Slightly more expensive
- Amazon: Search "DS18B20 TO-92 pre-wired"

## Air Circulation and Temperature Accuracy

### The Core Problem

When you mount a temperature sensor behind a wall plate, you're creating a potential issue:
- Sensor is behind the wall plate
- Wall plate blocks direct room air flow
- Sensor might measure wall cavity temperature instead of room temperature

### How Much Does This Matter?

**Temperature Difference Factors:**

1. **Interior Wall** (typical installation)
   - Wall cavity temperature ≈ room temperature (within 1-2°F)
   - Wall is same temperature on both sides
   - Adequate for HVAC control

2. **Exterior Wall**
   - Wall cavity can be significantly different from room temp
   - Insulation affects heat transfer
   - **NOT recommended for sensor placement**

3. **Air Circulation Through Gaps**
   - Standard wall plate has small gaps around edges
   - Air slowly circulates through gaps
   - Temperature equalizes over 5-15 minutes
   - May lag behind rapid room temperature changes

### Solutions Ranked by Accuracy

**1. Probe Protrusion (Most Accurate)**
```
Room air → [Probe]═══ → Plate → Box → Cable
           Directly
           exposed
```
- Drill 1/4" hole in plate for probe
- Push probe through into room
- Direct room air contact
- Fastest response (1-2 minutes)
- **Best for critical temperature sensing**

**2. Full Electrical Box with Blank Plate (Good)**
```
Room air ⟷ Plate gaps ⟷ Box air ⟷ Probe
        Natural convection
```
- Box creates defined air volume
- Air circulates through plate edge gaps
- Temperature equalizes within box
- Response time: 3-5 minutes
- **Recommended for standard installation**

**3. Low-Voltage Bracket with Ventilation Holes (Acceptable)**
```
Room air ⟶ Vent holes ⟶ Wall cavity ⟶ Probe
        + Plate gaps
```
- Drill 2-4 small holes (1/8") in wall plate
- Increases air exchange
- Faster equalization than no holes
- Response time: 5-10 minutes
- **Good budget option**

**4. Low-Voltage Bracket with Blank Plate (Least Accurate)**
```
Room air ⟷ Plate gaps ⟷ Wall cavity ⟷ Probe
        Minimal circulation
```
- Relies only on small gaps around plate
- Slower temperature equalization
- May lag room temperature changes
- Response time: 10-15 minutes
- **Use only on interior walls**

### Adding Ventilation Holes to Wall Plate

If using low-voltage bracket or concerned about air circulation:

```
    Wall Plate with Vent Holes:
    
    ┌─────────────┐
    │   ●     ●   │ ← Two 1/8" holes top
    │             │
    │   SENSOR    │
    │             │
    │   ●     ●   │ ← Two 1/8" holes bottom
    └─────────────┘
    
    Allows convection:
    Cold air sinks (bottom holes)
    Warm air rises (top holes)
```

**How to add vent holes:**
1. Mark hole positions (4 corners or top/bottom)
2. Drill 1/8" (3mm) holes
3. Deburr edges with knife
4. Optional: Paint holes to match plate

**Pros:**
- Significantly improves air circulation
- Still looks relatively clean
- Cheap and easy

**Cons:**
- Less professional appearance
- Small holes visible up close
- Dust can enter over time

### Testing Your Installation

To verify sensor is measuring room temperature:

1. **Install sensor** using chosen method
2. **Place reference thermometer** in same room (away from sensor)
3. **Wait 30 minutes** for temperatures to stabilize
4. **Compare readings** - should be within 1-2°F
5. **Test response time**:
   - Change room temperature (open window, adjust thermostat)
   - Time how long sensor takes to respond
   - Should see change within 5-10 minutes

**If sensor reads consistently different:**
- Add ventilation holes to wall plate
- OR: Switch to probe protrusion method
- OR: Use full electrical box instead of bracket

### Final Recommendation

For most accurate and reliable temperature sensing:

**Option A: Full Old-Work Electrical Box (Recommended)**
- Carlon B114R or similar (~$3 each)
- 2-3" deep box
- Blank wall plate (no holes)
- Probe hangs inside box
- Natural air circulation through plate gaps
- Most reliable approach

**Option B: Any Box + Probe Protrusion (Most Accurate)**
- Use either low-voltage bracket or electrical box
- Drill 1/4" hole in wall plate
- Push probe through into room
- Direct room air exposure
- Best accuracy and response time
- Visible probe (aesthetic trade-off)

**Option C: Low-Voltage Bracket + Vent Holes (Budget)**
- Low-voltage bracket (~$1 each)
- Drill 2-4 vent holes (1/8") in wall plate
- Adequate accuracy for HVAC control
- Cheapest option

## Physical Mounting Methods

### Method A1: TO-92 Sensor in Wall Box (BEST - Recommended)

**What you'll mount:**
- Bare DS18B20 TO-92 component with wires soldered to pins
- Sensor mounted inside wall box on small bracket or tape
- Wires run through wall to Pi
- Blank wall plate covers box

**Installation:**
```
    Front View                    Cross-Section
    ┌─────────────┐               
    │             │               Wall
    │   Blank     │               │
    │   Plate     │               ├────────┐
    │  (no hole)  │               │ Plate  │
    │             │               ├────────┤
    └─────────────┘               │  [DS]  │ ← TO-92 sensor
                                  │   ║   │    taped to box
    Clean appearance              │   ║   │ ← Old-work box
                                  │   ║   │
                                  ────║─────
                                      ║
                                  3 wires through wall
```

**Steps:**

1. **Prepare the sensor**
   - Strip 1/4" from three wires (22-24 AWG)
   - Solder wires to DS18B20 pins:
     - Pin 1 (GND) → Black wire
     - Pin 2 (Data) → Yellow/White wire  
     - Pin 3 (VDD) → Red wire
   - Cover connections with heat shrink tubing
   - Test sensor before installation

2. **Install wall box**
   - Old-work electrical box recommended
   - Mount at 4-5 feet height on interior wall
   - Fish wires through wall to box location

3. **Mount sensor in box**
   - **Option 1**: Double-sided foam tape on inside of box
   - **Option 2**: Hot glue to inside of box (non-conductive)
   - **Option 3**: Small plastic standoff or clip
   - Position sensor away from metal box walls
   - Ensure sensor can sense box air (don't bury in insulation)

4. **Route wires**
   - Bring wires through knockout into box
   - Leave 6" service loop
   - Exit through bottom knockout
   - Run to Pi location

5. **Attach wall plate**
   - **Best option**: Vented/brush wall plate (see Wall Plate Options section below)
   - Standard blank plate works but slower temperature response
   - Screw to box mounting holes
   - Done!

## Wall Plate Options for Optimal Air Circulation

### Option 1: Vented/Brush Wall Plate (RECOMMENDED)

**What it is:**
- Wall plate with built-in ventilation openings
- Originally designed for cable pass-through or electronics ventilation
- Perfect for temperature sensor applications

**Types available:**

**A. Cable/Brush Wall Plates**
```
    ┌─────────────┐
    │             │
    │   ▒▒▒▒▒▒▒   │ ← Brush insert allows
    │   ▒▒▒▒▒▒▒   │    air flow while
    │             │    looking clean
    └─────────────┘
```
- Flexible brush bristles in center opening
- Allows excellent air circulation
- Professional cable management appearance
- Search: "brush wall plate" or "cable pass through plate"
- Price: ~$3-5 each
- **Best choice** - combines airflow with clean look

**B. Louvered/Slotted Wall Plates**
```
    ┌─────────────┐
    │ ───────────  │
    │             │ ← Horizontal slots
    │ ───────────  │    for ventilation
    │             │
    │ ───────────  │
    └─────────────┘
```
- Multiple horizontal or vertical slots
- Direct air flow path
- May look slightly industrial
- Search: "louvered wall plate" or "ventilated outlet cover"
- Price: ~$4-6 each

**C. Keystone Jack Plates (with gaps)**
```
    ┌─────────────┐
    │   ┌─────┐   │
    │   │ [K] │   │ ← Keystone opening
    │   └─────┘   │    provides airflow
    │             │
    └─────────────┘
```
- Standard keystone wall plate
- Opening around keystone jack allows air circulation
- Can leave keystone empty or use blank insert with holes
- Search: "keystone wall plate single"
- Price: ~$2-4 each

**Advantages of vented plates:**
- ✅ Solves air circulation issue completely
- ✅ No need to drill your own holes
- ✅ Professional factory finish
- ✅ Better airflow than DIY vent holes
- ✅ Room air reaches sensor easily
- ✅ Temperature accuracy improved
- ✅ Faster response to temperature changes (1-2 min vs 5-10 min)
- ✅ Still looks clean and professional

**Where to find:**
- Amazon: Search "brush wall plate" or "cable wall plate"
- Home Depot/Lowe's: Cable management or low-voltage section
- Electrical supply stores
- Price: $3-6 each (only $2-3 more than blank plates)

### Option 2: Standard Blank Plate (Original Method)

Use blank wall plate with NO modifications:
- Relies on small gaps around plate edges for air circulation
- Works adequately on interior walls
- Slower temperature response (5-10 minutes)
- Good if vented plates unavailable
- Free if you have spare plates

### Option 3: Blank Plate + DIY Vent Holes

Drill your own ventilation holes:
```
    ┌─────────────┐
    │  ●  ●  ●    │
    │             │ ← Multiple small
    │  ●  ●  ●    │    ventilation holes
    │             │
    │  ●  ●  ●    │
    └─────────────┘
```
- 2-4 holes at 1/8" (3mm) diameter
- Top and bottom positions for convection
- Less professional appearance than factory vented
- Good if vented plates unavailable

### Recommendation for This Project

**Use vented/brush wall plates:**
- Only $2-3 more per sensor than blank plates
- Solves the air circulation concern completely
- Professional appearance maintained
- No DIY modifications needed
- Best temperature accuracy and response time

**Where this matters most:**
- Living areas where aesthetics important (use brush plates)
- Bedrooms needing accurate overnight temps
- Rooms where HVAC decisions will be made

**Where blank plates OK:**
- Utility rooms or less visible areas
- Rooms used only for supplemental data

**Advantages:**
- ✅ Smallest, cleanest installation
- ✅ No bulky probe to position
- ✅ Thin wires easy to run through walls
- ✅ Cheap (~$1 per sensor)
- ✅ Sensor can be positioned optimally in box
- ✅ Easy to test/replace
- ✅ Professional appearance
- ✅ Perfect for dry indoor environments

### Method A2: Waterproof Probe in Wall Box (Original Method)

**What you'll mount:****
- Wall box installed in/on wall
- Cable runs through wall to wall box knockout
- Probe hangs inside wall box
- Blank wall plate covers the box (NO hole needed)

**Box Options:**

**Option 1: Old-Work Electrical Box (Full Depth)**
- Standard single-gang electrical box
- ~2-3" depth
- Most protection for probe
- Amazon: B000BQS3KA (Carlon B114R)

**Option 2: Low-Voltage Mounting Bracket/Frame (BEST FOR THIS APPLICATION)**
- Just a plastic frame, NO box enclosure
- ~1/2" depth (very shallow)
- Specifically designed for low-voltage (data, sensors, etc.)
- Cheaper and easier to install
- Adequate space for temperature probe
- Amazon: B001JEOAG8 (Carlon SC100A) or B01MRZ2CHJ (Madison)
- **This is ideal for temperature sensors!**

**Option 3: Surface Mount Box**
- Mounts on wall surface, no cutting
- ~1.5" depth
- Good for finished walls where you can't cut in
- Amazon: B000HEL3QK

**Installation:****
```
    Front View                    Cross-Section
    ┌─────────────┐               
    │             │               Wall
    │   Blank     │               │
    │   Plate     │               ├────────┐
    │  (no hole)  │               │ Plate  │
    │             │               ├────────┤
    └─────────────┘               │ ╭──○─╮ │ ← Probe in box
                                  │ │    │ │
                                  │ ╰────╯ │ ← Wall box
                                  │   ║    │
    Simple and clean!             ────║──────
                                      ║
                                  Cable through wall
```

**Steps:**
1. **Install wall box** (old-work or surface mount)
   - Choose location at 4-5 feet height
   - Mark and cut/mount box
   - Fish cable through wall to box location

2. **Route cable into box**
   - Remove knockout plug from wall box
   - Pull cable through knockout into box
   - Leave 6-12" of cable inside box (service loop)

3. **Position probe**
   - Let probe hang freely inside box
   - Keep probe away from metal box sides
   - Ensure probe can sense room air
   - Coil excess cable neatly

4. **Secure cable**
   - Use small cable tie or velcro strap
   - Don't kink the cable
   - Route remaining cable out through bottom knockout

5. **Attach wall plate**
   - Use standard blank wall plate (no modifications needed!)
   - Screw plate to wall box mounting holes
   - Plate sits flush against wall

**How air circulation works:**
- Wall box has gaps and openings
- Room air circulates through plate edges
- Air inside box equalizes with room temperature
- Probe senses accurate room temperature
- No special ventilation needed

**Advantages:**
- ✅ Cleanest, most professional appearance
- ✅ No drilling/modifying wall plates
- ✅ Probe protected inside wall box
- ✅ Easy to replace sensor (just unscrew plate)
- ✅ Matches other wall plates exactly
- ✅ Adequate air circulation
- ✅ No visible probe or wires

### Method B: Probe Protrusion (Better Air Exposure - Optional)

**What you'll mount:**
- Wall box with standard cable routing (through wall)
- Modified wall plate with hole for probe
- Probe pushed through plate to protrude into room
- Better air exposure for faster response

**Installation:**
```
    Front view                    Cross-Section
    ┌─────────────┐              
    │      ●      │ ← Small       Wall
    │    [===]    │   hole        │
    │   Probe     │               ├──●[===] Probe protrudes
    │  protruding │               │ Plate  into room
    └─────────────┘               ├─────────┐
                                  │ ╭─○─────┤ Cable pulled
                                  │ │       │ through so
                                  │ ╰───────┤ probe exits
                                  │    ║    │
    Visible sensor                ─────║──────
    for faster response                ║
                                   Cable through wall
```

**Steps:**
1. **Install wall box and route cable** (same as Method A)
   - Cable comes through wall into box

2. **Modify wall plate**
   - Drill 1/4" (6.5mm) hole for probe (tight fit)
   - Or 5/16" (8mm) for easier positioning
   - Center of plate or slightly higher

3. **Position probe through plate**
   - From inside box, push probe through hole
   - Let probe protrude 5-10mm into room
   - Secure from behind:
     - **Option 1**: Friction fit (tight hole)
     - **Option 2**: Hot glue or silicone
     - **Option 3**: Small cable clamp on back of plate

4. **Mount plate to box**
   - Cable stays coiled in wall box
   - Probe exits through hole
   - Standard mounting to box

**How air circulation works:**
- Probe directly exposed to room air
- Maximum air circulation around probe
- Faster response to temperature changes (1-2 min vs 3-5 min)
- More representative of actual room temperature

**Advantages:**
- ✅ Better air circulation around sensor
- ✅ Faster temperature response
- ✅ More accurate readings
- ✅ Probe directly in room air
- ✅ Still uses standard wall box (cable through wall)
- ⚠️ Probe visible (may be undesirable aesthetically)

### Method C: Direct Surface Mount (No Wall Box - Budget Option)

**What you'll mount:**
- Wall plate mounted directly to wall surface
- Cable drilled through wall, exits behind plate
- Probe hangs in gap between plate and wall

**Parts needed:**
- 1/4" P-clip or cable clamp (Amazon: B07QKXT7DZ)
- Small screw and nut

**Installation:**
```
    Back of wall plate
    
    ┌─────────────────┐
    │                 │
    │     ╔═══╗       │ ← P-clip holds probe
    │     ║ ○ ║       │
    │     ╚═══╝       │
    │        │        │
    │        ● hole   │ ← Cable exit hole
    │                 │
    └─────────────────┘
```

**Steps:**
1. Drill small pilot hole in wall plate center
2. Drill 3/8" hole below for cable
3. Attach P-clip with small screw/nut
4. Insert probe into P-clip
5. Thread cable through lower hole
6. Tighten P-clip to secure probe

**Advantages:**
- Removable (can replace sensor easily)
- Secure mounting
- Probe position adjustable

### Method D: Using Keystone Insert

**What you'll mount:**
- Blank keystone insert modified for sensor
- Professional "plug and play" look

**Parts needed:**
- Blank keystone insert (Amazon: B07PHNMHLZ)
- Keystone wall plate

**Installation:**
```
    Keystone insert (back view)
    ┌─────────┐
    │    ●    │ ← Drill 1/4" hole
    │         │
    │  [===]  │ ← Probe inserted from back
    └─────────┘
    
    Snaps into keystone wall plate
```

**Steps:**
1. Remove center section of blank keystone insert (usually snaps out)
2. Drill 1/4" hole for probe
3. Insert probe from back side
4. Secure with hot glue or friction fit
5. Snap keystone insert into wall plate
6. Cable runs behind wall plate to wall box

**Advantages:**
- Most professional appearance
- Matches network/coax outlets
- Easy to remove/replace sensor
- Modular design

### Method E: 3D Printed Clip

**What you'll mount:**
- Custom 3D printed sensor holder
- Mounts to wall plate or directly to wall

**STL files available:**
- Search Thingiverse: "DS18B20 wall mount"
- Or design your own simple clip

**Example design:**
```
    Simple clip design:
    
    ┌────┐
    │    ├──● ← Screw hole
    │ ○  │   ← Holds probe
    └────┘
```

## Detailed Installation Example

### Complete Wall Plate Installation (Method A - Recommended)

**Tools needed:**
- Drill for wall box installation
- Drywall saw (if using old-work box)
- Phillips screwdriver
- Pencil for marking
- Level
- Fish tape or wire (for routing cable through wall)

**Parts for one sensor (TO-92):**
- 1× DS18B20 TO-92 sensor (~$1)
- 1× Blank single-gang wall plate (unmodified!)
- 1× Old-work electrical box (Carlon B114R ~$3)
- 3× Wires ~20-50 feet each (22-24 AWG) or use CAT5e cable
- Heat shrink tubing (1/8" and 1/4")
- Small piece of double-sided foam tape
- Solder and soldering iron

**Parts for one sensor (Waterproof probe):**
- 1× DS18B20 waterproof sensor with cable (~$5)
- 1× Blank single-gang wall plate (unmodified!)
- 1× **Low-voltage mounting bracket** (Recommended: Carlon SC100A ~$1)
  - OR: Old-work electrical box (Carlon B114R ~$3)
  - OR: Surface mount box (~$2)
- 2× Screws (usually included)
- 1× DS18B20 sensor
- Cable clips for wire management to Pi

**Step-by-step:**

1. **Plan cable route**
   - From sensor location through wall to Pi location
   - Through basement/attic/crawlspace if possible
   - Along baseboards if running exposed

2. **Install mounting bracket/box**
   
   **Low-Voltage Bracket (Easiest - Recommended):**
   - Mark location on wall (4-5 feet high)
   - Hold bracket against wall, trace opening
   - Cut hole with drywall saw (about 3" × 2")
   - Feed cable through wall to hole
   - Push bracket into hole
   - Tighten mounting screws until tabs grip drywall
   - Bracket should be flush with wall
   
   **Surface Mount Box (No Cutting):**
   - Mark location on wall (4-5 feet high)
   - Level the box
   - Screw directly to wall through mounting holes
   - Feed cable through box knockout
   
   **Old-Work Electrical Box (Full Enclosure):**
   - Trace box outline on wall
   - Cut drywall hole with drywall saw
   - Feed cable through wall to hole
   - Insert box, tighten mounting ears

4. **Mount the wall box** (if using)
   - Mark location on wall at desired height (4-5 feet)
   - Level the box
   - Screw surface mount box to wall
   - OR: Cut hole and install old-work box

5. **Thread the sensor cable**
   - Feed cable through wall box knockout
   - Pull cable through grommet in wall plate (back to front)
   - Pull until probe is inside wall box
   - Leave 6-12" of cable coiled inside box (service loop)

6. **Position the probe**
   - **Option 1**: Let probe hang freely inside box
   - **Option 2**: Position probe just behind grommet opening
   - **Option 3**: Pull probe through to sit flush in grommet
   - Avoid probe touching metal box (can affect reading)

7. **Secure the cable**
   - Use small cable tie or velcro strap to secure coil
   - Don't kink the cable
   - Route cable to edge of box for exit

8. **Attach wall plate to box**
   - Align wall plate with box mounting holes
   - Insert screws and tighten (don't over-tighten)
   - Plate should sit flat against wall

9. **Route cable to Pi**
   - Run cable along baseboard using cable clips
   - Or: Run through wall/attic to Pi location
   - Label cable with room name at both ends

## Mounting Dimensions

**Standard single-gang wall plate:**
- Width: 2.75" (70mm)
- Height: 4.5" (114mm)
- Mounting holes: 3.25" (83mm) apart vertically

**Suggested hole positions:**
- Center hole: 1.375" from left, 2.25" from bottom
- Upper position: 1.375" from left, 3.5" from bottom (if using 2 holes)

**DS18B20 probe dimensions:**
- Diameter: 6mm (0.236", about 1/4")
- Length: 30-50mm depending on model
- Cable diameter: 3-4mm

**Recommended hole sizes:**
- For cable only: 3/8" (10mm) with grommet
- For probe: 1/4" (6.5mm) - tight fit
- For probe + adjustment: 5/16" (8mm)

## Probe Position Best Practices

### Air Circulation
```
GOOD:                      BAD:

 Probe with space          Probe against wall
 around it:
                           │
   ┌─┐                     │ ○ ← Blocked
   │ │                     │    air flow
   │ ○ ← Open              │
   │ │    air flow         │
   └─┘                     └───────────
   
```

**Tips:**
- Leave 1/8" gap around probe for air circulation
- Don't pack insulation tightly around probe
- If probe touches metal, temperature may be affected
- Horizontal mounting often better than vertical

### Probe Orientation
```
Horizontal (Better):       Vertical (OK):

  ┌──────────┐            ┌──────────┐
  │          │            │    ║     │
  │  [===]   │            │    ║     │
  │          │            │    ○     │
  └──────────┘            └──────────┘
  
  More exposed            Less exposed
  to room air             to room air
```

## Troubleshooting Physical Mounting

### Probe won't fit through hole
- DS18B20 probe is 6mm diameter
- Drill 1/4" (6.35mm) hole for tight fit
- Or 5/16" (7.9mm) for easier insertion
- Check probe hasn't been damaged/bent

### Cable won't pull through
- Cable is 3-4mm diameter, needs 3/8" hole minimum
- Use grommet to ease cable pull
- Don't force cable (can damage wires inside)
- Thread cable from back to front

### Probe won't stay in position
- Tight hole: Use 1/4" drill for friction fit
- Loose hole: Add small dab of hot glue or silicone
- Heavy probe: Use P-clip or cable clamp
- Use non-permanent adhesive if rental property

### Plate looks crooked
- Use level when marking hole
- Align plate with nearby switches/outlets
- Wall boxes have adjustable mounting ears
- Shim behind plate if wall is uneven

## Alternative Mounting Ideas

### Quick & Temporary Mounts
1. **Command strip + small box**
   - Hot glue probe inside small plastic box
   - Drill vent holes in box
   - Attach box to wall with Command strip

2. **Behind picture frame**
   - Tape probe to back of picture frame
   - Ensure air can circulate
   - Wire runs down behind frame

3. **Magnetic mount** (if metal surface available)
   - Attach small magnet to probe with shrink tube
   - Stick to metal surface (junction box, etc.)

### Decorative Options
1. **Match switch plates**
   - Use same brand/color as existing switches
   - Align vertically for consistent look
   - Consider decorator-style plates

2. **Paint to match**
   - Paint wall plate to match wall color
   - Use spray paint for smooth finish
   - Mask grommet hole before painting

3. **Label plates**
   - Small printed label: "Temperature Sensor"
   - Or: Match naming scheme ("SENSOR-LR" for living room)
   - Professional label maker creates clean look

## Mounting Options

### Option 1: Wall Plate Mount (Recommended)

**Best for**: Permanent installation, clean appearance

**Materials Needed:**
- Blank single-gang wall plates (match your home's style)
- 3/8" or 1/2" cable entry grommets
- Wall anchors or old-work electrical box
- Drill with appropriate bit

**Installation Steps:**

1. **Prepare Wall Plate**
   - Drill hole in center of blank wall plate (3/8" or 1/2")
   - Insert rubber grommet to protect wire
   - Alternative: Use keystone jack wall plate for cleaner look

2. **Sensor Positioning**
   - Height: 4-5 feet from floor (typical thermostat height)
   - Location: Interior wall, away from:
     - Direct sunlight
     - Drafts (doors, windows, vents)
     - Heat sources (lamps, electronics, fireplace)
     - Cold sources (exterior walls, uninsulated areas)

3. **Mounting Methods**

   **Method A: Surface Mount Box**
   - Attach surface mount box to wall with screws
   - Feed sensor wire through box knockout
   - Attach wall plate to box
   - Good for: Finished walls, rental properties

   **Method B: Recessed (Old Work Box)**
   - Cut hole in drywall using old-work box as template
   - Insert old-work box, tighten mounting ears
   - Feed sensor wire through box
   - Attach wall plate to box
   - Good for: Permanent installation, cleanest look

   **Method C: Direct Mount (Budget)**
   - Drill hole in wall plate
   - Attach wall plate directly to wall with anchors
   - Feed sensor through hole
   - Good for: Quick installation, no box needed

4. **Sensor Wire Management**
   - Run wires along baseboards using cable clips
   - Or: Run through walls/attic (more work, cleanest)
   - Label each sensor wire at both ends

5. **Sensor Probe Placement**
   - Let waterproof probe hang down inside wall plate
   - Or: Coil excess wire in box, leave probe exposed
   - Ensure probe is not touching metal box (affects reading)

### Option 2: Keystone Jack Mount (Professional)

**Best for**: Integration with existing low-voltage systems

**Materials Needed:**
- Keystone jack wall plates
- Blank keystone inserts with holes
- Ethernet-style keystone jacks (optional, for termination)

**Advantages:**
- Matches network/cable outlets
- Easy to add/remove sensors
- Can use existing low-voltage boxes

**Installation:**
- Follow same wall box procedure as Option 1
- Use keystone plate instead of blank plate
- Feed sensor through blank keystone insert
- Snap insert into keystone plate

### Option 3: Decorative Cover Plate

**Best for**: Visible sensor in living areas

**Materials Needed:**
- Small decorative box or cover
- 3D printed enclosure (STL files available online)
- Command strips or small screws

**Installation:**
- Create small enclosure with ventilation holes
- Mount enclosure to wall at desired height
- Feed sensor wire into enclosure from behind
- Coil excess wire inside enclosure

### Option 4: Baseboard/Crown Molding Mount

**Best for**: Minimal visibility, existing cable runs

**Materials Needed:**
- Small cable clips or adhesive hooks
- Matching paint (optional)

**Installation:**
- Run sensor wire along baseboard or crown molding
- Secure with small clips every 12-18 inches
- Terminate sensor at desired location
- Can paint over for camouflage

### Option 5: Ceiling Mount (Advanced)

**Best for**: High-ceiling rooms, keeping out of reach

**Materials Needed:**
- Small junction box or pancake box
- Ceiling medallion or decorative cover (optional)

**Installation:**
- Mount box to ceiling joist
- Feed sensor wire through box
- Let sensor hang down slightly
- Cover with decorative medallion if desired

## Room-by-Room Recommendations

### Living Room / Family Room
- **Location**: Interior wall, 5 feet high
- **Mounting**: Wall plate (professional look)
- **Considerations**: Away from fireplace!

### Kitchen
- **Location**: Away from stove/oven, not near refrigerator
- **Mounting**: Near light switch area
- **Considerations**: High traffic, needs durable mounting

### Bedrooms
- **Location**: Interior wall opposite door
- **Mounting**: Wall plate matching light switches
- **Considerations**: Keep away from heating vents

### Basement
- **Location**: Central area, away from furnace
- **Mounting**: Surface mount (exposed walls)
- **Considerations**: May need weatherproof enclosure if damp

### Upstairs / Second Floor
- **Location**: Hallway or central room
- **Mounting**: Wall plate or baseboard
- **Considerations**: Heat rises, may read warmer

### Fireplace Room (Monitored Sensor)
- **Location**: Near thermostat location (where fireplace affects it)
- **Mounting**: Wall plate, permanent
- **Considerations**: This sensor will be ignored when fireplace active

## Wiring Runs

### Through Walls (Cleanest)
1. Drill hole behind wall plate location
2. Fish wire through wall cavity to basement/attic
3. Run wires to central Pi location
4. Use fish tape or coat hanger for fishing

### Along Baseboards (Easiest)
1. Use cable clips every 12-18 inches
2. Run in corners where baseboard meets wall
3. Paint clips to match (optional)
4. Use cable raceways for multiple wires

### Using CAT5/CAT6 Cable
Each CAT5e cable has 8 wires (4 pairs):
- Can run 2-3 sensors per cable
- DS18B20 needs 3 wires: Power, Ground, Data
- Use different colored pairs for each sensor
- Terminate all data wires to GPIO 4 at Pi

**CAT5e Wire Color Mapping:**
```
Sensor 1:
  - Orange    → 3.3V (or 5V)
  - Orange/W  → Ground
  - Green     → GPIO 4 (Data)

Sensor 2:
  - Blue      → 3.3V (or 5V)
  - Blue/W    → Ground
  - Brown     → GPIO 4 (Data)
```

## Professional Tips

1. **Label Everything**
   - Tag each sensor with room name at wall plate
   - Label at Pi end with matching room name
   - Write sensor ID on wall plate (inside)

2. **Test Before Finishing**
   - Verify sensor reads correctly before closing wall
   - Check for interference (shouldn't be any)
   - Run `tests/test_sensors.py` to confirm detection

3. **Leave Service Loop**
   - Coil 1-2 feet extra wire in wall box
   - Allows sensor replacement without re-running wire
   - Use velcro ties, not twist ties

4. **Future-Proof**
   - Consider running extra wires for future sensors
   - Use conduit if local code requires
   - Document wire paths in attic/basement

5. **Aesthetic Considerations**
   - Match wall plate color to switches/outlets
   - Align vertically with other wall plates
   - Keep height consistent (4-5 feet standard)

## Troubleshooting Sensor Location

### Sensor Reads Too High
- Check for nearby heat sources
- Ensure probe isn't touching metal
- Move away from ceiling/lights
- Verify air circulation around sensor

### Sensor Reads Too Low
- Check for drafts from windows/doors
- Move away from exterior walls
- Ensure not in return air path
- Raise sensor height if on cold floor

### Inconsistent Readings
- Check wire connections (loose?)
- Ensure probe is dry (waterproof ones only)
- Verify proper pull-up resistor (4.7kΩ)
- Check for electrical interference

## Alternative Sensor Enclosures

If you want custom enclosures:

### 3D Printed Options
Search Thingiverse/Printables for:
- "DS18B20 wall mount"
- "Temperature sensor cover"
- Many free STL files available

### DIY Enclosures
- Small plastic project boxes with ventilation
- Medicine cabinet samples (small decorative boxes)
- Electrical conduit fittings (industrial look)

### Commercial Options
- Small plastic junction boxes (paintable)
- Sensor enclosures from automation suppliers
- Thermostat mounting plates (repurposed)

## Cost Summary by Mounting Method

| Method | Material Cost | Difficulty | Appearance | Best For |
|--------|--------------|------------|------------|----------|
| Wall Plate (Surface) | $3/sensor | Easy | Professional | Most homes |
| Wall Plate (Recessed) | $4/sensor | Medium | Excellent | Permanent install |
| Keystone Jack | $4/sensor | Easy | Professional | Tech-savvy homes |
| Decorative Cover | $5-10/sensor | Easy | Good | Visible areas |
| Baseboard Mount | $1/sensor | Very Easy | Hidden | Rentals, temporary |
| 3D Printed | $2-5/sensor | Medium | Variable | Custom designs |

## Building Code Considerations

- Low voltage (1-Wire sensors) typically doesn't require permits
- Follow local electrical codes for wire routing
- Use appropriate wire gauge (22-24 AWG fine for sensors)
- If running through walls, consider conduit in some jurisdictions
- Check local codes before drilling into walls

## Rental-Friendly Options

If you can't make permanent modifications:

1. **Adhesive mounts**: Command strips with small enclosures
2. **Furniture placement**: Hide sensors behind pictures, shelves
3. **Existing outlets**: Mount near outlets using outlet covers
4. **Tape and paint**: Run wires along trim, paint to match
5. **Removable**: Surface mount boxes, easy to patch holes when moving

## Maintenance Access

Consider:
- Sensors may need replacement (they can fail)
- Easy access is better than hidden
- Wall plates allow easy sensor swap
- Document sensor IDs in case of replacement

## Sample Room Layout

```
                    Ceiling
                       │
    ┌──────────────────┼──────────────────┐
    │                  │                  │
    │                                     │
    │   [Sensor]       │        [Window] │
    │    @ 5ft         │                  │
Wall│     │            │                  │Wall
    │     │cable                          │
    │     └──→[clips]→[Door]              │
    │                  │                  │
    └──────────────────┼──────────────────┘
                       │
                    Floor
                    
Legend:
[Sensor] - Mounted on interior wall, 5ft height
[Window] - Avoid mounting near windows (drafts)
[Door] - Avoid mounting near doors (drafts)
[clips] - Cable clips along baseboard
```

## Complete Installation Diagram

```
Single sensor installation:

    Wall surface                    Inside wall box
    ──────────────                 ─────────────────
    
    ┌─────────┐                    ┌─────────┐
    │    ●    │ ← Grommet          │  ╭─○─╮  │ ← Probe coiled
    │ Sensor  │                    │  │ ● │  │    inside box
    │  Plate  │                    │  ╰───╯  │
    └────┬────┘                    └────┬────┘
         │                              │
         │ Cable                        │
         ↓                              ↓
    ═════════ Baseboard           Exit through
    [clip] [clip] [clip]          knockout hole
                  ↓
              To Raspberry Pi


Multiple sensors using CAT5e cable:

  Room 1          Room 2          Room 3
  [Sensor]        [Sensor]        [Sensor]
     │               │               │
     └───────CAT5e cable run─────────┘
                     │
                     ↓
              Raspberry Pi
         (All data wires to GPIO 4)
```

## Frequently Asked Questions

### Q: Will the wall cavity temperature be different from room temperature?
**A:** It depends on the wall type:

**Interior walls** (wall between two rooms):
- Wall cavity temp ≈ room temp (within 1-2°F)
- Both sides exposed to conditioned space
- Adequate for HVAC control

**Exterior walls** (wall facing outside):
- Wall cavity can be significantly colder/warmer
- Insulation creates temperature gradient
- **Do NOT mount sensors on exterior walls!**

**Air circulation factors:**
- Standard wall plate has small gaps around edges
- Air slowly circulates (5-15 min equalization)
- May lag rapid temperature changes
- For critical accuracy, use probe protrusion or add vent holes

### Q: Should I use a low-voltage bracket or full electrical box?
**A:** Based on your concern about temperature accuracy:

**Full electrical box (old-work) = BETTER for accuracy**
- Creates defined air space
- More predictable air circulation
- Temperature equalizes reliably
- Only ~$2 more per sensor
- Slightly more cutting required
- **Recommended choice**

**Low-voltage bracket = OK with modifications**
- Cheaper and easier to install
- Add 2-4 small vent holes in wall plate for better circulation
- Test against reference thermometer
- Good for non-critical locations

### Q: What's the difference between a low-voltage bracket and an electrical box?
**A:** 

**Low-Voltage Bracket (Frame Only):**
- Just a plastic frame/ring that screws hold the wall plate
- Open back - no enclosure
- Very shallow (1/2")
- Perfect for sensors, data cables, coax
- Probe hangs in wall cavity behind frame
- **This is ideal for temperature sensors!**

**Electrical Box (Full Enclosure):**
- Complete box with back and sides
- Encloses wires and devices
- Deeper (2-3")
- Required for electrical outlets/switches
- Overkill for temperature sensors but works fine
- Probe contained inside box

### Q: Is a low-voltage bracket strong enough?
**A:** Yes! They're designed to hold wall plates securely. Temperature sensors have no load or stress, so a low-voltage bracket is more than adequate. They're rated for data cables, phone jacks, and similar low-voltage applications.

### Q: Do I need to drill a hole in the wall plate?
**A:** **Usually NO!** For standard installation:

- **Method A** (recommended): Use blank wall plate with NO hole. Cable runs through wall to wall box. Plate just covers the box.
- **Method B** (optional): Drill hole ONLY if you want probe to protrude into room for faster response.
- **Method C** (budget): Drill hole only if mounting plate directly to wall without a box.

### Q: Where does the cable go?
**A:** The cable runs **through the wall cavity** (inside your walls), not through the front of the wall plate:

1. Cable enters wall box through knockout hole (from inside wall)
2. Probe sits inside wall box  
3. Wall plate covers the box
4. Cable continues through wall to Raspberry Pi location

### Q: Will the wall box trap hot/cold air and give wrong readings?
**A:** No, because:
- Wall boxes are not sealed (multiple openings)
- Air naturally convects through the box
- Temperature equalizes with room air within 1-2 minutes
- If concerned, use Method B with probe positioned at the hole opening

### Q: Do I need to drill ventilation holes in the wall plate?
**A:** No, additional ventilation holes are not needed:
- Standard installation has adequate air circulation
- Wall box gaps provide plenty of air exchange
- Extra holes would look unprofessional
- If you want better response, position probe at/through the main hole (Method B)

### Q: How fast does the sensor respond to temperature changes?
**A:** Response time depends on mounting:
- Inside wall box: ~3-5 minutes for full response
- At hole opening: ~2-3 minutes
- Protruding/exposed: ~1-2 minutes
- All methods are adequate for HVAC control (thermal systems are slow)

### Q: The cable is 3-4mm diameter. What size hole do I drill if I need one?
**A:** Only needed if mounting without wall box (Method C) or want probe protrusion (Method B):
- For cable pass-through: 3/8" (10mm) with grommet
- For probe protrusion: 1/4" (6.5mm) tight fit or 5/16" (8mm) with room
- For Method A (recommended): NO hole needed in plate!

### Q: Should the probe touch anything inside the box?
**A:** 
- **No** - Keep probe from touching metal box (can conduct heat/cold from wall)
- **No** - Don't let probe rest on back of wall plate (affects reading)
- **Yes** - Probe can touch air and cable only
- **Best** - Let probe hang freely or secure with non-conductive clip

### Q: What if I don't use a wall box at all?
**A:** You can mount the wall plate directly to the wall:
- Drill hole in plate for cable
- Drill small pilot holes in wall for plate screws
- Use wall anchors for hollow walls
- Probe hangs behind plate in the ~1/4" gap
- Less protection but simpler installation
- Still works fine - air circulates around plate edges

## Next Steps

1. **Survey rooms**: Identify best mounting locations
2. **Order parts**: Get wall plates, boxes, wire based on method
3. **Test fit**: Ensure sensors fit chosen enclosures
4. **Plan wire routes**: Mark paths before running wire
5. **Install incrementally**: Do one room, test, then proceed
6. **Label thoroughly**: Future you will thank you

## Questions to Consider

- [ ] How many rooms need monitoring? (= # of sensors)
- [ ] What's the wire run distance from each room to Pi?
- [ ] Can you run wires through walls or only surface mount?
- [ ] Match wall plates to existing décor?
- [ ] Need rental-friendly removable mounts?
- [ ] Want sensors hidden or acceptable to be visible?
