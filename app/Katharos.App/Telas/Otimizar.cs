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
/// Otimizar: 1) o modo, 2) cada item, com o que ganha, o que perde e se já está assim no PC, 3) aplicar exatamente o que ficou marcado.
/// Depois de aplicar: o que mudou, o que deu aviso, o que não ficou (conferido no Windows) e a volta a um clique.
/// </summary>
public class Otimizar : Tela
{
    class ItemVm
    {
        public required JsonNode J;
        public string Id => J.S("id");
        public string Pacote => J.S("pacote");
        public bool? Ja => J["ja"] is JsonValue v && v.TryGetValue(out bool b) ? b : null;
        /// <summary>Leitura com mais de um dia (ou nenhuma): mostrada, mas conferida de novo em segundo plano.</summary>
        public bool Velho => J.D("ja_idade_h") is not double h || h > 24;
        public bool Marcado;
        public CheckBox? Caixa; public TextBlock? Estado;
    }
    class AreaVm { public required JsonNode J; public List<ItemVm> Itens = new(); public bool Aberta; public TextBlock? Conta; public StackPanel? Lista; public TextBlock? Seta; public Border? Caixa; }

    string modo = "equilibrado";
    readonly string foco;
    bool focoFeito;
    List<AreaVm> areas = new();
    JsonNode? lista;   // a última lista inteira (para guardar com o que a conferência trouxer)
    readonly TextBlock resumo = T("", null, Tema.Osso, 15).Com(t => t.FontWeight = FontWeight.SemiBold);
    readonly TextBlock conferindo = T("", "rotulo");
    readonly Button lerDeNovo;
    Button aplicar = new();
    bool semEventos;
    Control? cab;

    readonly Border barra = new() { Background = Tema.Painel, BorderBrush = Tema.Linha, BorderThickness = new Thickness(0, 1, 0, 0), Padding = new Thickness(72, 16), IsVisible = false };

    public Otimizar(string areaFoco = "")
    {
        foco = areaFoco;
        // a barra de ação fica fixa embaixo; só a lista rola
        if (Content is ScrollViewer sv) sv.Content = null;
        var dock = new DockPanel();
        DockPanel.SetDock(barra, Dock.Bottom);
        dock.Children.Add(barra);
        dock.Children.Add(new ScrollViewer { Content = Corpo, HorizontalScrollBarVisibility = Avalonia.Controls.Primitives.ScrollBarVisibility.Disabled });
        Content = dock;
        lerDeNovo = new Button { Classes = { "link" }, Content = "Ler de novo", Padding = new Thickness(0), Background = Brushes.Transparent, Foreground = Tema.Ambar, FontSize = 13 };
        lerDeNovo.Click += (_, _) => Conferencia.Pede(areas.Select(x => x.J.S("nome")), forcar: true);
        // a conferência vive fora da tela: entrar e sair do Otimizar não a cancela; enquanto a tela está aberta, ela ouve
        AttachedToVisualTree += (_, _) => { Conferencia.AreaPronta += AreaConferida; Conferencia.Mudou += MostraAndamento; };
        DetachedFromVisualTree += (_, _) => { Conferencia.AreaPronta -= AreaConferida; Conferencia.Mudou -= MostraAndamento; };
    }

    object Pedido() => new { modo, conferir = false };

    protected override async Task Carrega()
    {
        cab = Cabecalho("Otimizar", "Escolha um modo. Antes de aplicar, você confere cada item e tira o que não quiser.");
        // abre na hora com o que está guardado (mesmo de outra abertura do Katharos); a leitura nova só troca o que mudou
        modo = Servico.Guardado("config_ler")?["modo"].S("valor", modo) ?? modo;
        var g = Servico.Guardado("itens", Pedido());
        if (g != null) { Le(g); Desenha(cab); }
        else Monta(cab, Carregando("Lendo o que dá para fazer neste PC").secao);
        var cfg = await Servico.Le("config_ler");
        string m = cfg?["modo"].S("valor", "equilibrado") ?? "equilibrado";
        if (m != modo) { modo = m; g = null; }
        var d = await Servico.Le("itens", Pedido());
        if (g == null || Forma(g) != Forma(d)) { Le(d); Desenha(cab); }
        else { lista = d; AtualizaItens(d.A("areas").SelectMany(a => a.A("itens"))); }
        PedeConferencia(d);
    }

