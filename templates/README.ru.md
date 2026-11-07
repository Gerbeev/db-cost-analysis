# Шаблоны

Мастер-копии. При создании аудита в интерфейсе они копируются в папку аудита - правьте копии там (реестры и документы открываются в интерфейсе), но никогда не эти файлы. Если аудит создаётся при русском языке интерфейса, документы `*.md` копируются из русских версий (`*.ru.md`).

| Шаблон | Куда копируется | Используется на шагах |
|---|---|---|
| `scope_record.md` | `audits/<id>/scope_record.md` | 00, 01, 02, 03, 08 |
| `evidence_register.csv` | `audits/<id>/evidence_register.csv` | все |
| `delta_bridge.csv` | `audits/<id>/delta_bridge.csv` | 02-07, 09 |
| `hypothesis_register.csv` | `audits/<id>/hypothesis_register.csv` | 03, 05, 06, 08 |
| `driver_card.md` | `audits/<id>/06_root_cause/_driver_card_TEMPLATE.md` | 06 (копия на каждый драйвер) |
| `ibm_discrepancy_register.csv` | `audits/<id>/08_validation/ibm_discrepancy_register.csv` | 08 (при лицензии IBM) |
| `findings_report.md` | `audits/<id>/09_report_and_controls/findings_report.md` | 09 |

## Категории delta_bridge.csv

| category | Значение | В тождестве |
|---|---|---|
| `TOTAL` | Δ/сутки Azure Actual для охвата (шаг 02) | = сумма строк ниже |
| `ACCOUNTING` | Календарь, покупки, обязательства, кредиты, тариф, курс, охват, корректировки (шаг 03) | да |
| `ROOT_CAUSE` | Строка на драйвер со статусом (шаг 06) | да |
| `SHARED_UNALLOCATED` | Общие ресурсы без ключа распределения (шаг 07) | да |
| `OUT_OF_SCOPE` | Сервисы, не связанные с Databricks (шаг 07) | да |
| `UNEXPLAINED` | Остаток `UNX` (шаг 07) | да |
| `BUCKET` | Подытог корзины из шага 04 | нет (справочно) |
| `DRIVER_CANDIDATE` | Основной объект/SKU из шага 05, по прайсу | нет (справочно) |

Значения колонок `category`, `status` и ID в CSV-реестрах - машинные коды и не переводятся.
