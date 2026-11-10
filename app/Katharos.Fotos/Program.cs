using Avalonia;
using Avalonia.Headless;
using Avalonia.Threading;
using Katharos.App;

// uso: Katharos.Fotos <pasta> [largura altura]     desenha as telas
//      Katharos.Fotos --motor                     confere a conversa com o motor de verdade (katharos.py api)
if (args.Length > 0 && args[0] == "--motor")
{
    await using var m = await MotorComum.Abre();
    Console.WriteLine("motor " + m.Versao);
    Console.WriteLine((await m.Pede("versao"))?.ToJsonString());
    var ini = await m.Pede("inicio");
    Console.WriteLine("inicio: " + string.Join(", ", ini!.AsObject().Select(kv => kv.Key)));
    int etapas = 0;
    var its = await m.Pede("itens", new { modo = "equilibrado" }, (t, d) => etapas++);
    Console.WriteLine("itens: " + its!["areas"]!.AsArray().Sum(a => a!["itens"]!.AsArray().Count(i => i!["marcado"]!.GetValue<bool>())) + " marcados");
    try { await m.Pede("aplicar", new { itens = new { servicos = new[] { "x" } } }); }
    catch (ErroDoMotor e) { Console.WriteLine("aplicar sem aceite: " + e.Codigo); }
    return;
}
var pasta = args.Length > 0 ? args[0] : "fotos";
double w = args.Length > 2 ? double.Parse(args[1]) : 1280, h = args.Length > 2 ? double.Parse(args[2]) : 820;
Directory.CreateDirectory(pasta);
Servico.Exemplo = true;
AppBuilder.Configure<App>().UseSkia().UseHeadless(new AvaloniaHeadlessPlatformOptions { UseHeadlessDrawing = false }).SetupWithoutStarting();
var j = new Janela { Width = w, Height = h };
j.Show();
foreach (var tela in new[] { "inicio", "raiox", "otimizar:servicos", "aovivo", "jogos", "sugestoes", "desfazer", "config", "aviso" })
{
    j.Mostra(tela);
    for (int i = 0; i < 6; i++) { Dispatcher.UIThread.RunJobs(); AvaloniaHeadlessPlatform.ForceRenderTimerTick(); Thread.Sleep(30); }
    var foto = j.CaptureRenderedFrame();
    var arq = Path.Combine(pasta, tela.Split(':')[0] + ".png");
    foto!.Save(arq);
    Console.WriteLine(arq);
}
