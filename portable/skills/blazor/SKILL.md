---
name: blazor
description: "Use when building Blazor apps: render trees, component lifecycle, JS interop, state management, forms/validation, SignalR circuits, WASM vs Server hosting, and AOT."
version: 1.0.0
---

# Blazor Deep Semantics

Load with `modern-csharp` for language questions. Targets .NET 10 Blazor (WebApp unified model).

## Hosting models (.NET 10 unified)
- **Blazor Web App** with per-page render modes:
  - `@rendermode InteractiveServer` — real-time over SignalR circuit, state lives on server.
  - `@rendermode InteractiveWebAssembly` — runs client-side after WASM runtime + assemblies download.
  - `@rendermode InteractiveAuto` — starts Server, silently upgrades to WASM once runtime cached (best UX).
- Static SSR (no interactivity) is the default for fast first paint; interactivity islands via render mode on a page or component.
- Global vs per-component render mode: set on `<Routes>` / `HeadOutlet` in App.razor for global.
- Prerendering is on by default; disable with `@rendermode @(new InteractiveServerRenderMode(prerender: false))`.
- Circuit: server-side user session over SignalR with reconnect UI (`Components/WebApp/Pages/...` ReconnectModal); state lost on disconnect unless persisted (`PersistentComponentState`).

## Component model
- `.razor` files compile to C# classes deriving from `ComponentBase`. BuildRenderTree(RenderTreeBuilder) is generated output; sequence numbers matter for diffing (never hand-write dynamic sequences).
```razor
@page "/counter"
@rendermode InteractiveServer
<h3>@currentCount</h3>
<button @onclick="IncrementCount">Click me</button>

@code {
    private int currentCount = 0;
    private void IncrementCount() => currentCount++;
}
```
- Parameters: `[Parameter] public int Size { get; set; }` — must not mutate parameters in component logic (overwrites parent on re-render). `SetParametersAsync` override for advanced control.
- Cascading values: `<CascadingValue Value="..." IsFixed="true">` + `[CascadingParameter]` — IsFixed skips subscription overhead. Cascade by Type or by Name.
- EventCallback for child→parent comms (supports async, avoids Task leak): `[Parameter] public EventCallback<MouseEventArgs> OnClick { get; set; }` invoked `await OnClick.InvokeAsync(args)`.
- RenderFragment & RenderFragment<T> for template parameters (generic templated components).
- Keyed rendering: `@key` directive to preserve element identity across re-renders (lists especially).

## Lifecycle (order matters!)
1. `SetParametersAsync`
2. **Prerender phase**: `OnInitialized{Async}` → `OnParametersSet{Async}` → `OnAfterRender{Async}(firstRender:true)`
3. **Interactive phase**: same chain again (component constructed twice under prerendering!) — beware double side effects.
4. On each re-render trigger (StateHasChanged, parameter change, event handled): `ShouldRender` gate → `OnParametersSet{Async}` → `BuildRenderTree` → `OnAfterRender{Async}`.
- Async lifecycle: UI shows nothing until first await completes; use loading placeholders.
- Dispose: implement `IDisposable`/`IAsyncDisposable` — called automatically. Unsubscribe events here.

## Rendering semantics
- Manual `StateHasChanged()` needed after non-blazor-invoked changes (timer, external event, background task). Automatic after event handlers and async lifecycle methods resume.
- Render tree diffing: by sequence number + type + key. Avoid LINQ inside markup that produces different sequence counts conditionally (use `if/else`, never `&&` chains to add attributes conditionally).
- `@bind` sugar: `@bind="Value"` → value + ValueChanged pair; `@bind:event="oninput"` for immediate updates; `@bind:after`, `@bind:get`, `@bind:set` modifiers (.NET 8+, standard in .NET 10).
- Virtualize component `<Virtualize Items="@items" Context="item" ItemSize="40" Overscan="10">` for large lists.

