using Avalonia;
using Avalonia.Headless;
using Avalonia.Threading;
using Katharos.App;

// uso: Katharos.Fotos <pasta> [largura altura]
var pasta = args.Length > 0 ? args[0] : "fotos";
double w = args.Length > 2 ? double.Parse(args[1]) : 1280, h = args.Length > 2 ? double.Parse(args[2]) : 820;
Directory.CreateDirectory(pasta);
AppBuilder.Configure<App>().UseSkia().UseHeadless(new AvaloniaHeadlessPlatformOptions { UseHeadlessDrawing = false }).SetupWithoutStarting();
var j = new Janela { Width = w, Height = h };
j.Show();
foreach (var tela in new[] { "inicio", "otimizar", "aovivo" })
{
    j.Mostra(tela);
    for (int i = 0; i < 3; i++) { Dispatcher.UIThread.RunJobs(); AvaloniaHeadlessPlatform.ForceRenderTimerTick(); }
    var foto = j.CaptureRenderedFrame();
    var arq = Path.Combine(pasta, tela + ".png");
    foto!.Save(arq);
    Console.WriteLine(arq);
}
