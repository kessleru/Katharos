using System.Text.Json.Nodes;
using Avalonia;
using Avalonia.Controls;
using Avalonia.Controls.Shapes;
using Path = Avalonia.Controls.Shapes.Path;
using Avalonia.Headless;
using Avalonia.Interactivity;
using Avalonia.Media;
using Avalonia.Threading;
using Avalonia.VisualTree;
using Katharos.App;

/// <summary>
/// Grava os vídeos do site com a interface de verdade, sem tela: um roteiro de cliques no tempo do vídeo (30 quadros por segundo),
/// cursor desenhado por cima, clique marcado com um anel âmbar e câmera que aproxima no que importa (a aproximação é feita na própria
/// interface, em vetor: nada fica borrado). Os quadros saem em PNG e o ffmpeg monta o vídeo.
/// </summary>
public class Filmagem
{
    const int Fps = 30;
    readonly Janela j;
    readonly string pasta;
    readonly Canvas camada = new() { IsHitTestVisible = false };
    readonly Path cursor;
    readonly Ellipse anel = new() { Width = 34, Height = 34, Stroke = Tema.Ambar, StrokeThickness = 2, Opacity = 0 };
    readonly ScaleTransform zoom = new(1, 1);
    readonly TranslateTransform anda = new();
    Point pos;
    double escala = 1; Point foco;
    int n;

    public Filmagem(Janela janela, string pastaQuadros)
    {
        j = janela; pasta = pastaQuadros;
        Directory.CreateDirectory(pasta);
        foreach (var f in Directory.GetFiles(pasta, "*.png")) File.Delete(f);
        cursor = new Path
        {
            Data = Geometry.Parse("M0,0 L0,17 L4.5,13 L7.6,20 L10.4,18.8 L7.4,12 L13,12 Z"), Fill = Tema.Osso, Stroke = Tema.Fundo, StrokeThickness = 1.2,
            RenderTransform = new ScaleTransform(1.25, 1.25), RenderTransformOrigin = new RelativePoint(0, 0, RelativeUnit.Relative),
        };
        camada.Children.Add(anel);
        camada.Children.Add(cursor);
        j.Raiz.Children.Add(camada);
        j.Raiz.RenderTransform = new TransformGroup { Children = { zoom, anda } };
        j.Raiz.RenderTransformOrigin = new RelativePoint(0, 0, RelativeUnit.Absolute);
        pos = new Point(j.Width * .62, j.Height * .7);
        foco = new Point(j.Width / 2, j.Height / 2);
        Poe();
    }

    void Poe() { Canvas.SetLeft(cursor, pos.X); Canvas.SetTop(cursor, pos.Y); }

    static double Suave(double t) => t < .5 ? 4 * t * t * t : 1 - Math.Pow(-2 * t + 2, 3) / 2;

    void Camera()
    {
        // escala em torno do foco, sem mostrar fora da janela
        double w = j.Width, h = j.Height;
        double tx = Math.Clamp(w / 2 - foco.X * escala, w - w * escala, 0), ty = Math.Clamp(h / 2 - foco.Y * escala, h - h * escala, 0);
        zoom.ScaleX = zoom.ScaleY = escala; anda.X = tx; anda.Y = ty;
    }

    public void Quadro()
    {
        for (int i = 0; i < 2; i++) { Dispatcher.UIThread.RunJobs(); AvaloniaHeadlessPlatform.ForceRenderTimerTick(); }
        // o quadro é liberado na hora: deixado para o coletor de lixo, ele era solto numa linha paralela ao desenho e derrubava o processo
        using var f = j.CaptureRenderedFrame();
        f!.Save(System.IO.Path.Combine(pasta, $"q{n++:00000}.png"));
    }

    public void Espera(double s) { for (int i = 0, q = (int)(s * Fps); i < q; i++) Quadro(); }

