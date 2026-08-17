# SymbolGen CLI Usage Guide - Complete Edition

## Features Implemented

✅ Category selection (MCU / Power)  
✅ Power subcategory auto-detection  
✅ Incomplete grouping validation (fail-fast)  
✅ Auto-fill with threshold  
✅ Four-sided symbols  
✅ Debug commands for everything  
✅ Complete feature parity with UI

---

## Quick Start

```bash
# MCU grouping
python cli.py build pins.json --grouping --category mcu

# Power with auto-detection
python cli.py suggest pins.json
python cli.py build pins.json --grouping --category power --suggest-subcategory

# Complete workflow
python cli.py build pins.json --grouping --sidealloc --category mcu
```

---

## Commands Overview

### 1. `suggest` - Power Subcategory Suggestion

Auto-detect best matching Power subcategory.

```bash
python cli.py suggest <input>
```

**Output:**
```
📊 Subcategory Match Analysis:
============================================================
✅ 1. Buck                    100.0% (45/45 pins)
⚠️  2. LDO                     87.2% (39/45 pins)
ℹ️  3. Boost                   45.0% (20/45 pins)
```

---

### 2. `build` - Process Pin Tables

Apply grouping and/or side allocation.

**Basic Syntax:**
```bash
python cli.py build <input> [OPTIONS]
```

**Key Options:**
- `--category {mcu|power}` - Device category (default: mcu)
- `--subcategory <name>` - Power subcategory (Buck, LDO, etc.)
- `--suggest-subcategory` - Auto-detect Power subcategory
- `--grouping` - Apply pin grouping
- `--sidealloc` - Apply side allocation
- `--mputype` - Use MPU-type splitting
- `--four-sided` - Create 4-sided symbol
- `--auto-fill` - Auto-fill partial matches
- `--threshold N` - Minimum match % (default: 100)
- `--allow-incomplete` - Proceed with warnings
- `--strict-population` - Strict population mode
- `--balanced-assignment` - Balanced assignment mode

---

### 3. `debug-grouping` - Detailed Grouping Analysis

Show detailed information about grouping issues.

```bash
python cli.py debug-grouping <input> [OPTIONS]
```

**Shows:**
- Unresolved pins with details
- Electrical type distribution
- Grouping distribution
- Complete/incomplete status

---

### 4. `debug-sidealloc` - Detailed Side Allocation Analysis

Show detailed information about side allocation.

```bash
python cli.py debug-sidealloc <input> [OPTIONS]
```

**Shows:**
- Priority distribution
- Side distribution
- Part distribution (for multi-part)

---

## Category Selection

### MCU Devices

```bash
python cli.py build pins.json --grouping --category mcu
```

**Uses database:**
- `Grouping/mcu&mpu_database/Combined_Added_mpu.json`

---

### Power Devices (19 Subcategories)

**Available subcategories:**
1. Buck
2. Boost
3. Buck-Boost
4. LDO
5. Charge-Pump
6. FlyBack
7. Battery-Charger-IC
8. PWM-Controller
9. Voltage-References
10. Power-Supply-Support
11. FET-Drivers
12. Battery-Protectors-Monitors-Balancers
13. LED-Drivers
14. DC-DC-Power-Modules
15. Multiphase-DC-DC-Switching-Controllers
16. ORing-FET-Controllers
17. Protected-Intelligent-Power-Devices
18. Smart-Power-Stages
19. Solid-State-Lighting-Interface-Ics
20. AC-DC-Isolated-DC-DC-Converters
21. USB-Type-C-Port-Manager
22. PMIC

**Manual selection:**
```bash
python cli.py build pins.json --grouping \
  --category power --subcategory Buck
```

**Auto-detection:**
```bash
python cli.py build pins.json --grouping \
  --category power --suggest-subcategory
```

---

## Incomplete Grouping Validation

### Strict Mode (Default)

Fails if any pins are ungrouped:

```bash
python cli.py build pins.json --grouping --category mcu
```

**If incomplete:**
```
❌ GROUPING INCOMPLETE: 5 pins unresolved
   Status: NOT AVAILABLE
   
   Unresolved pins:
   Pin Designator Pin Display Name
                3             P003
                4             P004
                
💡 Options:
   1. Run with --debug-grouping to see details
   2. Use --auto-fill --threshold 80 to fill partial matches
   3. Use --allow-incomplete to proceed anyway
```

### Allow Incomplete

Proceed with warnings:

```bash
python cli.py build pins.json --grouping --allow-incomplete
```

---

## Auto-Fill with Threshold

Auto-fill grouping if match confidence >= threshold.

```bash
python cli.py build pins.json --grouping \
  --auto-fill --threshold 80
```

**How it works:**
- `--threshold 100`: Only exact matches (default)
- `--threshold 80`: 80%+ similarity
- `--threshold 50`: 50%+ similarity

