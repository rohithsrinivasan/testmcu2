# CLI Missing Features Analysis

**Current Status:** Basic CLI implemented  
**Coverage:** ~30% of UI features  
**Goal:** 100% feature parity with Streamlit UI

---

## Current CLI Implementation ✅

**What we have now:**
```bash
python cli.py build <input> --grouping --sidealloc --mputype
python cli.py debug <input> --grouping
```

**Features covered:**
1. ✅ Load JSON/CSV/Excel input
2. ✅ Auto-assign Electrical Type from database
3. ✅ Auto-assign Pin Grouping (MCU only)
4. ✅ Priority assignment (MCU only)
5. ✅ Side allocation (single & multi-part)
6. ✅ MPU-type splitting
7. ✅ Debug mode with unresolved pins

---

## MISSING FEATURES - Categorized by Priority

---

## 🔴 CRITICAL MISSING (Must Have)

### 1. Category Selection (MCU vs Power)
**UI Location:** Grouping page, sidebar  
**Current:** CLI only uses MCU database  
**Missing:** Power device support with 19 sub-categories

**Implementation needed:**
```bash
# User should be able to specify:
python cli.py build pins.json --grouping --category power --subcategory Buck
python cli.py build pins.json --grouping --category mcu
```

**Sub-categories for Power:**
- Buck, Boost, Buck-Boost, LDO
- Charge-Pump, FlyBack
- Battery-Charger-IC
- PWM-Controller
- Voltage-References
- Power-Supply-Support
- FET-Drivers
- Battery-Protectors-Monitors-Balancers
- LED-Drivers
- DC-DC-Power-Modules
- Multiphase-DC-DC-Switching Controllers
- ORing-FET-Controllers
- Protected-Intelligent-Power-Devices
- Smart-Power-Stages
- Solid-State-Lighting-Interface-Ics
- AC-DC & Isolated DC-DC Converters
- USB Type-C Port Manager
- PMIC

**Why Critical:** Cannot process Power devices at all currently!

---

### 2. Power Subcategory Suggestions
**UI Location:** Grouping page, auto-analysis  
**Current:** Not implemented  
**Missing:** Suggest best matching subcategory based on pin analysis

**Implementation needed:**
```bash
python cli.py suggest <input>
# Output:
# Suggested subcategories:
# ✅ Buck: 100% (45/45 pins)
# ⚠️  LDO: 87% (39/45 pins)
# ℹ️  Boost: 45% (20/45 pins)
```

**Why Critical:** Users don't know which Power subcategory to use!

---

### 3. Handle Incomplete Grouping (Fail-Fast)
**UI Location:** Grouping page, validation  
**Current:** CLI continues even with unresolved grouping  
**Missing:** Block and return incomplete table for manual resolution

**Implementation needed:**
```bash
python cli.py build pins.json --grouping --strict
# Should FAIL if any grouping is empty:
# ❌ Error: 5 pins with unresolved grouping
# Run with --debug to see details
# Or use --allow-incomplete to proceed anyway
```

**Why Critical:** Silently incomplete data causes errors in side allocation!

---

### 4. Power Device Side Allocation
**UI Location:** Side Allocation page, Power-specific logic  
**Current:** Only MCU side allocation implemented  
**Missing:** Power device side allocation (different algorithm)

**Implementation needed:**
```bash
python cli.py build pins.json --category power --subcategory Buck --sidealloc
# Should use Power-specific priority mapping and side assignment
```

**Power-specific features:**
- Priority mapping per subcategory (19 different files)
- Fixed channelwise toggle
- L/R prefix-based side assignment

**Why Critical:** Current sidealloc command fails for Power devices!

---

### 5. Strict Population & Balanced Assignment Modes
**UI Location:** Side Allocation page, sidebar toggles  
**Current:** Always uses default mode  
**Missing:** Two constraint modes for multi-part symbols

**Implementation needed:**
```bash
python cli.py build pins.json --sidealloc --mputype \
  --strict-population \
  --balanced-assignment
```

**Why Critical:** Changes how pins are distributed across parts!

---

## 🟡 HIGH PRIORITY MISSING (Should Have)

### 6. Sensitivity & Smart Search Options
**UI Location:** Grouping page, matching options  
**Current:** Always uses `SENSITIVITY=False, SMARTSEARCH=False`  
**Missing:** Fuzzy matching options

**Implementation needed:**
```bash
python cli.py build pins.json --grouping --sensitivity --smart-search
```

**Why High:** Some pin names need fuzzy matching to find in database

---

### 7. Manual Grouping Input for Unresolved Pins
**UI Location:** Grouping page, data editor  
**Current:** Shows unresolved in debug, but can't provide input  
**Missing:** Interactive or file-based manual input

