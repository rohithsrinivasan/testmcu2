# SymbolGen Project Audit Report
**Generated:** 2026-08-17  
**Purpose:** Comprehensive audit for project cleanup, CLI implementation, and size reduction

---

## Executive Summary

This project requires significant restructuring to support the planned CLI interface and reduce technical debt. Total issues identified: **28** across 5 severity levels.

**Project Statistics:**
- Total Size: 11 MB (5.3 MB git, 5.7 MB working files)
- Python Files: 46
- JSON Database Files: 57
- Largest Database: 188 KB (mcu&mpu_database/Combined_Added_mpu.json)
- Function Definitions: 168
- __pycache__ Directories: 9 (should be 0)

---

## CRITICAL SEVERITY (Blocking CLI Implementation)

### 1. No CLI Entry Point ❌
**Impact:** Cannot implement requested command-line interface  
**Details:**
- No CLI parser or entry point module exists
- Required commands missing:
  - `symbolgen -build <part.json> --grouping`
  - `symbolgen -debug <part.json> --grouping`
  - `symbolgen -build <part.json/table> --sidealloc --mputype`
- Current interface is Streamlit-only (web UI)

**Fix Required:**
- Create `cli.py` with argparse/click
- Add console_scripts entry point in setup.py
- Refactor business logic to be callable from both CLI and Streamlit

**Priority:** P0 - Must fix for CLI implementation

---

### 2. Dependency Management Conflicts ❌
**Impact:** Cannot reliably install or distribute package  
**Details:**
- `requirements.txt` has 13 packages
- `setup.py` has 10 different packages
- Mismatches:
  - requirements.txt: `pdfplumber`, `streamlit`, `fuzzywuzzy`, `python-docx`, `Pillow==10.4.0`
  - setup.py: `fitz`, `jpype1`, `reportlab`, `tools` (invalid package name)
- Version pinning inconsistent (only Pillow and streamlit pinned)

**Fix Required:**
- Consolidate to single source of truth
- Remove invalid `tools` dependency
- Add all dependencies to setup.py install_requires
- Pin critical versions to avoid breaking changes

**Priority:** P0 - Must fix before distribution

---

### 3. Missing Environment Configuration ❌
**Impact:** Cannot run the application without manual setup  
**Details:**
- No `.env.example` file provided
- `GEMINI_API_KEY` required but undocumented
- `GOOGLE_API_KEY` also referenced in pin_out_reader_new.py
- Different API key names used (inconsistent)

**Fix Required:**
- Create `.env.example` with required keys
- Document API key acquisition in README
- Standardize on single API key name
- Add validation and helpful error messages

**Priority:** P0 - Blocks new user onboarding

---

### 4. README Completely Wrong ❌
**Impact:** Users have no idea what this project does  
**Details:**
- README describes "PDF Table Extractor" 
- Links to non-existent Heroku app
- No mention of SymbolGen, Renesas, or actual functionality
- No setup instructions for SymbolGen features

**Fix Required:**
- Complete rewrite of README.md
- Document actual purpose (IC symbol generation)
- Add setup, usage, and CLI examples
- Include architecture overview

**Priority:** P0 - Critical for project clarity

---

## HIGH SEVERITY (Major Technical Debt)

### 5. Duplicate Pinout Reader Implementations 🔴
**Impact:** Maintenance burden, confusion, code bloat  
**Details:**
- `Extraction/gemini_api_functions/pinout_reader.py` (incomplete)
- `Extraction/gemini_api_functions/pin_out_reader_new.py` (current)
- Both imported in interface.py
- Newer version uses different API structure

**Fix Required:**
- Delete old `pinout_reader.py`
- Rename `pin_out_reader_new.py` to `pinout_reader.py`
- Update all imports

**Size Reduction:** ~200 lines, minimal storage impact

**Priority:** P1

---

### 6. Redundant Database Files 🔴
**Impact:** 620 KB of duplicate data, confusion about source of truth  
**Details:**
- `Grouping/mcu_database/combined.json` (164 KB)
- `Grouping/mcu&mpu_database/combined.json` (124 KB) 
- `Grouping/mcu&mpu_database/Combined_Added_mpu.json` (188 KB)
- Unclear which is canonical
- Likely contains overlapping data