**Example output:**
```
⚙️  Auto-filling groups (threshold: 80%)...
✅ Auto-filled 12 pins
⚠️  Warning: 3 pins with unresolved Grouping
```

---

## Four-Sided Symbols

Create symbols with Top/Bottom/Left/Right sides.

```bash
python cli.py build pins.json --grouping --sidealloc --four-sided
```

**Algorithm:**
1. Divide pins equally across 4 sides
2. EPAD pins assigned to Top
3. Natural sort by pin number

**Output example:**
```
📦 Four-sided symbol
Total pins: 64
Base pins per side: 16
Assigned 16 pins to Left side
Assigned 16 pins to Bottom side
Assigned 16 pins to Right side
Assigned 16 pins to Top side
```

---

## MPU Type Splitting

Split multi-part symbols by functional groups.

```bash
python cli.py build pins.json --grouping --sidealloc \
  --mputype --strict-population --balanced-assignment
```

**Options:**
- `--mputype`: Enable functional grouping
- `--strict-population`: Enforce max 80 pins/part
- `--balanced-assignment`: Balance pins across parts

---

## Debug vs Build

### Build Commands
- **Run** the feature
- **Save** output files
- Show **summary** only

### Debug Commands
- **Run** the feature
- Show **detailed** analysis
- Show **all unresolved** items
- Save debug output

**Example comparison:**

**Build:**
```bash
python cli.py build pins.json --grouping
# Output:
# ✅ Loaded 100 pins
# ⚙️  Assigning groups...
# ✅ Grouping completed
# ✨ Success!
```

**Debug:**
```bash
python cli.py debug-grouping pins.json
# Output:
# ✅ Loaded 100 pins
# ⚙️  Assigning groups...
# ⚠️  Warning: 5 pins unresolved
#
# Unresolved pins:
# Pin 45: P045 - Type: I/O
# Pin 67: CUSTOM - Type: NAv
# ...
# 
# Electrical Type Distribution:
# Power: 20
# I/O: 60
# NAv: 5
# ...
```

---

## Complete Workflow Examples

### Example 1: MCU Device

```bash
# Step 1: Group pins
python cli.py build mcu_pins.json --grouping --category mcu

# Step 2: Review (optional)
python cli.py debug-grouping mcu_pins.json --category mcu

# Step 3: Side allocation
python cli.py build mcu_pins_grouped.json --sidealloc --category mcu

# Or do everything at once:
python cli.py build mcu_pins.json --grouping --sidealloc --category mcu
```

---

### Example 2: Power Device (Auto-detect)

```bash
# Step 1: Suggest subcategory
python cli.py suggest power_pins.json

# Output:
# ✅ 1. Buck  100.0% (45/45 pins)
#
# To use:
#   python cli.py build power_pins.json --grouping \
#       --category power --subcategory Buck

# Step 2: Build with suggestion
python cli.py build power_pins.json --grouping --sidealloc \
  --category power --suggest-subcategory
```

---

### Example 3: Large MCU with MPU Splitting

```bash
python cli.py build large_mcu.csv --grouping --sidealloc \
  --category mcu --mputype --strict-population --balanced-assignment
```

---

### Example 4: Four-Sided Symbol

```bash
python cli.py build pins.json --grouping --sidealloc --four-sided
```

---

### Example 5: Auto-Fill Partial Matches

```bash
# Try exact matches first
python cli.py build pins.json --grouping

# If many unresolved, try 80% threshold
python cli.py build pins.json --grouping --auto-fill --threshold 80

# Debug to see what's still missing
python cli.py debug-grouping pins.json --auto-fill --threshold 80
```

---

### Example 6: Incomplete Grouping Handling

```bash
# Strict mode (fails on incomplete)
python cli.py build pins.json --grouping

# If fails, debug to see issues
python cli.py debug-grouping pins.json

# Or allow incomplete and fix manually later
python cli.py build pins.json --grouping --allow-incomplete
```

---

## Input File Formats

### JSON Format

**Array:**
```json
[
  {
    "Pin Designator": "1",
    "Pin Display Name": "VCC",
    "Pin Alternate Name": "Power"
  }
]
```

**With metadata:**
```json
{
  "part_number": "R7FA8M85A",
  "pins": [...]
}
```

### CSV Format

```csv
Pin Designator,Pin Display Name,Pin Alternate Name
1,VCC,Power
2,GND,Ground
```

### Excel Format

Standard `.xlsx` with same columns.

---

## Output Files

**Naming convention:**
- `input_grouped.json` - After grouping
- `input_sidealloc.json` - After side allocation
- `input_debug_grouping.json` - Debug grouping output
- `input_debug_sidealloc.json` - Debug side alloc output

---

## Required Columns

**For Grouping:**
- Pin Designator
- Pin Display Name
- Pin Alternate Name

**For Side Allocation:**
- All grouping columns
- Electrical Type (auto-generated if missing)
- Grouping (auto-generated if missing)

---

## Output Columns

