# Development Tasks

## 1. Python Version Strategy
- [x] support policy: latest stable + 3 older versions (currently 3.10–3.13).
- [x] Add explicit policy note in project docs (README or CONTRIBUTING).
- [ ] Revisit policy quarterly as new Python releases come out.

## 2. CI/CD Modernization
- [x] Add GitHub Actions workflow with a Python matrix (3.10, 3.11, 3.12, 3.13).
- [x] Keep Travis/CircleCI only if still required; otherwise deprecate one CI path to reduce maintenance. CUrrently uses CircleCI. can remove travis.
- [x] Ensure build, test, and package publishing steps are aligned across CI providers.

## 3. Packaging Cleanup
- [x] Migrate packaging metadata from `setup.py` to `pyproject.toml` (PEP 517/518).
- [x] Keep `python_requires` and classifiers synchronized with CI matrix.
- [x] Review dependency minimums (e.g., `numpy>=1.7`) and raise where appropriate for modern Python.

## 4. Testing and Quality
- [x] Remove/resolve existing pytest warnings (return-not-none and deprecation warnings).
- [x] Add strict warning handling in CI for new code paths.
- [ ] Add regression tests for any version-specific behavior discovered during upgrades.

## 5. Documentation and Developer Experience
- [x] Document local setup for supported Python versions (venv + install + test commands).
- [x] Add a short release checklist for version bumps and packaging changes.
- [x] Add badges/status links for active CI pipelines.

## 6. Maintenance Backlog
- [ ] Audit deprecated APIs and define a removal timeline.
- [ ] Review examples/notebooks for compatibility with current supported Python versions.
- [ ] Periodically pin and refresh developer tooling dependencies.
