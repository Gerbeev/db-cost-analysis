# Шаг 05 - Декомпозиция Databricks · проверки

Отметки: `[x]` выполнено · `[-]` не применимо ` | причина` · `[!]` выполнено с ограничением ` | ограничение`. Контрольная точка (`G…`) - только `[x]`.
Отмечайте в интерфейсе: аудит → шаг → **Проверки**. Статус (проверки, результаты, автоматические проверки данных) обновляется после каждого изменения.

## Проверки

- [ ] C5.1 Для денежных выводов используются только SKU, прошедшие R7
- [ ] C5.2 5.1: основные SKU классифицированы как объёмные или ценовые; пары MIX_SHIFT (GONE + NEW) взаимозачтены
- [ ] C5.3 5.2: концентрация дельты по workspace отмечена
- [ ] C5.4 5.3: объекты перечислены до cumulative_share ≥ 0,90 - авто
- [ ] C5.5 5.4: дата начала каждого основного объекта сравнена с общим началом (±2 дня)
- [ ] C5.6 5.5: неатрибутированная / без тегов дельта оценена
- [ ] C5.7 5.6: новые продукты / SKU в окне перечислены с датой first_seen
- [ ] C5.8 Строки DRIVER_CANDIDATE добавлены в delta_bridge.csv
- [ ] C5.9 Для каждого кандидата открыты гипотезы в hypothesis_register.csv
- [ ] C5.10 Строки доказательств EVD-05-nnn добавлены - авто
- [ ] G5 Основные объекты объясняют ≥ 90% модельной дельты DBX, или остаток оценён

## Обязательные результаты

- `05_databricks_decomposition/results/5.1_sku_volume_rate*.csv` - SQL 5.1
- `05_databricks_decomposition/results/5.2_workspace_delta*.csv` - SQL 5.2
- `05_databricks_decomposition/results/5.3_object_delta*.csv` - SQL 5.3
- `05_databricks_decomposition/results/5.4_object_daily*.csv` - SQL 5.4
- `05_databricks_decomposition/results/5.5_attribution_coverage*.csv` - SQL 5.5
- `05_databricks_decomposition/results/5.6_first_seen_skus*.csv` - SQL 5.6
