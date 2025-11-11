# Project Workflow Policy

## Mandatory Workflow Requirements

### 0. Design-First Policy - **CRITICAL REQUIREMENT**
- **ALWAYS** create a Jupyter Notebook for design/planning BEFORE writing any code
- Notebook must be named: `design_[feature-name].ipynb`
- **NEVER** skip the design notebook step, even for "quick fixes"
- Incomplete planning leads to inefficient iteration and rework
- See "Design Notebook Template" section below for required structure

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

1. **Design Notebook**: Create Jupyter Notebook with complete design/plan
2. **Review**: Ensure all notebook sections are complete
3. **Assessment**: Check current state and identify what needs to be done
4. **Backup**: Create timestamped backup of current state  
5. **Options**: If multiple approaches exist, present options to user
6. **Selection**: Wait for user to choose which option to implement
7. **Permission**: Confirm scope and get explicit approval
8. **Implementation**: Make only the requested changes following notebook plan
9. **Verification**: Test and validate the changes
10. **Update**: Document deviations in notebook and lessons learned

## Design Notebook Template

Every feature/module must have a design notebook with these sections:

### 1. Problem Statement
- What are we solving?
- User requirements
- Pain points

### 2. Current State Analysis  
- What exists now?
- Files/modules affected
- Current limitations

### 3. Technical Design
- Architecture overview
- Data structures
- API/Interface design
- State management
- Error handling

### 4. Implementation Plan
- Step-by-step tasks
- Dependencies
- Files to modify/create
- Complexity estimates

### 5. Test Strategy
- Test cases
- Edge cases
- Expected outcomes

### 6. Risk Assessment
- Potential issues
- Breaking changes
- Performance impacts

## Violation Examples to Avoid

- ❌ Writing code without design notebook
- ❌ Incomplete design notebook sections

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