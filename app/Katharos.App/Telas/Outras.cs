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
        var cab = Cabecalho("Jogos", "FPS e o que segurou cada sessão.");
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
            var p = new StackPanel { Children = { Subtitulo("Antes e depois das mudanças", null, "grafico") } };
            foreach (var c in cs.Take(8))
            {
                string v = c.S("veredito");
                var cor = v.Contains("melhor") ? Tema.Verde : v.Contains("pior") ? Tema.Vermelho : Tema.Apagado;
                p.Children.Add(Linha($"{c.S("jogo")} · {c.S("rotulo")}: {Num(c.D("antes"), 0)} → {Num(c.D("depois"), 0)}", $"depois de {c.S("nome_pacote")} ({Quando(c.S("quando"))})", Etiqueta(v == "" ? "?" : v, cor)));
            }
            comp = G(p);
        }

        // I20: por jogo: o que segura o FPS, a evolução de FPS e travadas e a recomendação para aquele uso
        Control? porJogo = null;
        var pj = d.A("por_jogo").ToList();
        if (pj.Count > 0)
        {
            var p = new StackPanel { Children = { Subtitulo("Por jogo", null, "jogos") } };
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
            porJogo = G(p);
        }

        var lista = new StackPanel { Children = { Subtitulo("Sessões", null, "tempo") } };
        foreach (var s in ss.Take(30))
        {
            string fps = s.D("fps_med") is double f ? $" · {Num(f)} FPS médio · 1% mais lento {Num(s.D("fps_1low"))}" : "";
            lista.Children.Add(Linha($"{s.S("jogo")} · {Num(s.D("min"))} min{fps}", $"{Quando(s.S("inicio"))} · limite: {Limite(s.S("principal"))}" +
                                     (s.D("temp_cpu_max") is double tc ? $" · CPU até {Num(tc)} °C" : "")));
        }
        Monta(cab, numeros, porJogo, comp, G(lista));
    }

    static string Limite(string p) => p switch
    {
        "gpu" => "placa de vídeo", "cpu" => "CPU", "freio" => "CPU freando", "ram" => "memória RAM", "vram" => "memória da placa", "disco" => "disco",
        "calor" => "calor", "" => "-", _ => "nada no limite",
    };
}

/// <summary>
/// Desfazer: cada área aplicada abre a lista dos seus itens, com caixa de marcar: "Desfazer marcados" volta só esses (o resto continua
/// aplicado) e "Desfazer tudo" volta a área inteira. Mudanças gravadas antes da 4.2.1 não sabem de qual item vieram: essas só voltam com
/// a área inteira, e a tela diz isso.
/// </summary>
public class Desfazer : Tela
{
    readonly HashSet<string> abertas = new();

    protected override async Task Carrega()
    {
        var cab = Cabecalho("Desfazer", "Volte uma área inteira ou só alguns itens.");
        var g = Servico.Guardado("aplicado");
        if (g != null) Desenha(cab, g); else Monta(cab, Carregando("Lendo o que foi aplicado").secao);
        var d = await Servico.Le("aplicado");
        if (g == null || g.ToJsonString() != d?.ToJsonString()) Desenha(cab, d);
    }

    void Desenha(Control cab, JsonNode? d)
    {
        var ps = d.A("pacotes").ToList();
        if (ps.Count == 0) { Monta(cab, Vazio("Nada para desfazer", "Nenhuma mudança do Katharos está aplicada neste PC.")); return; }
        var lista = new StackPanel { Children = { Subtitulo("Aplicado neste PC", null, "desfazer") } };
        foreach (var p in ps) lista.Children.Add(Area(p));
        var tudo = Botao("Desfazer tudo", false, async () => await Volta(ps.Where(p => p.B("desfaz")).Select(p => p.S("pacote")).ToArray(), null, "tudo"));
        var ponto = d.S("ponto");
        var rodape = S(new Grid
        {
            ColumnDefinitions = new ColumnDefinitions("*,Auto"), Margin = new Thickness(32, 22),
            Children = { new StackPanel { Spacing = 3, Children = { T("Ponto de restauração", "rotulo"), T(ponto == "" ? "nenhum criado pelo Katharos ainda" : "o último foi criado " + Quando(ponto), null, Tema.Osso, 15) } }, tudo.Com(b => Grid.SetColumn(b, 1)) },
        });
        Monta(cab, S(lista), rodape);
    }

