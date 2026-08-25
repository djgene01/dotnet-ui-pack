---
name: modern-csharp
description: "Use when writing modern C#/.NET: language features (records, pattern matching, nullable, spans), async/await semantics, DI, generics, and performance idioms that underpin WPF/MAUI/Blazor."
version: 1.0.0
---

# Modern C# Foundations (for UI work)

Shared language/runtime knowledge behind the wpf / maui / blazor skills. Targets .NET 10 (current LTS), C# 14.

## Language essentials
- **Records** (`record class` / `record struct`): value-based equality, `with` expressions, init-only props. Ideal for view models' immutable messages/events.
- **Pattern matching**: property patterns (`if (obj is Person { Age: > 18 } p)`), relational (`>`, `<`), logical (`and/or/not`), list patterns (`[1, .., var last]`). Switch expressions for exhaustive mapping.
- **Nullable reference types**: `<Nullable>enable</Nullable>` — treat warnings as errors; `!` null-forgiving only with justification comment.
- **File-scoped namespaces**, global usings, primary constructors (C# 12) on classes/structs.
- **Span<T>/ReadOnlySpan<T>**: zero-alloc slicing for hot paths (parsers, text processing); never store spans in fields of heap classes or across await.
- **Collection expressions** `[1,2,3]`, spread `..` (C# 12).
- Init-only setters + required members for safe object construction.

## async/await deep semantics
- `async void` ONLY for event handlers (never elsewhere — exceptions crash the process). Return Task/ValueTask everywhere else.
- ConfigureAwait(false) in library code, NOT in UI event handlers (need to resume on UI context). Blazor/WPF/MAUI all have sync contexts.
- ValueTask for hot single-consume paths; double-awaiting a consumed ValueTask = undefined behavior.
- CancellationToken plumbing: accept parameter, pass down, throw via ThrowIfCancellationRequested. UI: register against DispatcherTimer or use linked tokens.
- Async disposal: IAsyncDisposable + `await using`.
- Deadlocks: `.Result`/`.Wait()` under a sync context = classic WPF deadlock — always await all the way up.
- Parallel when CPU-bound + independent: `Parallel.ForEachAsync` for async IO loops; PLINQ only for pure data parallelism.

## Dependency Injection (Microsoft.Extensions.DependencyInjection)
```csharp
services.AddSingleton<IConfigService, ConfigService>();   // one instance
services.AddScoped<CartService>();                        // per scope (per circuit/request)
services.AddTransient<DetailsViewModel>();                // new each resolve
```
- Service lifetimes vs consumer lifetime mismatches cause bugs (captive dependency: singleton holding scoped).
- `IOptions<T>`/`IOptionsSnapshot<T>`/`IOptionsMonitor<T>` for settings (singleton-safe/scope-refresh/live-reload respectively).
- Keyed services (.NET 8+, available in .NET 10): `[FromKeyedServices("name")]`, `AddKeyedSingleton`.
- Generic host is standard in all three frameworks — configure logging (ILogger<T>), config (IConfiguration), DI uniformly.

## MVVM toolkit idioms (CommunityToolkit.Mvvm 8.x)
```csharp
public partial class MainViewModel : ObservableObject
{
    [ObservableProperty]
    [NotifyPropertyChangedFor(nameof(FullName))]
    private string firstName = "";

    [RelayCommand(CanExecute = nameof(CanSave))]
    private async Task SaveAsync(CancellationToken ct) { ... }

    private bool CanSave() => !string.IsNullOrWhiteSpace(FirstName);
}
```
- Source generators emit the INPC boilerplate; partial keyword required.
- Messenger: `WeakReferenceMessenger.Default.Send(new MyMessage(...))` + `IRecipient<T>` interface auto-registration.

## Performance idioms
- Stackalloc/array pooling (`ArrayPool<T>.Shared`) for buffers; avoid LINQ in render/draw/update hot loops (measure first with BenchmarkDotNet).
- String interpolation with constant strings compiles to DefaultInterpolatedStringHandler — fine; but string.Concat beats multiple + in tight loops.
- Structs: readonly struct for small immutable values; avoid large structs (>16 bytes copies).
- Boxing traps: non-generic collections, struct→interface casts, string concat with value types pre-C#10.

## Testing
- xUnit + NSubstitute/Moq; FluentAssertions for readable asserts.
- UI testing: WPF → FlaUI/Appium.WinAppDriver; MAUI → Appium; Blazor → bUnit for components + Playwright for E2E.
- ViewModel tests are plain unit tests — keep VMs free of framework types so they test without UI thread.
