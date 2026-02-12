# OSImager Configuration Documentation

This directory contains comprehensive documentation and tools for OSImager's flexible configuration system.

## 📁 Files Overview

### Documentation
- **`CONFIGURATION.md`** - Complete configuration format reference
- **`examples/`** - Example configurations showing advanced features
- **`schemas/`** - JSON schemas for validation

### Validation Tools
- **`validate_config.py`** - Configuration validation utility
- **`tests/test_config_validation.py`** - Unit tests for validation

## 🚀 Quick Start

### 1. Validate a Single Configuration
```bash
# Auto-detect type and validate
python validate_config.py data/specs/rhel-9/spec.json

# Explicit type validation
python validate_config.py data/platforms/vmware.json --schema-type platform

# Check JSON syntax only
python validate_config.py --check-syntax data/specs/centos-7/spec.json
```

### 2. Validate All Configurations
```bash
# Validate entire project
python validate_config.py --validate-all

# Quiet mode (summary only)
python validate_config.py --validate-all --quiet
```

### 3. Run Tests
```bash
# Install test dependencies
pip install pytest jsonschema

# Run validation tests
python -m pytest tests/test_config_validation.py -v
```

## 🏗️ Configuration Structure

OSImager uses a hierarchical configuration system with these core concepts:

### Standard Sections
- **`files`** - File generation and templates
- **`evars`** - Environment variables
- **`defs`** - Variable definitions
- **`variables`** - Additional variables
- **`pre_provisioners`** - Pre-build actions
- **`provisioners`** - Main provisioning
- **`post_provisioners`** - Post-build actions
- **`config`** - Platform configuration

### Conditional Modifiers
- **`platform_specific`** - Platform-dependent settings
- **`location_specific`** - Environment-dependent settings
- **`dist_specific`** - Distribution-specific settings
- **`version_specific`** - Version-dependent settings
- **`arch_specific`** - Architecture-dependent settings

### Nesting Rules
1. **Modifiers can contain sections** - Each condition can define its own configuration
2. **Sections can contain modifiers** - Each section can have conditional logic
3. **Modifiers can contain other modifiers** - Complex multi-level conditions

## 🔧 Variable Substitution

OSImager supports multiple variable substitution syntaxes:

```json
{
  "basic_var": ">>name<<",
  "numeric_expr": "#>cpu_sockets*cpu_cores<#",
  "content_include": "%>cd_files<%",
  "python_expr": "E>'>>iso_path<<>>iso_name<<' if >>local_only<< else '>>iso_url<<'<E"
}
```

## 📋 Example Configurations

### Simple Platform-Specific Configuration
```json
{
  "defs": {
    "base_memory": 4096
  },
  "platform_specific": [
    {
      "platform": "vmware",
      "config": {
        "guest_os_type": "rhel9-64"
      }
    },
    {
      "platform": "virtualbox",
      "config": {
        "guest_os_type": "RedHat9_64"
      }
    }
  ]
}
```

### Complex Nested Modifiers
```json
{
  "platform_specific": [
    {
      "platform": "vmware",
      "arch_specific": [
        {
          "arch": "x86_64",
          "version_specific": [
            {
              "version": "9.0",
              "config": {
                "guest_os_type": "rhel9-64"
              }
            }
          ]
        }
      ]
    }
  ]
}
```

## ✅ Validation Features

The validation system provides:

- **JSON Schema Validation** - Structural validation against schemas
- **Syntax Checking** - JSON syntax validation
- **Type Detection** - Automatic configuration type detection
- **Batch Validation** - Validate entire directories
- **Detailed Error Reports** - Clear error messages with context

### Schema Coverage
- **Spec Files** - Complete schema for OS specifications
- **Platform Files** - Schema for platform configurations
- **Location Files** - Schema for location configurations (future)

## 🎯 Best Practices

### 1. Use Inheritance
```json
{
  "include": "linux-base",
  "platform_specific": [
    {
      "platform": "vmware",
      "include": "vmware-defaults"
    }
  ]
}
```

### 2. Minimize Duplication
```json
{
  "defs": {
    "base_memory": 4096
  },
  "arch_specific": [
    {
      "arch": "aarch64",
      "defs": {
        "memory": "#>base_memory*2<#"
      }
    }
  ]
}
```

### 3. Document Complex Logic
```json
{
  "config": {
    "firmware": "E>'bios' if '>>version<<'.startswith('9.0') else 'efi'<E"
  }
}
```

### 4. Validate Early and Often
```bash
# Validate before committing
python validate_config.py --validate-all

# Add validation to CI/CD
python validate_config.py data/specs/new-spec/spec.json
```

## 🔍 Troubleshooting

### Common Issues

1. **Missing Required Fields**
   ```
   Error: At provides: 'versions' is a required property
   ```
   **Solution**: Add missing required fields to spec files

2. **Invalid JSON Syntax**
   ```
   Error: JSON syntax error: Expecting ',' delimiter: line 15 column 5
   ```
   **Solution**: Fix JSON syntax (missing commas, brackets, quotes)

3. **Schema Not Found**
   ```
   Error: Schema for type 'spec' not available
   ```
   **Solution**: Install jsonschema: `pip install jsonschema`

4. **Type Detection Failed**
   ```
   Error: Could not detect configuration type
   ```
   **Solution**: Use explicit `--schema-type` parameter

### Debug Mode
```bash
# Verbose error output
python validate_config.py data/specs/problematic.json

# Syntax check only
python validate_config.py --check-syntax data/specs/problematic.json
```

## 🚀 Integration

### CI/CD Pipeline
```yaml
# .github/workflows/validate-configs.yml
name: Validate Configurations
on: [push, pull_request]
jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Setup Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.8'
      - name: Install dependencies
        run: pip install jsonschema
      - name: Validate configurations
        run: python validate_config.py --validate-all
```

### Pre-commit Hook
```bash
#!/bin/sh
# .git/hooks/pre-commit
python validate_config.py --validate-all --quiet
if [ $? -ne 0 ]; then
    echo "Configuration validation failed. Please fix errors before committing."
    exit 1
fi
```

## 📚 Additional Resources

- **`CONFIGURATION.md`** - Complete format specification
- **`examples/`** - Working example configurations
- **`schemas/`** - JSON schema definitions
- **`tests/`** - Test cases and examples

For more information on OSImager architecture and setup, see the main project documentation.