## JavaScript interop
```csharp
// Call JS
var result = await jsRuntime.InvokeAsync<string>("myModule.getText", "#editor");
// Import module (isolated JS, preferred)
var module = await jsRuntime.InvokeAsync<IJSObjectReference>("import", "./js/interop.js");
```
- IJSRuntime unavailable during prerender (throws) — guard with `OperatingSystem.IsBrowser()`, `rendererInfo.Name == "Static"`, or run in `OnAfterRenderAsync`.
- `IJSObjectReference` for holding JS objects; dispose via `.DisposeAsync()` or wrap in `IAsyncDisposable` component.
- JS → .NET: `[JSInvokable]` static or instance methods; DotNetObjectReference.Create + Dispose pattern to avoid leaks.
- CancellationToken variants (InvokeAsync with cancellation) to prevent hung circuits.
- JS isolation via collocated JS files (`Component.razor.js`) auto-imported per component.

## Forms & validation
- EditForm + Model + DataAnnotationsValidator (or FluentValidation/Manual):
```razor
<EditForm Model="model" OnValidSubmit="HandleSubmit">
    <DataAnnotationsValidator />
    <ValidationSummary />
    <InputText @bind-Value="model.Email" />
    <ValidationMessage For="() => model.Email" />
</EditForm>
```
- Input components: InputText, InputNumber, InputDate, InputSelect, InputCheckbox, InputRadioGroup, InputFile. All derive from `InputBase<T>` — subclass for custom widgets, override TryParseValueFromString.
- EditContext for programmatic validation: `editContext.Validate()`, `OnFieldChanged`, `ValidationMessageStore` for server-side errors mapped back to fields.
- .NET 9: `[SupplyParameterFromForm]` enables form handling in static SSR without interactivity.

## State management
- Scoped DI service per circuit (Server) or per browser tab (WASM). Singleton only sensible in WASM (per-tab anyway).
- `PersistentComponentState`: prerenders data into HTML payload, read back post-interactive-start (avoid double-fetch flicker).
- Auth state via AuthenticationStateProvider + `<AuthorizeView>`, `[Authorize]` attribute, `<AuthorizeRouteView>`; roles/policy-based.
- Browser storage: ProtectedBrowserStorage (ASP.NET Core Data Protection over localStorage/sessionStorage) — Server model only.
- URL as state: NavigationManager.GetUriWithQueryParameters + query-param binding `[SupplyParameterFromQuery]`.

## Routing
- `@page "/route/{Id:int}"` route constraints (int, guid, etc.); catch-all `{*PageName}`.
- NavigationManager: NavigateTo(url, replace:false), LocationChanged event, `NavigateTo(url, forceLoad:true)` legacy full reload (rarely needed now).
- NavLink component auto active-class matching; RouteView + LayoutView pipeline; custom layouts via `@layout MainLayout`.

## Performance
- ShouldRender override to skip redundant renders; avoid creating delegates/lambdas per-render in hot paths (cache Delegate.CreateDelegate or use EventCallback fields).
- `@key` on lists to minimize DOM churn.
- WASM: `PublishAot=true` (fully supported for Blazor WebAssembly in .NET 10), RunAOTCompilation for Mono AOT, trimming default on publish; startup budget ~2s target.
- Server: circuit memory ~ hundreds of KB per user; SignalR backplane (Redis/Azure SignalR) for scale-out; sticky sessions required behind load balancers.
- Virtualize all long lists; lazy-load assemblies with `LazyAssemblyLoader`.

## Security
- Auto HTML-encode everything; NEVER `((MarkupString)userInput)` without sanitizing.
- Anti-forgery auto-wired in current (.NET 10) templates.
- Server: never trust client-sent event data — all validation server-side regardless of client validation presence.
- Secrets never in WASM appsettings (shipped to client!) — proxy through your API.

## Common pitfalls
1. Prerendered + interactive double-execution of OnInitialized side effects — use PersistentComponentState or guard flags.
2. Injecting scoped services into components rendered statically at the wrong scope (scoped = per-request during SSR!).
3. IJSRuntime calls during OnInitialized under prerender throw.
4. Forgetting StateHasChanged after external events → UI appears frozen though state updated.
5. Large cascades cause whole-subtree re-renders — narrow cascade scope or split components.
6. Circuits dropped by idle timeouts/proxies — tune IdleTimeout + keepalive ping for corporate proxies.
