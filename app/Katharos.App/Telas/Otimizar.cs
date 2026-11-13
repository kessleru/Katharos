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
        public CheckBox? Caixa; public TextBlock? Estado; public Control? Linha;
        public string Busca => (J.S("titulo") + " " + J.S("explica") + " " + J.S("ganho")).ToLowerInvariant();
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
        cab = Cabecalho("Otimizar", null);
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

    void Le(JsonNode? d, bool novoModo = false)
    {
        lista = d;
        var abertas = areas.Where(a => a.Aberta).Select(a => a.J.S("nome")).ToHashSet();
        // vindo de um botão ("Escolher quais abrem"): só aquela área aberta
        if (!focoFeito && foco != "") abertas = new() { foco };
        // trocar de modo refaz as marcas pelo modo novo; uma leitura nova do mesmo modo mantém o que a pessoa marcou ou tirou
        var marcas = novoModo ? new Dictionary<string, bool>() : areas.SelectMany(a => a.Itens).ToDictionary(i => i.Pacote + "/" + i.Id, i => i.Marcado);
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
                if (area["por_modo"] is JsonNode pm) a["por_modo"] = pm.DeepClone();
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
                if (i.Caixa != null) { i.Caixa.IsChecked = i.Ja == true || i.Marcado; i.Caixa.Opacity = i.Ja == true ? 0.7 : 1; }
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
        // passo 1: o modo, com quantas mudanças cada um faria agora neste PC (o que já está feito não conta)
        var modos = new UniformGrid { Columns = 3, Margin = new Thickness(32, 0, 20, 24) };
        foreach (var (m, nome, explica) in new[] {
            ("seguro", "Seguro", "Telemetria, anúncios e lixo: nada que você use."),
            ("equilibrado", "Equilibrado", "O seguro e mais o que quase ninguém usa."),
            ("extremo", "Extremo", "Tudo o que ajuda. Cada item diz o que você perde.") })
        {
            bool esc = m == modo;
            int n = PorModo(m);
            var topo = new Grid { ColumnDefinitions = new ColumnDefinitions("*,Auto"), Children = { T(nome, "forte", tamanho: 17) } };
            if (esc) topo.Children.Add(Icones.De("ok", 16, Tema.Ambar).Com(i => Grid.SetColumn(i, 1)));
            var quantos = new StackPanel { Orientation = Orientation.Horizontal, Spacing = 6, Margin = new Thickness(0, 6, 0, 0), Children = {
                T(n < 0 ? "–" : Num(n), null, esc ? Tema.Ambar : Tema.Osso, 22).Com(t => { t.FontFamily = Tema.Mono; t.FontWeight = FontWeight.Bold; }),
                T(n == 1 ? "mudança" : "mudanças", "rotulo", tamanho: 13).Com(t => t.VerticalAlignment = VerticalAlignment.Bottom).Com(t => t.Margin = new Thickness(0, 0, 0, 4)) } };
            var cartao = new Border
            {
                BorderBrush = esc ? Tema.Ambar : Tema.Linha, Background = esc ? Tema.AmbarFraco : Brushes.Transparent, BorderThickness = new Thickness(1),
                CornerRadius = new CornerRadius(2), Padding = new Thickness(18, 16),
                Child = new StackPanel { Spacing = 4, Children = { topo, T(explica, "rotulo", tamanho: 13.5, quebra: true), quantos } },
            };
            var b = new Button { Content = cartao, Padding = new Thickness(0), Margin = new Thickness(0, 0, 12, 0), Background = Brushes.Transparent, HorizontalAlignment = HorizontalAlignment.Stretch, HorizontalContentAlignment = HorizontalAlignment.Stretch, VerticalAlignment = VerticalAlignment.Stretch, VerticalContentAlignment = VerticalAlignment.Stretch };
            ToolTip.SetTip(b, n < 0 ? nome : $"{nome}: {n} {(n == 1 ? "mudança" : "mudanças")} neste PC agora");
            b.Click += async (_, _) =>
            {
                if (modo == m || !modos.IsEnabled) return;
                var antes = modo;
                // a troca lê a lista de novo (pode levar uns segundos): o cartão escolhido acende na hora e diz que está trocando
                modos.IsEnabled = false;
                cartao.BorderBrush = Tema.Ambar; cartao.Background = Tema.AmbarFraco;
                if (quantos is Panel qp) { qp.Children.Clear(); qp.Children.Add(T("trocando…", "rotulo")); qp.Children.Add(new ProgressBar { IsIndeterminate = true, Width = 80, Height = 2, MinHeight = 2, Margin = new Thickness(8, 0, 0, 0), VerticalAlignment = VerticalAlignment.Center }); }
                resumo.Text = $"Trocando para o modo {nome}…";
                try { modo = m; var d = Servico.Guardado("itens", Pedido()) ?? await Servico.Le("itens", Pedido()); Le(d, novoModo: true); Desenha(cab); }
                catch (Exception e) { modo = antes; modos.IsEnabled = true; MostraErro(e, "Não deu para trocar de modo", "O modo continua o de antes."); Desenha(cab); }
            };
            modos.Children.Add(b);
        }
        var passo1 = S(new StackPanel { Children = {
            new Katharos.App.Controles.Fileira { Meio = Subtitulo("1. Escolha o modo", null),
                                               Direita = Link("Como funcionam os modos", () => Conceitos.Abre("modos")).Com(l => l.Margin = new Thickness(0, 0, 24, 0)), MinMeio = 260 },
            modos } });

        // passo 2: os itens por área, com a busca e os atalhos de marcar
        var lista = new StackPanel();
        lista.Children.Add(new StackPanel { Spacing = 6, Margin = new Thickness(32, 22, 32, 12), Children = { T("2. Confira os itens", "forte"),
            new WrapPanel { Children = { conferindo.Com(t => { t.TextWrapping = TextWrapping.Wrap; t.Margin = new Thickness(0, 0, 10, 0); t.VerticalAlignment = VerticalAlignment.Center; }), lerDeNovo,
                                        T("·", null, Tema.Apagado).Com(t => { t.Margin = new Thickness(10, 0); t.VerticalAlignment = VerticalAlignment.Center; }),
                                        Link("O que é \"já está assim\"?", () => Conceitos.Abre("ja_feito")) } } } });
        busca.Watermark = "Buscar um item (ex.: Xbox, impressão, Copilot)";
        busca.TextChanged -= Filtra; busca.TextChanged += Filtra;
        if (busca.Parent is Panel pb) pb.Children.Remove(busca);
        var atalhos = new WrapPanel { Margin = new Thickness(32, 0, 32, 14) };
        atalhos.Children.Add(busca.Com(b => { b.Width = 320; b.Margin = new Thickness(0, 0, 16, 8); }));
        atalhos.Children.Add(Botao("Desmarcar tudo", false, () => MarcaTudo(false)).Com(b => b.Margin = new Thickness(0, 0, 8, 8)));
        atalhos.Children.Add(Botao("Voltar ao modo", false, () => MarcaTudo(null)).Com(b => { b.Margin = new Thickness(0, 0, 8, 8); ToolTip.SetTip(b, "Marca de novo só o que o modo escolhido marca"); }));
        atalhos.Children.Add(Link(areas.All(x => x.Aberta) ? "Fechar todas" : "Abrir todas", () => AbreTodas(!areas.All(x => x.Aberta))).Com(l => l.Margin = new Thickness(0, 0, 0, 8)));
        lista.Children.Add(atalhos);
        foreach (var a in areas) lista.Children.Add(DesenhaArea(a));
        var passo2 = S(lista);

        // a ação, sempre à vista
        aplicar = Botao("", true, async () => await Aplica());
        if (resumo.Parent is Panel pr) pr.Children.Remove(resumo);
        barra.Child = new Katharos.App.Controles.Fileira
        {
            Meio = resumo,
            Direita = aplicar, MinMeio = 260,
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

    readonly TextBox busca = new() { MinHeight = 34 };

    /// <summary>Quantas mudanças o modo faria agora (do motor, área por área, já sem o que está feito). -1 = ainda não sabe.</summary>
    int PorModo(string m)
    {
        var pm = areas.Select(a => a.J?["por_modo"]?[m]).ToList();
        if (pm.Count == 0 || pm.Any(x => x == null)) return m == modo ? VaoMudar().Count() : -1;
        // o modo escolhido mostra o que está marcado de verdade (a pessoa pode ter tirado ou posto itens)
        return m == modo ? VaoMudar().Count() : pm.Sum(x => (int)x!.GetValue<double>());
    }

    /// <summary>Desmarcar tudo (marcar=false) ou voltar às marcas do modo (marcar=null). O que já está feito não muda.</summary>
    void MarcaTudo(bool? marcar)
    {
        semEventos = true;
        try
        {
            foreach (var i in areas.SelectMany(a => a.Itens).Where(i => i.Ja != true))
            {
                i.Marcado = marcar ?? i.J.B("marcado");
                if (i.Caixa != null) i.Caixa.IsChecked = i.Marcado;
            }
        }
        finally { semEventos = false; }
        AtualizaContas();
    }

    void AbreTodas(bool abrir)
    {
        foreach (var a in areas) a.Aberta = abrir;
        if (cab != null) Desenha(cab);
    }

    /// <summary>A busca: mostra só os itens com o texto (no nome, na explicação ou no ganho) e abre as áreas que têm algum.</summary>
    void Filtra(object? _, TextChangedEventArgs __)
    {
        string q = (busca.Text ?? "").Trim().ToLowerInvariant();
        foreach (var a in areas)
        {
            bool algum = false;
            if (q != "" && a.Lista != null && a.Lista.Children.Count == 0) PreencheItens(a);
            foreach (var i in a.Itens)
            {
                bool ve = q == "" || i.Busca.Contains(q);
                algum |= ve;
                if (i.Linha != null) i.Linha.IsVisible = ve;
            }
            if (a.Caixa != null) a.Caixa.IsVisible = q == "" || algum;
            if (a.Lista != null && a.Seta != null) { bool ab = q != "" ? algum : a.Aberta; a.Lista.IsVisible = ab; a.Seta.Text = ab ? "−" : "+"; }
        }
    }

    Control DesenhaArea(AreaVm a)
    {
        a.Seta = T(a.Aberta ? "−" : "+", null, Tema.Apagado).Com(t => t.FontFamily = Tema.Mono);
        a.Conta = T("", null, Tema.Ambar, 13).Com(t => { t.FontFamily = Tema.Mono; t.VerticalAlignment = VerticalAlignment.Center; });
        var topo = new Grid { ColumnDefinitions = new ColumnDefinitions("24,*") };
        topo.Children.Add(a.Seta);
        // só o nome no cabeçalho: o que a área é fica em "O que são ...?" e no mouse parado em cima (texto em espaço pequeno polui)
        var textoArea = new StackPanel { Spacing = 2, VerticalAlignment = VerticalAlignment.Center, Children = { T(Primeira(a.J.S("titulo")), null, Tema.Osso, 15).Com(t => t.FontWeight = FontWeight.SemiBold) } };
        if (a.J.S("resumo") != "") { ToolTip.SetTip(textoArea, Primeira(a.J.S("resumo"))); ToolTip.SetShowDelay(textoArea, 600); }
        // I22: o motor recomenda esta área para este PC, com o número que justifica (o modo continua decidindo o resto)
        if (a.J?["recomendado"] is JsonNode rec)
        {
            var selo = Etiqueta("recomendado", Tema.Ambar).Com(c => { c.HorizontalAlignment = HorizontalAlignment.Left; c.Margin = new Thickness(0, 2, 0, 0); ToolTip.SetTip(c, Primeira(rec.S("motivo"))); });
            textoArea.Children.Add(selo);
        }
        topo.Children.Add(new Katharos.App.Controles.Fileira { Meio = textoArea, Direita = a.Conta, MinMeio = 280 }.Com(f => Grid.SetColumn(f, 1)));
        var cab = new Button { Content = topo, Background = Brushes.Transparent, CornerRadius = new CornerRadius(0), Padding = new Thickness(32, 15), BorderBrush = Tema.Linha, BorderThickness = new Thickness(0, 1, 0, 0), HorizontalAlignment = HorizontalAlignment.Stretch, HorizontalContentAlignment = HorizontalAlignment.Stretch };
        a.Lista = new StackPanel { IsVisible = a.Aberta, Margin = new Thickness(48, 0, 0, 12) };
        if (a.Aberta) PreencheItens(a);
        // na área aberta: marcar ou tirar todos dela e o "?" do conceito
        cab.Click += (_, _) =>
        {
            a.Aberta = !a.Aberta; a.Seta.Text = a.Aberta ? "−" : "+"; a.Lista.IsVisible = a.Aberta;
            if (a.Aberta && a.Lista.Children.Count == 0) PreencheItens(a);
            if (a.Aberta) Movimento.Entra(a.Lista, 4);
            // abriu uma área com leitura de algumas horas: confere ela primeiro (pega o que a pessoa mudou à mão no Windows)
            if (a.Aberta && a.Itens.Any(i => i.J.D("ja_idade_h") is not double h || h > 6)) Conferencia.Pede(new[] { a.J.S("nome") }, frente: true);
        };
        // a área aberta: o cabeçalho numa faixa mais clara e os itens presos por uma régua (o mesmo jeito do raio-x)
        var regua = new Border { BorderBrush = Tema.LinhaForte, BorderThickness = new Thickness(2, 0, 0, 0), Child = a.Lista };
        a.Lista.Margin = new Thickness(0, 0, 0, 12);
        var corpo = new Border { Margin = new Thickness(46, 0, 0, 0), Child = regua };
        void Sincroniza() { corpo.IsVisible = a.Lista.IsVisible; cab.Background = a.Lista.IsVisible ? Tema.Painel : Brushes.Transparent; }
        Sincroniza();
        a.Lista.PropertyChanged += (_, e) => { if (e.Property == IsVisibleProperty) Sincroniza(); };
        a.Caixa = new Border { Child = new StackPanel { Children = { cab, corpo } } };
        return a.Caixa;
    }

    void PreencheItens(AreaVm a)
    {
        var acoes = new WrapPanel { Margin = new Thickness(14, 4, 32, 4) };
        acoes.Children.Add(Link("Marcar todos", () => MarcaArea(a, true)));
        acoes.Children.Add(Link("Desmarcar todos", () => MarcaArea(a, false)));
        if (Conceitos.DoComando(a.J.S("nome")) is string conc)
            acoes.Children.Add(Link("O que são " + Primeira(a.J.S("titulo")).ToLowerInvariant() + "?", () => Conceitos.Abre(conc)));
        a.Lista!.Children.Add(acoes);
        foreach (var i in a.Itens)
        {
            // À vista, só o nome e o que ganha. O resto (o que é, o que perde, os nomes técnicos) aparece parando o mouse em cima ou em
            // "detalhes": a lista de 23 serviços virava um paredão de texto. Os sinais ao lado do nome avisam, sem texto, que tem
            // contrapartida, atenção ou que não volta (etiquetas com a palavra, sem setas).
            var textos = new StackPanel { Spacing = 3, Margin = new Thickness(6, 0, 0, 0) };
            string explica = i.J.S("explica"), ganho = i.J.S("ganho"), custo = i.J.S("custo"), alerta = i.J.S("alerta");
            bool temCusto = custo != "" && custo != "nenhum";
            var nome = new StackPanel { Orientation = Orientation.Horizontal, Spacing = 8, Children = { T(Primeira(i.J.S("titulo")), null, Tema.Osso, 15, true).Com(t => t.FontWeight = FontWeight.SemiBold) } };
            // sem setas: só o raro vira etiqueta ao lado do nome (atenção, sem volta); o que perde fica em "detalhes" (quase todo item perde algo)
            void SinalNome(string texto, IBrush cor, string dica) => nome.Children.Add(Etiqueta(texto, cor).Com(c => { c.VerticalAlignment = VerticalAlignment.Center; ToolTip.SetTip(c, dica); }));
            if (alerta != "") SinalNome("atenção", Tema.Ambar, "Atenção: " + alerta);
            if (i.J.B("sem_volta")) SinalNome("sem volta", Tema.Vermelho, "O Desfazer não traz de volta");
            textos.Children.Add(nome);
            // "Ganha: ..." / "Perde: ...": a palavra em negrito no lugar do ícone
            Control Sinal(string rotulo, IBrush cor, string texto) => new TextBlock { FontSize = 13, TextWrapping = TextWrapping.Wrap, MaxWidth = 640, Foreground = Tema.Texto,
                Inlines = { new Avalonia.Controls.Documents.Run(rotulo + " ") { Foreground = cor, FontWeight = FontWeight.SemiBold }, new Avalonia.Controls.Documents.Run(texto) } };
            var linhaGanho = new WrapPanel();
            if (ganho != "") linhaGanho.Children.Add(Sinal("Ganha:", Tema.Verde, Primeira(ganho)).Com(c => c.Margin = new Thickness(0, 0, 12, 0)));
            textos.Children.Add(linhaGanho);
            // o que perde fica à vista também (pedido do dono): a primeira frase; o resto continua em "detalhes"
            textos.Children.Add(Sinal("Perde:", Tema.Osso, temCusto ? Primeira(custo) : "nada que você note."));
            var detalhes = new StackPanel { Spacing = 4, IsVisible = false, Margin = new Thickness(0, 4, 0, 0) };
            if (explica != "") detalhes.Children.Add(T(explica, "rotulo", tamanho: 13.5, quebra: true).Com(t => t.MaxWidth = 680));
            if (temCusto && custo.Trim().TrimEnd('.').Length > Primeira(custo).TrimEnd('.').Length + 2) detalhes.Children.Add(Sinal("Perde:", Tema.Osso, custo));
            if (alerta != "") detalhes.Children.Add(Sinal("Atenção:", Tema.Ambar, alerta));
            if (i.J.B("sem_volta")) detalhes.Children.Add(Sinal("Sem volta:", Tema.Vermelho, "o Desfazer não traz de volta."));
            if (detalhes.Children.Count > 0)
            {
                var ver = new Button { Classes = { "link" }, Padding = new Thickness(0), Content = "detalhes", FontSize = 12.5, HorizontalAlignment = HorizontalAlignment.Left, VerticalAlignment = VerticalAlignment.Center };
                ver.Click += (_, e) => { detalhes.IsVisible = !detalhes.IsVisible; ver.Content = detalhes.IsVisible ? "esconder" : "detalhes"; if (detalhes.IsVisible) Movimento.Entra(detalhes, 3); e.Handled = true; };
                linhaGanho.Children.Add(ver);
                textos.Children.Add(detalhes);
                // parar o mouse em cima mostra o mesmo, sem abrir nada
                var dica = new StackPanel { Spacing = 6, MaxWidth = 420, Children = { T(Primeira(i.J.S("titulo")), null, Tema.Osso, 14, true).Com(t => t.FontWeight = FontWeight.SemiBold) } };
                if (explica != "") dica.Children.Add(T(explica, null, Tema.Texto, 13, true));
                if (temCusto) dica.Children.Add(T("Perde: " + custo, null, Tema.Apagado, 13, true));
                ToolTip.SetTip(nome, dica);
                ToolTip.SetShowDelay(nome, 500);
            }
            i.Caixa = new CheckBox { Content = textos, IsChecked = i.Ja == true || i.Marcado, VerticalAlignment = VerticalAlignment.Top };
            i.Caixa.IsCheckedChanged += (_, _) =>
            {
                if (semEventos) return;
                // o que já está assim fica marcado (não há o que tirar); a caixa continua clicável só para os detalhes abrirem
                if (i.Ja == true) { semEventos = true; i.Caixa.IsChecked = true; semEventos = false; return; }
                i.Marcado = i.Caixa.IsChecked == true; if (i.Marcado) Exclui(a, i); AtualizaContas();
            };
            i.Estado = T("", null, null, 13).Com(t => { t.FontFamily = Tema.Mono; t.Margin = new Thickness(16, 3, 0, 0); });
            var g = new Grid { ColumnDefinitions = new ColumnDefinitions("*,Auto"), Children = { i.Caixa, i.Estado.Com(t => Grid.SetColumn(t, 1)) } };
            var linhaItem = new Border { Margin = new Thickness(22, 0, 32, 0), Padding = new Thickness(0, 12), BorderBrush = Tema.Linha, BorderThickness = new Thickness(0, a.Lista!.Children.Count > 1 ? 1 : 0, 0, 0), Child = g };
            i.Linha = linhaItem;
            if ((busca.Text ?? "") != "") linhaItem.IsVisible = i.Busca.Contains(busca.Text!.Trim().ToLowerInvariant());
            a.Lista!.Children.Add(linhaItem);
        }
        AtualizaContas();
    }

    void MarcaArea(AreaVm a, bool marcar)
    {
        semEventos = true;
        try
        {
            foreach (var i in a.Itens.Where(i => i.Ja != true))
            {
                i.Marcado = marcar;
                if (i.Caixa != null) i.Caixa.IsChecked = marcar;
            }
            // marcar todos respeita os grupos (só um de cada) e os conflitos, como marcar um por um
            if (marcar) foreach (var i in a.Itens.Where(i => i.Marcado && i.Ja != true).ToList()) if (i.Marcado) Exclui(a, i);
        }
        finally { semEventos = false; }
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
                // o Windows negou da última vez (mesmo como administrador): não conta como "vai mudar"; tentar de novo continua possível
                bool bloq = i.J.B("bloqueado") && i.Ja != true;
                ToolTip.SetTip(i.Estado, bloq ? "Da última vez o Windows não deixou mudar isto. Dá para marcar e tentar de novo." : null);
                i.Estado!.Text = bloq && !i.Marcado ? "o Windows bloqueia" : lendo && i.Ja != true ? "conferindo…" : i.Ja == true ? (i.Velho ? "já estava assim" : "já está assim") : i.Marcado ? "vai mudar" : "não marcado";
                i.Estado.Foreground = i.Ja == true ? (i.Velho ? Tema.Apagado : Tema.Verde) : i.Marcado ? Tema.Ambar : Tema.Apagado;
            }
        }
        int n = VaoMudar().Count(), feitos = areas.Sum(a => a.Itens.Count(i => i.Ja == true && i.Marcado)),
            semConferir = VaoMudar().Count(i => i.Ja == null);
        // o número do botão é o que vai mudar de verdade; o que ainda não foi conferido aparece separado (pode já estar assim)
        resumo.Text = n == 0 ? "Nada marcado para mudar" : $"{n} {(n == 1 ? "mudança" : "mudanças")}" + (semConferir > 0 ? $" · {semConferir} sem conferir" : "");
        ToolTip.SetTip(resumo, feitos > 0 ? $"{feitos} itens marcados já estão assim neste PC e não contam." : null);
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
