using Avalonia;


namespace Katharos.App;

static class Program
{
    [STAThread]
    public static void Main(string[] args)
    {
        // primeiro de tudo: o Velopack trata a instalação, a desinstalação e a troca de versão (e sai, quando é com ele)
        Velopack.VelopackApp.Build().Run();
        MontaApp().StartWithClassicDesktopLifetime(args);
    }

    public static AppBuilder MontaApp() => AppBuilder.Configure<App>().UsePlatformDetect().LogToTrace();
}
