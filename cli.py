#!/usr/bin/env python3
"""
SymbolGen CLI - Command-line interface for IC symbol generation

Complete feature parity with Streamlit UI
"""

import argparse
import sys
import json
import pandas as pd
from pathlib import Path

# Fix Windows encoding for console output
if sys.platform == 'win32':
    import codecs
    if sys.stdout.encoding != 'utf-8':
        sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    if sys.stderr.encoding != 'utf-8':
        sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

# Import existing modules
from Grouping.base_functions import general_funct, helper_funct
from Grouping import Assigning_Electrical_Type, Assigning_Pin_Group
from Side_Allocation import priority, side, part_division
from Side_Allocation.base_functions import four_sided_symbol


class SymbolGenCLI:
    """CLI wrapper for SymbolGen functionality"""

    def __init__(self):
        # MCU databases
        self.databases = {
            'mcu': 'Grouping/mcu&mpu_database/Combined_Added_mpu.json',
            'pin_types': {
                'Input': 'Grouping/mcu_database/mcu_input.json',
                'Power': 'Grouping/mcu_database/mcu_power.json',
                'Output': 'Grouping/mcu_database/mcu_output.json',
                'I/O': 'Grouping/mcu_database/mcu_io.json',
                'Passive': 'Grouping/mcu_database/mcu_passive.json'
            },
            'priority_mcu': 'Side_Allocation/priority_map_mpuadded.json'
        }

        # Power databases
        self.power_databases = {
            "Buck": 'Grouping/power_database/Buck.json',
            "Boost": 'Grouping/power_database/Boost.json',
            "Buck-Boost": 'Grouping/power_database/Buck-Boost.json',
            "LDO": 'Grouping/power_database/LDO.json',
            "Charge-Pump": 'Grouping/power_database/Charge-pump.json',
            "FlyBack": 'Grouping/power_database/FlyBack.json',
            "Battery-Charger-IC": 'Grouping/power_database/Battery-Charger-IC.json',
            "PWM-Controller": 'Grouping/power_database/pwm-controller.json',
            "Voltage-References": 'Grouping/power_database/Voltage-References.json',
            "Power-Supply-Support": 'Grouping/power_database/Power-Supply-Support.json',
            "FET-Drivers": 'Grouping/power_database/FET-Drivers.json',
            "Battery-Protectors-Monitors-Balancers": "Grouping/power_database/Battery-Protectors-Monitors-Balancers.json",
            "LED-Drivers": "Grouping/power_database/LED-Drivers.json",
            "DC-DC-Power-Modules": "Grouping/power_database/DC-DC Power Modules.json",
            "Multiphase-DC-DC-Switching-Controllers": "Grouping/power_database/Multiphase DC-DC Switching Controllers.json",
            "ORing-FET-Controllers": "Grouping/power_database/ORing-FET-Controllers.json",
            "Protected-Intelligent-Power-Devices": "Grouping/power_database/Protected-Intelligent-Power-Devices.json",
            "Smart-Power-Stages": "Grouping/power_database/Smart-Power-Stages.json",
            "Solid-State-Lighting-Interface-Ics": "Grouping/power_database/Solid-State-Lighting-Interface-Ics.json",
            "AC-DC-Isolated-DC-DC-Converters": "Grouping/power_database/AC-DC & Isolated DC-DC Converters.json",
            "USB-Type-C-Port-Manager": "Grouping/power_database/USB Type-C Port Manager.json",
            "PMIC": 'Grouping/power_database/PMIC.json'
        }

        # Power priority maps
        self.power_priority = {
            "Buck": "Side_Allocation/priority_map_buck.json",
            "Boost": "Side_Allocation/priority_map_boost.json",
            "LDO": "Side_Allocation/priority_map_ldo.json",
            "Buck-Boost": "Side_Allocation/priority_map_buck-boost.json",
            "Charge-Pump": "Side_Allocation/priority_map_charge-pump.json",
            "FlyBack": "Side_Allocation/priority_map_flyback.json",
            "Battery-Charger-IC": 'Side_Allocation/priority_map_battery-charger-IC.json',
            "PWM-Controller": 'Side_Allocation/priority_map_pwm-controller.json',
            "Voltage-References": 'Side_Allocation/priority_map_voltage-references.json',
            "Power-Supply-Support": 'Side_Allocation/priority_map_power-supply-support.json',
            "FET-Drivers": 'Side_Allocation/priority_map_fet-drivers.json',
            "Battery-Protectors-Monitors-Balancers": "Side_Allocation/priority_map_Battery-Protectors-Monitors-Balancers.json",
            "LED-Drivers": "Side_Allocation/priority_map_led-drivers.json",
            "DC-DC-Power-Modules": "Side_Allocation/priority_map_dc-dc-power-modules.json",
            "Multiphase-DC-DC-Switching-Controllers": "Side_Allocation/priority_map_multiphase-dcdc-switching-controllers.json",
            "ORing-FET-Controllers": "Side_Allocation/priority_map_oring-fet-controllers.json",
            "Protected-Intelligent-Power-Devices": "Side_Allocation/priority_map_protected-intelligent-power-devices.json",
            "Smart-Power-Stages": "Side_Allocation/priority_map_smart-power-stages.json",
            "Solid-State-Lighting-Interface-Ics": "Side_Allocation/priority_map_solid-state-lightening-interface-ics.json",
            "AC-DC-Isolated-DC-DC-Converters": "Side_Allocation/priority_map_ac-dc&isolated-dc-dc-converters.json",
            "USB-Type-C-Port-Manager": "Side_Allocation/priority_map_usb-type-c-port-manager.json",
            "PMIC": 'Side_Allocation/priority_map_PMIC.json'
        }

    def load_input(self, input_path):
        """Load input file (JSON or CSV)"""
        input_path = Path(input_path)

        if not input_path.exists():
            print(f"❌ Error: Input file not found: {input_path}")
            sys.exit(1)

        print(f"📂 Loading: {input_path}")

        try:
            if input_path.suffix == '.json':
                with open(input_path, 'r') as f:
                    data = json.load(f)
                    if isinstance(data, dict) and 'pins' in data:
                        df = pd.DataFrame(data['pins'])
                    elif isinstance(data, list):
                        df = pd.DataFrame(data)
                    else:
                        df = pd.DataFrame([data])
            elif input_path.suffix in ['.csv', '.xlsx']:
                if input_path.suffix == '.csv':
                    df = pd.read_csv(input_path)
                else:
                    df = pd.read_excel(input_path)
            else:
                print(f"❌ Error: Unsupported file format: {input_path.suffix}")
                print("   Supported formats: .json, .csv, .xlsx")
                sys.exit(1)

            print(f"✅ Loaded {len(df)} pins")
            return df

        except Exception as e:
            print(f"❌ Error loading file: {e}")
            sys.exit(1)

    def validate_columns(self, df, required_cols):
        """Validate that DataFrame has required columns"""
        missing = [col for col in required_cols if col not in df.columns]
        if missing:
            print(f"❌ Error: Missing required columns: {', '.join(missing)}")
            print(f"   Found columns: {', '.join(df.columns)}")
            sys.exit(1)

    def suggest_power_subcategory(self, df):
        """Suggest best matching Power subcategory"""
        print("\n🔍 Analyzing Power subcategories...")

        suggestions = Assigning_Pin_Group.suggest_power_subcategories(df, self.power_databases)

        if not suggestions:
            print("⚠️  No Power subcategory matches found")
            return None

        print("\n📊 Subcategory Match Analysis:")
        print("=" * 60)

        for i, sug in enumerate(suggestions[:5], 1):
            percentage = sug['percentage']
            filled = sug['filled']
            total = sug['total']
            subcat = sug['subcategory']

            if percentage == 100:
                icon = "✅"
            elif percentage >= 90:
                icon = "⚠️ "
            else:
                icon = "ℹ️ "

            print(f"{icon} {i}. {subcat:40s} {percentage:5.1f}% ({filled}/{total} pins)")

        best_match = suggestions[0]
        print("=" * 60)

        if best_match['percentage'] == 100:
            print(f"\n✨ Recommended: {best_match['subcategory']} (100% match)")
            return best_match['subcategory']
        elif best_match['percentage'] >= 80:
            print(f"\n💡 Suggested: {best_match['subcategory']} ({best_match['percentage']:.1f}% match)")
            return best_match['subcategory']
        else:
            print(f"\n⚠️  Best match: {best_match['subcategory']} ({best_match['percentage']:.1f}% match)")
            print("   Consider manual review")
            return best_match['subcategory']

    def apply_grouping(self, df, category='mcu', subcategory=None, auto_fill=False, threshold=100, debug=False):
        """Apply pin grouping using database"""
        print("\n🔄 Applying Grouping...")
        print(f"   Category: {category.upper()}")
        if subcategory:
            print(f"   Subcategory: {subcategory}")

        # Required columns for grouping
        required_cols = ['Pin Designator', 'Pin Display Name', 'Pin Alternate Name']
        self.validate_columns(df, required_cols)

        # Check if Electrical Type exists
        if 'Electrical Type' not in df.columns:
            print("  ⚙️  Assigning Electrical Types from database...")
            _, df = general_funct.check_excel_format(
                df, required_cols, optional_column='Electrical Type'
            )
            df = Assigning_Electrical_Type.pin_type_as_per_database(
                df, self.databases['pin_types'], sensitivity=False
            )

            # Check for unresolved types
            unresolved = df[df['Electrical Type'].isin(['NAv', 'NAss'])]
            if not unresolved.empty:
                print(f"  ⚠️  Warning: {len(unresolved)} pins with unresolved Electrical Type")
                if debug:
                    print("\n  Unresolved Electrical Types:")
                    print(unresolved[['Pin Designator', 'Pin Display Name', 'Electrical Type']].to_string(index=False))

        # Apply grouping based on category
        required_cols = ['Pin Designator', 'Pin Display Name', 'Electrical Type', 'Pin Alternate Name']
        self.validate_columns(df, required_cols)

        _, df = general_funct.check_excel_format(
            df, required_cols, optional_column='Grouping'
        )

        print("  ⚙️  Assigning Pin Groups from database...")

        if category == 'mcu':
            selected_database = {'MCU Devices': self.databases['mcu']}
        elif category == 'power':
            if not subcategory:
                print("❌ Error: Power category requires --subcategory")
                sys.exit(1)
            if subcategory not in self.power_databases:
                print(f"❌ Error: Invalid Power subcategory: {subcategory}")
                print(f"   Available: {', '.join(self.power_databases.keys())}")
                sys.exit(1)
            selected_database = {subcategory: self.power_databases[subcategory]}
        else:
            print(f"❌ Error: Invalid category: {category}")
            sys.exit(1)

        df = Assigning_Pin_Group.grouping_as_per_database(
            df,
            selected_database,
            SENSITIVITY=False,
            SMARTSEARCH=False,
            SINGLE_FILE=True
        )

        # Auto-fill if requested
        if auto_fill and threshold < 100:
            print(f"  ⚙️  Auto-filling groups (threshold: {threshold}%)...")
            # Load database JSON for auto-fill
            db_path = list(selected_database.values())[0]
            with open(db_path, 'r') as f:
                json_data = json.load(f)

            # Find unresolved
            unresolved_mask = df['Grouping'].isna() | (df['Grouping'] == '')
            if unresolved_mask.any():
                unresolved_df = df[unresolved_mask].copy()
                filled_df = helper_funct.auto_fill_grouping_if_exact_match(
                    unresolved_df, json_data, threshold
                )
                df.loc[unresolved_mask, 'Grouping'] = filled_df['Grouping']
                filled_count = filled_df['Grouping'].notna().sum()
                if filled_count > 0:
                    print(f"  ✅ Auto-filled {filled_count} pins")

        # Check for unresolved groups
        unresolved_groups = df[df['Grouping'].isna() | (df['Grouping'] == '')]

        if not unresolved_groups.empty:
            print(f"  ⚠️  Warning: {len(unresolved_groups)} pins with unresolved Grouping")
            if debug:
                print("\n  Unresolved Groups:")
                print(unresolved_groups[['Pin Designator', 'Pin Display Name', 'Grouping']].to_string(index=False))

        print("✅ Grouping completed")
        return df, unresolved_groups

    def apply_side_allocation(self, df, category='mcu', subcategory=None, mpu_type=False,
                             strict_population=False, balanced_assignment=False,
                             four_sided=False, debug=False):
        """Apply side allocation and priority"""
        print("\n🔄 Applying Side Allocation...")
        print(f"   Category: {category.upper()}")
        if subcategory:
            print(f"   Subcategory: {subcategory}")

        # Required columns
        required_cols = ['Pin Designator', 'Pin Display Name', 'Electrical Type', 'Pin Alternate Name', 'Grouping']
        self.validate_columns(df, required_cols)

        # Add priority
        print("  ⚙️  Assigning Priority...")
        _, df = general_funct.check_excel_format(
            df, required_cols, optional_column='Priority'
        )

        # Get priority file based on category
        if category == 'mcu':
            priority_file = self.databases['priority_mcu']
        elif category == 'power':
            if not subcategory or subcategory not in self.power_priority:
                print(f"❌ Error: Invalid Power subcategory for priority: {subcategory}")
                sys.exit(1)
            priority_file = self.power_priority[subcategory]
        else:
            print(f"❌ Error: Invalid category: {category}")
            sys.exit(1)

        df = priority.assigning_priority(df, priority_file)

        # Add side
        print("  ⚙️  Assigning Sides...")
        required_cols.append('Priority')
        _, df = general_funct.check_excel_format(
            df, required_cols, optional_column='Side'
        )

        pin_count = len(df)
        print(f"  📊 Total pins: {pin_count}")

        if category == 'mcu':
            if pin_count <= 80 and not four_sided:
                print("  📦 Single-part symbol (≤80 pins)")
                df = side.side_for_singlepart(df)
            elif four_sided:
                print("  📦 Four-sided symbol")
                df = four_sided_symbol.assign_pin_sides(df, use_four_sided=True)
            else:
                print(f"  📦 Multi-part symbol (>80 pins)")
                if strict_population:
                    print("  ⚙️  Mode: Strict Population")
                if balanced_assignment:
                    print("  ⚙️  Mode: Balanced Assignment")
                if mpu_type:
                    print("  ⚙️  MPU Type: Splitting by functional groups...")

                mpu_split_file = "Side_Allocation/mpu_splitting.json"
                df_dict = part_division.partitioning(
                    df,
                    mpu_split_file,
                    Strict_Population=strict_population,
                    Balanced_Assignment=balanced_assignment,
                    MPU_type=mpu_type
                )
                df = side.side_for_multipart(df_dict)

        elif category == 'power':
            # Power device side allocation
            print("  📦 Power device side allocation")
            df['Side'] = None
            df.loc[df['Priority'].str.startswith('L', na=False), 'Side'] = 'Left'
            df.loc[df['Priority'].str.startswith('R', na=False), 'Side'] = 'Right'

        print("✅ Side allocation completed")
        return df

    def save_output(self, df, input_path, suffix):
        """Save output file"""
        input_path = Path(input_path)
        output_path = input_path.parent / f"{input_path.stem}_{suffix}{input_path.suffix}"

        print(f"\n💾 Saving output to: {output_path}")

        try:
            if output_path.suffix == '.json':
                df.to_json(output_path, orient='records', indent=2)
            elif output_path.suffix == '.csv':
                df.to_csv(output_path, index=False)
            elif output_path.suffix == '.xlsx':
                df.to_excel(output_path, index=False)

            print(f"✅ Output saved successfully")
            return output_path

        except Exception as e:
            print(f"❌ Error saving file: {e}")
            sys.exit(1)

    def cmd_suggest(self, args):
        """Suggest best Power subcategory"""
        df = self.load_input(args.input)

        print("\n" + "=" * 60)
        print("Power Subcategory Suggestion")
        print("=" * 60)

        subcategory = self.suggest_power_subcategory(df)

        if subcategory:
            print(f"\n💡 To use this suggestion:")
            print(f"   python cli.py build {args.input} --grouping \\")
            print(f"       --category power --subcategory {subcategory}")

    def cmd_build(self, args):
        """Build command: process input with grouping and/or side allocation"""
        df = self.load_input(args.input)

        # Auto-suggest subcategory if Power and not specified
        if args.category == 'power' and not args.subcategory and not args.suggest_subcategory:
            print("\n💡 Tip: Use --suggest-subcategory to auto-detect best match")
            print("   Or specify --subcategory <name>")
            sys.exit(1)

        if args.suggest_subcategory and args.category == 'power':
            args.subcategory = self.suggest_power_subcategory(df)
            if not args.subcategory:
                print("❌ Could not determine subcategory")
                sys.exit(1)

        if args.grouping:
            df, unresolved = self.apply_grouping(
                df,
                category=args.category,
                subcategory=args.subcategory,
                auto_fill=args.auto_fill,
                threshold=args.threshold,
                debug=False
            )

            # Check for incomplete grouping if strict mode
            if not args.allow_incomplete and not unresolved.empty:
                print(f"\n❌ GROUPING INCOMPLETE: {len(unresolved)} pins unresolved")
                print("   Status: NOT AVAILABLE")
                print("\n   Unresolved pins:")
                print(unresolved[['Pin Designator', 'Pin Display Name']].to_string(index=False))
                print(f"\n💡 Options:")
                print(f"   1. Run with --debug-grouping to see details")
                print(f"   2. Use --auto-fill --threshold 80 to fill partial matches")
                print(f"   3. Use --allow-incomplete to proceed anyway")
                sys.exit(1)

            output = self.save_output(df, args.input, 'grouped')
            print(f"\n✨ Success! Grouped pin table saved to: {output}")

        if args.sidealloc:
            if not args.grouping:
                # Verify grouping column exists
                if 'Grouping' not in df.columns:
                    print("⚠️  No Grouping column found. Running grouping first...")
                    df, unresolved = self.apply_grouping(
                        df,
                        category=args.category,
                        subcategory=args.subcategory,
                        auto_fill=args.auto_fill,
                        threshold=args.threshold,
                        debug=False
                    )

                    if not args.allow_incomplete and not unresolved.empty:
                        print(f"\n❌ GROUPING INCOMPLETE: Cannot proceed to side allocation")
                        print(f"   {len(unresolved)} pins need grouping first")
                        sys.exit(1)

            df = self.apply_side_allocation(
                df,
                category=args.category,
                subcategory=args.subcategory,
                mpu_type=args.mputype,
                strict_population=args.strict_population,
                balanced_assignment=args.balanced_assignment,
                four_sided=args.four_sided,
                debug=False
            )
            output = self.save_output(df, args.input, 'sidealloc')
            print(f"\n✨ Success! Side-allocated pin table saved to: {output}")

        if not args.grouping and not args.sidealloc:
            print("⚠️  No operation specified. Use --grouping or --sidealloc")
            sys.exit(1)

    def cmd_debug_grouping(self, args):
        """Debug grouping: detailed analysis"""
        df = self.load_input(args.input)

        print("\n🔍 DEBUG MODE: Grouping Analysis")
        print("=" * 60)

        # Auto-suggest if Power
        if args.category == 'power' and not args.subcategory and not args.suggest_subcategory:
            print("\n⚠️  Power category requires subcategory")
            print("   Running auto-detection...\n")
            args.subcategory = self.suggest_power_subcategory(df)
            if not args.subcategory:
                print("❌ Could not determine subcategory")
                sys.exit(1)
        elif args.suggest_subcategory and args.category == 'power':
            args.subcategory = self.suggest_power_subcategory(df)

        df, unresolved = self.apply_grouping(
            df,
            category=args.category,
            subcategory=args.subcategory,
            auto_fill=args.auto_fill,
            threshold=args.threshold,
            debug=True
        )

        # Show summary
        print("\n" + "=" * 60)
        print("📊 Grouping Summary:")
        print("=" * 60)

        if 'Electrical Type' in df.columns:
            print("\nElectrical Type Distribution:")
            print(df['Electrical Type'].value_counts().to_string())

        if 'Grouping' in df.columns:
            print("\nGrouping Distribution:")
            grouping_counts = df['Grouping'].value_counts()
            print(grouping_counts.to_string())

            # Show empty/unresolved
            if not unresolved.empty:
                print(f"\n⚠️  INCOMPLETE: {len(unresolved)} pins need manual grouping:")
                print(unresolved[['Pin Designator', 'Pin Display Name', 'Electrical Type']].to_string(index=False))
                print("\n❌ Status: NOT AVAILABLE - Grouping incomplete")
            else:
                print("\n✅ Status: COMPLETE - All pins grouped")

        # Save debug output
        output = self.save_output(df, args.input, 'debug_grouping')
        print(f"\n💾 Debug output saved to: {output}")

    def cmd_debug_sidealloc(self, args):
        """Debug side allocation: detailed analysis"""
        df = self.load_input(args.input)

        print("\n🔍 DEBUG MODE: Side Allocation Analysis")
        print("=" * 60)

        # Check if already grouped
        if 'Grouping' not in df.columns:
            print("⚠️  No Grouping column. Running grouping first...\n")
            df, unresolved = self.apply_grouping(
                df,
                category=args.category,
                subcategory=args.subcategory,
                debug=True
            )
            if not unresolved.empty:
                print(f"\n❌ Cannot proceed: {len(unresolved)} pins ungrouped")
                sys.exit(1)

        df = self.apply_side_allocation(
            df,
            category=args.category,
            subcategory=args.subcategory,
            mpu_type=args.mputype,
            strict_population=args.strict_population,
            balanced_assignment=args.balanced_assignment,
            four_sided=args.four_sided,
            debug=True
        )

        # Show summary
        print("\n" + "=" * 60)
        print("📊 Side Allocation Summary:")
        print("=" * 60)

        if 'Priority' in df.columns:
            print("\nPriority Distribution:")
            print(df['Priority'].value_counts().to_string())

        if 'Side' in df.columns:
            print("\nSide Distribution:")
            print(df['Side'].value_counts().to_string())

        if 'Part' in df.columns:
            print("\nPart Distribution:")
            print(df['Part'].value_counts().to_string())

        # Save debug output
        output = self.save_output(df, args.input, 'debug_sidealloc')
        print(f"\n💾 Debug output saved to: {output}")


