using System.Text.Json.Nodes;
using Avalonia;
using Avalonia.Controls;
using Avalonia.Controls.Primitives;
using Avalonia.Layout;
using Avalonia.Media;
using Avalonia.Threading;
using Katharos.App.Controles;
using static Katharos.App.Ui;

namespace Katharos.App.Telas;

/// <summary>
/// Ao vivo: o que o segundo plano lê agora (agora.json, a cada segundo, sem custo), com o FPS do jogo aberto e o que limita, em
/// uma frase. Os gráficos guardam os últimos 2 minutos enquanto a tela está aberta.
/// </summary>
public class AoVivo : Tela
{
    record Cel(string Rotulo, Func<JsonNode, double?> Valor, string Unidade, int Casas, Func<JsonNode, (string, IBrush)> Contexto, double Max, double Limite, string Base = "")
    {
        public List<double> Hist = new();
        public TextBlock? Numero, Texto; public Grafico? G;
    }

    readonly DispatcherTimer relogio = new() { Interval = TimeSpan.FromSeconds(1) };
    readonly List<Cel> cels;
    StackPanel? jogo, conclusoes;
    TextBlock? ritmo;
    bool montado;

    public AoVivo()
    {
        cels = new()
        {
            new("Placa de vídeo", a => a.D("gpu"), "%", 0, a => a.D("gpu") >= 95 ? ("no limite: é ela que segura o FPS", Tema.Ambar) : ("sobra", Tema.Verde), 100, 95),
            new("CPU", a => a.D("cpu"), "%", 0, a => ($"núcleo mais usado em {Num(a.D("nucleo_max"))} %", a.D("nucleo_max") >= 95 ? Tema.Ambar : Tema.Verde), 100, double.NaN, "cpu"),
            new("Memória RAM", a => a.D("ram_pct"), "%", 0, a => ($"{Num(a.D("ram_gb"), 1)} de {Num(a.D("ram_total_gb"))} GB", a.D("ram_pct") >= 90 ? Tema.Vermelho : Tema.Verde), 100, 90, "ram"),
            new("Temperatura", a => a.D("temp_cpu") ?? a.D("temp_gpu"), "°C", 0, a => a.D("temp_cpu") == null && a.D("temp_gpu") == null
                ? ("sem leitura: abra o MSI Afterburner ou o HWiNFO", Tema.Apagado)
                : ($"CPU {Num(a.D("temp_cpu"))} · placa de vídeo {Num(a.D("temp_gpu"))}", (a.D("temp_cpu") ?? 0) >= 90 || (a.D("temp_gpu") ?? 0) >= 85 ? Tema.Vermelho : Tema.Verde), 100, 90, "temp_cpu"),
            new("Memória da placa", a => a.D("vram_gb"), "GB", 1, a => a.D("vram_total_gb") is double t ? ($"de {Num(t)} GB" + (a.D("vram_gb") / t >= .95 ? ": quase cheia" : ""), a.D("vram_gb") / t >= .95 ? Tema.Ambar : Tema.Verde) : ("", Tema.Apagado), 16, double.NaN),
            new("Disco", a => a.D("disco"), "%", 0, a => ($"lendo {Num(a.D("disco_le_mbs"), 1)} MB/s", a.D("disco") >= 95 ? Tema.Ambar : Tema.Verde), 100, 95, "disco"),
        };
        relogio.Tick += (_, _) => Atualiza();
        DetachedFromVisualTree += (_, _) => relogio.Stop();
    }

    JsonNode? normal;

    protected override async Task Carrega()
    {
        montado = false;
        Atualiza();
        relogio.Start();
        // o normal deste PC (linha de base do motor): a faixa clara atrás de cada gráfico
        try { normal = (await Servico.Le("linha_de_base"))?["metricas"]; } catch (Exception e) { Registro.Escreve("linha de base: " + e.Message); }
    }

    void Faixa(Cel c, bool emJogo)
    {
        if (c.G == null) return;
        var b = c.Base == "" ? null : normal?[c.Base]?[emJogo ? "jogo" : "sem_jogo"];
        c.G.FaixaMin = b.D("p10") ?? double.NaN;
        c.G.FaixaMax = b.D("p90") ?? double.NaN;
        ToolTip.SetTip(c.G, b == null ? null : $"O normal deste PC {(emJogo ? "em jogo" : "fora de jogo")}: entre {Num(b.D("p10"))} e {Num(b.D("p90"))} {c.Unidade} ({Num(b.D("dias"))} dias medidos).");
    }

