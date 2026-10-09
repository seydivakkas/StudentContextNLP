# GitHub release checklist

- [x] Project code and synthetic tests prepared locally.
- [x] `.gitignore` excludes source datasets, model weights, generated results, hidden env files.
- [x] GitHub Actions workflow defined for no-download synthetic CI.
- [x] Student-provided private content not included in release ZIP.
- [ ] New GitHub repository exists and connected GitHub app has write access.
- [ ] Source files pushed to `main` and commit URL recorded.
- [ ] GitHub Actions `Python offline synthetic tests` successful on that commit.
- [ ] Real SciEntsBank data downloaded *after* successful GitHub stage.
- [ ] Independent raw-data audit and research baseline completed.
