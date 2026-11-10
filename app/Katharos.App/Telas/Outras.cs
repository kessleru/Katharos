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

        var lista = new StackPanel { Children = { Subtitulo("Sessões") } };
        foreach (var s in ss.Take(30))
        {
            string fps = s.D("fps_med") is double f ? $" · {Num(f)} FPS médio · 1% mais lento {Num(s.D("fps_1low"))}" : "";
            lista.Children.Add(Linha($"{s.S("jogo")} · {Num(s.D("min"))} min{fps}", $"{Quando(s.S("inicio"))} · limite: {Limite(s.S("principal"))}" +
                                     (s.D("temp_cpu_max") is double tc ? $" · CPU até {Num(tc)} °C" : "")));
        }
        Monta(cab, numeros, comp, S(lista));
    }

    static string Limite(string p) => p switch
    {
        "gpu" => "placa de vídeo", "cpu" => "CPU", "freio" => "CPU freando", "ram" => "memória RAM", "vram" => "memória da placa", "disco" => "disco",
        "calor" => "calor", "" => "-", _ => "nada no limite",
    };
}

/// <summary>Sugestões: o que a central de inteligência propõe, com o número que justifica, e o que ela previu e aconteceu.</summary>
public class Sugestoes : Tela
{
    protected override async Task Carrega()
    {
        var cab = Cabecalho("Sugestões", "O que a central propõe com base no que o seu PC mediu. Nada muda sem você.");
        Monta(cab, Carregando("Pensando").secao);
        var d = await Servico.Le("sugestoes");
        var res = d.A("resultados").ToList();
        var props = d.A("propostas").ToList();
        if (props.Count == 0 && res.Count == 0)
        {
            Monta(cab, Vazio("Nenhuma sugestão agora", "A central precisa de alguns dias de medida (com o acompanhamento ligado) para propor algo com confiança. Ela não sugere nada sem número.",
                             Botao("Ver o acompanhamento", false, () => Abre("aovivo"))));
            return;
        }
        Control? resultados = null;
        if (res.Count > 0)
        {
            var p = new StackPanel { Children = { Subtitulo("O que eu previ e o que aconteceu", "Sua resposta ensina a central: o que não ajudou pesa menos da próxima vez.") } };
            foreach (var r in res)
            {
                string id = r.S("id");
                var bt = new StackPanel { Orientation = Orientation.Horizontal, Spacing = 8 };
                bt.Children.Add(Botao("Ajudou", false, async () => { await Servico.Le("responder", new { id, resposta = "sim" }); await Recarrega(); }));
                bt.Children.Add(Botao("Não ajudou", false, async () => { await Servico.Le("responder", new { id, resposta = "nao" }); await Recarrega(); }));
                p.Children.Add(Linha(r.S("titulo"), r.S("texto") is var tx && tx != "" ? tx : r.S("veredito"), null, bt));
            }
            resultados = S(p);
        }
        var lista = new StackPanel { Children = { Subtitulo("Propostas") } };
        foreach (var x in props)
        {
            string conf = x.S("confianca"), id = x.S("id"), cmd = x.S("comando");
            var cor = conf == "alta" ? Tema.Verde : conf == "media" ? Tema.Ambar : Tema.Apagado;
            var bt = new StackPanel { Orientation = Orientation.Horizontal, Spacing = 8 };
            bt.Children.Add(Botao("Não me importa", false, async () => { await Servico.Le("responder", new { id, resposta = "nao-importa" }); await Recarrega(); }));
            if (cmd != "") bt.Children.Add(Botao("Ver", true, () => Abre(cmd.StartsWith("desfazer") ? "desfazer" : cmd == "segundo-plano" ? "aovivo" : cmd == "raiox" ? "raiox" : "otimizar:" + cmd)));
            lista.Children.Add(Linha(x.S("titulo"), x.S("porque"), Etiqueta("confiança " + (conf == "media" ? "média" : conf), cor), bt));
        }
        Monta(cab, resultados, S(lista));
    }
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
            lista.Children.Add(Linha($"{char.ToUpper(titulo[0]) + titulo[1..]}: {n} {(n == 1 ? "item" : "itens")}", $"aplicado {Quando(p.S("quando"))}" + (p.B("desfaz") ? "" : " · remoções não voltam por aqui"), null, acao));
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
    static readonly string[] Mostrar = { "modo", "confirmar", "tempo-real", "avisos", "coleta-em-jogo" };

    protected override async Task Carrega()
    {
        var cab = Cabecalho("Configurações", "Valem para as janelas e para o terminal.");
        Monta(cab, Carregando("Lendo").secao);
        var d = await Servico.Le("config_ler");
        var lista = new StackPanel { Children = { Subtitulo("Preferências") } };
        foreach (var k in Mostrar)
        {
            var c = d?[k];
            if (c == null) continue;
            string atual = c.S("valor");
            var ops = new StackPanel { Orientation = Orientation.Horizontal, Spacing = 6 };
            foreach (var o in c.A("opcoes").Select(x => x.ToString()))
            {
                var b = Botao(o, o == atual, async () => { await Servico.Le("config_gravar", new { chave = k, valor = o }); await Recarrega(); });
                ops.Children.Add(b);
            }
            lista.Children.Add(Linha(char.ToUpper(c.S("rotulo")[0]) + c.S("rotulo")[1..], c.S("explica"), null, ops));
        }
        Monta(cab, S(lista));
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