    /// <summary>A forma da lista (áreas e ids): se mudou, a tela é refeita; se não, só o "já está assim" de cada linha muda.</summary>
    static string Forma(JsonNode? d) => string.Join("|", d.A("areas").Select(a => a.S("nome") + ":" + string.Join(",", a.A("itens").Select(i => i.S("id")))));

    void Le(JsonNode? d)
    {
        lista = d;
        var abertas = areas.Where(a => a.Aberta).Select(a => a.J.S("nome")).ToHashSet();
        // vindo de um botão ("Escolher quais abrem"): só aquela área aberta
        if (!focoFeito && foco != "") abertas = new() { foco };
        var marcas = areas.SelectMany(a => a.Itens).ToDictionary(i => i.Pacote + "/" + i.Id, i => i.Marcado);
        areas = d.A("areas").Where(a => a.A("itens").Any()).Select(a => new AreaVm
        {
            J = a, Aberta = abertas.Contains(a.S("nome")),
            // a marca da pessoa nunca se perde numa leitura nova; item novo vem como o modo marca
            Itens = a.A("itens").Select(i => new ItemVm { J = i, Marcado = marcas.TryGetValue(i.S("pacote") + "/" + i.S("id"), out var mk) ? mk : i.B("marcado") }).ToList(),
        }).ToList();
        foreach (var a in areas) Conferencia.Nomes[a.J.S("nome")] = a.J.S("titulo");
    }

    /// <summary>Confere em segundo plano, uma área por vez: primeiro a que a pessoa veio ver, depois as que estão sem leitura ou velhas.</summary>
    void PedeConferencia(JsonNode? d)
    {
        if (Servico.Exemplo) return;
        var faltam = d.A("areas").Where(a => (a.D("faltam") ?? 0) > 0).Select(a => a.S("nome")).ToList();
        Conferencia.Pede(faltam);
        if (foco != "" && faltam.Contains(foco)) Conferencia.Pede(new[] { foco }, frente: true);
        MostraAndamento();
    }

    /// <summary>Uma área conferida: troca o "já está assim" das linhas dela e guarda a lista inteira atualizada.</summary>
    void AreaConferida(string nome, JsonNode area)
    {
        AtualizaItens(area.A("itens"));
        if (lista?["areas"] is JsonArray arr)
            foreach (var a in arr.OfType<JsonObject>().Where(a => a.S("nome") == nome))
            {
                a["faltam"] = 0;
                foreach (var it in a.A("itens").OfType<JsonObject>())
                    if (area.A("itens").FirstOrDefault(n => n.S("id") == it.S("id")) is JsonNode novo) { it["ja"] = novo["ja"]?.DeepClone(); it["ja_idade_h"] = novo["ja_idade_h"]?.DeepClone(); }
            }
        if (lista != null) Servico.Guarda("itens", Pedido(), lista);
        MostraAndamento();
    }

    void AtualizaItens(IEnumerable<JsonNode> novos)
    {
        var vistos = novos.ToDictionary(x => x.S("pacote") + "/" + x.S("id"), x => x);
        semEventos = true;
        try
        {
            foreach (var i in areas.SelectMany(a => a.Itens))
            {
                if (!vistos.TryGetValue(i.Pacote + "/" + i.Id, out var v)) continue;
                i.J["ja"] = v["ja"]?.DeepClone(); i.J["ja_idade_h"] = v["ja_idade_h"]?.DeepClone();
                if (i.Caixa != null) { i.Caixa.IsEnabled = i.Ja != true; i.Caixa.IsChecked = i.Ja == true || i.Marcado; }
            }
        }
        finally { semEventos = false; }
        AtualizaContas();
    }

    void MostraAndamento()
    {
        if (Conferencia.Rodando) { conferindo.Text = Conferencia.Texto + "… Pode mexer: só a linha muda quando chegar."; lerDeNovo.IsVisible = false; }
        else if (Conferencia.Erro is string e) { conferindo.Text = "Não deu para conferir tudo: " + e; lerDeNovo.IsVisible = true; }
        else
        {
            var idades = areas.SelectMany(a => a.Itens).Select(i => i.J.D("ja_idade_h")).OfType<double>().ToList();
            double? h = idades.Count > 0 ? idades.Max() : null;
            conferindo.Text = h == null ? "O que já está assim no PC aparece aqui depois de conferido (nada muda)."
                : h < 0.1 ? "Conferido agora: o que já está assim não roda de novo."
                : $"Conferido há {Idade(h.Value)}: o que já está assim não roda de novo. Depois de aplicar, cada item é lido de volta no Windows.";
            lerDeNovo.IsVisible = true;
        }
        AtualizaContas();
    }

