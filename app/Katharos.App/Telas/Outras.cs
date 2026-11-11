using System.Text.Json.Nodes;
using Avalonia;
using Avalonia.Controls;
using Avalonia.Layout;
using Avalonia.Media;
using static Katharos.App.Ui;

namespace Katharos.App.Telas;

/// <summary>Jogos: as sessões gravadas pelo segundo plano, o que segurou cada uma, e o antes e depois de cada mudança por jogo.</summary>
public class Jogos : Tela
{
    protected override async Task Carrega()
    {
        var cab = Cabecalho("Jogos", "Cada vez que você joga, o Katharos grava quanto tempo, o FPS e o que segurou o jogo.");
        Monta(cab, Carregando("Lendo as sessões").secao);
        var d = await Servico.Le("sessoes", new { dias = 60 });
        var ss = d.A("sessoes").Reverse().ToList();
        if (ss.Count == 0)
        {
            Monta(cab, Vazio("Nenhuma sessão de jogo ainda", "Com o acompanhamento ligado, a próxima vez que você jogar aparece aqui sozinha: o jogo, o FPS de verdade e o que limitou (placa de vídeo, CPU, memória ou calor).",
                             Botao("Ver o acompanhamento", false, () => Abre("aovivo"))));
            return;
        }
        var r = d?["resumo"];
        var numeros = S(Celulas(
            Numero("Jogado em 60 dias", Num(r.D("horas"), 1), "h", $"{Num(r.D("sessoes"))} sessões", Tema.Apagado),
            Numero("O que mais segura", Limite(r.S("principal")), "", "no tempo somado das sessões", Tema.Apagado),
            Numero("Mais quente", Num(r.D("temp_cpu_max")), "°C", "CPU, no pico das sessões", (r.D("temp_cpu_max") ?? 0) >= 90 ? Tema.Vermelho : Tema.Verde)));

        // antes e depois: só o que tem sessões dos dois lados (a central diz "sem diferença" quando a mudança cabe no ruído)
        Control? comp = null;
        var cs = d.A("comparacoes").ToList();
        if (cs.Count > 0)
        {
            var p = new StackPanel { Children = { Subtitulo("Antes e depois das mudanças", "Pelo menos 3 sessões de cada lado; diferença menor que a variação normal conta como sem diferença.") } };
            foreach (var c in cs.Take(8))
            {
                string v = c.S("veredito");
                var cor = v.Contains("melhor") ? Tema.Verde : v.Contains("pior") ? Tema.Vermelho : Tema.Apagado;
                p.Children.Add(Linha($"{c.S("jogo")} · {c.S("rotulo")}: {Num(c.D("antes"), 0)} → {Num(c.D("depois"), 0)}", $"depois de {c.S("nome_pacote")} ({Quando(c.S("quando"))})", Etiqueta(v == "" ? "?" : v, cor)));
            }
            comp = S(p);
        }

        // I20: por jogo: o que segura o FPS, a evolução de FPS e travadas e a recomendação para aquele uso
        Control? porJogo = null;
        var pj = d.A("por_jogo").ToList();
        if (pj.Count > 0)
        {
            var p = new StackPanel { Children = { Subtitulo("Por jogo", "Cada jogo que o Katharos viu, com o que segura o FPS nele.") } };
            foreach (var j in pj.Take(8))
            {
                var segura = j.A("segura").Select(x => $"{x.S("nome")} em {Num(x.D("pct"))} % do tempo").ToList();
                var ev = j.A("evolucao").Where(x => x.D("fps_1low") != null).ToList();
                string fps = ev.Count >= 2 ? $"1% mais lento: {Num(ev[0].D("fps_1low"))} → {Num(ev[^1].D("fps_1low"))} FPS em {ev.Count} sessões" : "";
                var rec = j["recomendacao"];
                var txt = new List<string> { segura.Count > 0 ? "Segura: " + string.Join("; ", segura) + "." : "Nada ficou no limite por tempo que importe." };
                if (fps != "") txt.Add(fps + ".");
                if (rec != null) txt.Add($"O que eu faria: {rec.S("faria")}.");
                var vals = ev.Select(x => x.D("fps_1low") ?? 0).ToArray();
                var bloco = new StackPanel { Spacing = 4, Children = { T($"{j.S("jogo")} · {Num(j.D("horas"), 1)} h em {Num(j.D("sessoes"))} sessões", null, Tema.Osso, 15).Com(t => t.FontWeight = FontWeight.SemiBold),
                                                                       T(string.Join(" ", txt), "rotulo", tamanho: 13.5, quebra: true) } };
                if (vals.Length >= 3)
                {
                    double piso = vals.Min() * 0.8;   // a variação entre sessões importa mais que a distância do zero
                    bloco.Children.Add(new Controles.Grafico { Height = 44, Margin = new Thickness(0, 6, 0, 0), Valores = vals.Select(v => v - piso).ToArray(), Maximo = Math.Max(1, (vals.Max() - piso) * 1.15) });
                }
                p.Children.Add(new Border { Padding = new Thickness(32, 16), BorderBrush = Tema.Linha, BorderThickness = new Thickness(0, 1, 0, 0), Child = bloco });
            }
            porJogo = S(p);
        }

        var lista = new StackPanel { Children = { Subtitulo("Sessões") } };
        foreach (var s in ss.Take(30))
        {
            string fps = s.D("fps_med") is double f ? $" · {Num(f)} FPS médio · 1% mais lento {Num(s.D("fps_1low"))}" : "";
            lista.Children.Add(Linha($"{s.S("jogo")} · {Num(s.D("min"))} min{fps}", $"{Quando(s.S("inicio"))} · limite: {Limite(s.S("principal"))}" +
                                     (s.D("temp_cpu_max") is double tc ? $" · CPU até {Num(tc)} °C" : "")));
        }
        Monta(cab, numeros, porJogo, comp, S(lista));
    }

