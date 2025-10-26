# Project Workflow Policy

## Mandatory Workflow Requirements

### 1. Backup Policy
- **ALWAYS** create a timestamped backup before making ANY modifications to code files
- Use format: `filename.backup_description_YYYYMMDD_HHMMSS`
- Never modify code without first creating a backup

### 2. Permission Policy  
- **NEVER** make changes without explicit user request or permission
- **NEVER** add features, content, or design elements not specifically requested
- **NEVER** make assumptions about what the user wants

### 3. Options Policy - **NEW REQUIREMENT**
- When multiple solution options are identified, **ALWAYS** present them to the user
- **NEVER** implement a solution option without user selection
- **USER MAKES THE CHOICE** of which option to implement
- Wait for explicit user selection before proceeding with any implementation

### 4. Suggestion Policy - **NEW REQUIREMENT**
- **ALWAYS** give suggestions before doing anything
- **NEVER** make changes without presenting the approach first
- User's hardware/programming knowledge is more expansive
- Copilot should operate at suggestion level, not assumption level

### 5. Scope Policy
- Only implement what is explicitly requested
- Do not add cosmetic changes, additional features, or content modifications
- Stick to the technical requirements only

### 6. Restoration Policy
- Keep `main.cpp.clean` as the known-good baseline
- When in doubt, restore to clean baseline before making changes
- Document all departures from the baseline

## Workflow Steps

1. **Assessment**: Check current state and identify what needs to be done
2. **Backup**: Create timestamped backup of current state  
3. **Options**: If multiple approaches exist, present options to user
4. **Selection**: Wait for user to choose which option to implement
5. **Permission**: Confirm scope and get explicit approval
6. **Implementation**: Make only the requested changes
7. **Verification**: Test and validate the changes

## Violation Examples to Avoid

- ❌ Implementing solution without presenting options
- ❌ Adding content/features not requested (like Display 2 custom graphics)
- ❌ Making changes without creating backup first
- ❌ Assuming what the user wants rather than asking
- ❌ Making cosmetic improvements without permission

## Current Project Context

This project involves dual ST7735 displays with a broadcast SWRESET issue in the Adafruit library that causes Display 2 to reinitialize when Display 1 receives data. The user wants both displays working simultaneously but has not specified what Display 2 should show.

**Key Point**: Technical fixes are requested, but content/display design decisions belong to the user.