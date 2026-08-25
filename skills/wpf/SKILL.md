---
name: wpf
description: "Use when building Windows desktop apps with WPF: XAML semantics, DependencyProperties, routed events, data binding, styles/templates/triggers, MVVM, threading, and packaging."
version: 1.0.0
---

# WPF Deep Semantics

Load with `modern-csharp` for language-level questions. Targets .NET 10 WPF — the current LTS (also valid on .NET 9/8 and back to .NET Framework 4.8).

## Project setup
```
dotnet new wpf -n MyApp
```
csproj essentials:
```xml
<UseWPF>true</UseWPF>
<TargetFramework>net10.0-windows</TargetFramework>
<EnableWindowsTargeting>true</EnableWindowsTargeting> <!-- build from Linux CI -->
<ApplicationManifest /> or <ApplicationIcon />
```

## XAML compilation pipeline
- XAML → BAML (binary) embedded as resource at compile time; `InitializeComponent()` (in .g.cs) loads it via `Application.LoadComponent`. Generated partial class connects named elements (`x:Name` → generated fields).
- `x:Class` merges code-behind; markup extensions `{Binding}`, `{StaticResource}` are compiled to object graphs.
- Resource lookup order at runtime: element.Resources → up the visual tree → Window → Application.Current.Resources → theme dictionaries. Missing StaticResource = runtime exception (fail fast); DynamicResource silently stays null until found.

## Dependency Property (DP) system
```csharp
public static readonly DependencyProperty ValueProperty =
    DependencyProperty.Register(nameof(Value), typeof(double), typeof(Gauge),
        new FrameworkPropertyMetadata(0d,
            FrameworkPropertyMetadataOptions.AffectsRender | FrameworkPropertyMetadataOptions.BindsTwoWayByDefault,
            OnValueChanged, CoerceValue));

public double Value { get => (double)GetValue(ValueProperty); set => SetValue(ValueProperty, value); }
```
Semantics:
- Stored in an efficient sparse PropertyStore, not fields. Support inheritance down tree (`Inherits`), change callbacks, coercion, validation, animation targets.
- `AddOwner` shares a DP across types; `OverrideMetadata` specializes per subtype (e.g., TextBlock.Text wrapping).
- Attached properties = DPs registered via `RegisterAttached` — used by panels (Grid.Row), behaviors.
- Priority order for a value: animation > local value > template/trigger setters > style triggers > style setters > inherited > theme/default.
- Custom controls: ALWAYS expose DP + coerce + `AffectsMeasure/AffectsArrange/AffectsRender` so layout invalidates correctly.

## Routed events
Three strategies: **Bubbling** (MouseUp), **Tunneling** (PreviewMouseUp — tunnel events are Preview*, travel root→element), **Direct** (no routing).
- Handled flag stops routing: `e.Handled = true`; still see handled events with `AddHandler(ev, handler, handledEventsToo: true)`.
- Commands bubble too: `CommandManager` + `RoutedCommand` (Copy/Paste) — InputGestures map keys to commands.
- Class handlers run before instance handlers.