    static string Limite(string p) => p switch
    {
        "gpu" => "placa de vídeo", "cpu" => "CPU", "freio" => "CPU freando", "ram" => "memória RAM", "vram" => "memória da placa", "disco" => "disco",
        "calor" => "calor", "" => "-", _ => "nada no limite",
    };
}

/// <summary>Desfazer: cada mudança aplicada, com quando e quantos itens, e a volta a um clique (com confirmação).</summary>
public class Desfazer : Tela
{
    protected override async Task Carrega()
    {
        var cab = Cabecalho("Desfazer", "Tudo o que o Katharos mudou guarda o valor de antes. Escolha o que voltar.");
        Monta(cab, Carregando("Lendo o que foi aplicado").secao);
        var d = await Servico.Le("aplicado");
        var ps = d.A("pacotes").ToList();
        if (ps.Count == 0) { Monta(cab, Vazio("Nada para desfazer", "Nenhuma mudança do Katharos está aplicada neste PC.")); return; }
        var lista = new StackPanel { Children = { Subtitulo("Aplicado neste PC", "Do mais novo para o mais antigo.") } };
        foreach (var p in ps)
        {
            string nome = p.S("pacote"), titulo = p.S("titulo");
            int n = p.A("itens").Count();
            var acao = p.B("desfaz") ? Botao("Desfazer", false, async () => await Volta(new[] { nome }, titulo)) : null;
            lista.Children.Add(Linha($"{Maiuscula(titulo)}: {n} {(n == 1 ? "item" : "itens")}", $"aplicado {Quando(p.S("quando"))}" + (p.B("desfaz") ? "" : " · remoções não voltam por aqui"), null, acao));
        }
        var tudo = Botao("Desfazer tudo", false, async () => await Volta(ps.Where(p => p.B("desfaz")).Select(p => p.S("pacote")).ToArray(), "tudo"));
        var ponto = d.S("ponto");
        var rodape = S(new Grid
        {
            ColumnDefinitions = new ColumnDefinitions("*,Auto"), Margin = new Thickness(32, 22),
            Children = { new StackPanel { Spacing = 3, Children = { T("Ponto de restauração", "rotulo"), T(ponto == "" ? "nenhum criado pelo Katharos ainda" : "o último foi criado " + Quando(ponto), null, Tema.Osso, 15) } }, tudo.Com(b => Grid.SetColumn(b, 1)) },
        });
        Monta(cab, S(lista), rodape);
    }