    /// <summary>Anima ao mesmo tempo o cursor (até um ponto) e a câmera (escala e foco), com a mesma curva.</summary>
    public void Anima(double s, Point? ate = null, double? novaEscala = null, Point? novoFoco = null)
    {
        Point p0 = pos, f0 = foco; double e0 = escala;
        int q = Math.Max(1, (int)(s * Fps));
        for (int i = 1; i <= q; i++)
        {
            double t = Suave(i / (double)q);
            if (ate is Point a) { pos = new Point(p0.X + (a.X - p0.X) * t, p0.Y + (a.Y - p0.Y) * t); Poe(); }
            if (novaEscala is double e) escala = e0 + (e - e0) * t;
            if (novoFoco is Point fo) foco = new Point(f0.X + (fo.X - f0.X) * t, f0.Y + (fo.Y - f0.Y) * t);
            Camera();
            Quadro();
        }
    }

    public Point Centro(Control c)
    {
        Quadro();
        var p = c.TranslatePoint(new Point(c.Bounds.Width / 2, c.Bounds.Height / 2), j.Raiz) ?? default;
        // TranslatePoint já considera a câmera; o cursor vive dentro da raiz (antes da câmera): desfaz a câmera
        return new Point((p.X - anda.X) / escala, (p.Y - anda.Y) / escala);
    }

    /// <summary>Leva o cursor até o controle e clica: o anel abre e some, e o clique acontece de verdade.</summary>
    public void Clica(Control alvo, double ida = .7)
    {
        var c = Centro(alvo);
        Anima(ida, new Point(c.X - 4, c.Y - 3));
        Canvas.SetLeft(anel, pos.X - 17); Canvas.SetTop(anel, pos.Y - 17);
        for (int i = 0; i < 9; i++) { anel.Opacity = 1 - i / 9.0; anel.RenderTransform = new ScaleTransform(.5 + i / 9.0, .5 + i / 9.0); Quadro(); if (i == 2) Aperta(alvo); }
        anel.Opacity = 0;
    }

    static void Aperta(Control alvo)
    {
        if (alvo is CheckBox cb) cb.IsChecked = !(cb.IsChecked == true);
        else if (alvo is Button b) b.RaiseEvent(new RoutedEventArgs(Button.ClickEvent));
    }

    /// <summary>O botão (ou caixa de marcar) cujo texto é exatamente este, o primeiro visível de cima para baixo.</summary>
    public Control Acha(string texto, int qual = 0)
    {
        Quadro();
        var achados = j.GetVisualDescendants().OfType<Control>()
            .Where(c => (c is Button || c is CheckBox) && c.IsEffectivelyVisible && Texto(c).Any(t => t == texto))
            .ToList();
        if (achados.Count <= qual) throw new InvalidOperationException($"não achei \"{texto}\" na tela");
        return achados[qual];
    }

    /// <summary>O botão cujo texto começa assim (o último visível: o da caixa por cima, quando há).</summary>
    public Control AchaComeco(string prefixo)
    {
        Quadro();
        return j.GetVisualDescendants().OfType<Button>().Where(c => c.IsEffectivelyVisible && Texto(c).Any(t => t.StartsWith(prefixo))).LastOrDefault()
               ?? throw new InvalidOperationException($"não achei \"{prefixo}…\" na tela");
    }

    static IEnumerable<string> Texto(Control c) =>
        (c as ContentControl)?.Content is string s ? new[] { s } : c.GetVisualDescendants().OfType<TextBlock>().Select(t => t.Text ?? "");

    public void Rola(ScrollViewer sv, double ate, double s)
    {
        double y0 = sv.Offset.Y;
        int q = (int)(s * Fps);
        for (int i = 1; i <= q; i++) { sv.Offset = new Vector(0, y0 + (ate - y0) * Suave(i / (double)q)); Quadro(); }
    }
}

/// <summary>Os roteiros: cada um vira um vídeo curto do site.</summary>
public static class Roteiros
{
    static TaskCompletionSource<JsonNode?>? fim;
    static bool SemMotor;
    static Action<string, JsonNode?>? eventos;

