using Avalonia;

namespace Katharos.App;

static class Program
{
    [STAThread]
    public static void Main(string[] args) => MontaApp().StartWithClassicDesktopLifetime(args);

    public static AppBuilder MontaApp() => AppBuilder.Configure<App>().UsePlatformDetect().LogToTrace();
}