**Fix Required:**
- Determine correct/latest database
- Delete outdated versions
- Document database schema and update process
- Consider database versioning strategy

**Size Reduction:** ~300-400 KB estimated

**Priority:** P1

---

### 7. Package Structure Invalid 🔴
**Impact:** Cannot install as proper Python package  
**Details:**
- setup.py incomplete (missing long_description_content_type)
- No `__main__.py` for `python -m symbolgen` support
- setup.py lists packages but they're not properly structured
- No version management strategy

**Fix Required:**
- Add proper package metadata
- Create `symbolgen/__main__.py`
- Move core modules under `symbolgen/` package
- Add version.py or use setuptools_scm

**Priority:** P1

---

### 8. Test Files Without Framework 🔴
**Impact:** Tests cannot be run reliably  
**Details:**
- `test_active_screen.py`
- `test_checking_mapjsonfile.py`
- `test_Positive.py`
- No pytest or unittest framework used
- No test discovery possible
- No CI/CD integration

**Fix Required:**
- Convert to proper test framework (pytest recommended)
- Organize under `tests/` directory
- Add test requirements
- Document how to run tests

**Priority:** P1

---

### 9. Streamlit Session State Coupling 🔴
**Impact:** Cannot extract business logic for CLI  
**Details:**
- Heavy use of `st.session_state` throughout
- Business logic tightly coupled to Streamlit UI
- Functions like `pin_table_extraction`, `Assigning_Pin_Group` expect Streamlit context

**Fix Required:**
- Extract pure functions for business logic
- Create separate modules: `core/` for logic, `ui/` for Streamlit
- Pass data explicitly instead of via session_state
- Make CLI and UI thin wrappers around core

**Priority:** P1 - Blocker for clean CLI implementation

---

## MEDIUM SEVERITY (Quality & Maintainability)

### 10. Debug Code in Production 🟡
**Impact:** Performance overhead, cluttered logs  
**Details:**
- `Side_Allocation/base_functions/power_pins_constaints.py` has 10+ debug print statements
- `Side_Allocation/priority.py` has debug prints
- These execute on every run

**Fix Required:**
- Replace with proper logging module
- Add log levels (DEBUG, INFO, WARNING, ERROR)
- Make debug output configurable via CLI flag

**Priority:** P2

---

### 11. Large JSON Files Not Compressed 🟡
**Impact:** 880 KB of uncompressed JSON  
**Details:**
- Top 5 largest:
  - Combined_Added_mpu.json: 188 KB
  - combined.json (mcu_database): 164 KB
  - combined.json (mcu&mpu): 124 KB
  - mcu_io.json: 60 KB
  - cnt.json: 44 KB

**Fix Required:**
- Consider compression (gzip, zstd)
- Or migrate to SQLite database
- Implement lazy loading for databases

**Size Reduction:** ~400-600 KB with compression

**Priority:** P2

---

### 12. Inconsistent File Naming 🟡
**Impact:** Cross-platform compatibility issues, confusion  
**Details:**
- Spaces in directory names: `Build_Schematic/`, `Side_Allocation/`
- Mixed case inconsistent: `Extraction/`, `Grouping/` vs `pages/`, `utils/`
- Special characters: `clock&timing_database/` (& problematic in URLs)
- Inconsistent file extensions: `.txt` vs `.md` for docs

**Fix Required:**
- Standardize on lowercase with underscores for directories
- Remove spaces and special characters
- Update all imports

**Priority:** P2

---

### 13. Git Hygiene Issues 🟡
**Impact:** Bloated repo, harder to navigate history  
**Details:**
- `.gitignore` exists but `__pycache__/` directories still tracked (9 of them)
- `captured_images/` directory may contain large binaries
- No `.gitattributes` for line endings
- Commit messages unclear ("monthly changes", "changes made")

**Fix Required:**
- Run `git rm -r --cached **/__pycache__`
- Add `__pycache__/` explicitly to `.gitignore`
- Add `.gitattributes` for consistent line endings
- Document commit message conventions

