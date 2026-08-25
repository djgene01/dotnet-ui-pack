---
name: maui
description: "Use when building cross-platform apps with .NET MAUI: XAML vs C# UI, handlers architecture, MVVM, Shell navigation, platform integration, graphics, and deployment."
version: 1.0.0
---

# .NET MAUI Deep Semantics

Load with `modern-csharp` for language questions. Targets .NET 10 MAUI.

## Project setup
```
dotnet new maui -n MyApp
dotnet build -t:Run -f net10.0-android # run on device/emulator
```
- Single project model: platform heads referenced via `<TargetFrameworks>net10.0-android;net10.0-ios;net10.0-maccatalyst</TargetFrameworks>` plus Windows via `<TargetFramework>net10.0-windows10.0.19041.0</TargetFramework>`.
- Platform code lives in `Platforms/` folder (partial classes) or `#if ANDROID / #if IOS / #if WINDOWS` directives.
- Multi-targeting members: partial methods & partial properties bridge platform implementations.

## Architecture: handlers (the successor to renderers)
- Cross-platform control (e.g., `Button`) → **handler** (`ButtonHandler`) maps virtual view properties to native platform views via a **PropertyMapper**:
```csharp
public static IPropertyMapper<Button, ButtonHandler> Mapper =
    new PropertyMapper<Button, ButtonHandler>(ViewHandler.ViewMapper)
    {
        [nameof(IText.Text)] = MapText,
        [nameof(ITextStyle.TextColor)] = MapTextColor,
    };
```
- Mappers apply lazily + incrementally; `mapper.AppendToMapping(nameof(MyCustomization), (h, v) => {...})` for app-wide tweaks in MauiProgram.
- Native access per-platform inside handler: `handler.PlatformView` (Android.Widget.Button / UIKit.UIButton / Microsoft.UI.Xaml.Controls.Button).
- Customizing built-ins without full handler: `Microsoft.Maui.Handlers.ButtonHandler.Mapper` modification from `MauiProgram.CreateMauiApp`.
- Full custom control = define `class MyView : View` with BindableProperties + handlers per platform + register via `handlers.AddHandler<MyView, MyViewHandler>()`.

## Visual states
`VisualStateManager` with CommonStates groups: Normal, PointerOver, Pressed, Disabled, Focused, Selected — defined in styles; also `VisualStateGroup` inside ControlTemplate. Prefer over legacy triggers for interactive states.

## XAML specifics (differences from WPF!)
- Same `{Binding}` markup extension semantics, but binding engine is different implementation (not WPF's DP system — uses BindableProperty, analogous but separate).
- `x:DataType` + compiled bindings: ALWAYS set on CollectionView item templates — 8-10x faster bindings and compile-time checking:
```xml
<ContentPage x:DataType="vm:MainViewModel" ...>
    <Label Text="{Binding Name}" />
```
- RelativeSource supports only Self and FindAncestor (no TemplatedParent like WPF).
- ResourceDictionary merging: `<ResourceDictionary Source="Resources/Styles/Colors.xaml" />`; App-level resources in Resources/XAML.

## MVVM (canonical)
- CommunityToolkit.Mvvm is standard: `[ObservableProperty]`, `[RelayCommand]`, `[NotifyCanExecuteChangedFor]`.
- Built-in value converters in `Microsoft.Maui.Converters`; ship your own as `IValueConverter` in shared code.
- ViewModel-first navigation via dependency injection + `Routing.RegisterRoute`.

## Shell navigation
- `Shell` = URI-based nav hierarchy: FlyoutItem → TabBar → Tab → ContentTemplate.
- Routes: `Routing.RegisterRoute("details", typeof(DetailsPage));` then `await Shell.Current.GoToAsync("details?id=123", args)` — query params bind to `[QueryProperty(nameof(Id), "id")]` on the target VM/page.
- Back-stack semantics: GoToAsync("..") pops; `//route` absolute resets stack.
- Shell visual customization via `Shell.BackgroundColor`, `FlyoutHeaderBehavior`, etc.

## Layout panels
- Grid (column/row definitions with Auto/*), StackLayout (now orientation-based; prefer Grid for perf), FlexLayout (CSS-like), AbsoluteLayout, VerticalStackLayout/HorizontalStackLayout (MAUI-optimized).
- CollectionView (virtualized, no separators by default) replaces ListView — use `ItemsLayout="Grid"` for grids, SelectionMode, remaining items threshold for incremental load.
- Safe area: `On<iOS>().SetUseSafeArea(true)` or ignore via `SafeAreaEdges` (.NET 9).

## Essential APIs (replaces Xamarin.Essentials)
Namespace `Microsoft.Maui.ApplicationModel` etc. Key services:
- Connectivity, Geolocation, Permissions (request pattern: check → request → use), SecureStorage (Keychain/Keystore-backed), Preferences, FilePicker, MediaPicker, Share, Launcher, AppInfo/Battery/Sensors (Accelerometer, Compass with Start/Stop + ReadingChanged).
- All async, all throw FeatureNotSupportedException on unsupported platforms — wrap in try/catch or gate with `DeviceInfo.Platform`.
- DI container registration in MauiProgram: `builder.Services.AddSingleton<IDataService, DataService>(); builder.Services.AddTransient<DetailsPage>();` — constructor injection works into pages and VMs.

## Graphics & media
- `Microsoft.Maui.Graphics` (cross-platform ICanvas drawing): implement `IDrawable`, attach to `GraphicsView`. Drawing commands are retained per draw call; invalidate via `graphicsView.Invalidate()`.
- Shapes (Ellipse, Rectangle, Path) are layout-participating controls; Brushes/GradientBrush similar to WPF.
- Images: `ImageSource` variants (FileImageSource, UriImageSource with CachingEnabled+CacheValidity, FontImageSource for icon fonts).

## Lifecycle
- Application: OnStart/OnSleep/OnResume (+ Windows-specific OnActivated). Window-level events (.NET 8+; standard in .NET 10: multiple windows supported via CreateWindow override).
- Page lifecycle: Appearing/Disappearing events; NavigationPage Pushed/Popped.
- Android activity recreation on rotation/config change — persist state in Preferences/SecureStorage or OnSleep.

## Deployment
- Windows: MSIX packaging (Package.appxmanifest), self-signed cert for sideload.
- Android: keystore signing, AAB for Play Store; iOS provisioning profiles + `dotnet publish -f net10.0-ios -p:RuntimeIdentifier=ios-arm64`.
- Hot Restart (iOS from Windows) vs paired Mac (full builds).

## Common pitfalls
1. Missing x:DataType → runtime binding failures that look like silent nulls; enable compiled bindings everywhere.
2. Handlers not registered for custom controls → blank native view; check CreateMauiApp handler registrations.
3. iOS safe-area overlapping content; test notch/dynamic island devices.
4. Android emulator networking uses 10.0.2.2 for host localhost.
5. CollectionView DataTemplate x:DataType missing breaks virtualization recycling perf.
6. AOT/trimming: only fully supported on iOS/MacCatalyst; Android needs `PublishAot=true` + `TrimMode=partial` care; Windows no trimming support yet.
7. Debugging device crashes: adb logcat / Xcode Console, not just VS output.
