# Integration Validation

This folder contains **cross-phase integration tests** that verify all implemented phases (1–6) work together as a complete system.

## Validation Approach

1. **Path setup**  
   `tests/conftest.py` adds each phase’s `src` directory to `sys.path` so tests can import from `ai_restaurant`, `ai_restaurant_phase2`, … `ai_restaurant_phase6` without installing phases as packages.

2. **Data flow**  
   Tests and adapter helpers validate:
   - **Phase 1 → Phase 3**: `UserPreferences` (validated) used as input to filter/rank (same shape).
   - **Phase 2 → Phase 3**: Dataset records (dataset column names) converted to `Restaurant` via `_dataset_record_to_restaurant()`.
   - **Phase 3 → Phase 4**: `Restaurant` converted to `CandidateContext` for `build_prompt()`.
   - **Phase 4 → Phase 5**: Prompt built; mock “chosen” candidate + rationale passed to `format_recommendation()`.
   - **Phase 5**: Produces `FormattedRecommendation` (name, location, price, rating, cuisine, rationale, alternatives).
   - **Phase 6**: `with_request_id` and `with_graceful_fallback` wrap the flow; metrics checked.

3. **No cross-phase code changes**  
   Only this Integration folder and its tests were added; no existing phase code was modified.

## Test Execution Commands

Run **integration tests only** (from repo root or Integration):

```bash
cd Integration
pytest tests/test_cross_phase_integration.py -v
```

Run **all phase unit tests** (from repo root):

```bash
cd Phase1 && pytest -v && cd ..
cd Phase2 && pytest -v && cd ..
cd Phase3 && pytest -v && cd ..
cd Phase4 && pytest -v && cd ..   # Phase4: Groq connectivity test may fail in restricted network/proxy environments
cd Phase5 && pytest -v && cd ..
cd Phase6 && pytest -v && cd ..
```

## Expected Results

- **Integration tests**: 7 tests, all passing (data flow and adapter behavior).
- **Phase 1**: 11 passed.
- **Phase 2**: 12 passed.
- **Phase 3**: 6 passed.
- **Phase 4**: 2 tests; 1 may fail with `ProxyError`/`APIConnectionError` if Groq API is unreachable (network/proxy).
- **Phase 5**: 16 passed.
- **Phase 6**: 18 passed.

Any Phase 4 failure due to network/proxy is an **environment** issue, not an integration or code defect.
