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
        public bool Marcado;
        public CheckBox? Caixa; public TextBlock? Estado;
    }
    class AreaVm { public required JsonNode J; public List<ItemVm> Itens = new(); public bool Aberta; public TextBlock? Conta; public StackPanel? Lista; public TextBlock? Seta; }

    string modo = "equilibrado";
    readonly string foco;
    List<AreaVm> areas = new();
    Dictionary<string, bool?> ja = new();
    TextBlock resumo = T("", null, Tema.Osso, 15).Com(t => t.FontWeight = FontWeight.SemiBold);
    TextBlock conferindo = T("", "rotulo");
    Button aplicar = new();
    bool conferido;

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
    }

    protected override async Task Carrega()
    {
        var cab = Cabecalho("Otimizar", "Escolha um modo. Antes de aplicar, você confere cada item e tira o que não quiser.");
        Monta(cab, Carregando("Lendo o que dá para fazer neste PC").secao);
        var cfg = await Servico.Le("config_ler");
        modo = cfg?["modo"].S("valor", "equilibrado") ?? "equilibrado";
        await CarregaItens(false);
        Desenha(cab);
        if (!conferido && !Servico.Exemplo) _ = Confere();
    }

    async Task CarregaItens(bool conferir, Action<string, JsonNode?>? ev = null)
    {
        var d = await Servico.Le("itens", new { modo, conferir }, ev);
        var abertas = areas.Where(a => a.Aberta).Select(a => a.J.S("nome")).ToHashSet();
        if (abertas.Count == 0 && foco != "") abertas.Add(foco);
        areas = d.A("areas").Where(a => a.A("itens").Any()).Select(a => new AreaVm
        {
            J = a, Aberta = abertas.Contains(a.S("nome")),
            Itens = a.A("itens").Select(i => new ItemVm { J = i, Marcado = i.B("marcado") }).ToList(),
        }).ToList();
        if (conferir) { conferido = true; foreach (var i in areas.SelectMany(a => a.Itens)) ja[i.Pacote + "/" + i.Id] = i.Ja; }
        else foreach (var i in areas.SelectMany(a => a.Itens))   // troca de modo: mantém o "já está assim" conferido
                if (ja.TryGetValue(i.Pacote + "/" + i.Id, out var v)) i.J["ja"] = v;
    }

    /// <summary>Confere em segundo plano o que já está assim no PC (modo teste: nada muda), área por área.</summary>
    async Task Confere()
    {
        conferindo.Text = "Conferindo o que já está feito no PC…";
        try
        {
            await CarregaItens(true, (t, d) => Dispatcher.UIThread.Post(() =>
            {
                if (t == "etapa") conferindo.Text = Primeira(d.S("texto")) + (d.D("de") is double de ? $" ({Num(d.D("n"))} de {Num(de)})" : "") + "…";
            }));
            conferindo.Text = "Conferido agora: o que já está assim não roda de novo.";
            Desenha(Corpo.Children[0]);
        }
        catch (Exception e) { conferindo.Text = "Não deu para conferir o que já está feito: " + e.Message; }
    }

    void Desenha(Control cab)
    {
        // os textos que vivem de uma tela para a outra saem do lugar antigo antes de entrar no novo
        if (conferindo.Parent is Panel pc) pc.Children.Remove(conferindo);
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
            b.Click += async (_, _) => { if (modo == m) return; modo = m; await CarregaItens(false); Desenha(cab); };
            modos.Children.Add(b);
        }
        var passo1 = S(new StackPanel { Children = { Subtitulo("1. Escolha o modo"), modos } });

        // passo 2: os itens por área
        var lista = new StackPanel();
        lista.Children.Add(new StackPanel { Spacing = 4, Margin = new Thickness(32, 22, 32, 12), Children = { T("2. Confira os itens", "forte"), conferindo } });
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
        AtualizaContas();
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
        };
        return new StackPanel { Children = { cab, a.Lista } };
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
            i.Caixa.IsCheckedChanged += (_, _) => { i.Marcado = i.Caixa.IsChecked == true; if (i.Marcado) Exclui(a, i); AtualizaContas(); };
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
                i.Estado!.Text = i.Ja == true ? "já está assim" : i.Marcado ? "vai mudar" : "não marcado";
                i.Estado.Foreground = i.Ja == true ? Tema.Verde : i.Marcado ? Tema.Ambar : Tema.Apagado;
            }
        }
        int n = VaoMudar().Count(), feitos = areas.Sum(a => a.Itens.Count(i => i.Ja == true));
        resumo.Text = n == 0 ? "Nada marcado para mudar" : $"{n} {(n == 1 ? "mudança marcada" : "mudanças marcadas")}" + (feitos > 0 ? $" · {feitos} itens já estão feitos" : "");
        aplicar.Content = n == 0 ? "Aplicar" : $"Aplicar {n} {(n == 1 ? "mudança" : "mudanças")}";
        aplicar.IsEnabled = n > 0;
    }

    async Task Aplica()
    {
        var j = Janela.Atual!;
        var itens = VaoMudar().ToList();
        if (itens.Count == 0) return;
        var aviso = await Servico.Le("aviso");
        if (!aviso.B("aceito")) { Abre("aviso:otimizar"); return; }
        int semVolta = itens.Count(i => i.J.B("sem_volta"));
        var corpo = new StackPanel { Spacing = 8 };
        foreach (var g in itens.GroupBy(i => i.Pacote))
            corpo.Children.Add(T($"{Primeira(areas.First(a => a.J.S("nome") == g.Key).J.S("titulo"))}: {g.Count()} {(g.Count() == 1 ? "item" : "itens")}", null, Tema.Texto, 14));
        corpo.Children.Add(T("O Windows vai pedir permissão de administrador. Antes de mudar, o Katharos cria um ponto de restauração.", "rotulo", quebra: true).Com(t => t.Margin = new Thickness(0, 8, 0, 0)));
        if (semVolta > 0) corpo.Children.Add(T($"{semVolta} {(semVolta == 1 ? "item não volta" : "itens não voltam")} pelo Desfazer (remoções).", null, Tema.Vermelho, 13.5, true));
        if (!await j.Confirma($"Aplicar {itens.Count} {(itens.Count == 1 ? "mudança" : "mudanças")}?", corpo, $"Aplicar {itens.Count}")) return;

        var passo = T("Abrindo o motor com permissão de administrador", null, Tema.Osso, 15, true);
        var item = T("", "rotulo", quebra: true);
        var barra = new ProgressBar { IsIndeterminate = true, Height = 3, MinHeight = 3, Foreground = Tema.Ambar, Background = Tema.Linha, CornerRadius = new CornerRadius(0) };
        j.MostraCaixa(Janela.Caixa("Aplicando", new StackPanel { Spacing = 12, Children = { passo, barra, item, T("Pode usar o PC. Não desligue até terminar.", "rotulo") } }));
        try
        {
            var sel = new JsonObject();
            foreach (var g in itens.GroupBy(i => i.Pacote)) sel[g.Key] = new JsonArray(g.Select(i => (JsonNode)JsonValue.Create(i.Id)!).ToArray());
            var r = await Servico.Muda("aplicar", new { itens = sel }, (t, d) => Dispatcher.UIThread.Post(() =>
            {
                if (t == "etapa") passo.Text = Primeira(d.S("texto"));
                else if (t == "pacote") passo.Text = $"{Primeira(d.S("titulo"))} ({Num(d.D("n"))} de {Num(d.D("de"))})";
                else if (t == "progresso" && d.D("de") is double de && de > 0) { barra.IsIndeterminate = false; barra.Maximum = de; barra.Value = d.D("n") ?? 0; item.Text = d.S("item"); }
            }));
            await MostraResultado(r);
        }
        catch (ErroDoMotor e) when (e.Codigo == "precisa_aceite") { j.FechaCaixa(); Abre("aviso:otimizar"); }
        catch (Exception e)
        {
            j.MostraCaixa(Janela.Caixa("Não deu certo", T(e.Message + " Nada foi marcado como feito; o que chegou a mudar volta pelo Desfazer.", "sub"), Botao("Fechar", false, j.FechaCaixa)), true);
        }
    }

    async Task MostraResultado(JsonNode? r)
    {
        var j = Janela.Atual!;
        var corpo = new StackPanel { Spacing = 6 };
        int feitos = 0, problemas = 0;
        foreach (var p in r.A("pacotes"))
        {
            int f = (int)(p.D("feitos") ?? 0); feitos += f;
            var erros = p.A("erros").Select(x => x.ToString()).ToList();
            var avisos = p.A("avisos").Select(x => x.ToString()).ToList();
            var nao = p.A("nao_ficou").Select(x => x.ToString()).ToList();
            problemas += erros.Count + nao.Count;
            var bloco = new StackPanel { Spacing = 3 };
            // uma linha por área: o nome e, alinhado à direita, quantas mudaram (fácil de bater o olho numa lista longa)
            bloco.Children.Add(new Grid { ColumnDefinitions = new ColumnDefinitions("*,Auto"), Children = {
                T(Primeira(p.S("titulo")), null, Tema.Osso, 15),
                T(f == 0 ? "nada mudou" : $"{f} {(f == 1 ? "mudança" : "mudanças")}", null, f == 0 ? Tema.Apagado : Tema.Verde, 14).Com(t => { t.FontFamily = Tema.Mono; Grid.SetColumn(t, 1); }) } });
            foreach (var x in erros.Take(4)) bloco.Children.Add(T("erro: " + x, null, Tema.Vermelho, 13, true));
            foreach (var x in nao.Take(4)) bloco.Children.Add(T("não ficou (conferido no Windows): " + x, null, Tema.Ambar, 13, true));
            foreach (var x in avisos.Take(3)) bloco.Children.Add(T("aviso: " + x, "rotulo", tamanho: 13, quebra: true));
            if (p.D("liberado") is double lib && lib > 0) bloco.Children.Add(T($"liberou {Num(lib / 1073741824.0, 1)} GB", null, Tema.Verde, 13));
            // medido antes e depois de cada item, neste PC (o mesmo que fica em "provas")
            if (p.S("medido") != "") bloco.Children.Add(T("Medido agora: " + p.S("medido") + ".", "rotulo", tamanho: 13, quebra: true));
            corpo.Children.Add(bloco);
        }
        string titulo = problemas == 0 ? $"Pronto: {feitos} {(feitos == 1 ? "mudança feita e conferida" : "mudanças feitas e conferidas")}" : $"Feito, com {problemas} {(problemas == 1 ? "ponto" : "pontos")} para olhar";
        corpo.Children.Insert(0, T(problemas == 0 ? "Cada ajuste foi lido de volta no Windows depois de aplicado." : "O resto ficou como pedido; os pontos abaixo dizem o que não ficou e por quê.", "rotulo", quebra: true).Com(t => t.Margin = new Thickness(0, 0, 0, 8)));
        var manter = r.A("perguntar_manter").Select(x => x.ToString()).ToList();
        if (manter.Count > 0) { await PerguntaManter(manter, titulo, corpo); return; }
        j.MostraCaixa(Janela.Caixa(titulo, corpo, new StackPanel { Orientation = Orientation.Horizontal, Spacing = 10, HorizontalAlignment = HorizontalAlignment.Right, Margin = new Thickness(0, 16, 0, 0),
            Children = { Botao("Ver o Desfazer", false, () => { j.FechaCaixa(); Abre("desfazer"); }), Botao("Fechar", true, () => { j.FechaCaixa(); _ = Recarrega(); }) } }), true);
    }

    /// <summary>Como a troca de resolução do Windows: depois de mudança de risco, "está tudo funcionando?"; sem resposta em 90 s, desfaz.</summary>
    async Task PerguntaManter(List<string> pacotes, string titulo, Control corpo)
    {
        var j = Janela.Atual!;
        int resta = 90;
        var conta = T("", null, Tema.Ambar, 14, true);
        var tcs = new TaskCompletionSource<bool>();
        var rel = new DispatcherTimer { Interval = TimeSpan.FromSeconds(1) };
        void Texto() => conta.Text = $"Olhe o PC por um instante (tela, som, internet, o jogo abrindo). Se não responder em {resta} s, o Katharos desfaz sozinho.";
        Texto();
        rel.Tick += (_, _) => { if (--resta <= 0) tcs.TrySetResult(false); else Texto(); };
        rel.Start();
        var p = new StackPanel { Spacing = 14, Children = { corpo, T("Está tudo funcionando?", "forte", tamanho: 17), conta } };
        j.MostraCaixa(Janela.Caixa(titulo, p, new StackPanel { Orientation = Orientation.Horizontal, Spacing = 10, HorizontalAlignment = HorizontalAlignment.Right, Margin = new Thickness(0, 16, 0, 0),
            Children = { Botao("Desfazer agora", false, () => tcs.TrySetResult(false)), Botao("Manter", true, () => tcs.TrySetResult(true)) } }));
        bool manter = await tcs.Task;
        rel.Stop();
        if (manter) { j.FechaCaixa(); await Recarrega(); return; }
        j.MostraCaixa(Janela.Caixa("Desfazendo", T("Voltando " + string.Join(", ", pacotes) + " ao que era antes.", "sub")));
        try
        {
            var r = await Servico.Muda("desfazer", new { pacotes });
            bool ok = r.A("pacotes").All(x => x.B("ok"));
            j.MostraCaixa(Janela.Caixa(ok ? "Desfeito" : "Desfeito em parte", T(ok ? "Voltou ao que era antes." : "Algo não voltou: abra o Desfazer para ver.", "sub"), Botao("Fechar", true, () => { j.FechaCaixa(); _ = Recarrega(); })), true);
        }
        catch (Exception e) { j.MostraCaixa(Janela.Caixa("Não deu para desfazer", T(e.Message + " Tente pela tela Desfazer.", "sub"), Botao("Fechar", false, j.FechaCaixa)), true); }
    }

    static string Primeira(string s) => string.IsNullOrEmpty(s) ? s : char.ToUpper(s[0]) + s[1..];
}