    static string Idade(double h) => h < 1 ? $"{Math.Max(1, (int)Math.Round(h * 60))} min" : h < 48 ? $"{(int)Math.Round(h)} h" : $"{(int)Math.Round(h / 24)} dias";

    void Desenha(Control cab)
    {
        // os textos que vivem de uma tela para a outra saem do lugar antigo antes de entrar no novo
        if (conferindo.Parent is Panel pc) pc.Children.Remove(conferindo);
        if (lerDeNovo.Parent is Panel pl) pl.Children.Remove(lerDeNovo);
        if (cab.Parent is Panel pcab) pcab.Children.Remove(cab);
        // passo 1: o modo
        var modos = new UniformGrid { Columns = 3, Margin = new Thickness(32, 0, 32, 28) };
        foreach (var (m, nome, explica) in new[] {
            ("seguro", "Seguro", "Só o que não tem contrapartida: telemetria, anúncios e lixo."),
            ("equilibrado", "Equilibrado", "O seguro mais o que quase ninguém usa."),
            ("extremo", "Extremo", "Tudo o que ajuda neste PC. Cada item diz o que você perde.") })
        {
            bool esc = m == modo;
            var topo = new Grid { ColumnDefinitions = new ColumnDefinitions("*,Auto"), Children = { T(nome, "forte", tamanho: 17) } };
            if (esc) topo.Children.Add(T("escolhido", null, Tema.Ambar, 12).Com(t => { t.FontFamily = Tema.Mono; Grid.SetColumn(t, 1); }));
            var cartao = new Border
            {
                BorderBrush = esc ? Tema.Ambar : Tema.Linha, Background = esc ? Tema.AmbarFraco : Brushes.Transparent, BorderThickness = new Thickness(1),
                CornerRadius = new CornerRadius(2), Padding = new Thickness(20, 18),
                Child = new StackPanel { Spacing = 6, Children = { topo, T(explica, null, null, 14, true) } },
            };
            var b = new Button { Content = cartao, Padding = new Thickness(0), Margin = new Thickness(0, 0, 12, 0), Background = Brushes.Transparent, HorizontalAlignment = HorizontalAlignment.Stretch, HorizontalContentAlignment = HorizontalAlignment.Stretch };
            b.Click += async (_, _) =>
            {
                if (modo == m) return;
                var antes = modo;
                try { modo = m; var d = Servico.Guardado("itens", Pedido()) ?? await Servico.Le("itens", Pedido()); Le(d); Desenha(cab); }
                catch (Exception e) { modo = antes; MostraErro(e, "Não deu para trocar de modo", "O modo continua o de antes."); }
            };
            modos.Children.Add(b);
        }
        var passo1 = S(new StackPanel { Children = { Subtitulo("1. Escolha o modo"), modos } });

        // passo 2: os itens por área
        var lista = new StackPanel();
        lista.Children.Add(new StackPanel { Spacing = 4, Margin = new Thickness(32, 22, 32, 12), Children = { T("2. Confira os itens", "forte"),
            new WrapPanel { Children = { conferindo.Com(t => { t.TextWrapping = TextWrapping.Wrap; t.Margin = new Thickness(0, 0, 10, 0); }), lerDeNovo } } } });
        foreach (var a in areas) lista.Children.Add(DesenhaArea(a));
        var passo2 = S(lista);

        // a ação, sempre à vista
        aplicar = Botao("", true, async () => await Aplica());
        if (resumo.Parent is Panel pr) pr.Children.Remove(resumo);
        barra.Child = new Grid
        {
            ColumnDefinitions = new ColumnDefinitions("*,Auto"),
            Children = { new StackPanel { Spacing = 2, VerticalAlignment = VerticalAlignment.Center, Children = { resumo, T("Antes, o Katharos cria um ponto de restauração. Cada mudança volta pelo Desfazer.", "rotulo") } },
                         aplicar.Com(b => Grid.SetColumn(b, 1)) },
        };
        barra.IsVisible = true;
        Monta(cab, passo1, passo2);
        MostraAndamento();
        // veio de um botão: rola até a área e destaca por um instante (uma vez só, não a cada leitura nova)
        if (!focoFeito && foco != "" && areas.FirstOrDefault(x => x.J.S("nome") == foco)?.Caixa is Border alvo)
        {
            focoFeito = true;
            Dispatcher.UIThread.Post(() => { alvo.BringIntoView(); Movimento.Destaca(alvo); }, DispatcherPriority.Background);
        }
    }