**Implementation needed:**
```bash
# Option A: Interactive mode
python cli.py build pins.json --grouping --interactive
# Prompts for each unresolved pin

# Option B: Mapping file
python cli.py build pins.json --grouping --manual-map manual_groups.json
```

**Why High:** Cannot complete grouping for unmatched pins!

---

### 8. Dynamic Database Editing
**UI Location:** Grouping page, sidebar  
**Current:** Not implemented  
**Missing:** Add new patterns to database on-the-fly

**Implementation needed:**
```bash
python cli.py database add --pattern "NEW_PIN" --group "Custom_Group"
```

**Why High:** Extends database without manual JSON editing

---

### 9. Auto-fill with Threshold
**UI Location:** Grouping page, sidebar slider  
**Current:** Not implemented  
**Missing:** Auto-fill grouping if match >= threshold

**Implementation needed:**
```bash
python cli.py build pins.json --grouping --auto-fill --threshold 90
# Auto-fills if 90%+ match confidence
```

**Why High:** Reduces manual work for partial matches

---

### 10. Four-Sided Symbol Option
**UI Location:** Side Allocation page  
**Current:** Only Left/Right allocation  
**Missing:** Top/Bottom/Left/Right allocation

**Implementation needed:**
```bash
python cli.py build pins.json --sidealloc --four-sided
```

**Why High:** Some symbols need 4-sided layout!

---

## 🟢 MEDIUM PRIORITY MISSING (Nice to Have)

### 11. Symbol Preview/Visualization
**UI Location:** Side Allocation page, symbol viewer  
**Current:** Not implemented  
**Missing:** Generate visual preview of symbol

**Implementation needed:**
```bash
python cli.py preview output_sidealloc.json --format png
python cli.py preview output_sidealloc.json --format svg
```

**Why Medium:** Useful for validation but not required for data processing

---

### 12. Parameter Extraction
**UI Location:** Parameters page (03_Parameters.py)  
**Current:** Not implemented  
**Missing:** Extract parameter tables from datasheet PDF

**Implementation needed:**
```bash
python cli.py extract-params datasheet.pdf --part R7FA8M85A
```

**Why Medium:** Separate workflow, not part of pin processing

---

### 13. Build Schematic Symbols
**UI Location:** Build Schematic page (04_Build_Schematic.py)  
**Current:** Not implemented  
**Missing:** Add ground symbols and schematic elements

**Implementation needed:**
```bash
python cli.py build-schematic pins_sidealloc.json --add-grounds
```

**Why Medium:** Final step, usually done visually

---

### 14. Remove Electrical Type / Description
**UI Location:** Grouping page, buttons  
**Current:** Not implemented  
**Missing:** Strip columns before re-processing

**Implementation needed:**
```bash
python cli.py clean pins.json --remove electrical-type
python cli.py clean pins.json --remove description
```

**Why Medium:** Can manually edit JSON instead

---

### 15. Excel/CSV Input from Uploaded Data
**UI Location:** Grouping page, file uploader  
**Current:** Partially implemented (loads files)  
**Missing:** Handle uploaded CSV metadata extraction

**Implementation needed:**
```bash
python cli.py build uploaded.csv --extract-from-annotations
```

**Why Medium:** Already supports CSV, this is edge case

---

### 16. Priority Mapping Rules Display
**UI Location:** Side Allocation page, expander  
**Current:** Not implemented  
**Missing:** Show priority rules documentation

**Implementation needed:**
```bash
python cli.py docs priority-rules
```

**Why Medium:** Documentation, not functionality

---

### 17. Manual Pin Suggestions UI
**UI Location:** Grouping page, text input  
**Current:** Not implemented  
**Missing:** Interactive pin suggestion lookup

**Implementation needed:**
```bash
python cli.py lookup "P000" --suggest-groups
```

**Why Medium:** Debug/exploration tool, not batch processing

---

## 🔵 LOW PRIORITY MISSING (Optional)