**Priority:** P2

---

### 14. Empty and Orphaned Files 🟡
**Impact:** Clutter, confusion about what's active  
**Details:**
- `Extraction/ReadME.txt` - empty
- `Side_Allocation/ReadMe.txt` - empty
- `__init__.py` files all empty (6 of them)
- `packages.txt` - only 22 bytes, unclear purpose
- `quest.txt` - 9 KB, purpose unclear

**Fix Required:**
- Delete empty README files or add content
- Add module docstrings to __init__.py files
- Remove or document quest.txt and packages.txt

**Priority:** P2

---

### 15. Hardcoded Paths 🟡
**Impact:** Windows-specific, breaks on Linux/Mac  
**Details:**
- Backslashes in path strings (e.g., `Side_Allocation\priority_map.json`)
- Hardcoded relative paths throughout
- No use of `pathlib.Path` or `os.path.join`

**Fix Required:**
- Convert all path handling to pathlib
- Make paths OS-agnostic
- Consider config file for customizable paths

**Priority:** P2

---

### 16. No Error Handling Strategy 🟡
**Impact:** Cryptic errors, poor user experience  
**Details:**
- Most functions lack try-except blocks
- No validation of user inputs
- File operations unprotected
- API calls can fail silently

**Fix Required:**
- Add input validation
- Wrap file I/O in try-except
- Add custom exception types
- Provide helpful error messages

**Priority:** P2

---

### 17. Commented Out Code 🟡
**Impact:** Clutter, confusion about intent  
**Details:**
- `interface.py` line 6: `#import grouping_functions`
- `interface.py` line 36: `#st.markdown(hide_st_style, unsafe_allow_html=True)`
- Multiple files have commented sections