    Control DesenhaArea(AreaVm a)
    {
        a.Seta = T(a.Aberta ? "−" : "+", null, Tema.Apagado).Com(t => t.FontFamily = Tema.Mono);
        a.Conta = T("", null, Tema.Ambar, 13).Com(t => { t.FontFamily = Tema.Mono; t.VerticalAlignment = VerticalAlignment.Center; });
        var topo = new Grid { ColumnDefinitions = new ColumnDefinitions("24,*,Auto") };
        topo.Children.Add(a.Seta);
        var textoArea = new StackPanel { Spacing = 2, Children = { T(Primeira(a.J.S("titulo")), null, Tema.Osso, 15).Com(t => t.FontWeight = FontWeight.SemiBold), T(a.J.S("resumo"), "rotulo") } };
        // I22: o motor recomenda esta área para este PC, com o número que justifica (o modo continua decidindo o resto)
        if (a.J?["recomendado"] is JsonNode rec)
        {
            textoArea.Children.Insert(1, new StackPanel { Orientation = Orientation.Horizontal, Spacing = 8, Margin = new Thickness(0, 2, 0, 2),
                Children = { Etiqueta("recomendado", Tema.Ambar), T(Primeira(rec.S("motivo")), null, Tema.Ambar, 13, true).Com(t => { t.VerticalAlignment = VerticalAlignment.Center; t.MaxWidth = 640; }) } });
        }
        topo.Children.Add(textoArea.Com(s => Grid.SetColumn(s, 1)));
        topo.Children.Add(a.Conta.Com(t => Grid.SetColumn(t, 2)));
        var cab = new Button { Content = topo, Background = Brushes.Transparent, CornerRadius = new CornerRadius(0), Padding = new Thickness(32, 15), BorderBrush = Tema.Linha, BorderThickness = new Thickness(0, 1, 0, 0), HorizontalAlignment = HorizontalAlignment.Stretch, HorizontalContentAlignment = HorizontalAlignment.Stretch };
        a.Lista = new StackPanel { IsVisible = a.Aberta, Margin = new Thickness(0, 0, 0, 10) };
        if (a.Aberta) PreencheItens(a);
        cab.Click += (_, _) =>
        {
            a.Aberta = !a.Aberta; a.Seta.Text = a.Aberta ? "−" : "+"; a.Lista.IsVisible = a.Aberta;
            if (a.Aberta && a.Lista.Children.Count == 0) PreencheItens(a);
            if (a.Aberta) Movimento.Entra(a.Lista, 4);
            // abriu uma área com leitura de algumas horas: confere ela primeiro (pega o que a pessoa mudou à mão no Windows)
            if (a.Aberta && a.Itens.Any(i => i.J.D("ja_idade_h") is not double h || h > 6)) Conferencia.Pede(new[] { a.J.S("nome") }, frente: true);
        };
        a.Caixa = new Border { Child = new StackPanel { Children = { cab, a.Lista } } };
        return a.Caixa;
    }

