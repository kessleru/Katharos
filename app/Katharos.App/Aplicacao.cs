using System.Text.Json.Nodes;
using Avalonia;
using Avalonia.Controls;
using Avalonia.Layout;
using Avalonia.Threading;
using static Katharos.App.Ui;

namespace Katharos.App;

/// <summary>Um item escolhido para aplicar: a área (pacote), o id e o que aparece na confirmação.</summary>
public record Escolhido(string Area, string AreaTitulo, string Id, string Titulo, bool SemVolta);

/// <summary>
/// Aplicar, de qualquer lugar (Otimizar, "Aplicar esta correção", inicialização): confirmação com o que muda, permissão do Windows,
/// ponto de restauração, progresso por item, o resultado conferido no Windows e, em mudança de risco, o "está tudo funcionando?".
/// Manda ao motor exatamente os ids escolhidos (nada além). Depois, confere de novo só as áreas mexidas, em segundo plano.
/// </summary>
public static class Aplicacao
{
    /// <summary>true se aplicou (mesmo com pontos para olhar); false se a pessoa voltou ou deu erro antes.</summary>
    public static async Task<bool> Aplica(IReadOnlyList<Escolhido> itens, Action? depois = null, Action<string>? abre = null)
    {
        var j = Janela.Atual!;
        if (itens.Count == 0) return false;
        var aviso = await Servico.Le("aviso");
        if (!aviso.B("aceito")) { abre?.Invoke("aviso:otimizar"); return false; }
        int semVolta = itens.Count(i => i.SemVolta);
        var corpo = new StackPanel { Spacing = 8 };
        // poucos itens: um por linha (a pessoa vê exatamente o que muda); muitos: por área
        if (itens.Count <= 6)
            foreach (var i in itens) corpo.Children.Add(T("· " + Maiuscula(i.Titulo), null, Tema.Texto, 14, true));
        else
            foreach (var g in itens.GroupBy(i => i.Area))
                corpo.Children.Add(T($"{Maiuscula(g.First().AreaTitulo)}: {g.Count()} {(g.Count() == 1 ? "item" : "itens")}", null, Tema.Texto, 14));
        if (semVolta > 0) corpo.Children.Add(T($"{semVolta} {(semVolta == 1 ? "item não volta" : "itens não voltam")} pelo Desfazer (remoções).", null, Tema.Vermelho, 13.5, true));
        if (!await j.Confirma($"Aplicar {itens.Count} {(itens.Count == 1 ? "mudança" : "mudanças")}?", corpo, $"Aplicar {itens.Count}")) return false;

        var (painel, passo, barra) = Andamento("Esperando a permissão de administrador do Windows",
            "Se o pedido do Windows não aparecer na frente, ele pode estar piscando na barra de tarefas. Pode usar o PC. Não desligue até terminar.");
        var item = T("", "rotulo", quebra: true);
        painel.Children.Insert(2, item);
        j.MostraCaixa(Janela.Caixa("Aplicando", painel));
        Trabalho.Comeca("Aplicando mudanças…");
        var areas = itens.Select(i => i.Area).Distinct().ToList();
        try
        {
            var sel = new JsonObject();
            foreach (var g in itens.GroupBy(i => i.Area)) sel[g.Key] = new JsonArray(g.Select(i => (JsonNode)JsonValue.Create(i.Id)!).ToArray());
            var r = await Servico.Muda("aplicar", new { itens = sel }, (t, d) => Dispatcher.UIThread.Post(() =>
            {
                if (t == "etapa") { passo.Text = Maiuscula(d.S("texto")); if (painel.Children.Count > 4) painel.Children.RemoveAt(4); }   // permissão dada: a dica sai
                else if (t == "pacote") passo.Text = $"{Maiuscula(d.S("titulo"))} ({Num(d.D("n"))} de {Num(d.D("de"))})";
                else if (t == "progresso" && d.D("de") is double de && de > 0) { barra.IsIndeterminate = false; barra.Maximum = de; barra.Value = d.D("n") ?? 0; item.Text = d.S("item"); }
            }));
            Conferencia.Pede(areas, frente: true, forcar: true);
            await MostraResultado(r, depois, abre);
            return true;
        }
        catch (ErroDoMotor e) when (e.Codigo == "precisa_aceite") { j.FechaCaixa(); abre?.Invoke("aviso:otimizar"); return false; }
        catch (Exception e)
        {
            Conferencia.Pede(areas, frente: true, forcar: true);   // algo pode ter mudado antes do erro
            MostraErro(e, depois: "Nada foi marcado como feito. O que chegou a mudar antes do erro volta pela tela Desfazer.");
            return false;
        }
        finally { Trabalho.Termina(); }
    }