    Control Area(JsonNode p)
    {
        string nome = p.S("pacote"), titulo = p.S("titulo");
        var ids = p.A("itens").Select(x => x.ToString()).ToList();
        var porItem = p.A("por_item").Select(x => x.ToString()).ToHashSet();
        int soPacote = (int)(p.D("so_pacote") ?? 0);
        var titulos = p?["titulos"] as JsonObject;
        bool desfaz = p.B("desfaz");
        bool aberta = abertas.Contains(nome);
        var seta = T(aberta ? "−" : "+", null, Tema.Apagado).Com(t => t.FontFamily = Tema.Mono);
        var topo = new Grid { ColumnDefinitions = new ColumnDefinitions("24,*,Auto") };
        topo.Children.Add(seta);
        topo.Children.Add(new StackPanel { Spacing = 2, Children = {
            T($"{Maiuscula(titulo)}", null, Tema.Osso, 15).Com(t => t.FontWeight = FontWeight.SemiBold),
            T($"{ids.Count} {(ids.Count == 1 ? "item" : "itens")} · aplicado {Quando(p.S("quando"))}" + (desfaz ? "" : " · remoções não voltam por aqui"), "rotulo") } }.Com(x => Grid.SetColumn(x, 1)));
        var cabBt = new Button { Content = topo, Background = Brushes.Transparent, CornerRadius = new CornerRadius(0), Padding = new Thickness(32, 15), BorderBrush = Tema.Linha, BorderThickness = new Thickness(0, 1, 0, 0), HorizontalAlignment = HorizontalAlignment.Stretch, HorizontalContentAlignment = HorizontalAlignment.Stretch };
        var corpo = new StackPanel { IsVisible = aberta, Spacing = 6, Margin = new Thickness(56, 4, 32, 16) };
        var caixas = new List<(CheckBox c, string id)>();
        var marcados = Botao("Desfazer marcados", false, async () => await Volta(new[] { nome }, caixas.Where(x => x.c.IsChecked == true).Select(x => x.id).ToArray(), titulo));
        marcados.IsEnabled = false;
        foreach (var id in ids)
        {
            string nomeItem = titulos?[id]?.ToString() ?? Legivel(id);
            bool sozinho = porItem.Contains(id);
            var c = new CheckBox { Content = new StackPanel { Spacing = 1, Children = {
                    T(Maiuscula(nomeItem), null, Tema.Osso, 14, true),
                    T(sozinho ? "volta sozinho" : "só volta com a área inteira (aplicado antes da 4.2.1)", null, sozinho ? Tema.Apagado : Tema.Ambar, 12.5, true) } },
                IsEnabled = desfaz && sozinho };
            c.IsCheckedChanged += (_, _) => { int n = caixas.Count(x => x.c.IsChecked == true); marcados.Content = n == 0 ? "Desfazer marcados" : $"Desfazer {n} {(n == 1 ? "item" : "itens")}"; marcados.IsEnabled = n > 0; };
            caixas.Add((c, id));
            corpo.Children.Add(c);
        }
        if (soPacote > 0 && porItem.Count == 0)
            corpo.Children.Insert(0, Item("Esta área foi aplicada antes da 4.2.1: as mudanças não sabem de qual item vieram, então voltam juntas.", Tema.Ambar));
        if (desfaz)
            corpo.Children.Add(new StackPanel { Orientation = Orientation.Horizontal, Spacing = 10, Margin = new Thickness(0, 10, 0, 0), Children = {
                marcados, Botao($"Desfazer {Maiuscula(titulo)} inteiro", false, async () => await Volta(new[] { nome }, null, titulo)) } });
        cabBt.Click += (_, _) =>
        {
            bool ab = !corpo.IsVisible; corpo.IsVisible = ab; seta.Text = ab ? "−" : "+";
            if (ab) { abertas.Add(nome); Movimento.Entra(corpo, 4); } else abertas.Remove(nome);
        };
        return new StackPanel { Children = { cabBt, corpo } };
    }

    // "ini:Steam" → "Steam"; "svc-xbox" → "svc xbox" (só quando o nome do item não foi guardado)
    static string Legivel(string id) => id.Contains(':') ? id[(id.IndexOf(':') + 1)..] : id.Replace('-', ' ');

    async Task Volta(string[] pacotes, string[]? itens, string titulo)
    {
        var j = Janela.Atual!;
        if (pacotes.Length == 0 || (itens != null && itens.Length == 0)) return;
        string pergunta = titulo == "tudo" ? "Desfazer tudo?" : itens != null ? $"Desfazer {itens.Length} {(itens.Length == 1 ? "item" : "itens")} de {titulo}?" : $"Desfazer {titulo} inteiro?";
        string explica = itens != null ? "Só esses voltam ao valor de antes; o resto da área continua aplicado. O Windows vai pedir permissão de administrador."
                                       : "Os ajustes voltam ao valor de antes. O Windows vai pedir permissão de administrador.";
        if (!await j.Confirma(pergunta, T(explica, "sub", quebra: true), "Desfazer")) return;
        j.MostraCaixa(Janela.Caixa("Desfazendo", Andamento("Esperando a permissão de administrador do Windows",
            "Se o pedido do Windows não aparecer na frente, ele pode estar piscando na barra de tarefas. Depois disso, os ajustes voltam ao que eram antes.").painel));
        Trabalho.Comeca("Desfazendo…");
        try
        {
            JsonNode? r;
            if (itens != null)
            {
                var sel = new JsonObject { [pacotes[0]] = new JsonArray(itens.Select(x => (JsonNode)JsonValue.Create(x)!).ToArray()) };
                r = await Servico.Muda("desfazer", new { itens = sel });
            }
            else r = await Servico.Muda("desfazer", new { pacotes });
            Conferencia.Pede(pacotes, frente: true, forcar: true);
            var falhas = r.A("pacotes").Where(x => !x.B("ok") && !x.B("nada")).Select(x => x.S("titulo")).ToList();
            j.MostraCaixa(Janela.Caixa(falhas.Count == 0 ? "Desfeito" : "Desfeito em parte",
                T(falhas.Count == 0 ? "Voltou ao que era antes." : "Não voltou: " + string.Join(", ", falhas) + ". O detalhe está no relatório do Katharos.", "sub"),
                Botao("Fechar", true, () => { j.FechaCaixa(); _ = Recarrega(); })), true);
        }
        catch (Exception e) { MostraErro(e, "Não deu para desfazer", "As mudanças continuam aplicadas. Tente de novo; se repetir, um ponto de restauração do Windows também volta o PC."); }
        finally { Trabalho.Termina(); }
    }
}

