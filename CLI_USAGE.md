# SymbolGen CLI Usage Guide

## Quick Start

The SymbolGen CLI provides command-line access to pin grouping and side allocation functionality.

## Installation

```bash
# Install dependencies
pip install -r requirements.txt

# Or install as package
pip install -e .
```

## Commands

### 1. Build Command

Apply grouping and/or side allocation to pin tables.

**Basic Syntax:**
```bash
python cli.py build <input_file> [OPTIONS]
```

**Options:**
- `--grouping` - Apply pin grouping (assigns electrical types and groups)
- `--sidealloc` - Apply side allocation (assigns priority and sides)
- `--mputype` - Use MPU-type splitting for multi-part symbols (only with --sidealloc)

**Examples:**

```bash
# Apply grouping only
python cli.py build pins.json --grouping

# Apply both grouping and side allocation
python cli.py build pins.json --grouping --sidealloc

# Apply grouping and side allocation with MPU splitting
python cli.py build pins.csv --grouping --sidealloc --mputype

# Apply side allocation to already-grouped data
python cli.py build pins_grouped.json --sidealloc
```

---

### 2. Debug Command

Run in debug mode to see detailed information about unresolved pins.

**Basic Syntax:**
```bash
python cli.py debug <input_file> --grouping
```

**Example:**
```bash
# Debug grouping process
python cli.py debug pins.json --grouping
```

**Debug output includes:**
- Detailed list of unresolved pins
- Electrical type distribution
- Grouping distribution
- Statistics on coverage

---

## Input File Formats

The CLI accepts three input formats:

### 1. JSON Format

**Simple array:**
```json
[
  {
    "Pin Designator": "1",
    "Pin Display Name": "VCC",
    "Pin Alternate Name": "Power"
  },
  {
    "Pin Designator": "2",
    "Pin Display Name": "GND",
    "Pin Alternate Name": "Ground"
  }
]
```

**With part metadata:**
```json
{
  "part_number": "R7FA8M85A",
  "pins": [
    {
      "Pin Designator": "1",
      "Pin Display Name": "VCC",
      "Pin Alternate Name": "Power"
    }
  ]
}
```

### 2. CSV Format

```csv
Pin Designator,Pin Display Name,Pin Alternate Name
1,VCC,Power
2,GND,Ground
3,P000,AN000/IRQ0
```

### 3. Excel Format (.xlsx)

Standard Excel file with columns:
- Pin Designator
- Pin Display Name
- Pin Alternate Name

Optional columns (if already processed):
- Electrical Type
- Grouping
- Priority
- Side

---

## Required Columns

**For Grouping:**
- `Pin Designator` - Pin number/identifier
- `Pin Display Name` - Primary pin name
- `Pin Alternate Name` - Alternative function names

**For Side Allocation:**
- All grouping columns PLUS:
- `Electrical Type` - Pin electrical type (auto-assigned if missing)
- `Grouping` - Pin group assignment (auto-assigned if missing)

---

## Output Files

The CLI creates output files with suffixes:

- `_grouped.json` - After grouping
- `_sidealloc.json` - After side allocation
- `_debug.json` - Debug output

**Example:**
```bash
# Input: pins.json
# Outputs:
#   - pins_grouped.json
#   - pins_sidealloc.json (if --sidealloc used)
```

---

## Workflow Examples

### Complete Workflow

```bash
# 1. Start with raw pin data
python cli.py build raw_pins.json --grouping

# 2. Review grouped output (optional)
python cli.py debug raw_pins.json --grouping

# 3. Apply side allocation
python cli.py build raw_pins_grouped.json --sidealloc

# Or do everything in one step:
python cli.py build raw_pins.json --grouping --sidealloc
```

### MPU Multi-part Symbol

```bash
# For large pin counts (>80 pins) with MPU-type splitting
python cli.py build large_mcu.csv --grouping --sidealloc --mputype
```

---

## Understanding the Output

### Grouping Stage

**Adds columns:**
- `Electrical Type` - Power, I/O, Input, Output, Passive, etc.
- `Grouping` - Functional group (e.g., "Port Pins_00", "VCC_Pins", etc.)

**Example output:**
```json
{
  "Pin Designator": "3",
  "Pin Display Name": "P000",
  "Pin Alternate Name": "AN000/IRQ0",
  "Electrical Type": "I/O",
  "Grouping": "Port Pins_00"
}
```

### Side Allocation Stage

**Adds columns:**
- `Priority` - Pin placement priority (1-100+)
- `Side` - Symbol side (Left, Right, Top, Bottom)
- `Part` - Part number (for multi-part symbols)

**Example output:**
```json
{
  "Pin Designator": "3",
  "Pin Display Name": "P000",
  "Pin Alternate Name": "AN000/IRQ0",
  "Electrical Type": "I/O",
  "Grouping": "Port Pins_00",
  "Priority": 10,
  "Side": "Right"
}
```

---

## Troubleshooting

### Issue: "Missing required columns"

**Solution:** Ensure your input file has these columns:
- Pin Designator
- Pin Display Name
- Pin Alternate Name

### Issue: "Unresolved Electrical Type (NAv)"

**Cause:** Pin not found in database

**Solution:**
1. Run with `debug` command to see which pins are unresolved
2. Manually add `Electrical Type` column to input
3. Or add pin patterns to database JSON files

### Issue: "Unresolved Grouping"

**Cause:** Pin not found in grouping database

**Solution:**
1. Check if using correct device category (MCU vs Power)
2. Manually add `Grouping` column if needed
3. Or extend grouping database

### Issue: Unicode/Emoji errors on Windows

**Status:** Fixed in latest version with automatic encoding handling

---

## Advanced Usage

### Custom Input with Pre-filled Columns

If you have partial data already processed, the CLI will use existing values:

```json
[
  {
    "Pin Designator": "1",
    "Pin Display Name": "VCC",
    "Pin Alternate Name": "Power",
    "Electrical Type": "Power"
  }
]
```

Running `--grouping` will:
- Keep existing "Electrical Type"
- Only assign "Grouping"

### Batch Processing

```bash
# Process multiple files
for file in *.json; do
    python cli.py build "$file" --grouping --sidealloc
done
```

---

## Database Files

The CLI uses these databases:

**MCU/MPU:**
- `Grouping/mcu&mpu_database/Combined_Added_mpu.json`

**Pin Types:**
- `Grouping/mcu_database/mcu_input.json`
- `Grouping/mcu_database/mcu_power.json`
- `Grouping/mcu_database/mcu_io.json`
- `Grouping/mcu_database/mcu_output.json`
- `Grouping/mcu_database/mcu_passive.json`

**Priority:**
- `Side_Allocation/priority_map_mpuadded.json`

---

## Exit Codes

- `0` - Success
- `1` - Error (missing file, invalid format, etc.)
- `130` - Interrupted by user (Ctrl+C)

---

## Getting Help

```bash
# Show general help
python cli.py --help

# Show build command help
python cli.py build --help

# Show debug command help
python cli.py debug --help
```

---

## Integration with Existing Workflow

The CLI complements the Streamlit UI:

**Use CLI for:**
- Batch processing
- Automation/scripting
- CI/CD pipelines
- Headless environments

**Use Streamlit UI for:**
- Interactive exploration
- Visual feedback
- Manual corrections
- Learning the tool

Both interfaces use the same underlying functions, so results are consistent.

---

## Future Enhancements

Planned features:
- Support for Power device categories
- Custom database selection
- Output format options (CSV, Excel)
- Validation and pre-flight checks
- Progress bars for large files

---

**Last Updated:** 2026-08-17  
**Version:** 1.0.0
