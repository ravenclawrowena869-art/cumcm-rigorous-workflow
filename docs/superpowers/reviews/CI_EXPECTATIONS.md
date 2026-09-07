# CI Expectations

`validate-runtime-skill` 应执行：

1. `python -m unittest tests.test_runtime_skill_contract -v`
2. `python tools/validate_runtime_skill.py`
3. `python tools/build_runtime_skill.py`
4. `python tools/validate_runtime_skill.py dist/cumcm-rigorous-workflow-runtime-lite`
5. Runtime Lite forbidden binary scan

任一失败均阻止把 v2.1 宣称为验证完成。