    /// <summary>No lugar do motor: "aplicar" e "raiox" esperam o roteiro mandar o progresso e o fim; o resto vem dos dados de exemplo.</summary>
    public static void LigaSimulador()
    {
        Servico.Simulador = async (m, p, ev) =>
        {
            if (m is "aplicar" or "raiox" or "desfazer") { eventos = ev; fim = new TaskCompletionSource<JsonNode?>(); return await fim.Task; }
            if (m == "inicio" && SemMotor)
            {   // o tour mostra o caminho do raio-x; a frase do motor tem o vídeo dela (central)
                var d = DadosDeExemplo.Para("inicio")!.DeepClone();
                d.AsObject().Remove("motor");
                return d;
            }
            if (m == "itens")
            {   // o modo muda o que vem marcado, como no motor (nível 1 a 3; 0 = só se a pessoa marcar)
                string modo = JsonNode.Parse(System.Text.Json.JsonSerializer.Serialize(p))?["modo"]?.ToString() ?? "equilibrado";
                int nv = modo == "seguro" ? 1 : modo == "extremo" ? 3 : 2;
                var d = DadosDeExemplo.Para("itens")!.DeepClone();
                foreach (var a in d["areas"]!.AsArray())
                    foreach (var i in a!["itens"]!.AsArray())
                    { int n = i!["nivel"]!.GetValue<int>(); i["marcado"] = n >= 1 && n <= nv; }
                return d;
            }
            return DadosDeExemplo.Para(m);
        };
    }

    static void Evento(string tipo, string json) => eventos?.Invoke(tipo, JsonNode.Parse(json));
    static void Termina(string json) => fim?.TrySetResult(JsonNode.Parse(json));

