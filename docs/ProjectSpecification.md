# Marble Chaos Factory

**Проектная документация v1.0 · 15.10.2026**

## 1. Концепция
Marble Chaos Factory — автоматизированная виртуальная 3D-фабрика для длительных YouTube-трансляций. Тысячи разноцветных шариков движутся по спиралям, воронкам, сортировщикам, лифтам и препятствиям. Трансляция объединяет satisfying 3D physics, ASMR, гонки цветовых команд, результаты и зрительские голосования.

**Принцип:** Blender предварительно рассчитывает физику и рендерит сцены; Python составляет непрерывную программу и управляет OBS; YouTube Chat и DonationAlerts влияют на выбор будущих готовых сцен и HTML-overlay, но **не изменяют физику уже записанного видео**.

## 2. Паспорт
| Параметр | Решение |
|---|---|
| Название | Marble Chaos Factory |
| Жанр | Satisfying 3D Physics / Marble Run |
| Аудитория | Международная; надписи в игре на английском |
| ПО | Blender, Python, OBS Studio, FFmpeg, SQLite |
| ОС | Windows 11 |
| Физика | Blender Rigid Body; Geometry Nodes для визуализации; Molecular+ опционально |
| Целевое качество | 1080p60; позже 4K |
| Длительность | Старт 2–4 часа; после тестов 24/7 |

## 3. Режимы эфира
- **Endless Factory** — производственные циклы 10–30 минут.
- **Marble Race** — гонки команд 3–7 минут.
- **Funnel Madness** — массовое падение воронок 2–5 минут.
- **Spiral Challenge** — многоуровневые трассы 3–6 минут.
- **Marble Avalanche** — лавины 2–4 минуты.
- **Factory Challenge** — выбор испытания чатом 5–10 минут.
- **Relaxing ASMR** — спокойные сцены 10–20 минут.

Игровой цикл: генератор шариков → модульные механизмы → финиш и сортировка → результаты → голосование → выбор следующей сцены.

## 4. Визуальный стиль
Основной: **Neon Factory** — хромированные механизмы, прозрачные трубы, стеклянные шарики, мягкий студийный свет. Дополнительные: **Wood & Brass**, **Clean Laboratory**, **Arcade Arena**. 3D-сцена занимает большую часть экрана, динамические информационные элементы размещаются по краям.

## 5. Архитектура

```text
PRODUCTION
Python Scene Generator
   -> Blender Rigid Body / Bake
   -> Cycles or Eevee / Render Worker
   -> FFmpeg / ffprobe validation
   -> Media Library + SQLite
                      |
BROADCAST             v
YouTube Chat ---> Python Stream Orchestrator <--- DonationAlerts
                         |
                  Scheduler / Event Queue
                         |
                    OBS WebSocket
                         |
            PLAYER_A / PLAYER_B + Browser Overlay
                         |
                     OBS Studio
                         |
                     YouTube Live
```

Сервисы: `scene_generator`, `physics_engine`, `render_worker`, `media_manager`, `stream_scheduler`, `obs_controller`, `chat_listener`, `event_processor`, `overlay_server`, `watchdog`.

## 6. Физика и 3D-модули
**Прототип:** 100–500 шариков, далее 1000–5000. Стартовые физические значения (настроить по тестам): диаметр 0,08 м, масса 0,05 кг, g=9,81 м/с², friction=0,25–0,45, restitution=0,3–0,65, substeps=60, solver iterations=20. Для коллизий шариков использовать Sphere; Geometry Nodes не заменяет расчёт столкновений. Фиксировать random seed и версии Blender. Обязательны стабильный bake, отсутствие провалов и застреваний, корректный финиш и сериализация результатов.

Модули: `SpiralTower`, `GravityFunnel`, `PegMaze`, `MarbleElevator`, `RotatingWheel`, `ColorSorter`. Входы/выходы модулей должны соответствовать общему стандарту координат, масштаба, физических допусков и пропускной способности.

