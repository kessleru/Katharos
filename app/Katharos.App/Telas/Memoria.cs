using System.Diagnostics;
using System.Text.Json.Nodes;
using Avalonia;
using Avalonia.Controls;
using Avalonia.Layout;
using Avalonia.Media;
using Katharos.App.Controles;
using static Katharos.App.Ui;

namespace Katharos.App.Telas;

/// <summary>
/// Quem usa a RAM: um programa por linha, com o que é, quanto usa agora, a média e o pico (24 h e 7 dias) e o minigráfico do dia. Em
/// cima, se a RAM está cheia de verdade (memória prometida e comprimida), não só "alta". As ações são poucas e seguras: tirar da
/// inicialização, fechar (só quando você clica, e do jeito do X da janela) e abrir a página do Windows para desinstalar. Windows, drivers,
/// proteção e anti-cheat aparecem sem nenhuma ação; o que o Katharos não conhece diz "não conheço", sem palpite.
/// </summary>
public class Memoria : Tela
{
    bool todos;

    protected override async Task Carrega()
    {
        var cab = Cabecalho("Memória", "Quem está usando a RAM.");
        var g = Servico.Guardado("memoria_programas");
        if (g != null) Desenha(cab, g); else Monta(cab, Carregando("Lendo a memória dos últimos dias").secao);
        var d = await Servico.Le("memoria_programas");
        if (g == null || g.ToJsonString() != d?.ToJsonString()) Desenha(cab, d);
    }

    void Desenha(Control cab, JsonNode? d)
    {
        var ps = d.A("programas").ToList();
        if (ps.Count == 0)
        {
            Monta(cab, Vazio("Ainda sem medida", "Com o acompanhamento ligado, em alguns minutos aparece aqui quem usa a RAM. Ele é leve: lê a lista de programas uma vez por minuto.",
                             Botao("Ver o acompanhamento", true, () => Abre("aovivo"))));
            return;
        }
        var pr = d?["pressao"];
        string nivel = pr.S("nivel");
        var cor = nivel == "cheia" ? Tema.Vermelho : nivel == "apertada" ? Tema.Ambar : nivel == "folgada" ? Tema.Verde : Tema.Apagado;
        var estado = S(Celulas(
            Numero("A RAM está", nivel switch { "cheia" => "cheia", "apertada" => "apertada", "folgada" => "folgada", _ => "-" }, "",
                   nivel switch { "cheia" => "o PC já usa o disco no lugar da RAM", "apertada" => "mais um programa pesado engasga", "folgada" => "sobra memória", _ => "ainda sem medida" }, cor),
            Numero("Prometida", pr.D("commit_pct") is double c ? Num(c) : "-", "%", "RAM e arquivo de paginação juntos", (pr.D("commit_pct") ?? 0) >= 90 ? Tema.Vermelho : Tema.Apagado),
            Numero("Comprimida", pr.D("comprimida_gb") is double z ? Num(z, 1) : "-", "GB", "o Windows comprime o que não cabe", Tema.Apagado)));

        // a frase inteira do "cheia de verdade" fica numa linha só, embaixo dos números (na célula ela cortava)
        var frase = S(new StackPanel { Margin = new Thickness(32, 14), Children = { Item(pr.S("texto"), cor) } });
        var lista = new StackPanel { Children = { Subtitulo("Quem usa", $"Desde {Quando(d.S("desde"))} · {Num(d.D("ram_total_gb"))} GB no total", "memoria") } };
        foreach (var x in (todos ? ps : ps.Take(10))) lista.Children.Add(Programa(x));
        if (!todos && ps.Count > 10)
            lista.Children.Add(new Border { Padding = new Thickness(32, 10, 32, 14), BorderBrush = Tema.Linha, BorderThickness = new Thickness(0, 1, 0, 0),
                Child = Link($"Ver os outros {ps.Count - 10}", () => { todos = true; Desenha(cab, d); }) });
        Monta(cab, estado, frase, G(lista));
    }

