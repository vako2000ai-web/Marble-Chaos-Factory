# Marble Chaos Factory

Automated Blender marble simulation and YouTube livestream project.

## Current implementation (Milestone 1)

- Procedural Blender scene generator: ramp, four marble lanes, funnel-like collector, rigid-body marbles, camera and lights.
- JSON scene configuration.
- SQLite media catalog and repeat-aware playlist scheduler that works without OBS.
- Unit tests for scheduler.

This is an initial prototype, **not yet a working 24/7 YouTube stream**. Blender, OBS and YouTube integrations need local testing.

## Quick start (Windows 11)

Install Blender 4.x/5.x and Python 3.11+.

```powershell
git clone https://github.com/vako2000ai-web/Marble-Chaos-Factory.git
cd Marble-Chaos-Factory
python -m unittest discover -s tests -v
python -m backend.scheduler --db data/database/media.sqlite --demo
blender --background --python blender/scripts/generate_scene.py -- --config config/scenes/prototype_01.json --out data/prototype_01.blend
```

Open `data/prototype_01.blend` in Blender. Bake rigid bodies, preview and render after validating collision stability. The script deliberately doesn't run a huge expensive render automatically.

## Documentation
See [full specification](docs/ProjectSpecification.md).

## Roadmap
1. Physics prototype QA and bake automation.
2. Render worker and ffprobe media ingest.
3. OBS dual-player controller and browser overlay.
4. Chat voting, donations and monitoring.

## Notes
- Only committed example settings; never commit OAuth tokens, stream keys or passwords.
- Visual marbles use sphere collisions; physics speed depends on computer and Blender version.