## 7. Конфигурация сцены
```json
{
  "scene_id": "spiral_race_001",
  "title": "Rainbow Spiral Race",
  "template": "spiral_race",
  "seed": 14253,
  "ball_count": 500,
  "ball_radius": 0.04,
  "duration_seconds": 60,
  "fps": 60,
  "teams": ["RED", "BLUE", "GREEN", "YELLOW"],
  "physics": { "substeps": 60, "solver_iterations": 20 },
  "camera": "cinematic_follow",
  "render": {
    "engine": "CYCLES", "width": 1920,
    "height": 1080, "samples": 32
  }
}
```

Pipeline: шаблон → генерация → физика → bake → QA → результаты → рендер → валидация → утверждение → медиатека.

## 8. Схема данных
SQLite-таблицы:
- `scene_templates` — конфигурации 3D-модулей;
- `simulation_jobs`, `render_jobs` — фоновые задания;
- `media_assets` — путь, длительность, codec/fps, checksum;
- `scene_variants` — варианты seed, цвета и сложности;
- `playback_history` — история показов;
- `broadcast_sessions` — состояние трансляций;
- `viewer_votes`, `viewer_events` — голосования, команды, донаты;
- `competition_results` — реальные результаты рассчитанных соревнований;
- `system_events` — диагностика.

## 9. Автоматизированный эфир
OBS содержит два Media Source: `PLAYER_A` воспроизводит текущее видео, `PLAYER_B` предварительно готовит следующее. Переход по событиям OBS, проверенным длительностям медиа и запасному таймеру. Планировщик работает поверх транзакционной очереди.

Начальные веса: Endless Factory 35%, Marble Race 25%, Funnel Madness 15%, Spiral Challenge 10%, Marble Avalanche 10%, Special Event 5%. Голосование может переопределять веса. При достаточном ассортименте не повторять один файл в пределах последних 20 показов и не ставить подряд похожие сцены. MVP — 30 минут медиа; для длинного запуска — 3–4 часа разнообразного видео.

## 10. Отказоустойчивость
- Неиграбельное видео → следующий утверждённый файл.
- Нет альтернатив → резервная непрерывная программа.
- Отказ Chat API/DonationAlerts → основной эфир продолжается.
- Разрыв OBS WebSocket → переподключение и сверка состояния.
- Перезапуск контроллера → восстановление очереди из SQLite.
- Мало диска или GPU перегружен → фоновые задания Blender приостанавливаются.
- Watchdog не допускает параллельных экземпляров OBS.
- Хранить секреты в переменных окружения и вне Git.

## 11. Экран трансляции
Логотип MARBLE CHAOS FACTORY, LIVE, название испытания, шарики на трассе, следующий эпизод, leaderboard RED/BLUE/GREEN/YELLOW, таймер голосования, донат-уведомления. Технология: Browser Source с HTML/CSS/JS и WebSocket от FastAPI.

## 12. YouTube Chat
Официальный YouTube Live Streaming API, OAuth 2.0, предпочтительно `liveChatMessages.streamList`; резервный polling с учётом квот. Команды: `!red`, `!blue`, `!green`, `!yellow`, `!spiral`, `!funnel`, `!race`, `!stats`, `!help`. Один голос на один YouTube ID за раунд; защита от повторной обработки, ограничение частоты.

## 13. DonationAlerts
Второй этап разработки. Предлагаемые события: $1 — имя на экране; $3 — Marble Rain; $5 — выбор следующей трассы; $10 — Mega Marble Storm; $20 — Giant Chaos Challenge. Все действия в идемпотентной очереди, исполняются в безопасных точках; нельзя считать событие выполненным до фактического показа.

## 14. Аудио
Синхронизированные SFX качения и столкновений, фоновые позитивные треки с правами на стриминг, отдельные SFX для стартов, побед и событий зрителей. Нормализация громкости, кроссфейды, ASMR без музыки.

## 15. Рекомендуемая структура проекта
```text
MarbleChaosFactory/
├── README.md
├── requirements.txt
├── .env.example
├── config/{app.yaml,stream.yaml,physics.yaml,scenes/}
├── blender/{templates/,assets/,scripts/,projects/}
├── backend/{scheduler/,obs/,youtube/,donations/,media/,events/,database/,monitoring/}
├── frontend/{overlay/,dashboard/}
├── data/{database/,simulations/,rendered/,approved/,backups/}
├── audio/{music/,sfx/}
├── logs/
├── tests/
└── docs/
```

