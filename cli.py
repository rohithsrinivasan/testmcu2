#!/usr/bin/env python3
"""
SymbolGen CLI - Command-line interface for IC symbol generation

Commands:
  symbolgen build <input> --grouping
  symbolgen build <input> --sidealloc --mputype
  symbolgen debug <input> --grouping
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
from Grouping.base_functions import general_funct
from Grouping import Assigning_Electrical_Type, Assigning_Pin_Group
from Side_Allocation import priority, side, part_division


class SymbolGenCLI:
    """CLI wrapper for SymbolGen functionality"""

    def __init__(self):
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

    def apply_grouping(self, df, debug=False):
        """Apply pin grouping using existing database"""
        print("\n🔄 Applying Grouping...")

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
                    print("\n  Unresolved pins:")
                    print(unresolved[['Pin Designator', 'Pin Display Name', 'Electrical Type']].to_string(index=False))

        # Apply grouping
        required_cols = ['Pin Designator', 'Pin Display Name', 'Electrical Type', 'Pin Alternate Name']
        self.validate_columns(df, required_cols)

        _, df = general_funct.check_excel_format(
            df, required_cols, optional_column='Grouping'
        )

        print("  ⚙️  Assigning Pin Groups from database...")
        df = Assigning_Pin_Group.grouping_as_per_database(
            df,
            {'MCU Devices': self.databases['mcu']},
            SENSITIVITY=False,
            SMARTSEARCH=False,
            SINGLE_FILE=True
        )

        # Check for unresolved groups
        unresolved_groups = df[df['Grouping'].isna() | (df['Grouping'] == '')]
        if not unresolved_groups.empty:
            print(f"  ⚠️  Warning: {len(unresolved_groups)} pins with unresolved Grouping")
            if debug:
                print("\n  Unresolved groups:")
                print(unresolved_groups[['Pin Designator', 'Pin Display Name', 'Grouping']].to_string(index=False))

        print("✅ Grouping completed")
        return df

    def apply_side_allocation(self, df, mpu_type=False, debug=False):
        """Apply side allocation and priority"""
        print("\n🔄 Applying Side Allocation...")

        # Required columns
        required_cols = ['Pin Designator', 'Pin Display Name', 'Electrical Type', 'Pin Alternate Name', 'Grouping']
        self.validate_columns(df, required_cols)

        # Add priority
        print("  ⚙️  Assigning Priority...")
        _, df = general_funct.check_excel_format(
            df, required_cols, optional_column='Priority'
        )
        df = priority.assigning_priority(df, self.databases['priority_mcu'])

        # Add side
        print("  ⚙️  Assigning Sides...")
        required_cols.append('Priority')
        _, df = general_funct.check_excel_format(
            df, required_cols, optional_column='Side'
        )

        pin_count = len(df)
        print(f"  📊 Total pins: {pin_count}")

        if pin_count <= 80:
            print("  📦 Single-part symbol (≤80 pins)")
            df = side.side_for_singlepart(df)
        else:
            print(f"  📦 Multi-part symbol (>80 pins)")
            if mpu_type:
                print("  ⚙️  MPU Type: Splitting by functional groups...")
                # Use MPU splitting logic
                mpu_split_file = "Side_Allocation/mpu_splitting.json"
                df = part_division.part_division_logic(
                    df,
                    strict_population=False,
                    balanced_assignment=False,
                    MPU_type=True,
                    mpu_splitting_file=mpu_split_file
                )
            else:
                print("  ⚙️  Standard partitioning...")
                df = part_division.part_division_logic(
                    df,
                    strict_population=False,
                    balanced_assignment=False,
                    MPU_type=False
                )

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

    def cmd_build(self, args):
        """Build command: process input with grouping and/or side allocation"""
        df = self.load_input(args.input)

        if args.grouping:
            df = self.apply_grouping(df, debug=False)
            output = self.save_output(df, args.input, 'grouped')
            print(f"\n✨ Success! Grouped pin table saved to: {output}")

        if args.sidealloc:
            if not args.grouping:
                # Verify grouping column exists
                if 'Grouping' not in df.columns:
                    print("⚠️  No Grouping column found. Running grouping first...")
                    df = self.apply_grouping(df, debug=False)

            df = self.apply_side_allocation(df, mpu_type=args.mputype, debug=False)
            output = self.save_output(df, args.input, 'sidealloc')
            print(f"\n✨ Success! Side-allocated pin table saved to: {output}")

        if not args.grouping and not args.sidealloc:
            print("⚠️  No operation specified. Use --grouping or --sidealloc")
            sys.exit(1)

    def cmd_debug(self, args):
        """Debug command: show detailed information about unresolved pins"""
        df = self.load_input(args.input)

        print("\n🔍 Debug Mode: Detailed Analysis\n")
        print("=" * 60)

        if args.grouping:
            df = self.apply_grouping(df, debug=True)

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
                empty_groups = df[df['Grouping'].isna() | (df['Grouping'] == '')]
                if not empty_groups.empty:
                    print(f"\n⚠️  {len(empty_groups)} pins need manual grouping:")
                    print(empty_groups[['Pin Designator', 'Pin Display Name', 'Electrical Type']].to_string(index=False))

            # Save debug output
            output = self.save_output(df, args.input, 'debug')
            print(f"\n💾 Debug output saved to: {output}")


def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        description='SymbolGen - IC Symbol Generation Tool',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Apply grouping only
  symbolgen build pins.json --grouping

  # Apply grouping and side allocation
  symbolgen build pins.json --grouping --sidealloc

  # Apply side allocation with MPU type splitting
  symbolgen build pins.csv --grouping --sidealloc --mputype

  # Debug mode to see unresolved pins
  symbolgen debug pins.json --grouping
        """
    )

    subparsers = parser.add_subparsers(dest='command', help='Command to execute')

    # Build command
    build_parser = subparsers.add_parser('build', help='Build symbol with grouping and/or side allocation')
    build_parser.add_argument('input', help='Input file (JSON, CSV, or XLSX)')
    build_parser.add_argument('--grouping', action='store_true', help='Apply pin grouping')
    build_parser.add_argument('--sidealloc', action='store_true', help='Apply side allocation')
    build_parser.add_argument('--mputype', action='store_true', help='Use MPU-type splitting for multi-part symbols')

    # Debug command
    debug_parser = subparsers.add_parser('debug', help='Debug mode with detailed output')
    debug_parser.add_argument('input', help='Input file (JSON, CSV, or XLSX)')
    debug_parser.add_argument('--grouping', action='store_true', help='Debug grouping process')

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    # Initialize CLI
    cli = SymbolGenCLI()

    # Execute command
    try:
        if args.command == 'build':
            cli.cmd_build(args)
        elif args.command == 'debug':
            cli.cmd_debug(args)
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
