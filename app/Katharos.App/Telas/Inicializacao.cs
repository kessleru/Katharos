using System.Text.Json.Nodes;
using Avalonia;
using Avalonia.Controls;
using Avalonia.Layout;
using Avalonia.Media;
using static Katharos.App.Ui;

namespace Katharos.App.Telas;

/// <summary>
/// O que abre com o Windows: cada programa com o ícone, o nome, onde está, o atraso medido no boot e um interruptor. No topo,
/// "Desligar os sugeridos" já com o que o Katharos recomenda. Usa os mesmos itens da área de inicialização do Otimizar (desliga pelo
/// mesmo mecanismo do Gerenciador de Tarefas) e volta igual: os desligados pelo Katharos ficam embaixo, com "Religar".
/// </summary>
public class Inicializacao : Tela
{
    const string AREA = "inicializacao";
    readonly Dictionary<string, bool> pedidos = new();   // id → true: desligar (o interruptor foi para "não abre")
    List<JsonNode> itens = new();
    JsonNode? aplicado;
    string modo = "equilibrado", forma = "";
    readonly TextBlock resumo = T("", null, Tema.Osso, 15).Com(t => t.FontWeight = FontWeight.SemiBold);
    readonly TextBlock andamento = T("", "rotulo");
    Button aplicar = new();
    readonly Border barra = new() { Background = Tema.Painel, BorderBrush = Tema.Linha, BorderThickness = new Thickness(0, 1, 0, 0), Padding = new Thickness(72, 16), IsVisible = false };

    public Inicializacao()
    {
        if (Content is ScrollViewer sv) sv.Content = null;
        var dock = new DockPanel();
        DockPanel.SetDock(barra, Dock.Bottom);
        dock.Children.Add(barra);
        dock.Children.Add(new ScrollViewer { Content = Corpo, HorizontalScrollBarVisibility = Avalonia.Controls.Primitives.ScrollBarVisibility.Disabled });
        Content = dock;
        AttachedToVisualTree += (_, _) => { Conferencia.AreaPronta += Conferida; Conferencia.Mudou += MostraAndamento; };
        DetachedFromVisualTree += (_, _) => { Conferencia.AreaPronta -= Conferida; Conferencia.Mudou -= MostraAndamento; };
    }

    object Pedido() => new { modo, conferir = false, areas = new[] { AREA } };

    protected override async Task Carrega()
    {
        var cab = Cabecalho("O que abre com o Windows", "Desligar não desinstala.");
        modo = Servico.Guardado("config_ler")?["modo"].S("valor", modo) ?? modo;
        var g = Servico.Guardado("itens", Pedido());
        aplicado = Servico.Guardado("aplicado");
        if (g != null) { Le(g); Desenha(cab); } else Monta(cab, Carregando("Lendo o que abre com o Windows").secao);
        var cfg = await Servico.Le("config_ler");
        modo = cfg?["modo"].S("valor", "equilibrado") ?? "equilibrado";
        var d = await Servico.Le("itens", Pedido());
        aplicado = await Servico.Le("aplicado");
        Le(d); Desenha(cab);
        // a lista que aparece é sempre conferida: se tem mais de 6 h, confere agora (e a tela só troca as linhas que mudaram)
        if (itens.Any(i => i.D("ja_idade_h") is not double h || h > 6)) Conferencia.Pede(new[] { AREA }, frente: true);
        MostraAndamento();
    }

    void Le(JsonNode? d)
    {
        itens = d.A("areas").FirstOrDefault().A("itens").ToList();
        forma = string.Join(",", itens.Select(i => i.S("id")));
    }

    // conferida de novo (agora ou depois de aplicar): relê; o que a pessoa já tinha escolhido nos interruptores continua
    void Conferida(string nome, JsonNode area) { if (nome == AREA) _ = Recarrega(); }

    void MostraAndamento()
    {
        andamento.Text = Conferencia.NaFila(AREA) ? "Conferindo o que abre agora… Pode mexer: a lista só troca o que mudou." :
            itens.Select(i => i.D("ja_idade_h")).OfType<double>().DefaultIfEmpty(-1).Max() is double h && h >= 0 ? $"Conferido há {(h < 1 ? Math.Max(1, (int)(h * 60)) + " min" : (int)h + " h")}." : "";
    }

