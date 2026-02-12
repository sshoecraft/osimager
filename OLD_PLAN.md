# OSImager Development Plan

## Overview

This document outlines the development plan for OSImager, prioritized by security, stability, and feature importance. Each task includes specific implementation details and acceptance criteria.

## Priority Levels

- 🔴 **Critical** - Security vulnerabilities and breaking issues (Immediate)
- 🟡 **High** - Core functionality and stability (1-2 weeks)
- 🟢 **Medium** - Feature enhancements and improvements (2-4 weeks)
- 🔵 **Low** - Technical debt and code quality (Ongoing)

---

## 🔴 Critical Security & Stability Issues

### 1. Replace eval() Usage with Safe Template Engine
**Files:** `lib/osimager/utils.py`
**Issue:** Direct eval() usage is a severe security vulnerability allowing arbitrary code execution
**Solution:**
- Replace `eval_expression_safe()` and `eval_expression()` with Jinja2 custom filters
- Implement sandboxed expression evaluation using `ast.literal_eval()` for simple math
- Create custom parser for complex expressions if needed
**Acceptance Criteria:**
- No eval() usage in codebase
- All existing templates continue to work
- Security tests pass with malicious input attempts

### 2. Restrict CORS Origins
**Files:** `api/main.py`
**Issue:** `allow_origins=["*"]` permits requests from any domain
**Solution:**
```python
# Replace with:
allow_origins = [
    "http://localhost:3000",
    "http://localhost:8000",
    # Add production domains when deployed
]
```
**Acceptance Criteria:**
- CORS only allows specified origins
- Frontend continues to work in dev/prod

### 3. Remove Hardcoded Credentials
**Files:** `data/specs/redhat/spec.json`
**Issue:** Plain text passwords and credentials in configuration
**Solution:**
- Move all credentials to environment variables or Vault
- Update templates to use `|>vault_path<|` syntax
- Add validation to prevent commits with hardcoded secrets
**Acceptance Criteria:**
- No plaintext passwords in any config files
- Pre-commit hook blocks credential commits
- All credentials retrieved from Vault/env vars

### 4. Replace os.system() with subprocess.run()
**Files:** `lib/osimager/core.py`, other scripts
**Issue:** Shell injection vulnerability
**Solution:**
```python
# Replace:
os.system(f"some_command {arg}")
# With:
subprocess.run(["some_command", arg], check=True)
```
**Acceptance Criteria:**
- No os.system() calls remain
- All commands use subprocess with proper argument lists
- Error handling improved with check=True

### 5. Implement Proper Password Hashing
**Files:** `lib/osimager/utils.py`
**Issue:** MD5/SHA hashes are not suitable for password storage
**Solution:**
- Install bcrypt: `pip install bcrypt`
- Replace hash_password() implementation
- Add salt generation and verification methods
**Acceptance Criteria:**
- Passwords hashed with bcrypt
- Existing passwords migrated or deprecated
- Password verification works correctly

---

## 🟡 High Priority - Core Functionality

### 6. Add Comprehensive Test Suite
**Files:** Create new test files
**Issue:** Limited test coverage for critical components
**Solution:**
```
tests/
├── unit/
│   ├── test_core.py
│   ├── test_utils.py
│   └── test_build_manager.py
├── integration/
│   ├── test_api_endpoints.py
│   └── test_build_flow.py
└── fixtures/
    └── sample_configs.py
```
**Acceptance Criteria:**
- 80%+ code coverage for core modules
- All critical paths tested
- CI/CD runs tests on every commit

### 7. Refactor Large Functions
**Files:** `lib/osimager/core.py`, `lib/osimager/utils.py`
**Issue:** Functions exceeding 100 lines, difficult to test/maintain
**Solution:**
- Break down `init_settings()` into smaller methods
- Split `load_data()` into configuration steps
- Decompose `do_sub()` into specific substitution handlers
**Acceptance Criteria:**
- No function exceeds 50 lines
- Each function has single responsibility
- Existing functionality preserved

### 8. Standardize Error Handling
**Files:** All Python modules
**Issue:** Inconsistent error handling with print/sys.exit
**Solution:**
```python
# Create custom exceptions
class OSImagerError(Exception): pass
class ConfigurationError(OSImagerError): pass
class BuildError(OSImagerError): pass

# Use throughout codebase
raise ConfigurationError(f"Invalid spec: {spec_name}")
```
**Acceptance Criteria:**
- Custom exception hierarchy defined
- All errors use exceptions
- API returns proper HTTP status codes