    void Atualiza()
    {
        var a = Servico.Agora();
        if (a == null)
        {
            montado = false;
            Monta(Cabecalho("Ao vivo", "O que o PC está fazendo agora e o que segura o jogo."),
                  Vazio("O acompanhamento está desligado", "Ligado, ele lê o PC a cada segundo, em prioridade baixa (usa uns 50 MB de RAM e menos de 1 % da CPU), grava as sessões de jogo com o FPS e avisa quando algo fica no limite. Não abre nem lê o processo do jogo.",
                        Botao("Ligar o acompanhamento", true, async () => await Liga())));
            return;
        }
        if (!montado) MontaTela();
        ritmo!.Text = $"lendo a cada {Num(a.D("intervalo_s"))} s · o Katharos usa {Num(a["segundo_plano"].D("cpu_pct"), 1)} % da CPU";
        foreach (var c in cels)
        {
            var v = c.Valor(a);
            c.Numero!.Text = v.HasValue ? Num(v, c.Casas) : "-";
            var (txt, cor) = c.Contexto(a);
            c.Texto!.Text = txt; c.Texto.Foreground = cor;
            if (v.HasValue) { c.Hist.Add(v.Value); if (c.Hist.Count > 120) c.Hist.RemoveAt(0); }
            c.G!.Valores = c.Hist.ToArray();
        }
        var j = a["jogo"];
        jogo!.Children.Clear();
        jogo.IsVisible = j != null;
        if (j != null)
        {
            string limite = j.S("principal") switch { "gpu" => "O limite é a placa de vídeo: ela está no máximo e a CPU sobra.", "cpu" => "O limite é a CPU: a placa de vídeo espera por ela.", "calor" => "O PC está esquentando e freando.", _ => "Nada está no limite agora." };
            var g = new Grid { ColumnDefinitions = new ColumnDefinitions("*,Auto,Auto,Auto"), Margin = new Thickness(32, 24) };
            g.Children.Add(new StackPanel { Spacing = 4, VerticalAlignment = VerticalAlignment.Center, Children = { T($"Jogando agora · há {Num(j.D("min"))} min", "rotulo"), T(j.S("nome"), "forte", tamanho: 21), T(limite, null, null, 14, true) } });
            int col = 1;
            foreach (var (rot, val, un) in new[] { ("FPS médio", j.D("fps_med") ?? j.D("fps"), ""), ("1% mais lento", j.D("fps_1low"), ""), ("travadas", j.D("travadas_por_min"), "por min") })
            {
                var n = new StackPanel { Orientation = Orientation.Horizontal, Children = { T(val.HasValue ? Num(val) : "-", "numero") } };
                if (un != "") n.Children.Add(T(un, "unidade"));
                var s = new StackPanel { Margin = new Thickness(28, 0, 0, 0), VerticalAlignment = VerticalAlignment.Center, Children = { T(rot, "rotulo"), n } };
                Grid.SetColumn(s, col++); g.Children.Add(s);
            }
            if (j.S("fps_estado") is string est && est != "" && est != "medindo" && !j.D("fps_med").HasValue)
                g.Children.Add(T(est == "sem permissão" ? "FPS: libere em Configurações > FPS nos jogos" : "FPS: " + est, "rotulo").Com(t => { Grid.SetColumn(t, 1); Grid.SetColumnSpan(t, 3); t.Margin = new Thickness(28, 0, 0, 0); t.VerticalAlignment = VerticalAlignment.Center; }));
            jogo.Children.Add(g);
        }
        foreach (var c in cels) Faixa(c, a["jogo"] != null);
        conclusoes!.Children.Clear();
        var cs = a.A("conclusoes").ToList();
        if (cs.Count > 0)
        {
            conclusoes.Children.Add(Subtitulo("O que fazer agora"));
            foreach (var c in cs)
            {
                int n = (int)(c.D("nivel") ?? 0);
                var l = Linha(c.S("titulo"), c.S("texto"), Etiqueta(n >= 2 ? "grave" : n == 1 ? "atenção" : "normal", n >= 2 ? Tema.Vermelho : n == 1 ? Tema.Ambar : Tema.Apagado));
                ToolTip.SetTip(l, "Por quê: " + c.S("texto") + " É a mesma regra do ícone do Katharos, lida agora.");
                conclusoes.Children.Add(l);
            }
        }
        conclusoes.IsVisible = cs.Count > 0;
    }

    void MontaTela()
    {
        montado = true;
        ritmo = T("", "rotulo").Com(t => t.HorizontalAlignment = HorizontalAlignment.Right);
        var luz = new StackPanel { Spacing = 2, Children = { new StackPanel { Orientation = Orientation.Horizontal, Spacing = 8, HorizontalAlignment = HorizontalAlignment.Right, Children = { new Avalonia.Controls.Shapes.Ellipse { Width = 8, Height = 8, Fill = Tema.Verde, VerticalAlignment = VerticalAlignment.Center }, T("ao vivo", null, Tema.Osso) } }, ritmo } };
        jogo = new StackPanel();
        var grade = new UniformGrid { Columns = 3 };
        foreach (var c in cels)
        {
            c.Numero = T("-", "numero"); c.Texto = T("", null, null, 13).Com(t => t.TextTrimming = TextTrimming.CharacterEllipsis);
            c.G = new Grafico { Height = 54, Margin = new Thickness(0, 10, 0, 0), Maximo = c.Max, Limite = c.Limite };
            grade.Children.Add(new Border { Padding = new Thickness(32, 22, 32, 20), BorderBrush = Tema.Linha, BorderThickness = new Thickness(0, 0, 1, 1),
                Child = new StackPanel { Spacing = 4, Children = { T(c.Rotulo, "rotulo"), new StackPanel { Orientation = Orientation.Horizontal, Children = { c.Numero, T(c.Unidade, "unidade") } }, c.Texto, c.G } } });
        }
        conclusoes = new StackPanel();
        Monta(Cabecalho("Ao vivo", "O que o PC está fazendo agora e o que segura o jogo.", luz), S(jogo), S(grade), S(conclusoes));
    }

    async Task Liga()
    {
        try
        {
            Monta(Cabecalho("Ao vivo", "O que o PC está fazendo agora e o que segura o jogo."), Carregando("Ligando o acompanhamento").secao);
            await Servico.Le("segundo_plano", new { ligar = true });
            for (int i = 0; i < 20 && Servico.Agora() == null; i++) await Task.Delay(500);
            if (Servico.Agora() == null) throw new ErroDoMotor("nao_ligou", "O acompanhamento não começou a ler. Veja ~/.katharos/segundo-plano.log.");
            Atualiza();
        }
        catch (Exception e) { Monta(Cabecalho("Ao vivo", "O que o PC está fazendo agora."), Erro(e, async () => await Liga())); }
    }
}