    void Desenha(Control cab)
    {
        var abrem = itens.Where(i => i.B("ja") != true).ToList();
        var sugeridos = abrem.Where(i => i.B("marcado")).ToList();
        double atraso = sugeridos.Sum(i => i?["dados"].D("boot_s") ?? 0);
        foreach (var i in abrem) pedidos.TryAdd(i.S("id"), false);

        // dois números só (o de sugeridos já está no botão logo abaixo: nada repetido)
        var numeros = S(Celulas(
            Numero("Abrem com o Windows", Num(abrem.Count), abrem.Count == 1 ? "programa" : "programas", "que o Katharos pode desligar", Tema.Apagado),
            Numero("Atraso medido no boot", atraso > 0 ? Num(atraso, 1) : "-", atraso > 0 ? "s" : "", atraso > 0 ? "só dos sugeridos, medido pelo Windows" : "o Windows ainda não mediu", Tema.Apagado)));

        Control? topo = null;
        if (sugeridos.Count > 0)
            topo = S(new Grid
            {
                ColumnDefinitions = new ColumnDefinitions("*,Auto"), Margin = new Thickness(32, 20),
                Children = { new StackPanel { Spacing = 3, VerticalAlignment = VerticalAlignment.Center, Children = {
                                 T("Desligar os que não preciso", null, Tema.Osso, 16).Com(t => t.FontWeight = FontWeight.SemiBold),
                                 T("Antivírus, drivers e o que é do Windows ficam sempre.", "rotulo", quebra: true) } },
                             Botao($"Desligar {sugeridos.Count}", true, async () => await Aplica(sugeridos)).Com(b => Grid.SetColumn(b, 1)) },
            });

        var lista = new StackPanel { Children = { Subtitulo("Abrem agora", null, "inicializacao"), andamento.Com(t => { if (t.Parent is Panel pp) pp.Children.Remove(t); t.Margin = new Thickness(32, -6, 32, 10); }) } };
        if (abrem.Count == 0) lista.Children.Add(Linha("Nada para desligar", "Só abre com o Windows o que precisa abrir.", Etiqueta("ok", Tema.Verde)));
        foreach (var i in abrem.OrderByDescending(i => i.B("marcado")).ThenByDescending(i => i?["dados"].D("boot_s") ?? 0)) lista.Children.Add(Programa(i));

        // os que o Katharos desligou: o interruptor volta ("Religar") pelo desfazer do item
        var pac = aplicado.A("pacotes").FirstOrDefault(p => p.S("pacote") == AREA);
        Control? desligados = null;
        if (pac != null && pac.A("itens").Any())
        {
            var porItem = pac.A("por_item").Select(x => x.ToString()).ToHashSet();
            var p = new StackPanel { Children = { Subtitulo("Desligados pelo Katharos", null, "desligar") } };
            foreach (var id in pac.A("itens").Select(x => x.ToString()))
            {
                string nome = pac?["titulos"]?[id]?.ToString() ?? (id.StartsWith("ini:") ? id[4..] : id);
                Control acao = porItem.Contains(id) ? Botao("Religar", false, async () => await Religa(id, nome))
                                                    : T("volta com a área inteira, no Desfazer", "rotulo", tamanho: 12.5);
                p.Children.Add(Linha(nome, "não abre sozinho · desde " + Quando(pac.S("quando")), Etiqueta("desligado", Tema.Apagado), acao, "desligar"));
            }
            desligados = G(p);
        }

        aplicar = Botao("Aplicar", true, async () => await Aplica(itens.Where(i => pedidos.GetValueOrDefault(i.S("id"))).ToList()));
        if (resumo.Parent is Panel pr) pr.Children.Remove(resumo);
        barra.Child = new Grid { ColumnDefinitions = new ColumnDefinitions("*,Auto"), Children = {
            new StackPanel { Spacing = 2, VerticalAlignment = VerticalAlignment.Center, Children = { resumo } },
            aplicar.Com(b => Grid.SetColumn(b, 1)) } };
        Monta(cab, numeros, topo, G(lista), desligados);
        Conta();
    }