    void PreencheItens(AreaVm a)
    {
        foreach (var i in a.Itens)
        {
            var textos = new StackPanel { Spacing = 2, Margin = new Thickness(4, 0, 0, 0) };
            textos.Children.Add(T(Primeira(i.J.S("titulo")), null, Tema.Osso, 15, true));
            string explica = i.J.S("explica");
            if (explica != "") textos.Children.Add(T(explica, "rotulo", tamanho: 13.5, quebra: true));
            string ganho = i.J.S("ganho"), custo = i.J.S("custo");
            if (ganho != "") textos.Children.Add(T("ganha: " + ganho, null, Tema.Verde, 13, true));
            if (custo != "" && custo != "nenhum") textos.Children.Add(T("perde: " + custo, null, Tema.Texto, 13, true));
            if (i.J.S("alerta") != "") textos.Children.Add(T("atenção: " + i.J.S("alerta"), null, Tema.Ambar, 13, true));
            if (i.J.B("sem_volta")) textos.Children.Add(T("sem volta: o Desfazer não traz de volta", null, Tema.Vermelho, 13, true));
            i.Caixa = new CheckBox { Content = textos, IsChecked = i.Ja == true || i.Marcado, IsEnabled = i.Ja != true, VerticalAlignment = VerticalAlignment.Top };
            i.Caixa.IsCheckedChanged += (_, _) => { if (semEventos) return; i.Marcado = i.Caixa.IsChecked == true; if (i.Marcado) Exclui(a, i); AtualizaContas(); };
            i.Estado = T("", null, null, 13).Com(t => { t.FontFamily = Tema.Mono; t.Margin = new Thickness(16, 3, 0, 0); });
            var g = new Grid { ColumnDefinitions = new ColumnDefinitions("*,Auto"), Margin = new Thickness(56, 6, 32, 6), Children = { i.Caixa, i.Estado.Com(t => Grid.SetColumn(t, 1)) } };
            a.Lista!.Children.Add(g);
        }
        AtualizaContas();
    }

    /// <summary>Itens do mesmo grupo se excluem e alguns conflitam (como na CLI): marcar um desmarca o outro.</summary>
    static void Exclui(AreaVm a, ItemVm i)
    {
        string grupo = i.J.S("grupo");
        var conf = i.J.A("conflita").Select(x => x.ToString()).ToHashSet();
        foreach (var o in a.Itens)
            if (o != i && o.Marcado && o.Ja != true && ((grupo != "" && o.J.S("grupo") == grupo) || conf.Contains(o.Id)))
            { o.Marcado = false; if (o.Caixa != null) o.Caixa.IsChecked = false; }
    }

    IEnumerable<ItemVm> VaoMudar() => areas.SelectMany(a => a.Itens).Where(i => i.Marcado && i.Ja != true);

    void AtualizaContas()
    {
        foreach (var a in areas)
        {
            int m = a.Itens.Count(i => i.Marcado && i.Ja != true), f = a.Itens.Count(i => i.Ja == true);
            if (a.Conta != null) a.Conta.Text = (m > 0 ? $"{m} mudam" : "nada muda") + (f > 0 ? $" · {f} já feitos" : "") + $" · {a.Itens.Count} itens";
            foreach (var i in a.Itens.Where(i => i.Estado != null))
            {
                bool lendo = Conferencia.NaFila(i.Pacote) && (i.Ja == null || i.Velho);
                i.Estado!.Text = lendo && i.Ja != true ? "conferindo…" : i.Ja == true ? (i.Velho ? "já estava assim" : "já está assim") : i.Marcado ? "vai mudar" : "não marcado";
                i.Estado.Foreground = i.Ja == true ? (i.Velho ? Tema.Apagado : Tema.Verde) : i.Marcado ? Tema.Ambar : Tema.Apagado;
            }
        }
        int n = VaoMudar().Count(), feitos = areas.Sum(a => a.Itens.Count(i => i.Ja == true));
        resumo.Text = n == 0 ? "Nada marcado para mudar" : $"{n} {(n == 1 ? "mudança marcada" : "mudanças marcadas")}" + (feitos > 0 ? $" · {feitos} itens já estão feitos" : "");
        aplicar.Content = n == 0 ? "Aplicar" : $"Aplicar {n} {(n == 1 ? "mudança" : "mudanças")}";
        aplicar.IsEnabled = n > 0;
    }

    async Task Aplica()
    {
        var itens = VaoMudar().Select(i => new Escolhido(i.Pacote, areas.First(a => a.J.S("nome") == i.Pacote).J.S("titulo"), i.Id, i.J.S("titulo"), i.J.B("sem_volta"))).ToList();
        await Aplicacao.Aplica(itens, () => _ = Recarrega(), Abre);
    }

    static string Primeira(string s) => string.IsNullOrEmpty(s) ? s : char.ToUpper(s[0]) + s[1..];
}
