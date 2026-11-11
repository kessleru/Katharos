using System.Diagnostics;
using System.Text.Json.Nodes;
using Avalonia;
using Avalonia.Animation;
using Avalonia.Controls;
using Avalonia.Controls.Shapes;
using Avalonia.Media;
using Avalonia.Media.Imaging;
using Avalonia.Media.Transformation;
using Avalonia.Platform;
using Avalonia.Threading;

namespace Katharos.App;

/// <summary>
/// A tela de abertura (desenho no Figma: "Katharos · tela de abertura", quadros Abrindo, Lendo e Pronto): uma mini janela de 528×330
/// com o cavaleiro da hero do site (a mesma gravura, só recortada), as linhas horizontais com as marcas "+", a etapa real e a linha âmbar.
/// Ela faz o trabalho de verdade: abre o motor, carrega o que está guardado de todas as telas e confere, antes de mostrar, as áreas que o
/// Início vai citar (assim o Início nunca sugere algo que o Otimizar diria que já está feito). A linha só anda quando uma etapa termina:
/// nada de progresso inventado. Movimento só de opacidade e largura, curto, sem loop; com "reduzir animações", aparece parada.
/// </summary>
public class Abertura : Window
{
    readonly TextBlock etapa, passo;
    readonly Border progresso, linhaCima, linhaBaixo;
    readonly Image cavaleiro;
    readonly Control[] cruzes;
    const int Passos = 3;

    public Abertura()
    {
        Width = 528; Height = 330; CanResize = false; SystemDecorations = SystemDecorations.None;
        WindowStartupLocation = WindowStartupLocation.CenterScreen; ShowInTaskbar = true; Title = "Katharos";
        Background = Tema.Fundo;
        try { Icon = new WindowIcon(AssetLoader.Open(new Uri("avares://Katharos/Assets/katharos.ico"))); } catch { }
        var c = new Canvas { Width = 528, Height = 330, ClipToBounds = true };
        // a gravura da hero, 2× do tamanho exato (webp de ~100 KB, carregada uma vez)
        cavaleiro = new Image { Width = 528, Height = 330, Stretch = Stretch.UniformToFill, Opacity = 1 };
        try { cavaleiro.Source = new Bitmap(AssetLoader.Open(new Uri("avares://Katharos/Assets/abertura.webp"))); } catch (Exception e) { Registro.Escreve("abertura: imagem: " + e.Message); }
        c.Children.Add(cavaleiro);
        // sombras para o texto ler bem: da esquerda para o meio, e de baixo
        c.Children.Add(new Rectangle { Width = 528, Height = 330, Fill = Degrade(true) });
        c.Children.Add(new Rectangle { Width = 528, Height = 110, Fill = Degrade(false) }.Com(r => Canvas.SetTop(r, 220)));
        linhaCima = Linha(64); linhaBaixo = Linha(266);
        c.Children.Add(linhaCima); c.Children.Add(linhaBaixo);
        cruzes = new[] { Cruz(28, 60), Cruz(232, 60), Cruz(28, 262), Cruz(232, 262) };
        foreach (var x in cruzes) c.Children.Add(x);
        c.Children.Add(Pos(new TextBlock { Text = "Katharos", FontFamily = Tema.Mono, FontWeight = FontWeight.ExtraBold, FontSize = 30, Foreground = Tema.Osso }, 32, 92));
        string versao = typeof(Abertura).Assembly.GetName().Version is { } v ? $"{v.Major}.{v.Minor}.{v.Build}" : "";
        c.Children.Add(Pos(new TextBlock { Text = "otimizador do Windows\nversão " + versao, FontFamily = Tema.Mono, FontSize = 12.5, LineHeight = 18, Foreground = Tema.Apagado }, 33, 132));
        etapa = new TextBlock { Text = "Abrindo", FontFamily = Tema.Sans, FontSize = 14, Foreground = Tema.Osso };
        passo = new TextBlock { Text = $"1 de {Passos}", FontFamily = Tema.Mono, FontSize = 12.5, Foreground = Tema.Apagado, Width = 60, TextAlignment = TextAlignment.Right };
        c.Children.Add(Pos(etapa, 32, 284));
        c.Children.Add(Pos(passo, 436, 286));
        c.Children.Add(Pos(new Border { Width = 464, Height = 1, Background = Tema.Linha }, 32, 312));
        progresso = new Border { Width = 464, Height = 2, Background = Tema.Ambar, RenderTransformOrigin = new RelativePoint(0, 0.5, RelativeUnit.Relative),
                                 RenderTransform = TransformOperations.Parse("scaleX(0.02)") };
        c.Children.Add(Pos(progresso, 32, 311.5));
        Content = new Border { BorderBrush = Tema.LinhaForte, BorderThickness = new Thickness(1), Child = c };
        Opened += (_, _) => Entra();
    }