    Control Programa(JsonNode i)
    {
        string id = i.S("id");
        var dd = i?["dados"];
        string nome = dd.S("nome", i.S("titulo")), onde = dd.S("onde"), porque = i.S("explica");
        // "Programa de chat: abre sozinho. (registro: C:\...)": a primeira frase basta na linha; o caminho fica na dica
        string curto = porque.Split(". (")[0].TrimEnd('.');
        var sw = new ToggleSwitch { IsChecked = !pedidos.GetValueOrDefault(id), OnContent = "abre", OffContent = "não abre", VerticalAlignment = VerticalAlignment.Center };
        sw.IsCheckedChanged += (_, _) => { pedidos[id] = sw.IsChecked != true; Conta(); };
        var meio = new StackPanel { Spacing = 3, VerticalAlignment = VerticalAlignment.Center };
        var linha1 = new StackPanel { Orientation = Orientation.Horizontal, Spacing = 8, Children = { T(nome, null, Tema.Osso, 15, false).Com(t => t.FontWeight = FontWeight.SemiBold) } };
        if (i.B("marcado")) linha1.Children.Add(Etiqueta("sugerido", Tema.Ambar));
        if (i.S("nota") != "") linha1.Children.Add(Etiqueta("cuidado", Tema.Vermelho));
        meio.Children.Add(linha1);
        meio.Children.Add(T(Maiuscula(curto) + (onde != "" ? " · " + onde : ""), "rotulo", tamanho: 13, quebra: true));
        if (i.S("nota") != "") meio.Children.Add(T(Maiuscula(i.S("nota")) + ".", null, Tema.Ambar, 13, true));
        ToolTip.SetTip(meio, porque);
        var boot = dd.D("boot_s") is double b && b > 0 ? T($"+{Num(b, 1)} s", null, b >= 2 ? Tema.Ambar : Tema.Texto, 14).Com(t => { t.FontFamily = Tema.Mono; t.VerticalAlignment = VerticalAlignment.Center; ToolTip.SetTip(t, "atraso no boot medido pelo Windows"); })
                                                     : T("—", null, Tema.Apagado, 14).Com(t => { t.VerticalAlignment = VerticalAlignment.Center; ToolTip.SetTip(t, "o Windows ainda não mediu o atraso deste"); });
        var g = new Grid { ColumnDefinitions = new ColumnDefinitions("Auto,*,80,Auto") };
        g.Children.Add(IconeDoPrograma.De(dd.S("exe"), 22, nome).Com(c => { c.VerticalAlignment = VerticalAlignment.Center; c.Margin = new Thickness(0, 0, 16, 0); }));
        g.Children.Add(meio.Com(m => Grid.SetColumn(m, 1)));
        g.Children.Add(boot.Com(t => { Grid.SetColumn(t, 2); t.HorizontalAlignment = HorizontalAlignment.Right; t.Margin = new Thickness(0, 0, 18, 0); }));
        g.Children.Add(sw.Com(x => Grid.SetColumn(x, 3)));
        return new Border { Padding = new Thickness(32, 14), BorderBrush = Tema.Linha, BorderThickness = new Thickness(0, 1, 0, 0), Child = g };
    }

    void Conta()
    {
        int n = pedidos.Count(x => x.Value);
        resumo.Text = n == 0 ? "Nada para mudar" : $"{n} {(n == 1 ? "programa deixa" : "programas deixam")} de abrir com o Windows";
        aplicar.Content = n == 0 ? "Aplicar" : $"Desligar {n}";
        aplicar.IsEnabled = n > 0;
        barra.IsVisible = n > 0;
    }

    async Task Aplica(List<JsonNode> quais)
    {
        var esc = quais.Select(i => new Escolhido(AREA, "inicialização", i.S("id"), i?["dados"].S("nome", i.S("titulo")) ?? i.S("titulo"), i.B("sem_volta"))).ToList();
        if (await Aplicacao.Aplica(esc, () => { pedidos.Clear(); _ = Recarrega(); }, Abre)) pedidos.Clear();
    }

    async Task Religa(string id, string nome)
    {
        var j = Janela.Atual!;
        if (!await j.Confirma($"Religar {nome}?", T("Ele volta a abrir junto com o Windows, como antes. O Windows vai pedir permissão de administrador.", "sub", quebra: true), "Religar")) return;
        j.MostraCaixa(Janela.Caixa("Religando", Andamento("Esperando a permissão de administrador do Windows").painel));
        Trabalho.Comeca("Religando…");
        try
        {
            var r = await Servico.Muda("desfazer", new { itens = new JsonObject { [AREA] = new JsonArray(JsonValue.Create(id)) } });
            Conferencia.Pede(new[] { AREA }, frente: true, forcar: true);
            bool ok = r.A("pacotes").All(x => x.B("ok"));
            j.MostraCaixa(Janela.Caixa(ok ? "Religado" : "Não voltou", T(ok ? $"{nome} volta a abrir com o Windows." : "O detalhe está no relatório do Katharos.", "sub"),
                Botao("Fechar", true, () => { j.FechaCaixa(); _ = Recarrega(); })), true);
        }
        catch (Exception e) { MostraErro(e, "Não deu para religar"); }
        finally { Trabalho.Termina(); }
    }
}
