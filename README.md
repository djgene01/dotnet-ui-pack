# dotnet-ui-pack

[![Version](https://img.shields.io/badge/version-1.1.0-blue)](https://github.com/djgene01/dotnet-ui-pack/releases)
![Platform](https://img.shields.io/badge/platform-Hermes%20Agent%20%7C%20OpenAI%20Agent--Plugins-lightgrey)
![License](https://img.shields.io/badge/license-MIT-green)
![.NET](https://img.shields.io/badge/.NET-10%20LTS-512BD4)

**The ultimate C#/.NET UI plugin skills pack for AI agents** — deep semantic knowledge of
**WPF**, **.NET MAUI**, and **Blazor**, plus the modern C# language foundation they all
share. Targets **.NET 10 (current LTS)** / C# 14.

Not API listings — these skills encode *how the frameworks actually work*: rendering
pipelines, binding engines, threading models, lifecycle ordering, and the pitfalls that
cost real debugging time.

---

## Skills

| Skill | Load as | What it covers |
|---|---|---|
| 🖥️ **WPF** | `dotnet-ui-pack:wpf` | XAML→BAML compilation, DependencyProperties (priority, coercion, attached), routed events, the full binding engine, styles/templates/triggers, MVVM, measure/arrange + virtualization, Dispatcher threading & Freezables, pack URIs, MSIX packaging |
| 📱 **MAUI** | `dotnet-ui-pack:maui` | Handlers architecture + PropertyMappers, single-project multi-targeting, compiled bindings (`x:DataType`), Shell URI navigation, Essentials APIs, `Microsoft.Maui.Graphics`, app lifecycle, per-platform deployment |
| 🌐 **Blazor** | `dotnet-ui-pack:blazor` | Unified render modes (Server/WASM/Auto), prerendering pitfalls, component lifecycle ordering, render-tree diffing, JS interop isolation, EditForm/validation, state management, circuit scaling, security model |
| ⚡ **Modern C#** | `dotnet-ui-pack:modern-csharp` | Records, pattern matching, NRT, spans, async/await semantics (sync contexts, deadlocks), MS DI lifetimes, CommunityToolkit.Mvvm source generators, testing stack |

Every skill ends with a **"Common pitfalls"** section distilled from real-world failure modes —
silent binding errors, captive dependencies, prerender double-execution, circuit drops,
handler registration misses, and more.

---

## Install

### Hermes Agent

```bash
hermes plugins install djgene01/dotnet-ui-pack --enable
```

Or manually: copy the `dotnet-ui-pack/` folder into your Hermes home's `plugins/`
directory (`%LOCALAPPDATA%\hermes\plugins\` on Windows) and run
`hermes plugins enable dotnet-ui-pack`.

Skills are namespaced and opt-in — load them explicitly:

```
skill_view("dotnet-ui-pack:blazor")
```

> Takes effect on the next session after enabling.

### OpenAI / Agent-Plugins-v1-compatible agents

Use the portable package (`dotnet-ui-pack-*.zip` → `portable/` folder). It ships a
spec-compliant `plugin.json` pointing at `./skills`, which auto-discovers all four skills —
no Python bootstrap required.

---

## Repository layout

```
dotnet-ui-pack/
├── plugin.yaml          # Hermes manifest
├── __init__.py          # registers each skill via ctx.register_skill()
├── portable/            # Agent-Plugins-v1 variant (plugin.json + skills/)
└── skills/
    ├── wpf/SKILL.md
    ├── maui/SKILL.md
    ├── blazor/SKILL.md
    └── modern-csharp/SKILL.md
```

The `portable/` directory contains the Agent-Plugins-v1 distribution:

```
portable/
├── plugin.json          # $schema 1.0.0, components.skills = "./skills"
└── skills/              # same four SKILL.md files (auto-discovered)
```

---

## Why "semantics"?

Most AI answers about .NET UI frameworks are syntactically right and operationally wrong.
These skills focus on the mechanics that decide whether code *works*:

- **Why** a TextBox binding only updates on LostFocus, and how to change it
- **Why** an `async void` crash takes down the whole WPF process
- **Why** `OnInitialized` runs twice under Blazor prerendering, and how to guard side effects
- **Why** implicit styles don't cross template boundaries in WPF
- **Why** missing `x:DataType` silently destroys MAUI CollectionView performance

---

## Requirements

- .NET 10 SDK (samples/targeting; skills are also valid guidance back to .NET 8 / .NET Framework 4.8 for WPF)
- A Hermes Agent install *or* any OpenAI Agent-Plugins-v1-compatible runtime

## License

MIT © Eugene
