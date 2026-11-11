using Avalonia;
using Avalonia.Controls;
using Avalonia.Controls.Primitives;
using Avalonia.Layout;
using Avalonia.Media;
using Katharos.App.Controles;
using static Katharos.App.Ui;

namespace Katharos.App.Telas;

/// <summary>
/// Histórico (substitui o painel em HTML): cada medida por dia, com uma marca âmbar no dia de cada mudança, e o efeito de cada mudança
/// com veredito honesto ("sem diferença mensurável" e "já vinha mudando" aparecem como são).
/// </summary>
public class Historico : Tela
{
    protected override async Task Carrega()
    {
        var cab = Cabecalho("Histórico", "O seu PC ao longo do tempo e o que cada mudança fez de verdade.");
        Monta(cab, Carregando("Lendo as medidas").secao);
        var d = await Servico.Le("historico", new { dias = 60 });
        var series = d.A("series").ToList();
        if (series.Count == 0)
        {
            Monta(cab, Vazio("Ainda não há medidas", "O Katharos mede o PC um pouco por dia (boot, memória, espaço, processos) quando o acompanhamento está ligado. Com alguns dias, aparece aqui com as marcas de cada mudança.",
                             Botao("Ver o acompanhamento", false, () => Abre("aovivo"))));
            return;
        }
        var marcas = d.A("marcas").Select(m => DateTime.TryParse(m.S("quando"), out var q) ? q : DateTime.MinValue).Where(q => q > DateTime.MinValue).ToList();

        // o que está mudando agora (só aparece quando é claro: o motor não chama oscilação de tendência)
        Control? tend = null;
        var ts = d.A("tendencia").Select(x => x.ToString()).ToList();
        if (ts.Count > 0)
        {
            var p = new StackPanel { Children = { Subtitulo("Mudando agora") } };
            foreach (var t in ts) p.Children.Add(Linha(Maiuscula(t) + ".", null, Etiqueta("atenção", Tema.Ambar)));
            tend = S(p);
        }

        // uma célula por medida: o valor de hoje, o de 60 dias atrás e a linha com as marcas
        var grade = new UniformGrid { Columns = 2 };
        foreach (var s in series)
        {
            var pts = s.A("pontos").ToList();
            var dias = pts.Select(x => DateTime.Parse(x.S("dia"))).ToList();
            var vals = pts.Select(x => x.D("v") ?? 0).ToArray();
            int casas = (int)(s.D("casas") ?? 0);
            double max = Math.Max(1, vals.Max() * 1.15);
            DateTime ini = dias.First(), fim = dias.Last();
            double total = Math.Max(1, (fim - ini).TotalDays);
            var fx = s?["faixa"];
            var g = new Grafico { Height = 70, Margin = new Thickness(0, 10, 0, 0), Valores = vals, Maximo = max, FaixaMin = fx.D("p10") ?? double.NaN, FaixaMax = fx.D("p90") ?? double.NaN,
                                  Marcas = marcas.Where(m => m >= ini && m <= fim.AddDays(1)).Select(m => (m - ini).TotalDays / total).ToArray() };
            string un = s.S("unidade");
            string rot = s.S("rotulo");
            var corpo = new StackPanel { Spacing = 4, Children =
            {
                T(Maiuscula(rot), "rotulo"),
                new StackPanel { Orientation = Orientation.Horizontal, Children = { T(Num(vals[^1], casas), "numero"), T(un, "unidade") } },
                T($"era {Num(vals[0], casas)} {un} em {ini:dd/MM}".Replace("  ", " "), "rotulo", tamanho: 13),
                g,
            } };
            grade.Children.Add(new Border { Padding = new Thickness(32, 22, 32, 20), BorderBrush = Tema.Linha, BorderThickness = new Thickness(0, 0, 1, 1), Child = corpo });
        }
        var legenda = T("A linha âmbar tracejada marca o dia de cada mudança aplicada; a faixa clara é o normal deste PC.", "rotulo", tamanho: 13).Com(t => t.Margin = new Thickness(32, 14));

        // o que o motor achou fora do normal: clicar abre a explicação
        Control? anomalias = null;
        var an = d.A("anomalias").ToList();
        if (an.Count > 0)
        {
            var p = new StackPanel { Children = { Subtitulo("Fora do normal", "O que o motor viu diferente do normal deste PC. Clique para ver o porquê.") } };
            foreach (var x in an)
            {
                string vezes = (x.D("dias") ?? 1) > 1 ? $" · apareceu em {Num(x.D("dias"))} dias" : "";
                var exp = new Expander { Header = T($"{x.S("titulo")} ({Quando(x.S("dia") + "T12:00")}{vezes})", null, Tema.Osso, 15), HorizontalAlignment = Avalonia.Layout.HorizontalAlignment.Stretch,
                                         Content = T(Maiuscula(x.S("vi")) + ". Confiança " + x.S("confianca") + ".", "rotulo", quebra: true), Margin = new Thickness(32, 8) };
                p.Children.Add(exp);
            }
            anomalias = S(p);
        }

        // o efeito de cada mudança, medida por medida
        Control? efeitos = null;
        var es = d.A("efeitos").ToList();
        if (es.Count > 0)
        {
            var p = new StackPanel { Children = { Subtitulo("O que cada mudança fez", "Sete dias antes contra sete dias depois. Diferença que cabe na oscilação normal conta como sem diferença.") } };
            foreach (var e in es)
            {
                var linhas = e.A("medidas").Where(m => m.S("veredito") != "poucas medidas").Select(m =>
                {
                    int c = (int)(m.D("casas") ?? 0); string u = m.S("unidade");
                    return $"{m.S("rotulo")}: {Num(m.D("antes"), c)} → {Num(m.D("depois"), c)} {u} ({m.S("veredito")})";
                }).ToList();
                string titulo = e.S("titulo");
                string q = e?["qualidade"].S("texto") ?? "";
                if (q != "" && e?["qualidade"].S("nivel") != "") linhas.Add(Maiuscula(q) + ".");
                p.Children.Add(Linha($"{Maiuscula(titulo)}, {Quando(e.S("quando"))}",
                                     linhas.Count > 0 ? string.Join("\n", linhas) : "Poucas medidas antes e depois para dizer algo com certeza."));
            }
            efeitos = S(p);
        }
        // nos jogos: o antes e depois de cada mudança (2c.7)
        Control? jogos = null;
        var js = d.A("jogos").ToList();
        if (js.Count > 0)
        {
            var p = new StackPanel { Children = { Subtitulo("Nos jogos", "Sessões do mesmo jogo antes e depois de cada mudança; diferença menor que a variação normal conta como sem diferença.") } };
            foreach (var c in js)
            {
                string v = c.S("veredito");
                var cor = v.Contains("melhor") ? Tema.Verde : v.Contains("pior") ? Tema.Vermelho : Tema.Apagado;
                p.Children.Add(Linha($"{c.S("jogo")} · {c.S("rotulo")}: {Num(c.D("antes"))} → {Num(c.D("depois"))} {c.S("un")}", $"depois de {c.S("nome_pacote")} ({Quando(c.S("quando"))})", Etiqueta(v == "" ? "?" : v, cor)));
            }
            jogos = S(p);
        }
        Monta(cab, tend, S(new StackPanel { Children = { grade, legenda } }), anomalias, efeitos, jogos);
    }
}
