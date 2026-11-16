# docs/

| Folder | What it is |
|--------|------------|
| `working_docs/` | Git submodule: the documentation team's repository. Answers are drawn from `working_docs/starter-kit/docs/` |
| `docs-proto/` | The earlier copy of the starter kit, kept in this repo. The alarm catalogue (`starter-kit/alarms/alarms.sample.json`) and the eval's gold answers (`starter-kit/alarms/reference-answers.json`) still come from here |
| `answer-quality.md` | Current eval scores, what has been tried, and the open gaps |
| `alarm-description-guidelines.md` | How to write alarm descriptions that retrieve the right documentation |

`working_docs/` is empty until the submodule is checked out:

```bash
git submodule update --init --recursive     # make ingest also runs this
```

Documentation is not edited from this repo. Changes are made in the
documentation team's repository. Moving the submodule to their latest commit,
re-ingesting and recording the new pointer is described in the main README,
under [Documentation and ingestion](../README.md#documentation-and-ingestion).