    public static readonly Dictionary<string, Action<Janela, Filmagem>> Todos = new()
    {
        // o caminho inteiro: do Início ao resultado, passando pelo raio-x e por um item desmarcado
        ["tour"] = (j, f) =>
        {
            SemMotor = true;
            j.Mostra("inicio"); f.Espera(1.2);
            f.Clica(f.Acha("Ver o que fazer")); f.Espera(.9);
            f.Anima(.9, null, 1.35, new Point(760, 430)); f.Espera(.8);
            f.Clica(f.Acha("Resolver", 1)); f.Anima(.6, null, 1, new Point(640, 410)); f.Espera(.6);
            f.Anima(.9, null, 1.3, new Point(700, 560)); f.Espera(.4);
            f.Clica(f.Acha("Tirar o Spotify da inicialização")); f.Espera(.7);
            f.Anima(.8, null, 1, new Point(640, 410)); f.Espera(.3);
            f.Clica(f.AchaComeco("Aplicar ")); f.Espera(.9);
            f.Clica(f.AchaComeco("Aplicar ")); f.Espera(.4);
            // o progresso e o resultado com os números exatos do que estava marcado (as mesmas áreas e contas da tela)
            var areas = DadosDeExemplo.Para("itens")!["areas"]!.AsArray()
                .Select(a => (titulo: a!["titulo"]!.ToString(), nome: a["nome"]!.ToString(),
                              n: a["itens"]!.AsArray().Count(i => i!["nivel"]!.GetValue<int>() is >= 1 and <= 2 && i["ja"]?.ToString() != "true" && i["id"]!.ToString() != "spotify")))
                .Where(a => a.n > 0).ToList();
            Evento("etapa", """{"texto": "criando o ponto de restauração"}"""); f.Espera(.8);
            for (int k = 0; k < areas.Count; k++)
            {
                Evento("pacote", $$"""{"titulo": "{{areas[k].titulo}}", "n": {{k + 1}}, "de": {{areas.Count}}}""");
                Evento("progresso", $$"""{"n": {{areas[k].n}}, "de": {{areas[k].n}}, "item": ""}""");
                f.Espera(k < 3 ? .5 : .18);
            }
            Termina(new JsonObject
            {
                ["pacotes"] = new JsonArray(areas.Select(a => (JsonNode)new JsonObject { ["pacote"] = a.nome, ["titulo"] = a.titulo, ["itens"] = a.n, ["feitos"] = a.n,
                    ["avisos"] = new JsonArray(), ["erros"] = new JsonArray(), ["nao_ficou"] = new JsonArray(), ["liberado"] = 0 }).ToArray()),
                ["perguntar_manter"] = new JsonArray(),
            }.ToJsonString());
            f.Espera(.8); f.Anima(1, null, 1.2, new Point(640, 260)); f.Espera(1.6);
        },
        // escolher: o modo muda o que vem marcado; cada item diz o que ganha e o que perde, e dá para tirar
        ["otimizar"] = (j, f) =>
        {
            j.Mostra("otimizar"); f.Espera(.8);
            f.Clica(f.Acha("Extremo")); f.Espera(.9);
            f.Clica(f.Acha("Equilibrado")); f.Espera(.6);
            f.Clica(f.Acha("Serviços")); f.Espera(.4);
            f.Anima(1, null, 1.35, new Point(660, 600)); f.Espera(.5);
            f.Clica(f.Acha("Impressão")); f.Espera(.9);
            f.Anima(1, null, 1, new Point(640, 410)); f.Espera(1.4);
        },
        // o raio-x rodando: as etapas e a nota
        ["raiox"] = (j, f) =>
        {
            j.Mostra("raiox"); f.Espera(.8);
            f.Clica(f.Acha("Fazer de novo")); f.Espera(.3);
            Evento("etapa", """{"texto": "lendo o PC", "n": 1, "de": 3}"""); f.Espera(1.1);
            Evento("etapa", """{"texto": "analisando", "n": 2, "de": 3}"""); f.Espera(1.1);
            Termina(DadosDeExemplo.Para("raiox_guardado")!.ToJsonString());
            f.Espera(.6); f.Anima(1.2, null, 1.25, new Point(560, 300)); f.Espera(1.4); f.Anima(1, null, 1, new Point(640, 410));
        },
        // ao vivo: números andando e o jogo aberto
        ["aovivo"] = (j, f) =>
        {
            var r = new Random(4); int t = 0;
            Servico.AgoraSimulado = () =>
            {
                var a = DadosDeExemplo.Para("agora")!;
                double o = Math.Sin(t++ / 3.0);
                a["gpu"] = Math.Round(95 + 2 * o + r.NextDouble() * 2); a["cpu"] = Math.Round(36 + 6 * o + r.NextDouble() * 5);
                a["temp_cpu"] = Math.Round(71 + o + r.NextDouble()); a["jogo"]!["fps_med"] = Math.Round(117 + 2 * o);
                return a;
            };
            j.Mostra("aovivo");
            for (int i = 0; i < 70; i++) f.Quadro();   // os gráficos enchem antes de começar
            var tela = j.Raiz.GetVisualDescendants().OfType<Katharos.App.Telas.AoVivo>().First();
            for (int s = 0; s < 7; s++)
            {
                typeof(Katharos.App.Telas.AoVivo).GetMethod("Atualiza", System.Reflection.BindingFlags.NonPublic | System.Reflection.BindingFlags.Instance)!.Invoke(tela, null);
                if (s == 2) f.Anima(1, null, 1.3, new Point(760, 220)); else if (s == 5) f.Anima(1, null, 1, new Point(640, 410)); else f.Espera(1);
            }
            Servico.AgoraSimulado = null;
        },
        // a central: a frase do motor no Início, o porquê (o que viu, por que acha isso, o que faria) e a proposta com como desfazer
        ["central"] = (j, f) =>
        {
            SemMotor = false;
            j.Mostra("inicio"); f.Espera(1);
            f.Anima(.9, null, 1.3, new Point(560, 215)); f.Espera(1.4);
            f.Anima(.6, null, 1, new Point(640, 410));
            f.Clica(f.Acha("Por que isso?")); f.Espera(.9);
            f.Anima(1, null, 1.3, new Point(700, 330)); f.Espera(2.2);
            f.Anima(.8, null, 1, new Point(640, 410)); f.Espera(.4);
            f.Rola(j.Raiz.GetVisualDescendants().OfType<ScrollViewer>().First(sv => sv.Extent.Height > sv.Viewport.Height + 10), 420, .9); f.Espera(1.6);
            f.Anima(.8, null, 1.25, new Point(760, 520)); f.Espera(1.4);
            f.Anima(.6, null, 1, new Point(640, 410)); f.Espera(.4);
        },
        // desfazer: a volta a um clique, com confirmação
        ["desfazer"] = (j, f) =>
        {
            j.Mostra("desfazer"); f.Espera(.8);
            f.Clica(f.Acha("Desfazer")); f.Espera(.8);
            f.Clica(f.Acha("Desfazer", 1)); f.Espera(.5);
            Termina("""{"pacotes": [{"pacote": "privacidade", "titulo": "privacidade", "ok": true, "nada": false}]}""");
            f.Espera(2);
        },
    };
}
