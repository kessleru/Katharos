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
    bool montado, lendo;
    string assinaturaConclusoes = "";
    bool? faixaEmJogo;
    TextBlock? jogoTopo, jogoNome, jogoLimite, jogoFps;
    TextBlock[] jogoValores = Array.Empty<TextBlock>();
    // o que a tela mostra quando não há leitura: o aviso de desligado, o "ligando" ou o erro. O relógio de 1 s não pode refazer
    // nada disso (refazer o botão a cada segundo derruba o clique, e trocar o "ligando" pelo aviso faz a tela piscar)
    enum Estado { Leitura, Desligado, Ligando, Erro }
    Estado estado = Estado.Leitura;

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
        // o arquivo é lido fora da linha da tela (num disco lento ou com o antivírus olhando, a leitura não trava a janela), uma por vez
        relogio.Tick += async (_, _) =>
        {
            if (lendo) return;
            lendo = true;
            try { var a = await Task.Run(Servico.Agora); Atualiza(a); }
            finally { lendo = false; }
        };
        DetachedFromVisualTree += (_, _) => relogio.Stop();
    }

    JsonNode? normal;

    protected override async Task Carrega()
    {
        montado = false;
        estado = Estado.Leitura;
        Atualiza(Servico.Agora());
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

    void Atualiza(JsonNode? a)
    {
        if (estado is Estado.Ligando or Estado.Erro) return;
        if (a == null)
        {
            montado = false;
            if (estado == Estado.Desligado) return;
            estado = Estado.Desligado;
            Monta(Cabecalho("Ao vivo", null),
                  Vazio("O acompanhamento está desligado", "Ligado, ele lê o PC a cada segundo, em prioridade baixa (usa uns 50 MB de RAM e menos de 1 % da CPU), grava as sessões de jogo com o FPS e avisa quando algo fica no limite. Não abre nem lê o processo do jogo.",
                        Botao("Ligar o acompanhamento", true, async () => await Liga())));
            return;
        }
        estado = Estado.Leitura;
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
        jogo!.IsVisible = j != null;
        if (j != null)
        {   // os controles do jogo são os mesmos a cada segundo: só os textos mudam (refazer tudo a cada leitura pesava e piscava)
            jogoTopo!.Text = $"Jogando agora · há {Num(j.D("min"))} min";
            jogoNome!.Text = j.S("nome");
            jogoLimite!.Text = j.S("principal") switch { "gpu" => "O limite é a placa de vídeo: ela está no máximo e a CPU sobra.", "cpu" => "O limite é a CPU: a placa de vídeo espera por ela.", "calor" => "O PC está esquentando e freando.", _ => "Nada está no limite agora." };
            var vals = new[] { j.D("fps_med") ?? j.D("fps"), j.D("fps_1low"), j.D("travadas_por_min") };
            for (int k = 0; k < jogoValores.Length; k++) jogoValores[k].Text = vals[k].HasValue ? Num(vals[k]) : "-";
            string est = j.S("fps_estado");
            jogoFps!.IsVisible = est != "" && est != "medindo" && !j.D("fps_med").HasValue;
            jogoFps.Text = est == "sem permissão" ? "FPS: libere em Configurações > FPS nos jogos" : "FPS: " + est;
        }
        bool emJogo = a["jogo"] != null;
        if (faixaEmJogo != emJogo) { faixaEmJogo = emJogo; foreach (var c in cels) Faixa(c, emJogo); }
        var cs = a.A("conclusoes").ToList();
        string assinatura = string.Join("|", cs.Select(c => c.S("id") + c.D("nivel") + c.S("titulo") + c.S("texto")));
        if (assinatura == assinaturaConclusoes) return;   // as mesmas conclusões: nada a refazer
        assinaturaConclusoes = assinatura;
        conclusoes!.Children.Clear();
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
        jogoTopo = T("", "rotulo"); jogoNome = T("", "forte", tamanho: 21); jogoLimite = T("", null, null, 14, true);
        jogoFps = T("", "rotulo").Com(t => { Grid.SetColumn(t, 1); Grid.SetColumnSpan(t, 3); t.Margin = new Thickness(28, 0, 0, 0); t.VerticalAlignment = VerticalAlignment.Center; t.IsVisible = false; });
        var gj = new Grid { ColumnDefinitions = new ColumnDefinitions("*,Auto,Auto,Auto"), Margin = new Thickness(32, 24) };
        gj.Children.Add(new StackPanel { Spacing = 4, VerticalAlignment = VerticalAlignment.Center, Children = { jogoTopo, jogoNome, jogoLimite } });
        int col = 1;
        var valores = new List<TextBlock>();
        foreach (var (rot, un) in new[] { ("FPS médio", ""), ("1% mais lento", ""), ("travadas", "por min") })
        {
            var v = T("-", "numero"); valores.Add(v);
            var n = new StackPanel { Orientation = Orientation.Horizontal, Children = { v } };
            if (un != "") n.Children.Add(T(un, "unidade"));
            var s = new StackPanel { Margin = new Thickness(28, 0, 0, 0), VerticalAlignment = VerticalAlignment.Center, Children = { T(rot, "rotulo"), n } };
            Grid.SetColumn(s, col++); gj.Children.Add(s);
        }
        gj.Children.Add(jogoFps);
        jogoValores = valores.ToArray();
        jogo.Children.Add(gj);
        faixaEmJogo = null; assinaturaConclusoes = "\u0000";
        var grade = new UniformGrid { Columns = 3 };
        foreach (var c in cels)
        {
            c.Numero = T("-", "numero"); c.Texto = T("", null, null, 13).Com(t => t.TextTrimming = TextTrimming.CharacterEllipsis);
            var cc = c;
            c.G = new Grafico { Height = 54, Margin = new Thickness(0, 10, 0, 0), Maximo = c.Max, Limite = c.Limite, Formata = v => (Num(v) + " " + cc.Unidade).Trim() };
            // ampliar: a mesma série, grande, com eixos (é a foto deste instante; o Ao vivo continua andando atrás)
            c.G.PedeAmpliar += () => Amplia(cc);
            var topo = new Grid { ColumnDefinitions = new ColumnDefinitions("*,Auto"), Children = { T(c.Rotulo, "rotulo") } };
            if (c.Rotulo.Contains("RAM") || c.Rotulo.Contains("Memória"))
                topo.Children.Add(Link("Quem usa", () => Abre("memoria")).Com(b => { Grid.SetColumn(b, 1); b.Padding = new Thickness(4, 0); }));
            grade.Children.Add(new Border { Padding = new Thickness(32, 22, 32, 20), BorderBrush = Tema.Linha, BorderThickness = new Thickness(0, 0, 1, 1),
                Child = new StackPanel { Spacing = 4, Children = { topo, new StackPanel { Orientation = Orientation.Horizontal, Children = { c.Numero, T(c.Unidade, "unidade") } }, c.Texto, c.G } } });
        }
        conclusoes = new StackPanel();
        Monta(Cabecalho("Ao vivo", null, luz), S(jogo), S(grade), S(conclusoes));
    }

    void Amplia(Cel c)
    {
        var j = Janela.Atual!;
        var vals = c.G?.Valores?.ToArray() ?? Array.Empty<double>();
        int n = vals.Length;
        var g = new Grafico { Height = 380, Eixos = true, Valores = vals, Maximo = c.Max, Limite = c.Limite, Formata = v => (Num(v) + " " + c.Unidade).Trim(),
                              Rotulos = Enumerable.Range(0, n).Select(i => "há " + (n - 1 - i) + " s").ToArray() };
        var verTudo = Botao("Ver tudo", false, () => g.VerTudo()).Com(b => b.IsVisible = false);
        g.ZoomMudou += () => verTudo.IsVisible = g.ComZoom;
        j.MostraCaixa(Janela.Caixa(c.Rotulo + " agora", new StackPanel { Spacing = 10, Children = { verTudo, g,
            T("Roda: zoom · arrastar: trecho · Esc fecha", "rotulo", tamanho: 12.5) } },
            Botao("Fechar", true, j.FechaCaixa).Com(b => b.HorizontalAlignment = HorizontalAlignment.Right)), true);
    }

    async Task Liga()
    {
        if (estado == Estado.Ligando) return;   // dois cliques seguidos não abrem duas ligações
        estado = Estado.Ligando;
        bool comecou = false;
        try
        {
            var (sec, passo, _) = Carregando("Abrindo o acompanhamento (na primeira vez, o Windows e o antivírus podem levar alguns segundos)");
            Monta(Cabecalho("Ao vivo", null), sec);
            Trabalho.Comeca("Ligando o acompanhamento…"); comecou = true;
            await Servico.Le("segundo_plano", new { ligar = true });
            passo.Text = "Aberto. Esperando a primeira leitura do PC";
            // o segundo plano leva alguns segundos para gravar a primeira leitura (num PC mais lento, mais): espera até 20 s
            for (int i = 0; i < 40 && Servico.Agora() == null; i++) await Task.Delay(500);
            if (Servico.Agora() == null && SegundoPlano.Rodando())
            {   // abriu, mas a primeira leitura demora (PC lento, antivírus olhando): espera mais, dizendo isso
                passo.Text = "Está rodando. A primeira leitura demora mais neste PC: esperando mais um pouco";
                for (int i = 0; i < 80 && Servico.Agora() == null; i++) await Task.Delay(500);
                if (Servico.Agora() == null)
                {
                    Trabalho.Termina(); comecou = false;
                    estado = Estado.Desligado;   // o relógio troca para as leituras assim que a primeira chegar
                    Monta(Cabecalho("Ao vivo", null),
                          Vazio("O acompanhamento está rodando", "Ele abriu (o ícone fica perto do relógio), mas ainda não gravou a primeira leitura: neste PC isso está demorando. Esta tela muda sozinha quando ela chegar; não precisa clicar de novo."));
                    return;
                }
            }
            if (Servico.Agora() == null) throw new ErroDoMotor("nao_ligou", "O acompanhamento não começou a ler. Veja ~/.katharos/segundo-plano.log.");
            estado = Estado.Leitura;
            Trabalho.Termina(); comecou = false;
            Atualiza(Servico.Agora());
        }
        catch (Exception e)
        {
            Registro.Escreve("ligar o acompanhamento: " + e);
            if (comecou) Trabalho.Termina();
            estado = Estado.Erro;   // a mensagem fica na tela até a pessoa tentar de novo
            Monta(Cabecalho("Ao vivo", null), Erro(e, async () => { estado = Estado.Leitura; await Liga(); }));
        }
    }
}
