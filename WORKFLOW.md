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

### 7. Modularity Policy - **NEW REQUIREMENT**
- **ALWAYS** suggest modular, configuration-driven approaches
- **ALWAYS** favor external config files over hardcoded values
- **ALWAYS** advocate for reusable, maintainable solutions
- If user request suggests hardcoding or non-modular approach:
  - Gently suggest modular alternative
  - Explain benefits (maintainability, reusability, extensibility)
  - Offer example: "Would you like me to [modular approach] instead? This would make it easier to [benefit]."
  - Still respect user's final decision if they prefer direct approach

### 8. Learning Partnership Policy - **NEW REQUIREMENT**
- Both user and AI are learning together
- If user's request deviates from modular best practices, provide guidance:
  - Point out potential maintenance issues
  - Suggest more scalable alternatives
  - Explain trade-offs clearly
- Frame suggestions as collaborative learning, not corrections
- Example: "I notice this approach hardcodes values - would a config file work better here? That way you could reuse it for other displays."

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
- ❌ Implementing hardcoded values when config-driven approach would be better
- ❌ Failing to suggest modular alternatives when user requests non-modular solution

## Good Practice Examples

- ✅ "I could hardcode this, but would a config file work better? You could reuse it for other displays."
- ✅ "This would require editing code for each device. A TOML config would let you add devices without code changes."
- ✅ "I notice this approach isn't very modular. Would you like me to suggest an alternative that's easier to maintain?"
- ✅ "Before implementing, let me suggest a more scalable approach: [explanation]. Which would you prefer?"

## Current Project Context

This project involves dual ST7735 displays with a broadcast SWRESET issue in the Adafruit library that causes Display 2 to reinitialize when Display 1 receives data. The user wants both displays working simultaneously but has not specified what Display 2 should show.

**Key Point**: Technical fixes are requested, but content/display design decisions belong to the user.