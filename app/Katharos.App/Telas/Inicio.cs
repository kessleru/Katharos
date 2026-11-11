using System.Text.Json.Nodes;
using Avalonia.Controls;
using Avalonia.Layout;
using static Katharos.App.Ui;

namespace Katharos.App.Telas;

/// <summary>Início: como o PC está e o próximo passo. Abre na hora, só com o que já está guardado (nada roda).</summary>
public class Inicio : Tela
{
    protected override async Task Carrega()
    {
        var cab = Cabecalho("Início", "Como está o seu PC e o que fazer agora.");
        // a última leitura aparece na hora; a nova troca quando chegar (só se mudou)
        var g = Servico.Guardado("inicio");
        jogos = Servico.Guardado("sessoes", new { dias = 30 });
        if (g != null) Desenha(cab, g); else Monta(cab, Carregando("Lendo o que já está guardado").secao);
        var d = await Servico.Le("inicio");
        try { jogos = await Servico.Le("sessoes", new { dias = 30 }); } catch (Exception e) { Registro.Escreve("início: sessões: " + e.Message); }
        if (g == null || g.ToJsonString() != d?.ToJsonString()) Desenha(cab, d);
        else if (jogosDesenhados != jogos?.ToJsonString()) Desenha(cab, d);
    }

    JsonNode? jogos;
    string? jogosDesenhados;