### 9. Remove Dead Code
**Files:** `lib/osimager/core.py`, `lib/osimager/utils.py`
**Issue:** Commented out and unused functions
**Solution:**
- Delete all `old_*` functions
- Remove commented code blocks
- Archive if historical reference needed
**Acceptance Criteria:**
- No commented-out code remains
- No unused imports
- Code coverage doesn't flag dead code

---

## 🟢 Medium Priority - Feature Enhancements

### 10. Enhance Build Progress Monitoring
**Files:** `api/services/build_manager.py`
**Issue:** Basic progress parsing misses details
**Solution:**
- Parse Packer's machine-readable output
- Track individual provisioner steps
- Calculate accurate completion percentage
**Acceptance Criteria:**
- Progress shows current step name
- Percentage accurately reflects completion
- WebSocket updates are smooth

### 11. Improve Variable Input UI
**Files:** `frontend/src/components/pages/new-build.tsx`
**Issue:** JSON textarea is error-prone
**Solution:**
- Create dynamic key-value pair component
- Add variable type validation
- Show available variables from spec
**Acceptance Criteria:**
- User-friendly variable input
- Client-side validation
- Helpful tooltips for each variable

### 12. Complete Platform/Location CRUD
**Files:** `frontend/src/components/pages/platforms.tsx`, `locations.tsx`
**Issue:** Partial implementation of management features
**Solution:**
- Add create/edit modals
- Implement delete with confirmation
- Add validation for required fields
**Acceptance Criteria:**
- Full CRUD operations work
- Changes persist to backend
- UI updates reflect changes immediately

### 13. Consolidate Spec Models
**Files:** `api/models/spec.py`, `frontend/src/types/api.ts`
**Issue:** Duplicate/overlapping model definitions
**Solution:**
- Define single source of truth
- Use inheritance where appropriate
- Generate TypeScript types from Python models
**Acceptance Criteria:**
- Single model definition
- Frontend/backend types match
- No field mismatches

---

## 🔵 Low Priority - Technical Debt

### 14. Migrate to pathlib
**Files:** All Python modules
**Issue:** Mixed path handling approaches
**Solution:**
```python
# Replace:
os.path.join(dir, file)
# With:
Path(dir) / file
```
**Acceptance Criteria:**
- All paths use pathlib.Path
- Cross-platform compatibility maintained
- No string concatenation for paths

### 15. Optimize WebSocket Broadcasting
**Files:** `api/services/build_manager.py`
**Issue:** Redundant JSON stringification
**Solution:**
```python
# Stringify once
message_str = json.dumps(message)
# Send to all clients
for client in self._connections:
    await client.send_text(message_str)
```
**Acceptance Criteria:**
- Single JSON serialization
- Performance improvement measurable
- No message corruption

### 16. Add Complete Type Hints
**Files:** `lib/osimager/utils.py`, all Python files
**Issue:** Missing type annotations
**Solution:**
- Add type hints to all functions
- Use typing module features
- Run mypy for validation
**Acceptance Criteria:**
- 100% type hint coverage
- mypy passes with strict mode
- IDE autocomplete improves

### 17. Modernize CLI Framework
**Files:** `lib/osimager/core.py`, `bin/*.py`
**Issue:** Complex argparse usage
**Solution:**
- Migrate to Click or Typer
- Add command groups
- Improve help text
**Acceptance Criteria:**
- Cleaner CLI code
- Better help/documentation
- Backward compatibility maintained

---

## Implementation Timeline

### Week 1-2: Critical Security
- Complete all 🔴 Critical items
- Deploy security fixes immediately
- Add security scanning to CI/CD

### Week 3-4: Core Stability
- Implement test suite foundation
- Refactor large functions
- Standardize error handling

### Week 5-6: Feature Enhancements
- Improve build monitoring
- Complete frontend CRUD operations
- Enhance user experience

### Ongoing: Technical Debt
- Gradually migrate to modern patterns
- Improve code quality metrics
- Update documentation

---

## Success Metrics

1. **Security**: Zero high/critical vulnerabilities in security scan
2. **Stability**: 99.9% uptime, <1% build failure rate
3. **Quality**: 80%+ test coverage, <5% code duplication
4. **Performance**: <2s API response time, <100ms WebSocket latency
5. **Usability**: 90%+ user satisfaction score

---

## Notes

- Security fixes should be implemented and deployed immediately
- Each task should include tests before marking complete
- Documentation updates required for all API changes
- Consider feature flags for gradual rollout of major changes