    static IBrush Degrade(bool lado) => new LinearGradientBrush
    {
        StartPoint = new RelativePoint(lado ? 0 : 0, lado ? 0 : 0, RelativeUnit.Relative), EndPoint = new RelativePoint(lado ? 0.62 : 0, lado ? 0 : 1, RelativeUnit.Relative),
        GradientStops = lado
            ? new GradientStops { new GradientStop(Color.FromArgb(235, 12, 12, 13), 0), new GradientStop(Color.FromArgb(150, 12, 12, 13), 0.55), new GradientStop(Color.FromArgb(0, 12, 12, 13), 1) }
            : new GradientStops { new GradientStop(Color.FromArgb(0, 12, 12, 13), 0), new GradientStop(Color.FromArgb(230, 12, 12, 13), 1) },
    };

    static Border Linha(double y) => new Border { Width = 236, Height = 1, Background = Tema.LinhaForte, RenderTransformOrigin = new RelativePoint(0.5, 0.5, RelativeUnit.Relative) }.Com(b => { Canvas.SetTop(b, y); });

    static Control Cruz(double x, double y)
    {
        var p = new Canvas { Width = 9, Height = 9 };
        p.Children.Add(new Rectangle { Width = 9, Height = 1, Fill = Tema.Texto }.Com(r => Canvas.SetTop(r, 4)));
        p.Children.Add(new Rectangle { Width = 1, Height = 9, Fill = Tema.Texto }.Com(r => Canvas.SetLeft(r, 4)));
        Canvas.SetLeft(p, x); Canvas.SetTop(p, y);
        return p;
    }

    static T Pos<T>(T c, double x, double y) where T : Control { Canvas.SetLeft(c, x); Canvas.SetTop(c, y); return c; }

    static Transitions Trans(AvaloniaProperty p, int ms) => new() { p == Visual.OpacityProperty
        ? new DoubleTransition { Property = p, Duration = TimeSpan.FromMilliseconds(ms), Easing = new Avalonia.Animation.Easings.CubicEaseOut() }
        : new TransformOperationsTransition { Property = p, Duration = TimeSpan.FromMilliseconds(ms), Easing = new Avalonia.Animation.Easings.CubicEaseOut() } };

    /// <summary>A entrada: a janela por opacidade (200 ms), as linhas do centro para fora e os "+" acendendo (300 ms), o cavaleiro de 35 % a 100 % (600 ms).</summary>
    void Entra()
    {
        if (Movimento.Reduzido) return;
        Opacity = 0; cavaleiro.Opacity = 0.35;
        foreach (var l in new[] { linhaCima, linhaBaixo }) l.RenderTransform = TransformOperations.Parse("scaleX(0)");
        foreach (var x in cruzes) x.Opacity = 0;
        Transitions = Trans(OpacityProperty, 200);
        cavaleiro.Transitions = Trans(OpacityProperty, 600);
        foreach (var l in new[] { linhaCima, linhaBaixo }) l.Transitions = Trans(RenderTransformProperty, 300);
        foreach (var x in cruzes) x.Transitions = Trans(OpacityProperty, 300);
        Dispatcher.UIThread.Post(() =>
        {
            Opacity = 1; cavaleiro.Opacity = 1;
            foreach (var l in new[] { linhaCima, linhaBaixo }) l.RenderTransform = TransformOperations.Parse("none");
            DispatcherTimer.RunOnce(() => { foreach (var x in cruzes) x.Opacity = 1; }, TimeSpan.FromMilliseconds(180));
        }, DispatcherPriority.Render);
        progresso.Transitions = Trans(RenderTransformProperty, 200);
    }

