# Guidelines for writing alarm descriptions

For the people who write and maintain the alarm catalogue.

**Status: first version, not yet validated.** These guidelines follow from how the assistant uses alarm text and from one test on one alarm. See [What this is based on](#what-this-is-based-on) before treating them as a standard.

## Why the description matters

When a technician asks the assistant about an alarm, the assistant searches the documentation by meaning, using the alarm's text as the search query. It then picks the best-matching sections and writes resolution steps from them.

The description's job is therefore to point at the right documentation sections. It does not need to contain the fix.

Today the search query is the alarm's title and its runtime message. A runtime message such as "Program mdi1.pp, line 1: Could not activate part program 'm101.pp'" carries details of one occurrence and few of the terms the manuals use, so it is a weak query.

## Guidelines

1. **Write one fixed description per alarm code, separate from the runtime message.** Leave out anything that changes per occurrence: program names, line numbers, device names, addresses, counts. Those belong in the alarm's data fields.

2. **Use the documentation's own terms.** Name features, parameters and configuration properties exactly as the manuals do, for example "part program search hierarchy", "M-code mode", `opcua.enable`.

3. **Name every area the fix can involve.** If the alarm can be resolved in two ways, mention both areas. In testing, the area the description named dominated the answer and the area it left out disappeared from it.

4. **Say what distinguishes this alarm from its neighbours.** Similar alarms pull in each other's documentation. State the specific condition: "the device sent an emergency message" and "a frame was malformed or went unanswered" lead to different sections of the same page.

5. **Describe the condition and its trigger, not the procedure.** Say what went wrong and when it occurs. Leave the resolution steps in the manuals, so there is one source of truth for the fix.

6. **Keep it to one to three sentences, roughly 20 to 60 words.** Longer text dilutes the match.

7. **Write plain, full sentences and expand abbreviations once.** "Part program interpreter (PPI)" matches more documentation than "PPI" alone.

8. **Do not mention what the alarm is not about.** Naming an unrelated feature, even to rule it out, pulls its documentation into the answer.

9. **If the manuals do not cover the fix, do not write it into the description.** Report the documentation gap instead.

## Template

> **What happened:** [component] could not [action] because [condition].
> **When it occurs:** [trigger].
> **Related areas:** [feature or setting 1], [feature or setting 2].

## Example: `am.nc.0003`

Runtime message, used as the search query today:

> PPI Execution Error — Program mdi1.pp, line 1: Could not activate part program 'm101.pp' for M-code M101.

A description that follows the guidelines:

> An M-code that is configured to run as a part program could not be executed because its program file could not be found or activated. This occurs when the M-code is called from a part program. Related areas: the M-code mode configured for this M-code (part program or PLC), and the part program search hierarchy.

This exact wording has not been tested.

## Checklist before saving a description

- [ ] No values from a single occurrence (file names, line numbers, device names, addresses).
- [ ] Features and settings are named as the manuals name them.
- [ ] Every area the fix can involve is mentioned.
- [ ] It is clear how this alarm differs from similar ones.
- [ ] It describes the condition, not the steps to fix it.
- [ ] One to three sentences.
- [ ] Abbreviations are expanded on first use.
- [ ] No unrelated features are mentioned.

## What this is based on

- **One test on one alarm.** For `am.nc.0003`, replacing the runtime message with a description-style query moved the correct documentation page from third place to first. The answer then covered only the area that query emphasised, which is the basis for guideline 3.
- **The tested query was written by someone who had already read the reference answer** for that alarm, so the result shows the direction of the effect, not its size.
- **Guidelines 4, 6, 7 and 8 come from how meaning-based search generally behaves** and from patterns seen in the assistant's logs, not from a controlled test.

## How these guidelines will be validated

1. Someone who has not seen the reference answers writes descriptions for the 11 sample alarms using this document.
2. The evaluation runs with each description as the search query, and the results are compared with the current ones.

The alarm catalogue has an optional `description` field for this (`alarms.sample.json`), and the
assistant searches with it when it is present. The 11 sample alarms carry first-draft descriptions
written by someone who had read the reference answers, so they do not count as this validation.