    async Task Volta(string[] pacotes, string titulo)
    {
        var j = Janela.Atual!;
        if (pacotes.Length == 0) return;
        if (!await j.Confirma(titulo == "tudo" ? "Desfazer tudo?" : $"Desfazer {titulo}?",
                T("Os ajustes voltam ao valor de antes. O Windows vai pedir permissão de administrador.", "sub"), "Desfazer")) return;
        j.MostraCaixa(Janela.Caixa("Desfazendo", T("Voltando os ajustes ao que eram antes.", "sub")));
        try
        {
            var r = await Servico.Muda("desfazer", new { pacotes });
            var falhas = r.A("pacotes").Where(x => !x.B("ok") && !x.B("nada")).Select(x => x.S("titulo")).ToList();
            j.MostraCaixa(Janela.Caixa(falhas.Count == 0 ? "Desfeito" : "Desfeito em parte",
                T(falhas.Count == 0 ? "Voltou ao que era antes." : "Não voltou: " + string.Join(", ", falhas) + ". O detalhe está no relatório do Katharos.", "sub"),
                Botao("Fechar", true, () => { j.FechaCaixa(); _ = Recarrega(); })), true);
        }
        catch (Exception e) { j.MostraCaixa(Janela.Caixa("Não deu para desfazer", T(e.Message, "sub"), Botao("Fechar", false, j.FechaCaixa)), true); }
    }
}

/// <summary>Configurações: as mesmas preferências da CLI, cada uma com o que faz e as opções em botões.</summary>
public class Configuracoes : Tela
{
    // as que importam para quem usa as janelas, na ordem de uso (as de aparência do terminal ficam na CLI)
    static readonly string[] Mostrar = { "modo", "confirmar", "tempo-real", "avisos", "coleta-em-jogo", "atualizacoes", "canal" };
    // o que o motor pode avisar e quando (I24)
    static readonly string[] Motor = { "avisos-intervalo", "avisos-no-jogo", "resumo-diario" };
    static readonly Dictionary<string, string[]> OpcoesCurtas = new() { ["avisos-intervalo"] = new[] { "2", "6", "12", "24" } };
    static readonly Dictionary<string, string> Rotulos = new() { ["so-grave"] = "só o grave", ["estavel"] = "estável", ["previa"] = "prévia", ["automatico"] = "automático", ["nao"] = "não" };

    protected override async Task Carrega()
    {
        var cab = Cabecalho("Configurações", "Valem para as janelas e para o terminal.");
        Monta(cab, Carregando("Lendo").secao);
        var d = await Servico.Le("config_ler");
        var lista = new StackPanel { Children = { Subtitulo("Preferências") } };
        foreach (var k in Mostrar) Preferencia(d, k, lista);
        var motor = new StackPanel { Children = { Subtitulo("O motor de inteligência", "O que ele pode avisar e com que frequência.") } };
        foreach (var k in Motor) Preferencia(d, k, motor);
        // o que ele nunca propõe: comandos separados por vírgula
        var nunca = new TextBox { Text = d?["motor-nunca"].S("valor") ?? "", Watermark = "ex.: turbo, energia", MinWidth = 220 };
        var salvar = Botao("Salvar", false, async () => { await Servico.Le("config_gravar", new { chave = "motor-nunca", valor = (nunca.Text ?? "").Trim() }); await Recarrega(); });
        motor.Children.Add(Linha("O que ele nunca propõe", "Os comandos que a central não deve sugerir neste PC.", null, new StackPanel { Orientation = Orientation.Horizontal, Spacing = 8, Children = { nunca, salvar } }));

        // a memória do PC: o que ele aprendeu, exportar e apagar (com exportação antes)
        var mem = await Servico.Le("memoria");
        var cont = mem?["contagens"];
        string resumo = mem.S("desde") == "" ? "Ainda vazia: começa a encher com o acompanhamento ligado."
            : $"Desde {Quando(mem.S("desde"))}: {Num(cont.D("minutos"))} minutos medidos, {Num(cont.D("sessoes"))} sessões de jogo, {Num(cont.D("resultados"))} resultados medidos ({Num((mem.D("bytes") ?? 0) / 1048576, 1)} MB).";
        var acoes = new StackPanel { Orientation = Orientation.Horizontal, Spacing = 8 };
        acoes.Children.Add(Botao("Exportar", false, async () => await Exporta()));
        acoes.Children.Add(Botao("Apagar", false, async () => await Apaga()));
        var memoria = S(new StackPanel { Children = { Subtitulo("Memória do PC", "Tudo o que o Katharos aprendeu deste PC fica neste computador, em ~/.katharos. Nada vai para a internet."),
                                                      Linha("O que ele guarda", resumo, null, acoes) } });
        Monta(cab, S(lista), S(motor), memoria);
    }