### 18. Session State Management
**UI Location:** Throughout UI (st.session_state)  
**Current:** Not applicable  
**Missing:** N/A (CLI doesn't need session state)

**Why Low:** Different paradigm for CLI

---

### 19. Progress Indicators
**UI Location:** st.spinner throughout  
**Current:** Simple print statements  
**Missing:** Progress bars

**Why Low:** Cosmetic

---

### 20. Streamlit-Specific UI Elements
**UI Location:** buttons, toggles, sliders, expanders  
**Current:** Not applicable  
**Missing:** N/A

**Why Low:** CLI uses flags instead

---

## SUMMARY TABLE

| Feature | Priority | Current | Implementation Effort |
|---------|----------|---------|----------------------|
| **Category Selection (Power)** | 🔴 CRITICAL | ❌ Missing | 2-3 hours |
| **Power Subcategory Suggestions** | 🔴 CRITICAL | ❌ Missing | 1-2 hours |
| **Incomplete Grouping Fail-Fast** | 🔴 CRITICAL | ❌ Missing | 30 mins |
| **Power Device Side Allocation** | 🔴 CRITICAL | ❌ Missing | 2-3 hours |
| **Strict/Balanced Modes** | 🔴 CRITICAL | ❌ Missing | 1 hour |
| **Sensitivity & Smart Search** | 🟡 HIGH | ❌ Missing | 1 hour |
| **Manual Grouping Input** | 🟡 HIGH | ❌ Missing | 2-3 hours |
| **Dynamic Database Edit** | 🟡 HIGH | ❌ Missing | 2 hours |
| **Auto-fill Threshold** | 🟡 HIGH | ❌ Missing | 1 hour |
| **Four-Sided Symbol** | 🟡 HIGH | ❌ Missing | 1-2 hours |
| **Symbol Preview** | 🟢 MEDIUM | ❌ Missing | 3-4 hours |
| **Parameter Extraction** | 🟢 MEDIUM | ❌ Missing | 2-3 hours |
| **Build Schematic** | 🟢 MEDIUM | ❌ Missing | 2-3 hours |
| **Remove Columns** | 🟢 MEDIUM | ❌ Missing | 30 mins |
| **CSV Annotations** | 🟢 MEDIUM | ❌ Missing | 1 hour |
| **Priority Docs** | 🟢 MEDIUM | ❌ Missing | 15 mins |
| **Pin Lookup** | 🟢 MEDIUM | ❌ Missing | 30 mins |

---

## RECOMMENDED IMPLEMENTATION PHASES

### Phase 1: Core Power Support (CRITICAL) - 6-8 hours
1. ✅ Category & subcategory selection
2. ✅ Power subcategory suggestions
3. ✅ Power-specific side allocation
4. ✅ Power priority mappings
5. ✅ Incomplete grouping validation

**Result:** Power devices fully supported

---

### Phase 2: Advanced Options (HIGH) - 6-8 hours
6. ✅ Sensitivity & smart search flags
7. ✅ Manual grouping via file
8. ✅ Strict/balanced modes
9. ✅ Auto-fill with threshold
10. ✅ Four-sided symbols

**Result:** All common use cases covered

---

### Phase 3: Workflow Tools (MEDIUM) - 8-10 hours
11. ✅ Symbol preview generation
12. ✅ Parameter extraction
13. ✅ Database utilities
14. ✅ Column cleanup commands

**Result:** Complete workflow automation

---

### Phase 4: Polish (MEDIUM/LOW) - 2-3 hours
15. ✅ Progress bars
16. ✅ Documentation commands
17. ✅ Lookup utilities

**Result:** Professional CLI experience

---

## CRITICAL PATH TO FEATURE PARITY

**Must implement for minimal viable CLI:**
1. Power category support (3 hours)
2. Power subcategory suggestions (2 hours)
3. Incomplete grouping validation (30 mins)

**Total:** ~5-6 hours for critical features

**Full feature parity:** ~25-30 hours total

---

## PROPOSED NEW CLI SYNTAX

### Complete Command Structure
```bash
# Grouping with all options
python cli.py build <input> \
  --category {mcu|power} \
  [--subcategory <name>] \
  [--suggest-subcategory] \
  --grouping \
  [--sensitivity] \
  [--smart-search] \
  [--auto-fill] \
  [--threshold <0-100>] \
  [--manual-map <file>] \
  [--strict] \
  [--allow-incomplete]

# Side allocation with all options
python cli.py build <input> \
  --category {mcu|power} \
  [--subcategory <name>] \
  --sidealloc \
  [--mputype] \
  [--strict-population] \
  [--balanced-assignment] \
  [--four-sided] \
  [--fixed-channelwise]

# Utilities
python cli.py suggest <input>
python cli.py preview <output> --format {png|svg|json}
python cli.py clean <input> --remove {electrical-type|description|grouping}
python cli.py database add --pattern <name> --group <group>
python cli.py lookup <pin-name> --suggest-groups
python cli.py extract-params <pdf> --part <part-number>
```

---

## YOUR DECISION NEEDED 🎯

**Which phase should I implement?**

**Option A:** Phase 1 only (Critical - 6-8 hours)
- Power device support
- Validation improvements
- Covers 80% of real use cases

**Option B:** Phase 1 + Phase 2 (Critical + High - 12-16 hours)
- Everything from Option A
- Advanced matching options
- Manual override support
- Covers 95% of use cases

**Option C:** Full implementation (All phases - 25-30 hours)
- Complete feature parity with UI
- Every UI feature has CLI equivalent
- Production-ready

**Option D:** Custom selection
- Pick specific features from the list above
- I implement only what you approve

---

**Please review and tell me:**
1. Which features are MUST-HAVE for your workflow?
2. Which can wait or be skipped?
3. Should I implement Phase 1 now, or do you want to pick specific features?

I'll wait for your approval before implementing! 🚀