**After Grouping:**
- Original columns
- Electrical Type (Power, I/O, Input, Output, Passive)
- Grouping (functional group name)

**After Side Allocation:**
- All grouping columns
- Priority (placement priority)
- Side (Left, Right, Top, Bottom)
- Part (for multi-part symbols)

---

## Error Handling

### Missing Subcategory for Power

```bash
python cli.py build pins.json --grouping --category power
# ❌ Error: Power category requires --subcategory
```

**Fix:**
```bash
python cli.py build pins.json --grouping --category power --suggest-subcategory
```

---

### Incomplete Grouping

```bash
python cli.py build pins.json --grouping
# ❌ GROUPING INCOMPLETE: 5 pins unresolved
#    Status: NOT AVAILABLE
```

**Options:**
1. Debug: `python cli.py debug-grouping pins.json`
2. Auto-fill: `python cli.py build pins.json --grouping --auto-fill --threshold 80`
3. Allow: `python cli.py build pins.json --grouping --allow-incomplete`

---

### Invalid Subcategory

```bash
python cli.py build pins.json --grouping --category power --subcategory InvalidName
# ❌ Error: Invalid Power subcategory: InvalidName
#    Available: Buck, Boost, LDO, ...
```

---

## Tips & Best Practices

### 1. Always Use Debug Mode First

```bash
# Debug to see what will happen
python cli.py debug-grouping pins.json --category mcu

# Then run actual build
python cli.py build pins.json --grouping --category mcu
```

### 2. Power Devices: Use Auto-Suggest

```bash
# Don't guess the subcategory
python cli.py suggest pins.json

# Use the suggestion
python cli.py build pins.json --grouping --category power --suggest-subcategory
```

### 3. Handle Incomplete Grouping

```bash
# Start strict
python cli.py build pins.json --grouping

# If fails, try auto-fill
python cli.py build pins.json --grouping --auto-fill --threshold 80

# Still fails? Debug
python cli.py debug-grouping pins.json --auto-fill --threshold 80

# Last resort: allow incomplete and fix manually
python cli.py build pins.json --grouping --allow-incomplete
```

### 4. Large Symbols: Use MPU Type

```bash
# For MCUs with >80 pins and functional grouping
python cli.py build large_mcu.json --grouping --sidealloc \
  --mputype --balanced-assignment
```

### 5. Compact Symbols: Use Four-Sided

```bash
# Better layout for 30-80 pin devices
python cli.py build pins.json --grouping --sidealloc --four-sided
```

---

## Command Cheat Sheet

```bash
# Suggest Power subcategory
python cli.py suggest <input>

# MCU grouping only
python cli.py build <input> --grouping --category mcu

# Power grouping with auto-detect
python cli.py build <input> --grouping --category power --suggest-subcategory

# Complete MCU flow
python cli.py build <input> --grouping --sidealloc --category mcu

# Power with specific subcategory
python cli.py build <input> --grouping --sidealloc \
  --category power --subcategory Buck

# Auto-fill partial matches (80% threshold)
python cli.py build <input> --grouping --auto-fill --threshold 80

# Four-sided symbol
python cli.py build <input> --grouping --sidealloc --four-sided

# MPU type splitting
python cli.py build <input> --grouping --sidealloc --mputype

# Allow incomplete grouping
python cli.py build <input> --grouping --allow-incomplete

# Debug grouping
python cli.py debug-grouping <input> --category mcu

# Debug side allocation
python cli.py debug-sidealloc <input> --category mcu
```

---

## Troubleshooting

### Q: "GROUPING INCOMPLETE" error

**A:** Use one of:
1. `--debug-grouping` to see which pins
2. `--auto-fill --threshold 80` to fill partial matches
3. `--allow-incomplete` to proceed anyway

### Q: Power device - which subcategory?

**A:** Use `suggest` command:
```bash
python cli.py suggest pins.json
```

### Q: How to see detailed output?

**A:** Use debug commands:
```bash
python cli.py debug-grouping pins.json
python cli.py debug-sidealloc pins.json
```

### Q: Symbol too crowded on 2 sides?

**A:** Use `--four-sided`:
```bash
python cli.py build pins.json --grouping --sidealloc --four-sided
```

### Q: Multi-part symbol not splitting right?

**A:** Try MPU type with options:
```bash
python cli.py build pins.json --grouping --sidealloc \
  --mputype --strict-population --balanced-assignment
```

---

## Version History

**v2.0.0** (Current)
- ✅ Power device support (19 subcategories)
- ✅ Auto-suggest Power subcategory
- ✅ Incomplete grouping validation
- ✅ Auto-fill with threshold
- ✅ Four-sided symbols
- ✅ Debug commands for all features
- ✅ Complete feature parity with UI

**v1.0.0**
- Basic MCU grouping and side allocation

---

**Last Updated:** 2026-08-17  
**Features:** Complete  
**Status:** Production Ready
