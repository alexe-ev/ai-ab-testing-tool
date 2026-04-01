# Как пользоваться prompt-ab

Пошаговая инструкция для запуска A/B теста двух системных промптов.

Два способа работы: **Web UI** (рекомендуется) и **CLI** (для автоматизации и CI).

---

## Что это делает

Берёт два системных промпта, прогоняет оба через набор тест-кейсов, оценивает ответы через LLM-as-judge, считает статистику и генерирует отчёт. На выходе: какой промпт лучше, насколько, и можно ли доверять этому выводу.

---

## Предварительные требования

Python 3.10+. Node.js 18+ (для Web UI). API ключ OpenAI или Anthropic.

Нужен только тот провайдер, который используешь. Провайдер определяется автоматически по имени модели: `gpt-*` = OpenAI, `claude-*` = Anthropic.

---

# Web UI

## Быстрый старт

```bash
# Backend
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
uvicorn src.api.app:app --reload --port 8000

# Frontend (в отдельном терминале)
cd frontend
npm install
npm run dev
```

Открой http://localhost:3000. API ключи можно ввести на странице Settings.

## Работа в Web UI

### 1. Создай эксперимент

Главная страница > "New Experiment". Заполни:
- Название и описание
- Два варианта: системный промпт + модель для каждого
- Модель-судью

**Два режима тестирования:**
- **Разные промпты, одна модель:** классический A/B тест промптов. Одна модель, два системных промпта.
- **Разные модели, один промпт:** кросс-модельное сравнение. Один и тот же промпт, но variant A на gpt-4o-mini, variant B на claude-sonnet. Каждый вариант может иметь свою модель, temperature и max_tokens.

### 2. Создай тест-кейсы

Страница эксперимента > вкладка "Test Sets" > "New Test Set".
- Добавляй кейсы по одному через форму
- Или импортируй пачкой из YAML/CSV
- Каждый кейс: input (обязательно), category, context (опционально), reference

### 3. Создай рубрику

Вкладка "Rubrics" > "New Rubric".
- Выбери шаблон (Support, Content, Code) или создай с нуля
- Добавь измерения с весами (сумма = 1.0)
- Каждое измерение: 5 уровней с описаниями

### 4. Запусти эксперимент

Страница эксперимента > "Run". Выбери тест-сет, рубрику, модель-судью. Нажми "Run".
- Dry run: проверить конфиг без API вызовов
- Full run: полный прогон с live-логом (SSE стриминг)
- Прогресс виден в реальном времени: кейс X из Y, таймер

### 5. Смотри результаты

После завершения открывается дашборд:
- Summary card: победитель, уверенность, рекомендация
- Score bars: визуальное сравнение средних баллов
- Dimension table: p-values, Cohen's d, delta по каждому измерению
- Pairwise win rates: процент прямых побед с swap consistency
- Category breakdown: результаты по категориям (обнаружение сплитов)
- Response browser: ответы бок о бок, оценки судьи с reasoning

### 6. Итерируй

"Clone & Iterate" создаёт копию эксперимента с привязкой к предшественнику. Цепочка итераций (v1 > v2 > v3) отображается на странице запуска вместе с графиком тренда.

### 7. Сравнивай запуски

History > выбери два запуска чекбоксами > "Compare". Показывает оба результата бок о бок с дельтой по каждому измерению.

## Context Source (RAG)

Для тестирования RAG-промптов, где каждый тест-кейс должен получить контекст из retrieval pipeline:

**Статический контекст:** добавь поле `context` в тест-кейс. Оба промпта получат одинаковый контекст.

**Динамический контекст:** настрой в эксперименте (секция "Context Source"):

*Script:*
```
python my_rag.py --query '{input}'
```
Выполняет команду, подставляя input тест-кейса. stdout = контекст.

*HTTP:*
```
POST https://my-api.com/retrieve
Body: {"query": "{input}", "top_k": 5}
Response path: data.context
```
Вызывает API, подставляя input. Извлекает контекст по dot-path из ответа.