    static async Task MostraResultado(JsonNode? r, Action? depois, Action<string>? abre)
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
            bloco.Children.Add(new Grid { ColumnDefinitions = new ColumnDefinitions("*,Auto"), Children = {
                T(Maiuscula(p.S("titulo")), null, Tema.Osso, 15),
                T(f == 0 ? "nada mudou" : $"✓ {f} {(f == 1 ? "mudança" : "mudanças")}", null, f == 0 ? Tema.Apagado : Tema.Verde, 14).Com(t => { t.FontFamily = Tema.Mono; Grid.SetColumn(t, 1); }) } });
            foreach (var x in erros.Take(4)) bloco.Children.Add(T("erro: " + x, null, Tema.Vermelho, 13, true));
            foreach (var x in nao.Take(4)) bloco.Children.Add(T("não ficou (conferido no Windows): " + x, null, Tema.Ambar, 13, true));
            foreach (var x in avisos.Take(3)) bloco.Children.Add(T("aviso: " + x, "rotulo", tamanho: 13, quebra: true));
            if (p.D("liberado") is double lib && lib > 0) bloco.Children.Add(T($"liberou {Num(lib / 1073741824.0, 1)} GB", null, Tema.Verde, 13));
            if (p.S("medido") != "") bloco.Children.Add(T("Medido agora: " + p.S("medido") + ".", "rotulo", tamanho: 13, quebra: true));
            corpo.Children.Add(bloco);
        }
        string titulo = problemas == 0 ? $"Pronto: {feitos} {(feitos == 1 ? "mudança feita e conferida" : "mudanças feitas e conferidas")}" : $"Feito, com {problemas} {(problemas == 1 ? "ponto" : "pontos")} para olhar";
        corpo.Children.Insert(0, T(problemas == 0 ? "Cada ajuste foi lido de volta no Windows depois de aplicado." : "O resto ficou como pedido; os pontos abaixo dizem o que não ficou e por quê.", "rotulo", quebra: true).Com(t => t.Margin = new Thickness(0, 0, 0, 8)));
        Movimento.Entra(corpo);
        var manter = r.A("perguntar_manter").Select(x => x.ToString()).ToList();
        if (manter.Count > 0) { await PerguntaManter(manter, titulo, corpo, depois); return; }
        j.MostraCaixa(Janela.Caixa(titulo, corpo, new StackPanel { Orientation = Orientation.Horizontal, Spacing = 10, HorizontalAlignment = HorizontalAlignment.Right, Margin = new Thickness(0, 16, 0, 0),
            Children = { Botao("Ver o Desfazer", false, () => { j.FechaCaixa(); abre?.Invoke("desfazer"); }), Botao("Fechar", true, () => { j.FechaCaixa(); depois?.Invoke(); }) } }), true);
    }

    /// <summary>
    /// Como a troca de resolução do Windows: depois de mudança de risco, "está tudo funcionando?". O tempo para desfazer sozinho (3 min)
    /// só corre com a pessoa no PC: aplicação longa termina com ela longe (foi tomar água), e voltar e achar tudo desfeito era pior que
    /// o risco. Longe (mais de 1 min sem mexer no mouse ou no teclado), o relógio para e espera; mexeu, ele volta a correr. Se a
    /// mudança quebrou a tela ou a rede, a pessoa mexe no mouse para tentar e o relógio corre e desfaz.
    /// </summary>
    static async Task PerguntaManter(List<string> pacotes, string titulo, Control corpo, Action? depois)
    {
        var j = Janela.Atual!;
        const int Total = 180;
        int resta = Total;
        var conta = T("", null, Tema.Ambar, 14, true);
        var tcs = new TaskCompletionSource<bool>();
        var rel = new DispatcherTimer { Interval = TimeSpan.FromSeconds(1) };
        void Texto()
        {
            bool longe = Presenca.OciosoSegundos() >= 60;
            conta.Text = longe
                ? "Esperando você voltar."
                : $"Sem resposta em {resta / 60}:{resta % 60:00}, desfaz sozinho.";
        }
        Texto();
        rel.Tick += (_, _) =>
        {
            if (Presenca.OciosoSegundos() < 60 && --resta <= 0) { tcs.TrySetResult(false); return; }
            Texto();
        };
        rel.Start();
        Presenca.ChamaAtencao(j);
        var p = new StackPanel { Spacing = 14, Children = { corpo, T("Está tudo funcionando?", "forte", tamanho: 17), conta } };
        j.MostraCaixa(Janela.Caixa(titulo, p, new StackPanel { Orientation = Orientation.Horizontal, Spacing = 10, HorizontalAlignment = HorizontalAlignment.Right, Margin = new Thickness(0, 16, 0, 0),
            Children = { Botao("Desfazer agora", false, () => tcs.TrySetResult(false)), Botao("Manter", true, () => tcs.TrySetResult(true)) } }));
        bool manter = await tcs.Task;
        rel.Stop();
        if (manter) { j.FechaCaixa(); depois?.Invoke(); return; }
        j.MostraCaixa(Janela.Caixa("Desfazendo", Andamento("Voltando " + string.Join(", ", pacotes) + " ao que era antes").painel));
        Trabalho.Comeca("Desfazendo…");
        try
        {
            var r = await Servico.Muda("desfazer", new { pacotes });
            Conferencia.Pede(pacotes, frente: true, forcar: true);
            bool ok = r.A("pacotes").All(x => x.B("ok"));
            j.MostraCaixa(Janela.Caixa(ok ? "Desfeito" : "Desfeito em parte", T(ok ? "Voltou ao que era antes." : "Algo não voltou: abra o Desfazer para ver.", "sub"), Botao("Fechar", true, () => { j.FechaCaixa(); depois?.Invoke(); })), true);
        }
        catch (Exception e) { MostraErro(e, "Não deu para desfazer", "As mudanças continuam aplicadas. Tente de novo pela tela Desfazer."); }
        finally { Trabalho.Termina(); }
    }

    /// <summary>
    /// "Aplicar esta correção": uma caixa só com os itens de uma área que ainda não estão feitos, o que cada um muda, como desfazer e um
    /// botão. Os que o modo escolhido recomenda vêm marcados; a pessoa tira o que não quiser. Nunca abre o Otimizar com o modo inteiro.
    /// </summary>
    static void Solta(Control c) { if (c.Parent is Panel p) p.Children.Remove(c); else if (c.Parent is ContentControl cc) cc.Content = null; else if (c.Parent is Decorator d) d.Child = null; }

    public static async Task Correcao(string area, string porque, Action<string>? abre, Action? depois = null)
    {
        var j = Janela.Atual!;
        var corpo = new StackPanel { Spacing = 10, MaxWidth = 640 };
        corpo.Children.Add(T("Lendo o que esta correção muda…", "rotulo"));
        j.MostraCaixa(Janela.Caixa("Aplicar esta correção", corpo, null), true);
        JsonNode? cfg, d;
        string modo;
        try
        {
            cfg = Servico.Guardado("config_ler") ?? await Servico.Le("config_ler");
            modo = cfg?["modo"].S("valor", "equilibrado") ?? "equilibrado";
            var p = new { modo, conferir = false, areas = new[] { area } };
            d = Servico.Guardado("itens", p) ?? await Servico.Le("itens", p);
        }
        catch (Exception e) { j.FechaCaixa(); MostraErro(e, "Não deu para abrir a correção"); return; }
        var a = d.A("areas").FirstOrDefault();
        // a primeira caixa ("Lendo…") ainda segura o corpo: solta antes de pôr numa caixa nova (relatório KTH-MM9NKS, 4.3.0:
        // "The control StackPanel already has a visual parent")
        Solta(corpo);
        var faltam = a.A("itens").Where(i => !i.B("ja") && !i.B("bloqueado")).ToList();
        corpo.Children.Clear();
        if (porque != "") corpo.Children.Add(T(porque, "sub", quebra: true));
        if (a == null || faltam.Count == 0)
        {
            corpo.Children.Add(T(a == null ? "Esta área não tem itens neste PC." : a.A("itens").Any(i => !i.B("ja")) ? "O que falta o Windows não deixa mudar." : "Tudo desta área já está assim neste PC.", null, Tema.Verde, 14, true));
            j.MostraCaixa(Janela.Caixa("Aplicar esta correção", corpo, Botao("Fechar", true, j.FechaCaixa).Com(b => b.HorizontalAlignment = HorizontalAlignment.Right)), true);
            return;
        }
        string tituloArea = a.S("titulo", area);
        corpo.Children.Add(T(Maiuscula(tituloArea), "rotulo"));
        var caixas = new List<(CheckBox c, JsonNode i)>();
        var botao = Botao("Aplicar", true, () => { });
        void Conta()
        {
            int n = caixas.Count(x => x.c.IsChecked == true);
            botao.Content = n == 0 ? "Aplicar" : $"Aplicar {n} {(n == 1 ? "mudança" : "mudanças")}";
            botao.IsEnabled = n > 0;
        }
        // marcados primeiro (o que o modo recomenda), o resto embaixo
        foreach (var i in faltam.OrderByDescending(i => i.B("marcado")))
        {
            // igual ao Otimizar: nome e o que ganha; o que perde e a atenção em "detalhes"; "sem volta" como etiqueta
            var tx = new StackPanel { Spacing = 2, Margin = new Thickness(4, 0, 0, 0) };
            var nome = new WrapPanel { Children = { T(Maiuscula(i.S("titulo")), null, Tema.Osso, 15, true).Com(t => t.Margin = new Thickness(0, 0, 8, 0)) } };
            if (i.S("alerta") != "") nome.Children.Add(Etiqueta("atenção", Tema.Ambar));
            if (i.B("sem_volta")) nome.Children.Add(Etiqueta("sem volta", Tema.Vermelho).Com(e => e.Margin = new Thickness(6, 0, 0, 0)));
            tx.Children.Add(nome);
            if (i.S("ganho") != "") tx.Children.Add(T("Ganha: " + i.S("ganho"), null, Tema.Verde, 13, true));
            tx.Children.Add(T("Perde: " + (i.S("custo") != "" && i.S("custo") != "nenhum" ? Maiuscula(i.S("custo")) : "nada que você note."), null, Tema.Osso, 13, true));
            var det = new List<string>();
            if (i.S("custo") != "" && i.S("custo") != "nenhum") det.Add("Perde: " + i.S("custo"));
            if (i.S("alerta") != "") det.Add("Atenção: " + i.S("alerta"));
            if (i.B("sem_volta")) det.Add("Sem volta: o Desfazer não traz de volta.");
            if (det.Count > 0) tx.Children.Add(Detalhes(T(string.Join("\n", det), "rotulo", tamanho: 13, quebra: true)));
            var c = new CheckBox { Content = tx, IsChecked = i.B("marcado"), VerticalAlignment = VerticalAlignment.Top };
            c.IsCheckedChanged += (_, _) => Conta();
            caixas.Add((c, i));
            corpo.Children.Add(c);
        }
        Conta();
        botao.Click += async (_, _) =>
        {
            var esc = caixas.Where(x => x.c.IsChecked == true).Select(x => new Escolhido(area, tituloArea, x.i.S("id"), x.i.S("titulo"), x.i.B("sem_volta"))).ToList();
            await Aplica(esc, depois, abre);
        };
        var rodape = new StackPanel { Orientation = Orientation.Horizontal, Spacing = 10, HorizontalAlignment = HorizontalAlignment.Right, Margin = new Thickness(0, 14, 0, 0),
            Children = { Botao("Ver a área inteira", false, () => { j.FechaCaixa(); abre?.Invoke("otimizar:" + area); }), Botao("Voltar", false, j.FechaCaixa), botao } };
        j.MostraCaixa(Janela.Caixa("Aplicar esta correção", corpo, rodape), true);
    }
}

