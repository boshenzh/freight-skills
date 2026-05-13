# Industry reference templates

Sanitized industry-generic templates for freight forwarders, distilled from production files. These are starting points — adapt to your company's voice/terms/lanes.

## Files in this directory

| File | Original source | Use case |
|---|---|---|
| `运价表-template.xlsx` | 运价表.xlsx (sanitized) | Structured rate sheet — 9 columns mirror the 运价表（人） WeCom smartsheet |
| `运价信息-template.docx` | 运价信息.docx (sanitized) | Unstructured rate paragraph notes — single doc, multiple labeled sections |
| `推广模板-template.docx` | 推广模板.docx (sanitized) | Customer-facing promotion format — compact per-route blocks |
| `跟进话术-template.docx` | 跟进话术.docx (sanitized) | Customer follow-up phrasing patterns |
| `每日运价简报-template.docx` | 每日运价简报.docx (sanitized) | Internal daily-brief layout — 船司 × 区域 blocks |

> **Status**: these files are placeholder pending sanitization. The originals are kept private (they contain company branding, real lane names with internal pricing, and 业务员 contact info). De-identified versions will land here in a follow-up commit — open an issue at https://github.com/boshenzh/freight-skills/issues if you need one before then.

## How to use

These are reference shapes — not magic. The skills `freight-rate-daily-promotion` and `freight-lead-profiling` reference these via their `references/{daily-rate-brief-source, promotion-template-source, ...}.md` files (which are the distilled / structural versions used directly by the agent). The xlsx/docx originals are useful when:

- Onboarding a new operator who wants to see the layout in their familiar tooling
- Hand-editing a one-off promotion before it goes through 推广审核
- Auditing what specific structural decisions inform the skill's output rules

## License

Apache-2.0. Free to adapt and redistribute.