Кнопка "Test" проверяет конфиг без запуска эксперимента.

**Приоритет:** статический контекст в тест-кейсе всегда важнее динамического.

**Шаблон инъекции:** секция "Context Injection Format" позволяет настроить формат (`{context}` и `{input}` плейсхолдеры) и позицию (user message или system prompt).

## Production Deployment

```bash
cp .env.example .env
# Заполни DOMAIN, OPENAI_API_KEY, ANTHROPIC_API_KEY

docker compose -f docker-compose.prod.yml up -d
```

Caddy автоматически получит SSL-сертификат. Подробности в `DEPLOY.md`.

---

# CLI

## Установка

```bash
cd prompt-ab-testing
python -m venv .venv
source .venv/bin/activate
pip install -e .
```

Добавь ключ в `.env`:

```
OPENAI_API_KEY=sk-proj-...
ANTHROPIC_API_KEY=sk-ant-...
```

---

## Шаг 1. Создай конфиг эксперимента

Создай файл в `configs/`, например `configs/my_experiment.yaml`:

```yaml
experiment:
  name: "my-experiment"
  description: "Что тестируем и зачем."
  hypothesis: "Что ожидаем увидеть."

model:
  name: "gpt-4o-mini"       # глобальная модель по умолчанию
  temperature: 0.3
  max_tokens: 1024

prompts:
  prompt_a:
    name: "Current"          # короткое название для отчёта
    system: |
      Твой текущий системный промпт.

  prompt_b:
    name: "New"
    system: |
      Новая версия, которую хочешь проверить.

test_set: "test_sets/my_cases.yaml"
rubric: "rubrics/my_rubric.yaml"

output:
  dir: "results"
  formats: ["markdown", "json"]
```

**Per-prompt model override** для кросс-модельного сравнения:

```yaml
model:
  name: "gpt-4o-mini"       # fallback, если у промпта нет своей модели
  temperature: 0.3
  max_tokens: 1024

prompts:
  prompt_a:
    name: "GPT-4o-mini"
    system: |
      Одинаковый промпт для обоих.
    model:                   # переопределяет глобальный model
      name: "gpt-4o-mini"
      temperature: 0.3

  prompt_b:
    name: "Claude Sonnet"
    system: |
      Одинаковый промпт для обоих.
    model:
      name: "claude-sonnet-4-20250514"
      temperature: 0.3
```

Если у промпта есть блок `model`, он используется вместо глобального. Можно переопределить только модель, только temperature или всё сразу.

**Важно:** меняй одну переменную за раз. Если изменить и промпт, и модель одновременно, непонятно что именно сработало.

Готовый пример: `configs/example.yaml`.

---

## Шаг 2. Создай тест-кейсы

Файл в `test_sets/`, например `test_sets/my_cases.yaml`:

```yaml
test_cases:
  - id: "billing-001"
    category: "billing"
    input: "Меня дважды списали за подписку в этом месяце. Нужен возврат."

  - id: "technical-001"
    category: "technical"
    input: "Кнопка экспорта в PDF не работает. Кликаю — ничего не происходит. Chrome, Mac."

  - id: "complaint-001"
    category: "complaint"
    input: "Ваш продукт падал три раза за месяц. Мы платим $500/мес, это неприемлемо."
```

**Сколько кейсов:**
- 5 штук: только проверить, что пайплайн работает, статистика бессмысленна
- 30: минимум для реального анализа
- 50+: рекомендуется

**По категориям:** покрывай реальные сценарии продукта. Категории позволяют увидеть сплиты — промпт B может выигрывать в целом, но проигрывать на технических вопросах.

Готовые примеры: `test_sets/support_5.yaml`, `test_sets/support_50.yaml`.

---

## Шаг 3. Создай рубрику оценки

Файл в `rubrics/`, например `rubrics/my_rubric.yaml`:

```yaml
dimensions:
  - name: "accuracy"
    weight: 0.40
    description: "Фактически правильный ли ответ?"
    levels:
      - score: 5
        description: "Полностью верно, включает оговорки и крайние случаи."
      - score: 4
        description: "Верно. Незначительные упущения, не влияющие на результат."
      - score: 3
        description: "В основном верно, но есть неточности, способные запутать."
      - score: 2
        description: "Частично верно. Может навести на ложные действия."
      - score: 1
        description: "Ошибки, которые приведут к неверным действиям пользователя."

  - name: "actionability"
    weight: 0.30
    description: "Может ли пользователь предпринять конкретные действия?"
    levels:
      - score: 5
        description: "Чёткие пронумерованные шаги. Понятно что делать и в каком порядке."
      - score: 4
        description: "Хорошее руководство. Пользователь может действовать с минимальными уточнениями."
      - score: 3
        description: "Общее направление есть, конкретных шагов нет."
      - score: 2
        description: "Размытые советы. Непонятно что делать."
      - score: 1
        description: "Нет ничего actionable. Пользователь завис."

  - name: "tone"
    weight: 0.30
    description: "Тон уместный?"
    levels:
      - score: 5
        description: "Тепло и профессионально. Пользователь чувствует, что его услышали."
      - score: 4
        description: "Профессионально и вежливо."
      - score: 3
        description: "Нейтрально. Транзакционно, но не плохо."
      - score: 2
        description: "Роботизированно или немного пренебрежительно."
      - score: 1
        description: "Грубо или неуместно по тону."
```

**Рекомендации:**
- Сумма весов должна быть 1.0
- Описания уровней должны быть конкретными. "Хороший ответ" — бесполезно. "Содержит пронумерованные шаги" — работает.
- 3-5 измерений — оптимально. Больше — судья становится менее точным.
- Все 5 уровней должны быть заполнены.

Готовый пример: `rubrics/support.yaml`.

---

## Шаг 4. Запусти тест

Сначала проверь пайплайн на 5 кейсах:

```bash
prompt-ab run --config configs/test_5.yaml
```

Если всё прошло без ошибок — запускай полный эксперимент:

```bash
prompt-ab run --config configs/my_experiment.yaml
```

Файлы результатов появятся в `results/`.

**Сколько это стоит** (ориентир для 50 кейсов, без учёта судьи):
- `gpt-4o-mini`: ~$1-2, ~10 минут
- `gpt-4o` / Claude Sonnet: ~$3-5
- Судья `gpt-5.4` добавляет ~$2-5 поверх (60 вызовов на 15 кейсов в режиме both)

---

## Шаг 5. Прочитай результаты

Открой HTML-дашборд в браузере:

```bash
open results/report_*.html
```

Что смотреть:

**Таблица по измерениям**
Какой промпт выиграл на каждом из измерений рубрики. Рядом p-value и effect size.

**p-value**: если < 0.05 — разница статистически значимая (не случайная).