    Control Programa(JsonNode x)
    {
        string proc = x.S("processo"), nome = x.S("nome", proc), classe = x.S("classe");
        static string Mb(double? v) => v is double m ? (m >= 1024 ? Num(m / 1024, 1) + " GB" : Num(m) + " MB") : "-";
        var meio = new StackPanel { Spacing = 3, VerticalAlignment = VerticalAlignment.Center };
        var l1 = new StackPanel { Orientation = Orientation.Horizontal, Spacing = 8, Children = { T(nome, null, Tema.Osso, 15).Com(t => t.FontWeight = FontWeight.SemiBold) } };
        if (classe == "protegido") l1.Children.Add(Etiqueta("do Windows", Tema.Apagado));
        if (classe == "desconhecido") l1.Children.Add(Etiqueta("não conheço", Tema.Apagado));
        meio.Children.Add(l1);
        string oque = x.S("o_que_e");
        // o que o programa é aparece com o mouse parado no nome (na coluna estreita virava três linhas)
        ToolTip.SetTip(l1, Maiuscula(oque == nome ? x.S("faz") : oque) + (proc.ToLowerInvariant() != nome.ToLowerInvariant() ? $" · {proc}" : ""));
        ToolTip.SetShowDelay(l1, 400);
        var acoes = new WrapPanel { Margin = new Thickness(-8, 2, 0, 0) };
        foreach (var a in x.A("acoes").Select(a => a.ToString()))
            acoes.Children.Add(a switch
            {
                "inicializacao" => Link("Tirar da inicialização", () => Abre("inicializacao")),
                "fechar" => Link("Fechar", async () => await Fecha(proc, nome)),
                "desinstalar" => Link("Desinstalar…", () => AbreNoWindows("ms-settings:appsfeatures")),
                _ => new Control(),
            });
        if (acoes.Children.Count > 0) meio.Children.Add(acoes);

        var numeros = new StackPanel { Spacing = 2, HorizontalAlignment = HorizontalAlignment.Right, VerticalAlignment = VerticalAlignment.Center, Children = {
            T(Mb(x.D("agora_mb")), null, Tema.Osso, 17).Com(t => { t.FontFamily = Tema.Mono; t.HorizontalAlignment = HorizontalAlignment.Right; }),
            T($"média {Mb(x.D("media_24h_mb"))} · pico {Mb(x.D("pico_24h_mb"))}", "rotulo", tamanho: 12.5).Com(t => { t.HorizontalAlignment = HorizontalAlignment.Right; ToolTip.SetTip(t, $"7 dias: média {Mb(x.D("media_7d_mb"))}, pico {Mb(x.D("pico_7d_mb"))}"); }) } };
        var mini = new Minigrafico { Valores = x.A("horas").Select(v => v is JsonValue jv && jv.TryGetValue(out double dv) ? dv : (double?)null).ToArray(), Width = 90, Height = 30,
                                     VerticalAlignment = VerticalAlignment.Center, Margin = new Thickness(18, 0, 18, 0) };
        ToolTip.SetTip(mini, "últimas 24 h, uma média por hora");
        var g = new Grid { ColumnDefinitions = new ColumnDefinitions("Auto,*,Auto,Auto") };
        g.Children.Add(IconeDoPrograma.Inicial(nome, 24).Com(c => { c.VerticalAlignment = VerticalAlignment.Top; c.Margin = new Thickness(0, 2, 16, 0); }));
        g.Children.Add(meio.Com(m => Grid.SetColumn(m, 1)));
        g.Children.Add(mini.Com(m => Grid.SetColumn(m, 2)));
        g.Children.Add(numeros.Com(n => Grid.SetColumn(n, 3)));
        return new Border { Padding = new Thickness(32, 14), BorderBrush = Tema.Linha, BorderThickness = new Thickness(0, 1, 0, 0), Child = g };
    }

    /// <summary>
    /// Fecha como o X da janela: pede ao programa para fechar (ele pode perguntar se quer salvar). Nunca força: programa sem janela, ou
    /// que não responde, continua aberto, e a tela diz isso. Só quando a pessoa clica e confirma.
    /// </summary>
    async Task Fecha(string proc, string nome)
    {
        var j = Janela.Atual!;
        if (!await j.Confirma($"Fechar {nome}?", T("Como o X da janela: se tiver algo sem salvar, ele pergunta.", "sub", quebra: true), "Fechar")) return;
        int pedidos = 0;
        if (OperatingSystem.IsWindows())
            foreach (var p in Process.GetProcessesByName(proc))
                using (p) { try { if (p.MainWindowHandle != IntPtr.Zero && p.CloseMainWindow()) pedidos++; } catch { } }
        j.MostraCaixa(Janela.Caixa(pedidos > 0 ? "Pedido enviado" : "Não fechou",
            T(pedidos > 0 ? $"{nome} recebeu o pedido para fechar. A memória dele aparece livre na próxima leitura." : $"{nome} não tem janela aberta para fechar. Ele roda por trás; se não precisa dele, tire da inicialização ou desinstale.", "sub", quebra: true),
            Botao("Fechar", true, j.FechaCaixa)), true);
    }

    static void AbreNoWindows(string alvo)
    {
        try { Process.Start(new ProcessStartInfo(alvo) { UseShellExecute = true }); }
        catch (Exception e) { MostraErro(e, "Não deu para abrir", "Abra Configurações > Aplicativos pelo menu Iniciar."); }
    }
}
