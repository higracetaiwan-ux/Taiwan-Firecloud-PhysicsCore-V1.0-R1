# Taiwan Firecloud PhysicsCore V1.0-R5.7.6

Runtime integration hotfix on top of R5.7.5.

- Fix `NameError: name 'time' is not defined` in `firecloud/model.py` CAMS prefetch progress/watchdog path.
- Add explicit `import time` for `time.monotonic()` usage.
- Add regression coverage ensuring the CAMS scheduler source imports `time` whenever `time.monotonic()` is used.
- No scientific equations, thresholds, provider data semantics, Formation/Viewing separation, or six-band physics changed.