**Effect size (Cohen's d)**:
- < 0.2: пренебрежимо, не стоит переходить
- 0.2-0.5: маленький эффект, переходить только если это критичный промпт
- 0.5-0.8: средний, стоит переходить
- 0.8+: большой, точно переходить

**Head-to-head win rate**: сколько прямых сравнений выиграл промпт B. 70%+ — сильный сигнал.

**Swap consistency**: должна быть 80%+. Если ниже — у судьи позиционное смещение (предпочитает ответ, который стоит первым). Попробуй более сильную модель-судью.

**Breakdown по категориям**: может оказаться, что B выигрывает в целом, но A лучше справляется с техническими вопросами. Это повод использовать разные промпты для разных типов запросов.

---

## Дополнительные команды

**Dry run** (посмотреть что будет, без API вызовов):
```bash
prompt-ab run --config configs/my_experiment.yaml --dry-run
```

**Выбор моделей — важно:**

- **Тестируемая модель** должна быть идентична той, что стоит у тебя в продакшене. Тестируешь промпт для `gpt-4o-mini` в проде — в конфиге ставишь `gpt-4o-mini`. Иначе результаты не переносятся.
- **Судья** должен быть флагманской моделью с поддержкой reasoning. Сейчас это `gpt-5.4` (OpenAI) или `claude-opus-4-6` (Anthropic). Судья слабее тестируемой модели — ненадёжный судья.

```bash
prompt-ab run --config configs/my_experiment.yaml --judge-model gpt-5.4
```

**Перезапуск оценки без повторной генерации ответов** (если изменил рубрику):
```bash
# Важно: явно указывай путь к нужному run-файлу, иначе возьмётся не тот:
prompt-ab evaluate --results results/run_my-experiment_XXXXXX.json --rubric rubrics/new_rubric.yaml
```

**Отдельные шаги по одному** (указывай конкретные файлы, не glob):
```bash
prompt-ab evaluate --results results/run_my-experiment_XXXXXX.json --rubric rubrics/my_rubric.yaml --judge-model gpt-5.4
prompt-ab analyze --eval results/eval_my-experiment_XXXXXX.json
prompt-ab report --analysis results/analysis_my-experiment_XXXXXX.json --run results/run_my-experiment_XXXXXX.json --eval results/eval_my-experiment_XXXXXX.json
```

---

## Что в папке results/

| Файл | Что внутри |
|------|------------|
| `run_*.json` | Сырые ответы обоих промптов |
| `eval_*.json` | Оценки судьи по каждому ответу |
| `analysis_*.json` | Статистический анализ |
| `report_*.html` | Интерактивный дашборд |
| `report_*.md` | Отчёт в Markdown |
| `summary_*.json` | Компактный JSON для автоматизации |

### Структура summary.json (для автоматизации / агентов)

```json
{
  "run_id": "my-experiment_20260319_...",
  "prompt_a": "Current",
  "prompt_b": "New",
  "recommendation": "New",        // какой промпт победил
  "confidence": "high",           // high / medium / low
  "overall_score_a": 3.98,
  "overall_score_b": 4.15,
  "win_rate_a": 0.43,
  "win_rate_b": 0.45,
  "swap_consistency": 0.84,
  "dimensions": {
    "accuracy": {
      "score_a": 4.02,
      "score_b": 4.10,
      "p_value": 0.55,            // > 0.05 = незначимо
      "effect_size": -0.09        // отрицательный = B лучше
    }
  }
}
```

Прочитать вывод без браузера:
```bash
cat results/summary_*.json | python3 -m json.tool
```

---

## Если эксперимент запускает агент

Минимальный набор действий для автономного запуска:

1. Создать три файла: `configs/NAME.yaml`, `test_sets/NAME.yaml`, `rubrics/NAME.yaml`
2. Запустить dry run и убедиться что конфиг валидный: `prompt-ab run --config configs/NAME.yaml --dry-run`
3. Запустить полный прогон с явным судьёй: `prompt-ab run --config configs/NAME.yaml --judge-model gpt-5.4`
4. Прочитать результат: `cat results/summary_NAME_*.json`
5. Интерпретировать: `recommendation` = победитель, `confidence` = уверенность, `dimensions` = по каким измерениям

Правила для агента:
- Всегда указывай `--judge-model` явно. Дефолт требует Anthropic ключа.
- Не используй `--eval-only` без явного пути к run-файлу (`--results results/run_NAME_*.json`) — иначе возьмётся последний файл в папке, который может быть от другого эксперимента.
- Минимум 30 кейсов для значимой статистики. Меньше — pipeline пройдёт, но p-value бессмысленны.
- При интерпретации effect_size: отрицательное значение означает что B лучше A.

---

## Когда результатам нельзя доверять

- Меньше 30 кейсов: статистика ненадёжная
- Swap consistency < 80%: у судьи позиционное смещение
- Изменено больше одной переменной между промптами: неясно, что именно сработало
- Рубрика не отражает реальные приоритеты продукта: высокие оценки не равно хороший промпт
- Тест-кейсы не покрывают реальное распределение запросов: результаты не переносятся в прод