    void Preferencia(JsonNode? d, string k, StackPanel lista)
    {
        var c = d?[k];
        if (c == null) return;
        string atual = c.S("valor");
        var ops = new StackPanel { Orientation = Orientation.Horizontal, Spacing = 6 };
        var opcoes = OpcoesCurtas.TryGetValue(k, out var curtas) ? curtas : c.A("opcoes").Select(x => x.ToString()).ToArray();
        foreach (var o in opcoes)
        {
            string rot = Rotulos.TryGetValue(o, out var r) ? r : o;
            if (k == "avisos-intervalo") rot = o + " h";
            ops.Children.Add(Botao(rot, o == atual, async () => { await Servico.Le("config_gravar", new { chave = k, valor = o }); await Recarrega(); }));
        }
        lista.Children.Add(Linha(Maiuscula(c.S("rotulo")), c.S("explica"), null, ops));
    }

    async Task Exporta()
    {
        var j = Janela.Atual!;
        try { var r = await Servico.Le("memoria_exportar"); j.MostraCaixa(Janela.Caixa("Exportado", T("Salvo em " + r.S("arquivo"), "sub"), Botao("Fechar", true, j.FechaCaixa)), true); }
        catch (Exception e) { j.MostraCaixa(Janela.Caixa("Não deu para exportar", T(e.Message, "sub"), Botao("Fechar", false, j.FechaCaixa)), true); }
    }

    async Task Apaga()
    {
        var j = Janela.Atual!;
        if (!await j.Confirma("Apagar a memória do PC?", T("O motor esquece o que aprendeu deste PC (medidas, sessões, resultados e suas respostas). Antes, eu guardo uma exportação em ~/.katharos. Backups do desfazer e configurações não são tocados.", "sub"), "Apagar")) return;
        try
        {
            var r = await Servico.Le("memoria_apagar", new { confirmo = true });
            j.MostraCaixa(Janela.Caixa("Memória apagada", T(r.S("exportado") == "" ? "Não havia nada guardado." : "A exportação ficou em " + r.S("exportado"), "sub"), Botao("Fechar", true, () => { j.FechaCaixa(); _ = Recarrega(); })), true);
        }
        catch (Exception e) { j.MostraCaixa(Janela.Caixa("Não deu para apagar", T(e.Message, "sub"), Botao("Fechar", false, j.FechaCaixa)), true); }
    }
}

/// <summary>O aviso de uso (o mesmo da CLI), lido e aceito uma vez antes de mudar o PC.</summary>
public class Aviso : Tela
{
    readonly string volta;
    public Aviso(string voltaPara) { volta = voltaPara == "" ? "inicio" : voltaPara; }

    protected override async Task Carrega()
    {
        var cab = Cabecalho("Antes de usar", "Leia uma vez. Vale para as janelas e para o terminal.");
        var d = await Servico.Le("aviso");
        var lista = new StackPanel();
        foreach (var p in d.A("pontos")) lista.Children.Add(Linha(p.S("titulo"), p.S("texto")));
        var li = new CheckBox { Content = T("Li o aviso e quero continuar", null, Tema.Osso, 15) };
        var seguir = Botao("Continuar", true, async () => { await Servico.Le("aceitar_aviso", new { li = true }); Abre(volta); }, false);
        li.IsCheckedChanged += (_, _) => seguir.IsEnabled = li.IsChecked == true;
        var rodape = S(new Grid { ColumnDefinitions = new ColumnDefinitions("*,Auto"), Margin = new Thickness(32, 22), Children = { li, seguir.Com(b => Grid.SetColumn(b, 1)) } });
        Monta(cab, S(lista), rodape);
    }
}
