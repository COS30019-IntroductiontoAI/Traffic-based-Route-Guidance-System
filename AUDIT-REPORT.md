```markdown
**Full Vulnerability Report (Backend + ML Pipeline Audit)**  
No code was changed. This is a strict grading-oriented static audit against the checklist criteria.

### [backend/api_server.py](backend/api_server.py)
1. **File & Line(s):** [backend/api_server.py](backend/api_server.py#L14-L16)  
   **The Issue:** Heavy service initialization and prediction precomputation happen at import time. This creates startup side effects before the server is even running and can fail module import if data/artifacts are missing.  
   **Lecturer Deduction Risk:** **HIGH** - Strict graders penalize import-time side effects and brittle startup flow.

2. **File & Line(s):** [backend/api_server.py](backend/api_server.py#L204), [backend/api_server.py](backend/api_server.py#L218), [backend/api_server.py](backend/api_server.py#L232), [backend/api_server.py](backend/api_server.py#L246), [backend/api_server.py](backend/api_server.py#L292), [backend/api_server.py](backend/api_server.py#L325)  
   **The Issue:** Broad exception catches return raw error strings to clients. This masks root causes and can leak internals.  
   **Lecturer Deduction Risk:** **HIGH** - Violates defensive programming and robust error taxonomy expectations.

3. **File & Line(s):** [backend/api_server.py](backend/api_server.py#L263), [backend/api_server.py](backend/api_server.py#L336)  
   **The Issue:** Uses print instead of structured logging in API request and server lifecycle paths.  
   **Lecturer Deduction Risk:** **MEDIUM** - Directly conflicts with checklist logging expectations.

4. **File & Line(s):** [backend/api_server.py](backend/api_server.py#L265)  
   **The Issue:** k is parsed but has no upper bound. Large values can trigger path-search blowups downstream.  
   **Lecturer Deduction Risk:** **HIGH** - Input hardening gap, potential performance abuse.

5. **File & Line(s):** [backend/api_server.py](backend/api_server.py#L109-L124)  
   **The Issue:** Repeated per-test-id DataFrame slicing in loops for each metric causes avoidable repeated scans.  
   **Lecturer Deduction Risk:** **MEDIUM** - Inefficient data processing pattern (strict marker may call this out as algorithmic inefficiency).

6. **File & Line(s):** [backend/api_server.py](backend/api_server.py#L165)  
   **The Issue:** Hardcoded 3-hour sampling in traffic profile drops resolution with no configuration hook.  
   **Lecturer Deduction Risk:** **LOW** - Arbitrary output shaping can be viewed as a band-aid decision.

---

### [backend/services/route_service.py](backend/services/route_service.py)
1. **File & Line(s):** [backend/services/route_service.py](backend/services/route_service.py#L122)  
   **The Issue:** get_routes lacks an explicit return type annotation despite returning a complex dict payload.  
   **Lecturer Deduction Risk:** **MEDIUM** - Type hint completeness is a checklist item.

2. **File & Line(s):** [backend/services/route_service.py](backend/services/route_service.py#L161)  
   **The Issue:** Inner edge_cost function is untyped, reducing type safety in critical routing math.  
   **Lecturer Deduction Risk:** **LOW** - Style/type rigor penalty under strict marking.

3. **File & Line(s):** [backend/services/route_service.py](backend/services/route_service.py#L183)  
   **The Issue:** Fallback computes distance from base_time_minutes / 60.0 (unit mismatch risk: minutes converted as if distance proxy). This can distort travel-time estimation.  
   **Lecturer Deduction Risk:** **HIGH** - Mathematical correctness concern in core routing logic.

4. **File & Line(s):** [backend/services/route_service.py](backend/services/route_service.py#L92)  
   **The Issue:** Sorting node ids by int assumes all ids are numeric; non-numeric id causes runtime failure.  
   **Lecturer Deduction Risk:** **MEDIUM** - Fragile assumption, avoidable runtime break.

---

### [backend/route_guidance/top_k.py](backend/route_guidance/top_k.py)
1. **File & Line(s):** [backend/route_guidance/top_k.py](backend/route_guidance/top_k.py#L63-L83)  
   **The Issue:** Best-first enumeration of simple paths can grow exponentially before collecting k results; no frontier-size cap, timeout, or pruning strategy.  
   **Lecturer Deduction Risk:** **HIGH** - Classic algorithmic memory/time explosion risk.

2. **File & Line(s):** [backend/route_guidance/top_k.py](backend/route_guidance/top_k.py#L74)  
   **The Issue:** visited set is rebuilt for every popped state, adding avoidable overhead in large frontier states.  
   **Lecturer Deduction Risk:** **MEDIUM** - Performance inefficiency in hot loop.

3. **File & Line(s):** [backend/route_guidance/top_k.py](backend/route_guidance/top_k.py#L32)  
   **The Issue:** next(...) on neighbor lookup can raise StopIteration if graph inconsistency appears; no guard/catch.  
   **Lecturer Deduction Risk:** **MEDIUM** - Unhandled exception path in route construction.

---

### [backend/route_guidance/astar.py](backend/route_guidance/astar.py)
1. **File & Line(s):** [backend/route_guidance/astar.py](backend/route_guidance/astar.py#L73)  
   **The Issue:** next(...) neighbor resolution can raise StopIteration with malformed or stale path-edge relation.  
   **Lecturer Deduction Risk:** **MEDIUM** - Unhandled exceptional control path.

2. **File & Line(s):** [backend/route_guidance/astar.py](backend/route_guidance/astar.py#L40)  
   **The Issue:** edge_cost_lookup parameter is untyped in a critical algorithm entrypoint.  
   **Lecturer Deduction Risk:** **LOW** - Type rigor deduction.

---

### [backend/route_guidance/build_scats_graph.py](backend/route_guidance/build_scats_graph.py)
1. **File & Line(s):** [backend/route_guidance/build_scats_graph.py](backend/route_guidance/build_scats_graph.py#L136-L139)  
   **The Issue:** Pairwise all-node distance table construction is O(n^2) in time and memory.  
   **Lecturer Deduction Risk:** **HIGH** - Direct algorithmic scalability concern.

2. **File & Line(s):** [backend/route_guidance/build_scats_graph.py](backend/route_guidance/build_scats_graph.py#L154-L164)  
   **The Issue:** For each site, candidates are fully sorted from all other sites. This repeats costly O(n log n) sorting per node.  
   **Lecturer Deduction Risk:** **HIGH** - Redundant sorting pattern can be penalized as inefficiency.

3. **File & Line(s):** [backend/route_guidance/build_scats_graph.py](backend/route_guidance/build_scats_graph.py#L236-L243)  
   **The Issue:** connect_components uses nested loops across components and repeatedly recomputes connectivity, causing high worst-case overhead.  
   **Lecturer Deduction Risk:** **HIGH** - Poor scaling pattern likely flagged by strict assessor.

4. **File & Line(s):** [backend/route_guidance/build_scats_graph.py](backend/route_guidance/build_scats_graph.py#L21), [backend/route_guidance/build_scats_graph.py](backend/route_guidance/build_scats_graph.py#L150), [backend/route_guidance/build_scats_graph.py](backend/route_guidance/build_scats_graph.py#L264)  
   **The Issue:** Hardcoded correction for one SCATS id and fixed neighbors_per_site=3 are heuristic band-aids without configuration or validation path.  
   **Lecturer Deduction Risk:** **MEDIUM** - Hardcoded assumptions often penalized unless justified/documented.

5. **File & Line(s):** [backend/route_guidance/build_scats_graph.py](backend/route_guidance/build_scats_graph.py#L329-L330)  
   **The Issue:** print used in CLI pipeline output instead of logging abstraction.  
   **Lecturer Deduction Risk:** **LOW** - Style/engineering quality deduction.

---

### [backend/main.py](backend/main.py)
1. **File & Line(s):** [backend/main.py](backend/main.py#L14-L16)  
   **The Issue:** Hardcoded origin, destination, k, and algorithm in smoke-test path.  
   **Lecturer Deduction Risk:** **LOW** - Hardcoded values in executable script reduce robustness.

2. **File & Line(s):** [backend/main.py](backend/main.py#L17)  
   **The Issue:** print used for output instead of logging.  
   **Lecturer Deduction Risk:** **LOW** - Logging style deduction.

---

### [backend/route_guidance/route_formatter.py](backend/route_guidance/route_formatter.py)
1. **File & Line(s):** [backend/route_guidance/route_formatter.py](backend/route_guidance/route_formatter.py#L9-L11)  
   **The Issue:** Traffic-level thresholds (2.0, 3.0) are hardcoded and not calibrated/configurable.  
   **Lecturer Deduction Risk:** **LOW** - Arbitrary thresholding can be criticized as brittle logic.

---

### [src/data_loader.py](src/data_loader.py)
1. **File & Line(s):** [src/data_loader.py](src/data_loader.py#L144), [src/data_loader.py](src/data_loader.py#L120), [src/data_loader.py](src/data_loader.py#L292), [src/data_loader.py](src/data_loader.py#L59)  
   **The Issue:** Multiple core functions have missing or partial type hints (inputs and/or returns).  
   **Lecturer Deduction Risk:** **MEDIUM** - Explicit checklist target.

2. **File & Line(s):** [src/data_loader.py](src/data_loader.py#L176)  
   **The Issue:** Concatenation assumes at least one valid group; if all groups filtered out, np.concatenate raises runtime error (unhandled).  
   **Lecturer Deduction Risk:** **HIGH** - Defensive programming failure.

3. **File & Line(s):** [src/data_loader.py](src/data_loader.py#L251), [src/data_loader.py](src/data_loader.py#L256-L258)  
   **The Issue:** Uses fixed lag windows (-16, -8, -4, -2) without enforcing seq_len minimum. Small seq_len causes invalid indexing/incorrect features.  
   **Lecturer Deduction Risk:** **HIGH** - Hidden hardcoded assumptions and potential runtime faults.

4. **File & Line(s):** [src/data_loader.py](src/data_loader.py#L225-L266)  
   **The Issue:** Row-by-row feature dict creation with per-window loops is computationally heavy on large datasets.  
   **Lecturer Deduction Risk:** **MEDIUM** - Inefficient pipeline design.

5. **File & Line(s):** [src/data_loader.py](src/data_loader.py#L271)  
   **The Issue:** split_tabular_by_time has no explicit empty-data guard before index access.  
   **Lecturer Deduction Risk:** **MEDIUM** - Edge-case safety gap.

---

### [src/evaluation.py](src/evaluation.py)
1. **File & Line(s):** [src/evaluation.py](src/evaluation.py#L37-L41)  
   **The Issue:** If all actual values are zero, MAPE computation can become mean of empty array (NaN) with no guard.  
   **Lecturer Deduction Risk:** **HIGH** - Metric integrity issue in evaluation core.

2. **File & Line(s):** [src/evaluation.py](src/evaluation.py#L47), [src/evaluation.py](src/evaluation.py#L63), [src/evaluation.py](src/evaluation.py#L68), [src/evaluation.py](src/evaluation.py#L102), [src/evaluation.py](src/evaluation.py#L199)  
   **The Issue:** Several major functions have missing return/type detail.  
   **Lecturer Deduction Risk:** **MEDIUM** - Type completeness deduction.

3. **File & Line(s):** [src/evaluation.py](src/evaluation.py#L151-L155), [src/evaluation.py](src/evaluation.py#L200-L221)  
   **The Issue:** Heavy use of print for run/status/metrics output in pipeline context.  
   **Lecturer Deduction Risk:** **LOW** - Logging hygiene issue.

---

### [src/predict.py](src/predict.py)
1. **File & Line(s):** [src/predict.py](src/predict.py#L96), [src/predict.py](src/predict.py#L153), [src/predict.py](src/predict.py#L47), [src/predict.py](src/predict.py#L54)  
   **The Issue:** Key functions have incomplete type hints.  
   **Lecturer Deduction Risk:** **MEDIUM** - Style/maintainability penalty.

2. **File & Line(s):** [src/predict.py](src/predict.py#L113)  
   **The Issue:** Reads metadata file directly with no existence/parse guard (JSONDecodeError/FileNotFoundError path not handled).  
   **Lecturer Deduction Risk:** **MEDIUM** - Incomplete exception handling.

3. **File & Line(s):** [src/predict.py](src/predict.py#L98), [src/predict.py](src/predict.py#L102), [src/predict.py](src/predict.py#L158-L180)  
   **The Issue:** print used throughout model inference pipeline.  
   **Lecturer Deduction Risk:** **LOW** - Logging-quality deduction.

---

### [src/process_2014.py](src/process_2014.py)
1. **File & Line(s):** [src/process_2014.py](src/process_2014.py#L7)  
   **The Issue:** warnings.filterwarnings('ignore') globally suppresses warnings, potentially hiding real data or parsing defects.  
   **Lecturer Deduction Risk:** **HIGH** - Strong defensive-programming red flag.

2. **File & Line(s):** [src/process_2014.py](src/process_2014.py#L79), [src/process_2014.py](src/process_2014.py#L177)  
   **The Issue:** Broad and bare exception handling, including a raw except:.  
   **Lecturer Deduction Risk:** **HIGH** - Explicitly penalized pattern.

3. **File & Line(s):** [src/process_2014.py](src/process_2014.py#L166), [src/process_2014.py](src/process_2014.py#L189)  
   **The Issue:** Uses exit() instead of raising controlled exceptions or returning explicit status.  
   **Lecturer Deduction Risk:** **MEDIUM** - Abrupt control-flow termination is brittle.

4. **File & Line(s):** [src/process_2014.py](src/process_2014.py#L20), [src/process_2014.py](src/process_2014.py#L95), [src/process_2014.py](src/process_2014.py#L249)  
   **The Issue:** Hardcoded SCATS region list and expected count of 39.  
   **Lecturer Deduction Risk:** **MEDIUM** - Hardcoded scope assumptions; portability/scalability concern.

5. **File & Line(s):** [src/process_2014.py](src/process_2014.py#L44-L52)  
   **The Issue:** Column-name fallback heuristics are ad hoc and can silently pick wrong longitude field.  
   **Lecturer Deduction Risk:** **MEDIUM** - Band-aid schema handling.

6. **File & Line(s):** [src/process_2014.py](src/process_2014.py#L171-L192)  
   **The Issue:** Accumulates all daily processed chunks into memory list before concat; memory pressure risk for larger corpora.  
   **Lecturer Deduction Risk:** **MEDIUM** - Scalability inefficiency.

7. **File & Line(s):** [src/process_2014.py](src/process_2014.py#L29-L254)  
   **The Issue:** Extensive print-based operational reporting instead of logger usage.  
   **Lecturer Deduction Risk:** **LOW** - Logging-policy deduction.

8. **File & Line(s):** [src/process_2014.py](src/process_2014.py#L63), [src/process_2014.py](src/process_2014.py#L76)  
   **The Issue:** Critical helper functions missing type annotations and docstrings; also weak variable naming (for example short token p in direction parsing loop).  
   **Lecturer Deduction Risk:** **LOW** - Code quality/style deduction.

---

### [src/process_2006.py](src/process_2006.py)
1. **File & Line(s):** [src/process_2006.py](src/process_2006.py#L18-L20), [src/process_2006.py](src/process_2006.py#L30)  
   **The Issue:** File names and output target are hardcoded in orchestration script.  
   **Lecturer Deduction Risk:** **LOW** - Configuration rigidity.

2. **File & Line(s):** [src/process_2006.py](src/process_2006.py#L14)  
   **The Issue:** main has no return type annotation/docstring.  
   **Lecturer Deduction Risk:** **LOW** - Type/docstring compliance deduction.

3. **File & Line(s):** [src/process_2006.py](src/process_2006.py#L15-L73)  
   **The Issue:** print-only operational output.  
   **Lecturer Deduction Risk:** **LOW** - Logging style deduction.

---

### [src/models/lstm_model.py](src/models/lstm_model.py)
1. **File & Line(s):** [src/models/lstm_model.py](src/models/lstm_model.py#L34), [src/models/lstm_model.py](src/models/lstm_model.py#L44), [src/models/lstm_model.py](src/models/lstm_model.py#L108)  
   **The Issue:** Training pipeline executes at import time (data loading, model build, fitting) because logic is top-level, not guarded function entry.  
   **Lecturer Deduction Risk:** **HIGH** - Severe engineering anti-pattern; fragile and hard to test.

2. **File & Line(s):** [src/models/lstm_model.py](src/models/lstm_model.py#L1-L130)  
   **The Issue:** No encapsulated train function, no type-annotated API surface, no module-level docstring.  
   **Lecturer Deduction Risk:** **MEDIUM** - Maintainability and quality deduction.

3. **File & Line(s):** [src/models/lstm_model.py](src/models/lstm_model.py#L130)  
   **The Issue:** plt.show in training scripts can hang non-interactive execution environments.  
   **Lecturer Deduction Risk:** **LOW** - Execution robustness concern.

---

### [src/models/gru_model.py](src/models/gru_model.py)
1. **File & Line(s):** [src/models/gru_model.py](src/models/gru_model.py#L34), [src/models/gru_model.py](src/models/gru_model.py#L44), [src/models/gru_model.py](src/models/gru_model.py#L106)  
   **The Issue:** Same import-time training side effects as LSTM script.  
   **Lecturer Deduction Risk:** **HIGH** - Same strict penalty rationale.

2. **File & Line(s):** [src/models/gru_model.py](src/models/gru_model.py#L1-L128)  
   **The Issue:** Missing modularized callable training interface, weak type/docstring discipline.  
   **Lecturer Deduction Risk:** **MEDIUM** - Code quality deduction.

3. **File & Line(s):** [src/models/gru_model.py](src/models/gru_model.py#L128)  
   **The Issue:** plt.show in script path can block headless runs.  
   **Lecturer Deduction Risk:** **LOW** - Runtime stability concern.

---

### [src/models/lightgbm_model.py](src/models/lightgbm_model.py)
1. **File & Line(s):** [src/models/lightgbm_model.py](src/models/lightgbm_model.py#L22-L23), [src/models/lightgbm_model.py](src/models/lightgbm_model.py#L36-L40), [src/models/lightgbm_model.py](src/models/lightgbm_model.py#L107)  
   **The Issue:** Many hardcoded model/data parameters (sequence length, estimators, leaves, depth, min child samples, early-stopping rounds) with no external configuration.  
   **Lecturer Deduction Risk:** **MEDIUM** - Hardcoded tuning likely criticized as inflexible and not reproducibly justified.

2. **File & Line(s):** [src/models/lightgbm_model.py](src/models/lightgbm_model.py#L27), [src/models/lightgbm_model.py](src/models/lightgbm_model.py#L51), [src/models/lightgbm_model.py](src/models/lightgbm_model.py#L68), [src/models/lightgbm_model.py](src/models/lightgbm_model.py#L73)  
   **The Issue:** Several function signatures have incomplete typing.  
   **Lecturer Deduction Risk:** **MEDIUM** - Checklist type-hint deficiency.

3. **File & Line(s):** [src/models/lightgbm_model.py](src/models/lightgbm_model.py#L137-L141)  
   **The Issue:** print-based training lifecycle reporting.  
   **Lecturer Deduction Risk:** **LOW** - Logging quality deduction.

---

### [src/preprocessing/clean_scats_traffic.py](src/preprocessing/clean_scats_traffic.py)
1. **File & Line(s):** [src/preprocessing/clean_scats_traffic.py](src/preprocessing/clean_scats_traffic.py#L102)  
   **The Issue:** Hardcoded removal of SCATS 4335 with no explanation/config.  
   **Lecturer Deduction Risk:** **MEDIUM** - Band-aid data exclusion.

2. **File & Line(s):** [src/preprocessing/clean_scats_traffic.py](src/preprocessing/clean_scats_traffic.py#L109)  
   **The Issue:** Hardcoded minimum day threshold >= 25 can silently bias dataset composition.  
   **Lecturer Deduction Risk:** **MEDIUM** - Arbitrary filter risk.

3. **File & Line(s):** [src/preprocessing/clean_scats_traffic.py](src/preprocessing/clean_scats_traffic.py#L79)  
   **The Issue:** Nested helper convert_time_code_to_timedelta lacks type hints/docstring in transformation-critical path.  
   **Lecturer Deduction Risk:** **LOW** - Type/doc quality deduction.

4. **File & Line(s):** [src/preprocessing/clean_scats_traffic.py](src/preprocessing/clean_scats_traffic.py#L8-L148)  
   **The Issue:** Extensive print usage in data processing script.  
   **Lecturer Deduction Risk:** **LOW** - Logging style deduction.

---

### [src/preprocessing/clean_scats_sites.py](src/preprocessing/clean_scats_sites.py)
1. **File & Line(s):** [src/preprocessing/clean_scats_sites.py](src/preprocessing/clean_scats_sites.py#L5)  
   **The Issue:** No return type annotation and no proper function docstring (comment style instead).  
   **Lecturer Deduction Risk:** **LOW** - Type/doc compliance deduction.

2. **File & Line(s):** [src/preprocessing/clean_scats_sites.py](src/preprocessing/clean_scats_sites.py#L9-L104)  
   **The Issue:** print-based pipeline status reporting.  
   **Lecturer Deduction Risk:** **LOW** - Logging style deduction.

---

### [src/preprocessing/clean_traffic_locations.py](src/preprocessing/clean_traffic_locations.py)
1. **File & Line(s):** [src/preprocessing/clean_traffic_locations.py](src/preprocessing/clean_traffic_locations.py#L5)  
   **The Issue:** Missing return type/docstring on core function.  
   **Lecturer Deduction Risk:** **LOW** - Type/doc quality deduction.

2. **File & Line(s):** [src/preprocessing/clean_traffic_locations.py](src/preprocessing/clean_traffic_locations.py#L9), [src/preprocessing/clean_traffic_locations.py](src/preprocessing/clean_traffic_locations.py#L35-L36)  
   **The Issue:** print-based progress reporting.  
   **Lecturer Deduction Risk:** **LOW** - Logging style deduction.

---

### [src/preprocessing/merge_data.py](src/preprocessing/merge_data.py)
1. **File & Line(s):** [src/preprocessing/merge_data.py](src/preprocessing/merge_data.py#L6)  
   **The Issue:** Missing explicit return type annotation and no formal docstring.  
   **Lecturer Deduction Risk:** **LOW** - Type/doc compliance deduction.

2. **File & Line(s):** [src/preprocessing/merge_data.py](src/preprocessing/merge_data.py#L16-L120)  
   **The Issue:** print-heavy execution path instead of logging.  
   **Lecturer Deduction Risk:** **LOW** - Logging style deduction.

---

### [src/select_data_to_storytelling.py](src/select_data_to_storytelling.py)
1. **File & Line(s):** [src/select_data_to_storytelling.py](src/select_data_to_storytelling.py#L5)  
   **The Issue:** Main generator function lacks type hints and docstring.  
   **Lecturer Deduction Risk:** **LOW** - Quality/style penalty.

2. **File & Line(s):** [src/select_data_to_storytelling.py](src/select_data_to_storytelling.py#L66)  
   **The Issue:** groupby apply custom boxplot stats can be slow on large datasets; no batching or vectorized summary fallback.  
   **Lecturer Deduction Risk:** **LOW** - Efficiency concern.

3. **File & Line(s):** [src/select_data_to_storytelling.py](src/select_data_to_storytelling.py#L6-L83)  
   **The Issue:** print-based reporting throughout.  
   **Lecturer Deduction Risk:** **LOW** - Logging style deduction.

---

### [src/test_stratified.py](src/test_stratified.py)
1. **File & Line(s):** [src/test_stratified.py](src/test_stratified.py#L181)  
   **The Issue:** Broad except Exception in main test workflow.  
   **Lecturer Deduction Risk:** **MEDIUM** - Error handling not specific and can hide test root causes.

2. **File & Line(s):** [src/test_stratified.py](src/test_stratified.py#L167)  
   **The Issue:** main missing return type annotation.  
   **Lecturer Deduction Risk:** **LOW** - Type-hint deduction.

3. **File & Line(s):** [src/test_stratified.py](src/test_stratified.py#L41-L182)  
   **The Issue:** print-heavy test orchestration.  
   **Lecturer Deduction Risk:** **LOW** - Logging style penalty.

---

### [src/test_runner.py](src/test_runner.py)
1. **File & Line(s):** [src/test_runner.py](src/test_runner.py#L100), [src/test_runner.py](src/test_runner.py#L115)  
   **The Issue:** Silent continuation paths can produce empty/partial CSV outputs without explicit failure status (if tests return empty dicts).  
   **Lecturer Deduction Risk:** **MEDIUM** - Test reliability/reporting quality concern.

2. **File & Line(s):** [src/test_runner.py](src/test_runner.py#L135)  
   **The Issue:** main missing return type annotation.  
   **Lecturer Deduction Risk:** **LOW** - Type-hint compliance.

3. **File & Line(s):** [src/test_runner.py](src/test_runner.py#L27-L130)  
   **The Issue:** print-based status and metrics output.  
   **Lecturer Deduction Risk:** **LOW** - Logging style deduction.

---

### [src/test_filters.py](src/test_filters.py)
1. **File & Line(s):** [src/test_filters.py](src/test_filters.py#L129)  
   **The Issue:** Unknown test name falls back to full dataset instead of raising, which can mask wrong test IDs.  
   **Lecturer Deduction Risk:** **MEDIUM** - Band-aid fallback can invalidate strict testing claims.

2. **File & Line(s):** [src/test_filters.py](src/test_filters.py#L64), [src/test_filters.py](src/test_filters.py#L109-L123)  
   **The Issue:** Missing return annotation on get_test_cases and print usage inside filtering logic.  
   **Lecturer Deduction Risk:** **LOW** - Style/type rigor deduction.

---

### [backend/core/config.py](backend/core/config.py)
1. **File & Line(s):** [backend/core/config.py](backend/core/config.py#L17), [backend/core/config.py](backend/core/config.py#L23-L26)  
   **The Issue:** Hardcoded month/date/time defaults; behavior is fixed unless source edit is made.  
   **Lecturer Deduction Risk:** **LOW** - Config rigidity may be penalized if not justified.

---

### [src/config/model_config.py](src/config/model_config.py)
1. **File & Line(s):** [src/config/model_config.py](src/config/model_config.py#L9-L16)  
   **The Issue:** Hyperparameters are hardcoded constants with no runtime config path or experiment registry linkage.  
   **Lecturer Deduction Risk:** **LOW** - Reproducibility/configurability criticism likely under strict marking.

---

If you want, I can next produce a ranked “Top 10 mark-losing issues” shortlist from this full report so you can prioritize fixes for maximum grade impact first.
```