/// <summary>Se a pessoa está no PC (há quanto tempo não mexe no mouse ou no teclado) e como chamar a atenção dela sem roubar o foco.</summary>
public static class Presenca
{
    [System.Runtime.InteropServices.StructLayout(System.Runtime.InteropServices.LayoutKind.Sequential)] struct ULTIMA { public uint tamanho; public uint quando; }
    [System.Runtime.InteropServices.DllImport("user32.dll")] static extern bool GetLastInputInfo(ref ULTIMA u);
    [System.Runtime.InteropServices.StructLayout(System.Runtime.InteropServices.LayoutKind.Sequential)] struct PISCA { public uint tamanho; public IntPtr janela; public uint como, vezes, intervalo; }
    [System.Runtime.InteropServices.DllImport("user32.dll")] static extern bool FlashWindowEx(ref PISCA p);

    public static double OciosoSegundos()
    {
        if (!OperatingSystem.IsWindows()) return 0;
        try
        {
            var u = new ULTIMA { tamanho = 8 };
            return GetLastInputInfo(ref u) ? Math.Max(0, ((uint)Environment.TickCount - u.quando) / 1000.0) : 0;
        }
        catch { return 0; }
    }

    /// <summary>Pisca o botão na barra de tarefas até a pessoa olhar (o mesmo aviso que o Windows usa para "precisa de você").</summary>
    public static void ChamaAtencao(Window j)
    {
        if (!OperatingSystem.IsWindows() || j.IsActive) return;
        try
        {
            var h = j.TryGetPlatformHandle()?.Handle ?? IntPtr.Zero;
            if (h == IntPtr.Zero) return;
            var p = new PISCA { tamanho = (uint)System.Runtime.InteropServices.Marshal.SizeOf<PISCA>(), janela = h, como = 3 | 12, vezes = 0, intervalo = 0 };
            FlashWindowEx(ref p);
        }
        catch { }
    }
}