## 16. Система изготовления и пополнения медиатеки
Из проверенных шаблонов генерируются новые сиды и цветовые схемы; выполняются физический QA, bake, рендер, FFmpeg normalization, ffprobe validation, checksum, превью и подтверждение качества. В MVP утверждение человеком; позже автоутверждение только для проверенных шаблонов. Не следует запускать тяжёлый Cycles одновременно с OBS на единственной GPU до стресс-тестирования.

## 17. OBS
Коллекция `MarbleChaosFactory`. Сцены: `MCF_MAIN_A`, `MCF_MAIN_B`, `MCF_INTRO`, `MCF_VOTING`, `MCF_RESULTS`, `MCF_MAINTENANCE`, `MCF_TEST`.

Начальные параметры: 1920×1080, 60 FPS, NVENC H.264 при поддержке, CBR 12 Mbps, keyframe interval 2 sec, AAC stereo 128–160 Kbps, RTMPS. OBS WebSocket защищён паролем, обычно порт 4455. Проверить рекомендации YouTube до запуска.

## 18. Панель управления
Локальный Control Center: статус стрима, текущее и следующее видео, Media Library, render queue, расписание, Event Log, голосования, аварийное управление и системные метрики. При удалённом доступе — аутентификация и защищённый канал.

## 19. План реализации
| Этап | Содержание | Приёмка |
|---|---|---|
| 1 (1 день) | Установить Blender, Python, OBS, FFmpeg, Git; проверить OBS WebSocket | Переключение сцен Python |
| 2 (2–3 дня) | Бункер, спираль, воронка, 100–500 шариков | Чистый MP4 20–30 сек |
| 3 (3–5 дней) | Python JSON scene generator, bake/render CLI | Разные сцены по одной команде |
| 4 (3–4 дня) | SQLite, Media Manager, два OBS-плеера, overlay | Несколько часов воспроизведения |
| 5 (3–5 дней) | OAuth, Chat API, голосование, антиспам | Голоса меняют следующую сцену |
| 6 (5–10 дней) | 6 модулей, варианты и аудио | 3–4 часа библиотеки |
| 7 (3–5 дней) | Dashboard, watchdog, DonationAlerts | Восстановление после сбоев |
| 8 | Тест YouTube, запуск 2–4 ч, затем 24/7 | Метрики и стабильность |

Примерный ориентир полноценной первой версии — **3–6 недель**, без гарантий времени физического bake и рендера.

## 20. Приёмочные критерии
Нет провалов или телепортаций шариков; Full HD стабильный FPS; 100 переключений без пустых кадров; 8-часовой тест; анти-повторы; корректный restart recovery; дедупликация голосов; обработка отказов API/OBS/сети; отсутствие длительной перегрузки GPU; без клиппинга аудио; логи всех ошибок. Перед 24/7 — не менее 72 часов стресс-теста.

## 21. Первый прототип и YouTube-материалы
**Prototype 01 — Rainbow Spiral Factory**: бункер → прозрачная спираль → воронка → 4 цветных ёмкости; 500 шариков, 30 секунд, Full HD, bake, рендер, управление OBS. Затем масштабирование до 1000–5000 шариков.

Рекомендуемый заголовок: **MARBLE CHAOS FACTORY LIVE | Colorful Marbles, Satisfying 3D Physics & Marble Runs**.

Теги: `#MarbleRun #Satisfying #Blender3D #PhysicsSimulation #MarbleRace #YouTubeLive`.

Не обещать реальное число шариков или 24/7, пока эти показатели не достигнуты.

## Официальные источники
- [Blender Manual](https://docs.blender.org/)
- [OBS Studio](https://obsproject.com/)
- [obs-websocket](https://github.com/obsproject/obs-websocket)
- [YouTube Live Streaming API](https://developers.google.com/youtube/v3/live)
- [FFmpeg](https://ffmpeg.org/)