def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        description='SymbolGen - IC Symbol Generation Tool',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Suggest Power subcategory
  python cli.py suggest pins.json

  # MCU grouping
  python cli.py build pins.json --grouping --category mcu

  # Power grouping with auto-detection
  python cli.py build pins.json --grouping --category power --suggest-subcategory

  # Power grouping with specific subcategory
  python cli.py build pins.json --grouping --category power --subcategory Buck

  # Auto-fill partial matches
  python cli.py build pins.json --grouping --auto-fill --threshold 80

  # Complete flow with side allocation
  python cli.py build pins.json --grouping --sidealloc --category mcu

  # Four-sided symbol
  python cli.py build pins.json --grouping --sidealloc --four-sided

  # MPU type splitting
  python cli.py build pins.json --grouping --sidealloc --mputype

  # Debug modes
  python cli.py debug-grouping pins.json --category mcu
  python cli.py debug-sidealloc pins.json --category mcu
        """
    )

    subparsers = parser.add_subparsers(dest='command', help='Command to execute')

    # Suggest command
    suggest_parser = subparsers.add_parser('suggest', help='Suggest best Power subcategory')
    suggest_parser.add_argument('input', help='Input file (JSON, CSV, or XLSX)')

    # Build command
    build_parser = subparsers.add_parser('build', help='Build symbol with grouping and/or side allocation')
    build_parser.add_argument('input', help='Input file (JSON, CSV, or XLSX)')
    build_parser.add_argument('--category', choices=['mcu', 'power'], default='mcu',
                             help='Device category (default: mcu)')
    build_parser.add_argument('--subcategory', help='Power subcategory (required for Power)')
    build_parser.add_argument('--suggest-subcategory', action='store_true',
                             help='Auto-detect best Power subcategory')
    build_parser.add_argument('--grouping', action='store_true', help='Apply pin grouping')
    build_parser.add_argument('--sidealloc', action='store_true', help='Apply side allocation')
    build_parser.add_argument('--mputype', action='store_true',
                             help='Use MPU-type splitting for multi-part symbols')
    build_parser.add_argument('--strict-population', action='store_true',
                             help='Enable strict population mode')
    build_parser.add_argument('--balanced-assignment', action='store_true',
                             help='Enable balanced assignment mode')
    build_parser.add_argument('--four-sided', action='store_true',
                             help='Create four-sided symbol (Top/Bottom/Left/Right)')
    build_parser.add_argument('--auto-fill', action='store_true',
                             help='Auto-fill partial matches')
    build_parser.add_argument('--threshold', type=int, default=100,
                             help='Minimum match percentage for auto-fill (default: 100)')
    build_parser.add_argument('--allow-incomplete', action='store_true',
                             help='Allow incomplete grouping (proceed with warnings)')

    # Debug grouping command
    debug_group_parser = subparsers.add_parser('debug-grouping',
                                               help='Debug grouping with detailed analysis')
    debug_group_parser.add_argument('input', help='Input file (JSON, CSV, or XLSX)')
    debug_group_parser.add_argument('--category', choices=['mcu', 'power'], default='mcu',
                                   help='Device category (default: mcu)')
    debug_group_parser.add_argument('--subcategory', help='Power subcategory')
    debug_group_parser.add_argument('--suggest-subcategory', action='store_true',
                                   help='Auto-detect best Power subcategory')
    debug_group_parser.add_argument('--auto-fill', action='store_true',
                                   help='Auto-fill partial matches')
    debug_group_parser.add_argument('--threshold', type=int, default=100,
                                   help='Minimum match percentage for auto-fill (default: 100)')

    # Debug sidealloc command
    debug_side_parser = subparsers.add_parser('debug-sidealloc',
                                             help='Debug side allocation with detailed analysis')
    debug_side_parser.add_argument('input', help='Input file (JSON, CSV, or XLSX)')
    debug_side_parser.add_argument('--category', choices=['mcu', 'power'], default='mcu',
                                  help='Device category (default: mcu)')
    debug_side_parser.add_argument('--subcategory', help='Power subcategory')
    debug_side_parser.add_argument('--mputype', action='store_true',
                                  help='Use MPU-type splitting')
    debug_side_parser.add_argument('--strict-population', action='store_true',
                                  help='Enable strict population mode')
    debug_side_parser.add_argument('--balanced-assignment', action='store_true',
                                  help='Enable balanced assignment mode')
    debug_side_parser.add_argument('--four-sided', action='store_true',
                                  help='Create four-sided symbol')

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    # Initialize CLI
    cli = SymbolGenCLI()

    # Execute command
    try:
        if args.command == 'suggest':
            cli.cmd_suggest(args)
        elif args.command == 'build':
            cli.cmd_build(args)
        elif args.command == 'debug-grouping':
            cli.cmd_debug_grouping(args)
        elif args.command == 'debug-sidealloc':
            cli.cmd_debug_sidealloc(args)
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user")
        sys.exit(130)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