/// <summary>Configurações: as mesmas preferências da CLI, cada uma com o que faz e as opções em botões.</summary>
public class Configuracoes : Tela
{
    // as que importam para quem usa as janelas, na ordem de uso (as de aparência do terminal ficam na CLI)
    static readonly string[] Mostrar = { "modo", "confirmar", "tempo-real", "avisos", "coleta-em-jogo", "atualizacoes", "canal", "animacoes" };
    // o que o motor pode avisar e quando (I24)
    static readonly string[] Motor = { "avisos-intervalo", "avisos-no-jogo", "resumo-diario" };
    static readonly Dictionary<string, string[]> OpcoesCurtas = new() { ["avisos-intervalo"] = new[] { "2", "6", "12", "24" } };
    static readonly Dictionary<string, string> Rotulos = new() { ["so-grave"] = "só o grave", ["estavel"] = "estável", ["previa"] = "prévia", ["automatico"] = "automático", ["nao"] = "não" };

    protected override async Task Carrega()
    {
        var cab = Cabecalho("Configurações", null);
        Monta(cab, Carregando("Lendo").secao);
        var d = await Servico.Le("config_ler");
        var lista = new StackPanel { Children = { Subtitulo("Preferências", null, "config") } };
        foreach (var k in Mostrar) Preferencia(d, k, lista);
        var motor = new StackPanel { Children = { Subtitulo("O motor de inteligência", null, "central") } };
        foreach (var k in Motor) Preferencia(d, k, motor);
        // o que ele nunca propõe: comandos separados por vírgula
        var nunca = new TextBox { Text = d?["motor-nunca"].S("valor") ?? "", Watermark = "ex.: turbo, energia", MinWidth = 220 };
        var salvar = Botao("Salvar", false, async () => { await Servico.Le("config_gravar", new { chave = "motor-nunca", valor = (nunca.Text ?? "").Trim() }); await Recarrega(); });
        motor.Children.Add(Linha("O que ele nunca propõe", null, null, new StackPanel { Orientation = Orientation.Horizontal, Spacing = 8, Children = { nunca, salvar } }));

        // a memória do PC: o que ele aprendeu, exportar e apagar (com exportação antes)
        var mem = await Servico.Le("memoria");
        var cont = mem?["contagens"];
        string resumo = mem.S("desde") == "" ? "Ainda vazia: começa a encher com o acompanhamento ligado."
            : $"Desde {Quando(mem.S("desde"))}: {Num(cont.D("minutos"))} minutos medidos, {Num(cont.D("sessoes"))} sessões de jogo, {Num(cont.D("resultados"))} resultados medidos ({Num((mem.D("bytes") ?? 0) / 1048576, 1)} MB).";
        var acoes = new StackPanel { Orientation = Orientation.Horizontal, Spacing = 8 };
        acoes.Children.Add(Botao("Exportar", false, async () => await Exporta()));
        acoes.Children.Add(Botao("Apagar", false, async () => await Apaga()));
        var memoria = S(new StackPanel { Children = { Subtitulo("Memória do PC", "Fica só neste PC.", "memoria"),
                                                      Linha("O que ele guarda", resumo, null, acoes) } });
        var versao = S(new StackPanel { Children = { Subtitulo("Esta versão", null, "info"),
                                                     Linha("Novidades", null, null, Botao("Ver", false, async () => await Janela.Atual!.MostraNovidades(soSePrecisa: false))) } });
        Monta(cab, G(lista), G(motor), memoria, versao);
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
            ops.Children.Add(Botao(rot, o == atual, async () =>
            {
                await Servico.Le("config_gravar", new { chave = k, valor = o });
                if (k == "animacoes") Movimento.Ligado = o != "desligadas";   // vale na hora, sem reabrir
                await Recarrega();
            }));
        }
        lista.Children.Add(Linha(Maiuscula(c.S("rotulo")), c.S("explica"), null, ops));
    }

    async Task Exporta()
    {
        var j = Janela.Atual!;
        try { var r = await Servico.Le("memoria_exportar"); j.MostraCaixa(Janela.Caixa("Exportado", T("Salvo em " + r.S("arquivo"), "sub"), Botao("Fechar", true, j.FechaCaixa)), true); }
        catch (Exception e) { MostraErro(e, "Não deu para exportar"); }
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
        catch (Exception e) { MostraErro(e, "Não deu para apagar", "A memória continua como estava."); }
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