## Data binding engine
```xml
<TextBlock Text="{Binding Path=Name, Mode=TwoWay, UpdateSourceTrigger=PropertyChanged,
                  ValidatesOnNotifyDataErrors=True, StringFormat={}{0:C}}" />
```
- Binding modes: OneWay (default for most), TwoWay (default for editable controls' properties via metadata), OneWayToSource, OneTime.
- UpdateSourceTrigger: PropertyChanged / LostFocus (TextBox.Text default!) / Explicit.
- Sources: DataContext, ElementName, RelativeSource ({x:Type self/FindAncestor/TemplateBindingParent}), StaticResource, x:Static.
- Converters: implement `IValueConverter`; return `Binding.DoNothing` to leave unchanged, `DependencyProperty.UnsetValue` to fall through to fallback. `FallbackValue`, `TargetNullValue`, `ConverterParameter`.
- MultiBinding + IMultiValueConverter for composite values.
- Debugging bindings: PresentationTraceSources.TraceLevel=High on binding; listen to `BindingError` trace source; check Output window for binding errors (they don't throw).
- INotifyPropertyChanged: raise before dependent computed props; use `[CallerMemberName]`. Collection changes need `INotifyCollectionChanged` (ObservableCollection) — replacing an item inside ObservableCollection does NOT fire change notifications for that item's own props unless item implements INPC.
- `Delay=250` on binding for search-as-you-type throttling.

## Styles, templates, resources
- Style: Setter collection; BasedOn inheritance; implicit style (only TargetType key) applies automatically — but NOT to elements inside ControlTemplate unless explicitly referenced.
- Triggers: Trigger (property), DataTrigger (binding), EventTrigger (storyboards only), MultiTrigger/MultiDataTrigger.
- ControlTemplate redefines entire visual tree; TemplateBinding is lightweight one-way to templated parent; `{RelativeSource TemplatedParent}` allows TwoWay.
- DataTemplate maps data type → visuals (DataType + ImplicitDataTemplates by type resolution); HierarchicalDataTemplate for TreeView; ItemsPanelTemplate for container layout.
- Resources: x:Key required (except implicit styles); merged dictionaries `Source="pack://application:,,,/Assembly;component/Themes/Light.xaml"`; DynamicResource for runtime theme switching.
- pack URIs: `pack://application:,,,/DllName;component/path/file.xaml`.

## MVVM (canonical)
- ViewModels: POCO + INPC, no `using System.Windows`. Commands: `RelayCommand`/`AsyncRelayCommand` (CommunityToolkit.Mvvm).
- CommunityToolkit.Mvvm source generators: `[ObservableProperty]`, `[RelayCommand]`, `[NotifyPropertyChangedFor]` — prefer these over hand-written INPC boilerplate.
- Dialogs/services injected as interfaces (IDialogService) so VMs stay testable; use messenger (`WeakReferenceMessenger`) for cross-VM events.
- Navigation: ContentControl + DataTemplates keyed on VM types, or NavigationService swapping CurrentPage.

## Layout system (measure/arrange)
1. Measure pass: parent calls child.Measure(availableSize) bottom-up constraint propagation.
2. Arrange pass: Arrange(finalRect).
- Panels implement MeasureOverride/ArrangeOverride. Infinite available size (scroll viewers) breaks percentage sizing — know this when content vanishes inside ScrollViewer (use Width=Auto + alignment, or Grid with star sizes).
- Virtualization: VirtualizingStackPanel (default for ListBox/ListView) — set `VirtualizingPanel.IsVirtualizing="True"`, `ScrollUnit=Item`, `CacheLength` tuning; custom items control loses it unless you restore the panel.
- RenderTransform vs LayoutTransform: render doesn't trigger layout (cheap, overlaps), layout does (expensive, participates).

## Threading model
- Single UI thread owns DispatcherObject tree. All visual updates via `Dispatcher.Invoke/BeginInvoke(DispatcherPriority)`.
- Background threads touching controls = InvalidOperationException ("owned by another thread").
- Freeze Freezables (Brushes, Geometries): `brush.Freeze()` → cross-thread safe + faster.
- `DispatcherTimer` for UI-tick work; never System.Timers.Timer directly into UI.
- Async command pattern keeps UI responsive; long CPU work → `Task.Run`, then marshal result.

## Graphics/media
- Retained-mode composition: DrawingVisual/DrawingContext for lightweight custom drawing (no hit-test overhead of full controls); WriteableBitmap for pixel pushing; InteropBitmap for D3D shared surfaces.
- Animations: Storyboard/DoubleAnimation on DPs; hand-off semantics (animation holds value — remove or set FillBehavior.Stop, then assign local value).

## Packaging & deployment
- MSIX (recommended), single-file self-contained exe (`PublishSingleFile`), or ClickOnce legacy.
- Trim warnings: WPF is not trim-safe — avoid PublishTrimmed.
- High DPI: PerMonitorV2 manifest; test multi-monitor scaling.

## Common pitfalls
1. Binding errors silent — always scan output; wire trace sources in debug builds.
2. Memory leaks: static events, DispatcherTimer holding refs, subscribing to long-lived service events from short-lived views (use weak events/messenger).
3. Modifying ObservableCollection from background thread throws — marshal first.
4. Implicit styles don't cross template boundaries for Controls (only FrameworkElements like TextBlock get implicit style inside templates).
5. x:Name vs Name: identical in code-behind pages, but x:Name works anywhere (styles, templates).
