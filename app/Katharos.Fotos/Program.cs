using Avalonia.VisualTree;
using Avalonia;
using Avalonia.Headless;
using Avalonia.Threading;
using Katharos.App;

// uso: Katharos.Fotos <pasta> [largura altura]     desenha as telas
//      Katharos.Fotos --video <pasta> [roteiro...]  grava os vídeos do site (quadros em PNG; o ffmpeg monta)
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
Servico.Exemplo = true;
if (args.Length > 1 && args[0] == "--video")
{
    AppBuilder.Configure<App>().UseSkia().UseHeadless(new AvaloniaHeadlessPlatformOptions { UseHeadlessDrawing = false }).SetupWithoutStarting();
    Roteiros.LigaSimulador();
    foreach (var nome in args.Length > 2 ? args[2..] : Roteiros.Todos.Keys.ToArray())
    {
        var jv = new Janela { Width = 1280, Height = 800 };
        jv.Show();
        var f = new Filmagem(jv, Path.Combine(args[1], nome));
        Roteiros.Todos[nome](jv, f);
        jv.Close();
        Console.WriteLine(nome + ": " + Directory.GetFiles(Path.Combine(args[1], nome), "*.png").Length + " quadros");
    }
    return;
}
var pasta = args.Length > 0 ? args[0] : "fotos";
double w = args.Length > 2 ? double.Parse(args[1]) : 1280, h = args.Length > 2 ? double.Parse(args[2]) : 820;
Directory.CreateDirectory(pasta);
AppBuilder.Configure<App>().UseSkia().UseHeadless(new AvaloniaHeadlessPlatformOptions { UseHeadlessDrawing = false }).SetupWithoutStarting();
var j = new Janela { Width = w, Height = h };
j.Show();
// 2.12: cada tela, além da foto, é conferida: abriu sem a tela de erro e mostra o texto que a tarefa dela pede
var espera = new Dictionary<string, string> {
    ["inicio"] = "Próximo passo", ["raiox"] = "O que o acompanhamento viu", ["otimizar:servicos"] = "recomendado", ["aovivo"] = "Placa de vídeo",
    ["jogos"] = "Por jogo", ["sugestoes"] = "Diagnóstico", ["historico"] = "Fora do normal", ["desfazer"] = "Aplicado neste PC",
    ["config"] = "Memória do PC", ["aviso"] = "Li o aviso" };
int falhas = 0;
foreach (var tela in espera.Keys)
{
    j.Mostra(tela);
    for (int i = 0; i < 6; i++) { Dispatcher.UIThread.RunJobs(); AvaloniaHeadlessPlatform.ForceRenderTimerTick(); Thread.Sleep(30); }
    var textos = j.GetVisualDescendants().OfType<Avalonia.Controls.TextBlock>().Select(t => t.Text ?? string.Concat(t.Inlines?.OfType<Avalonia.Controls.Documents.Run>().Select(r => r.Text) ?? Array.Empty<string>())).ToList();
    if (textos.Any(t => t == "Não deu certo")) { Console.Error.WriteLine($"{tela}: abriu a tela de erro"); falhas++; }
    else if (!textos.Any(t => t.Contains(espera[tela]))) { Console.Error.WriteLine($"{tela}: não mostrou \"{espera[tela]}\""); falhas++; }
    using var foto = j.CaptureRenderedFrame();
    var arq = Path.Combine(pasta, tela.Split(':')[0] + ".png");
    foto!.Save(arq);
    Console.WriteLine(arq);
}
// a caixa de novidades (aberta pelas Configurações; ao abrir depois de atualizar é a mesma)
{
    j.Mostra("config");
    for (int i = 0; i < 6; i++) { Dispatcher.UIThread.RunJobs(); AvaloniaHeadlessPlatform.ForceRenderTimerTick(); Thread.Sleep(30); }
    _ = j.MostraNovidades(soSePrecisa: false);
    for (int i = 0; i < 6; i++) { Dispatcher.UIThread.RunJobs(); AvaloniaHeadlessPlatform.ForceRenderTimerTick(); Thread.Sleep(30); }
    var textos = j.GetVisualDescendants().OfType<Avalonia.Controls.TextBlock>().Select(t => t.Text ?? "").ToList();
    if (!textos.Contains("Novidades") || !textos.Any(t => t.StartsWith("4.0.2 ·"))) { Console.Error.WriteLine("novidades: a caixa não abriu"); falhas++; }
    using var foto = j.CaptureRenderedFrame();
    var arq = Path.Combine(pasta, "novidades.png");
    foto!.Save(arq);
    Console.WriteLine(arq);
    j.FechaCaixa();
}
if (falhas > 0) { Console.Error.WriteLine($"{falhas} tela(s) com problema"); Environment.Exit(1); }