    public void Etapa(int n, string texto)
    {
        etapa.Text = texto; passo.Text = $"{Math.Min(n, Passos)} de {Passos}";
        // a linha avança só quando uma etapa real termina (n - 1 etapas feitas)
        double f = Math.Max(0.02, (n - 1) / (double)Passos);
        progresso.RenderTransform = TransformOperations.Parse($"scaleX({f.ToString(System.Globalization.CultureInfo.InvariantCulture)})");
    }

    /// <summary>Prepara tudo e devolve quando o Início pode abrir pronto. Erro no meio não segura a abertura: a janela abre e cada tela trata o seu.</summary>
    public async Task Prepara()
    {
        var relogio = Stopwatch.StartNew();
        try
        {
            Etapa(1, "Abrindo o motor");
            var cfg = await Servico.Le("config_ler");
            Movimento.Ligado = cfg?["animacoes"].S("valor", "ligadas") != "desligadas";
            string modo = cfg?["modo"].S("valor", "equilibrado") ?? "equilibrado";

            Etapa(2, "Lendo o que já sei deste PC");
            // o guardado do disco vai para a memória (cada tela abre na hora); o Início vem fresco do motor (é rápido: nada roda)
            foreach (var (m, p) in new (string, object?)[] { ("raiox_guardado", null), ("aplicado", null), ("historico", new { dias = 60 }), ("sugestoes", null), ("itens", new { modo, conferir = false }) })
                Servico.Guardado(m, p);
            var ini = await Servico.Le("inicio");

            // as áreas que o Início vai citar, se a leitura delas tem mais de 6 h: confere agora (com limite de tempo), para o Início não
            // mostrar uma sugestão que o Otimizar diria que já está feita
            var citadas = ini?["raiox"].A("achados").Select(a => Rotas.Cabeca(a.S("comando"))).Append(Rotas.Cabeca(ini?["motor"]?["acao"].S("comando") ?? ""))
                              .Where(Rotas.Areas.Contains).Distinct().ToList() ?? new();
            if (citadas.Count > 0)
            {
                var d = await Servico.Le("itens", new { modo, conferir = false, areas = citadas });
                var velhas = d.A("areas").Where(a => (a.D("faltam") ?? 0) > 0 || a.A("itens").Any(i => i.D("ja_idade_h") is double h && h > 6)).Select(a => a.S("nome")).ToList();
                if (velhas.Count > 0)
                {
                    Etapa(3, "Conferindo o que mudou no PC");
                    var conf = Task.Run(async () => { foreach (var a in velhas) await Servico.Le("itens", new { modo = "seguro", conferir = true, areas = new[] { a } }); });
                    // até 8 s: num PC muito lento, a janela abre e a conferência continua por trás (o Início troca só a linha que mudou)
                    if (await Task.WhenAny(conf, Task.Delay(8000)) == conf) await Servico.Le("inicio");
                    else Conferencia.Pede(velhas, frente: true);
                }
            }
            Etapa(Passos + 1, "Pronto");
            etapa.Text = "Pronto"; passo.Text = $"{Passos} de {Passos}";
        }
        catch (Exception e) { Registro.Escreve("abertura: " + e.Message); }
        Registro.Escreve($"abertura: {relogio.ElapsedMilliseconds} ms");
        await Task.Delay(Movimento.Reduzido ? 0 : 120);   // o "Pronto" aparece um instante, sem enfeite
    }

    /// <summary>Some em 150 ms.</summary>
    public async Task Sai()
    {
        if (!Movimento.Reduzido) { Transitions = Trans(OpacityProperty, 150); Opacity = 0; await Task.Delay(160); }
        Close();
    }
}