**Fix Required:**
- Delete commented code (it's in git history)
- If experimental, move to separate branch
- Document decisions in commit messages

**Priority:** P2

---

### 18. No Type Hints 🟡
**Impact:** Harder to maintain, no static type checking  
**Details:**
- No function has type annotations
- Makes refactoring risky
- IDE autocompletion limited

**Fix Required:**
- Add type hints to function signatures
- Start with public API functions
- Use mypy for validation

**Priority:** P2

---

### 19. Duplicate Functionality 🟡
**Impact:** Maintenance burden  
**Details:**
- `general_funct.py` and `helper_funct.py` likely overlap
- Multiple priority_map JSON files when could use single file with categories
- `methods.py` generic name suggests utility dumping ground

**Fix Required:**
- Audit and merge overlapping utilities
- Consolidate priority maps into single structure
- Rename generic modules to specific purposes

**Priority:** P2

---

### 20. No Documentation 🟡
**Impact:** Hard to onboard, hard to maintain  
**Details:**
- No docstrings in most functions
- No API documentation
- No architecture diagrams
- No data flow documentation

**Fix Required:**
- Add docstrings (Google or NumPy style)
- Create ARCHITECTURE.md
- Document data schemas
- Add inline comments for complex logic

**Priority:** P2

---

## LOW SEVERITY (Polish & Best Practices)

### 21. Inconsistent Import Style 🔵
**Details:**
- Mix of `from X import Y` and `import X.Y as Z`
- Inconsistent ordering (not following PEP 8)

**Fix:** Apply isort or black for consistency

**Priority:** P3

---

### 22. No Logging Configuration 🔵
**Details:**
- Print statements instead of logging
- No log rotation or level management

**Fix:** Implement proper logging with config file

**Priority:** P3

---

### 23. Magic Numbers and Strings 🔵
**Details:**
- Hardcoded values throughout (e.g., `max_rows=80`)
- No constants module

**Fix:** Create constants.py with named constants

**Priority:** P3

---

### 24. No Version Control for Databases 🔵
**Details:**
- JSON databases updated but no changelog
- No version numbers in files

**Fix:** Add version field to JSON, maintain CHANGELOG

**Priority:** P3

---

### 25. Streamlit Config Not Customized 🔵
**Details:**
- No `.streamlit/config.toml`
- Default theme used

**Fix:** Add custom config for branding

**Priority:** P3

---

### 26. No Pre-commit Hooks 🔵
**Details:**
- Could auto-format code
- Could run linters

**Fix:** Add pre-commit config with black, isort, flake8

**Priority:** P3

---

### 27. No CI/CD Pipeline 🔵
**Details:**
- No GitHub Actions / GitLab CI
- No automated testing
- No automated deployments

**Fix:** Add basic CI pipeline

**Priority:** P3

---

### 28. Unclear Module Boundaries 🔵
**Details:**
- `utils/` only has path.py (17 lines)
- `dados/` unclear purpose (Portuguese for "data")
- Business logic mixed with UI code

**Fix:** Better organize module structure

**Priority:** P3

---

## Recommended Action Plan

### Phase 1: CLI Foundation (Week 1)
1. Fix README.md (Issue #4)
2. Consolidate dependencies (Issue #2)
3. Add .env.example (Issue #3)
4. Create cli.py entry point (Issue #1)

### Phase 2: Code Quality (Week 2)
5. Remove duplicate files (Issues #5, #6)
6. Extract business logic from Streamlit (Issue #9)
7. Fix package structure (Issue #7)
8. Clean git history (Issue #13)

### Phase 3: Testing & Documentation (Week 3)
9. Set up proper test framework (Issue #8)
10. Add error handling (Issue #16)
11. Add logging (Issues #10, #22)
12. Write documentation (Issue #20)

### Phase 4: Polish (Week 4)
13. Fix naming conventions (Issue #12)
14. Add type hints (Issue #18)
15. Compress databases (Issue #11)
16. Clean up remaining issues (Issues #14-#28)

---

## Size Reduction Opportunities

| Action | Estimated Savings |
|--------|------------------|
| Remove duplicate databases | 300-400 KB |
| Compress JSON files | 400-600 KB |
| Remove __pycache__ from git | 50-100 KB |
| Remove old pinout_reader | 5-10 KB |
| Clean git history (optional) | 1-2 MB |
| **Total Potential Reduction** | **~2-3 MB (20-30%)** |

---

## CLI Implementation Roadmap

### Required Components

1. **Command Parser** (`cli.py`)
   ```python
   symbolgen build <part.json> --grouping
   symbolgen build <part.json> --sidealloc --mputype
   symbolgen debug <part.json> --grouping
   ```

2. **Business Logic Extraction**
   - Extract from `pages/01_Grouping_2.py`
   - Extract from `pages/02_Side_Allocation.py`
   - Remove Streamlit dependencies

3. **Configuration Management**
   - Replace session_state with config objects
   - Support config files (YAML/JSON)

4. **Output Formats**
   - JSON output for machine consumption
   - Pretty-printed table for human consumption
   - CSV export option

5. **Setup.py Entry Points**
   ```python
   entry_points={
       'console_scripts': [
           'symbolgen=symbolgen.cli:main',
       ],
   }
   ```

---

## Questions for Resolution

1. **Database Consolidation**: Which is the correct database?
   - `mcu_database/combined.json`
   - `mcu&mpu_database/Combined_Added_mpu.json`

2. **API Keys**: Should we support both Google APIs or migrate to one?
   - `GEMINI_API_KEY` vs `GOOGLE_API_KEY`

3. **Test Strategy**: Keep existing tests or start fresh with pytest?

4. **Deployment Target**: Is this for internal use only or external distribution?

5. **Python Version Support**: What's the minimum Python version? (affects type hints, f-strings, etc.)

---

## Conclusion

The project has solid core functionality but requires significant refactoring to support CLI usage and reduce technical debt. The critical path is:

1. ✅ Create CLI entry point
2. ✅ Decouple business logic from Streamlit
3. ✅ Fix dependency management
4. ✅ Clean up duplicate files

Estimated effort: **3-4 weeks** for comprehensive cleanup and CLI implementation.

---

**Report Generated by:** Claude Code Audit  
**Contact:** rohith.srinivasan.wr@renesas.com  
**Last Updated:** 2026-08-17