    void Desenha(Control cab, JsonNode? d)
    {
        var rx = d?["raiox"];

        // a ação principal: uma só, a que faz mais sentido agora
        Control passo;
        if (rx == null)
            passo = Proximo("Faça o raio-x", "Leva de 1 a 3 minutos e não muda nada. Ele diz o que vale a pena fazer neste PC.",
                            Botao("Fazer o raio-x", true, () => Abre("raiox")));
        else
        {
            var achados = rx.A("achados").ToList();
            int graves = achados.Count(a => a.D("impacto") >= 3);
            passo = achados.Count == 0
                ? Proximo("Nada urgente", "O último raio-x não achou problema. Se quiser ir além, escolha um modo para otimizar.",
                          Botao("Otimizar", true, () => Abre("otimizar")))
                : Proximo(achados.Count == 1 ? "Resolver 1 coisa que o raio-x achou" : $"Resolver {achados.Count} coisas que o raio-x achou",
                          (graves > 0 ? $"{(graves == 1 ? "Uma é grave" : graves + " são graves")}: {achados[0].S("titulo")}." : "Nenhuma é grave.")
                          + (rx.D("resolvidos") is double rs && rs > 0 ? $" {(rs == 1 ? "Uma já foi resolvida" : Num(rs) + " já foram resolvidas")} desde o raio-x." : ""),
                          Botao("Ver o diagnóstico", true, () => Abre("raiox")));
        }

        // I16: quando o motor já concluiu algo, a frase principal e a ação que mais rende vêm dele (com a previsão e como desfazer)
        var motor = d?["motor"];
        var acao = motor?["acao"];
        if (acao != null && motor.S("frase") != "")
        {
            string cmd = acao.S("comando");
            var txt = new List<string> { Primeira(acao.S("porque")) };
            if (acao.S("previsao") != "") txt.Add("O que eu faria: " + acao.S("previsao"));
            if (acao.S("desfazer") != "") txt.Add("Para voltar: " + ComoDesfazer(acao.S("desfazer")) + ".");
            passo = Proximo(motor.S("frase"), string.Join(" ", txt), Detalhe.Botoes(acao, Abre, "Central", primario: true));
        }
        // 2.13: primeira abertura guiada, em três passos (o raio-x só lê; mudar vem depois e sempre item por item)
        if (d.B("primeira_vez")) passo = PrimeirosPassos(d?["pc"].B("notebook") == true);

        double? nota = rx.D("nota"), notaRx = rx.D("nota_raiox");
        var t = d?["temperatura"];
        double? tc = t.D("cpu");
        var pc = d?["pc"];
        double? livre = pc.D("disco_livre_gb"), total = pc.D("disco_total_gb");
        var numeros = S(Celulas(
            Numero("Nota do PC", nota.HasValue ? Num(nota) : "-", "de 100",
                   nota == null ? "faça o raio-x para ter a nota" : (nota >= 80 ? "bem cuidado" : nota >= 55 ? "dá para melhorar" : "precisa de atenção")
                       + (notaRx is double nr && nr != nota ? $" · era {Num(nr)} no raio-x" : " · raio-x " + Quando(rx.S("quando"))),
                   nota == null ? Tema.Apagado : nota >= 80 ? Tema.Verde : nota >= 55 ? Tema.Ambar : Tema.Vermelho),
            Numero("Temperatura da CPU", tc.HasValue ? Num(tc) : "-", "°C",
                   tc == null ? "sem leitura: abra o MSI Afterburner ou o HWiNFO" : (tc >= 90 ? "quente" : tc >= 80 ? "morna" : "normal") + " · lida do " + t.S("cpu_fonte"),
                   tc == null ? Tema.Apagado : tc >= 90 ? Tema.Vermelho : tc >= 80 ? Tema.Ambar : Tema.Verde),
            Numero("Espaço livre no C:", livre.HasValue ? Num(livre) : "-", total.HasValue ? "GB de " + Num(total) : "GB",
                   livre == null ? "aparece depois do raio-x" : livre < 15 ? "quase cheio" : livre < 40 ? "apertado" : "folgado",
                   livre == null ? Tema.Apagado : livre < 15 ? Tema.Vermelho : livre < 40 ? Tema.Ambar : Tema.Verde)));

        // as três coisas que mais importam agora (o motor já tirou as resolvidas depois do raio-x); o diagnóstico completo fica no Raio-x
        Control? lista = null;
        if (rx != null && rx.A("achados").Any())
        {
            var p = new StackPanel { Children = { Subtitulo("O mais importante agora", null, "alerta") } };
            foreach (var a in rx.A("achados").Take(3))
            {
                var (g, cor) = Gravidade((int)(a.D("impacto") ?? 0));
                p.Children.Add(Linha(a.S("titulo"), a.S("evidencia"), Etiqueta(g, cor), Detalhe.Botoes(a, Abre, "Início"), Icones.DaCategoria(Rotas.Categoria(a.S("categoria"), a.S("titulo"), a.S("comando")))));
            }
            if (rx.D("total") is double tot && tot > 3)
                p.Children.Add(new Border { Padding = new Avalonia.Thickness(32, 12, 32, 16), BorderBrush = Tema.Linha, BorderThickness = new Avalonia.Thickness(0, 1, 0, 0),
                    Child = Botao($"Ver as outras {Num(tot - 3)} no Raio-x", false, () => Abre("raiox")).Com(b => b.HorizontalAlignment = HorizontalAlignment.Left) });
            lista = S(p);
        }
        jogosDesenhados = jogos?.ToJsonString();
        var secJogos = SecaoJogos(jogos);

        var um = d?["ultima_mudanca"];
        Control? ultima = um == null ? null : S(new Grid
        {
            ColumnDefinitions = new ColumnDefinitions("*,Auto"), Margin = new Avalonia.Thickness(32, 22),
            Children =
            {
                new StackPanel { Spacing = 3, Children = { T("Última mudança", "rotulo"), T($"{Primeira(um.S("titulo"))}, {Quando(um.S("quando"))}: {Num(um.D("itens"))} itens", null, Tema.Osso, 15) } },
                Botao("Desfazer", false, () => Abre("desfazer")).Com(b => Grid.SetColumn(b, 1)),
            }
        });
        Control? versao = Atualizacao.VersaoPronta is string v ? S(new Avalonia.Controls.Grid
        {
            ColumnDefinitions = new ColumnDefinitions("*,Auto"), Margin = new Avalonia.Thickness(32, 18),
            Children = { new StackPanel { Spacing = 2, Children = { T($"Versão {v} pronta", null, Tema.Osso, 15).Com(t => t.FontWeight = Avalonia.Media.FontWeight.SemiBold), T("Já baixada. Reinicia em segundos e nada do que você fez se perde.", "rotulo") } },
                         Botao("Reiniciar agora", false, () =>
                         {
                             if (!Atualizacao.Aplica())
                                 Janela.Atual?.MostraCaixa(Janela.Caixa("Daqui a pouco", T("O Katharos está mudando algo no PC agora. A versão nova entra assim que terminar.", "sub"), Botao("Fechar", true, () => Janela.Atual!.FechaCaixa())), true);
                         }).Com(b => Avalonia.Controls.Grid.SetColumn(b, 1)) },
        }) : null;
        // achou um erro ou tem uma ideia: o relatório e o feedback a um clique, sempre à vista
        var enviar = S(new Grid
        {
            ColumnDefinitions = new ColumnDefinitions("*,Auto"), Margin = new Avalonia.Thickness(32, 20),
            Children = { new StackPanel { Spacing = 3, Children = { T("Achou um erro ou tem uma ideia?", null, Tema.Osso, 15).Com(t => t.FontWeight = Avalonia.Media.FontWeight.SemiBold),
                                                                     T("Mande um relatório, a sua opinião ou os dois. Você vê tudo antes de sair.", "rotulo") } },
                         Botao("Enviar relatório", false, () => Abre("enviar")).Com(b => Grid.SetColumn(b, 1)) },
        });
        Monta(cab, versao, passo, numeros, lista, secJogos, ultima, enviar);
    }

    Control PrimeirosPassos(bool notebook)
    {
        var p = new StackPanel { Margin = new Avalonia.Thickness(32, 26, 32, 22), Spacing = 4 };
        p.Children.Add(T("Primeiros passos", "rotulo"));
        p.Children.Add(T("Três passos, nesta ordem. Nada muda no PC sem você ver antes.", "forte", tamanho: 21));
        var passos = new (string titulo, string texto, string botao, string tela)[]
        {
            ("Faça o raio-x", "Leva de 1 a 3 minutos e só lê. Ele dá a nota do PC e diz o que vale a pena fazer.", "Fazer o raio-x", "raiox:rodar"),
            ("Otimize no modo seguro", "Você vê cada item com o que ganha e o que perde, marca o que quiser e aplica. Tudo volta com Desfazer.", "Abrir Otimizar", "otimizar"),
            ("Ligue o acompanhamento (opcional)", "Um ícone perto do relógio mede o PC e os jogos, leve, e avisa quando algo pesa."
                + (notebook ? " Num notebook ele também pode trocar o plano de energia na tomada e na bateria, se você quiser." : ""), "Ver Ao vivo", "aovivo"),
        };
        for (int i = 0; i < passos.Length; i++)
        {
            var (ti, tx, bo, te) = passos[i];
            var g = new Grid { ColumnDefinitions = new ColumnDefinitions("44,*,Auto"), Margin = new Avalonia.Thickness(0, 14, 0, 0) };
            g.Children.Add(T((i + 1).ToString(), "numero", tamanho: 26));
            var meio = new StackPanel { Spacing = 2, Children = { T(ti, null, Tema.Osso, 16).Com(t => t.FontWeight = Avalonia.Media.FontWeight.SemiBold), T(tx, "rotulo", quebra: true).Com(t => t.MaxWidth = 620) } };
            Grid.SetColumn(meio, 1); g.Children.Add(meio);
            var b = Botao(bo, i == 0, () => Abre(te)); b.VerticalAlignment = VerticalAlignment.Center; Grid.SetColumn(b, 2); g.Children.Add(b);
            p.Children.Add(g);
        }
        return S(p);
    }

    static Control Proximo(string titulo, string texto, params Control[] botoes)
    {
        var g = new Grid { ColumnDefinitions = new ColumnDefinitions("*,Auto"), Margin = new Avalonia.Thickness(32, 28) };
        g.Children.Add(new StackPanel { Spacing = 6, VerticalAlignment = VerticalAlignment.Center, Children = { T("Próximo passo", "rotulo"), T(titulo, "forte", tamanho: 21), T(texto, "sub").Com(x => { x.MaxWidth = 600; x.HorizontalAlignment = HorizontalAlignment.Left; }) } });
        var b = new StackPanel { Orientation = Orientation.Horizontal, Spacing = 10, VerticalAlignment = VerticalAlignment.Center };
        foreach (var x in botoes.Reverse()) b.Children.Add(x);
        Grid.SetColumn(b, 1); g.Children.Add(b);
        return S(g);
    }

    static string Primeira(string s) => string.IsNullOrEmpty(s) ? s : char.ToUpper(s[0]) + s[1..];

    /// <summary>Jogos, dentro do Início: as últimas sessões, o que limitou o jogo e o caminho para os detalhes.</summary>
    Control? SecaoJogos(JsonNode? j)
    {
        var ses = j.A("sessoes").OrderByDescending(x => x.S("inicio")).Take(3).ToList();
        if (ses.Count == 0) return null;
        var p = new StackPanel { Children = { Subtitulo("Jogos", "Últimas sessões medidas", "jogos") } };
        static string Limite(string x) => x switch { "gpu" => "placa de vídeo no limite", "cpu" => "processador segurando", "ram" => "memória cheia", "disco" => "disco", "" => "sem limite claro", _ => x };
        foreach (var x in ses)
        {
            string fps = x.D("fps_med") is double f ? $"{Num(f)} FPS médio" + (x.D("fps_1low") is double l ? $", {Num(l)} no 1% mais lento" : "") : "sem FPS medido";
            p.Children.Add(Linha($"{x.S("jogo")} · {Quando(x.S("inicio"))}", $"{Num(x.D("min"))} min · {fps} · o que limitou: {Limite(x.S("principal"))}"));
        }
        p.Children.Add(new Border { Padding = new Avalonia.Thickness(32, 12, 32, 16), BorderBrush = Tema.Linha, BorderThickness = new Avalonia.Thickness(0, 1, 0, 0),
            Child = Botao("Ver por jogo e antes e depois", false, () => Abre("jogos")).Com(b => b.HorizontalAlignment = HorizontalAlignment.Left) });
        return S(p);
    }
}
