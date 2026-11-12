using Avalonia;
using Avalonia.Controls;
using Avalonia.Controls.Primitives;
using Avalonia.Layout;
using System.Text.Json.Nodes;
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
    int periodo = 30;
    JsonNode? dados;

    protected override async Task Carrega()
    {
        var cab = Cabecalho("Histórico", null);
        var g = Servico.Guardado("historico", new { dias = 60 });
        if (g != null) Desenha(cab, g); else Monta(cab, Carregando("Lendo as medidas").secao);
        var d = await Servico.Le("historico", new { dias = 60 });
        if (g == null || g.ToJsonString() != d?.ToJsonString()) Desenha(cab, d);
    }

    /// <summary>Uma medida pronta para desenhar: um valor por dia do período (NaN no dia sem leitura) e as marcas agrupadas por dia.</summary>
    record Serie(string Rotulo, string Unidade, int Casas, double[] Valores, string[] Dias, double FaixaMin, double FaixaMax, int DiasComDado, List<MarcaGrafico> Marcas);

    Serie Monta(JsonNode s, List<(DateTime quando, string titulo)> marcas, int dias)
    {
        var porDia = new Dictionary<DateTime, double>();
        foreach (var x in s.A("pontos")) if (DateTime.TryParse(x.S("dia"), out var dd) && x.D("v") is double v) porDia[dd.Date] = v;
        DateTime fim = porDia.Count > 0 ? porDia.Keys.Max() : DateTime.Today, ini = fim.AddDays(-(dias - 1));
        var vals = new double[dias]; var rot = new string[dias];
        for (int i = 0; i < dias; i++) { var dd = ini.AddDays(i); vals[i] = porDia.TryGetValue(dd, out var v) ? v : double.NaN; rot[i] = dd.ToString("dd/MM"); }
        // as mudanças do mesmo dia viram uma marca só ("inicialização e serviços · 12/11")
        var ms = marcas.Where(m => m.quando.Date >= ini && m.quando.Date <= fim).GroupBy(m => m.quando.Date)
                       .Select(gr => new MarcaGrafico((gr.Key - ini).TotalDays / Math.Max(1, dias - 1), string.Join(" e ", gr.Select(m => m.titulo).Distinct()) + " · " + gr.Key.ToString("dd/MM"))).ToList();
        var fx = s?["faixa"];
        return new Serie(s.S("rotulo"), s.S("unidade"), (int)(s.D("casas") ?? 0), vals, rot, fx.D("p10") ?? double.NaN, fx.D("p90") ?? double.NaN,
                         porDia.Count(kv => kv.Key >= ini), ms);
    }

    static string Fmt(double v, Serie s) => (Num(v, s.Casas) + " " + s.Unidade).Trim();

    void Desenha(Control cab, JsonNode? d)
    {
        dados = d;
        var series = d.A("series").ToList();
        if (series.Count == 0)
        {
            Monta(cab, Vazio("Ainda não há medidas", "O Katharos mede o PC um pouco por dia (boot, memória, espaço, processos) quando o acompanhamento está ligado. Com alguns dias, aparece aqui com as marcas de cada mudança.",
                             Botao("Ver o acompanhamento", false, () => Abre("aovivo"))));
            return;
        }
        var marcas = d.A("marcas").Select(m => (DateTime.TryParse(m.S("quando"), out var q) ? q : DateTime.MinValue, m.S("titulo"))).Where(m => m.Item1 > DateTime.MinValue).ToList();

        // o que está mudando agora (só aparece quando é claro: o motor não chama oscilação de tendência)
        Control? tend = null;
        var ts = d.A("tendencia").Select(x => x.ToString()).ToList();
        if (ts.Count > 0)
        {
            var p = new StackPanel { Children = { Subtitulo("Mudando agora", null, "aovivo") } };
            foreach (var t in ts) p.Children.Add(Linha(Maiuscula(t) + ".", null, Etiqueta("atenção", Tema.Ambar)));
            tend = G(p);
        }

        // período: 7, 30 ou 60 dias
        var per = new StackPanel { Orientation = Orientation.Horizontal, Spacing = 8, Margin = new Thickness(32, 18, 32, 14) };
        per.Children.Add(T("Período", "rotulo").Com(t => { t.VerticalAlignment = VerticalAlignment.Center; t.Margin = new Thickness(0, 0, 6, 0); }));
        foreach (var n in new[] { 7, 30, 60 })
            per.Children.Add(Botao(n + " dias", n == periodo, () => { periodo = n; Desenha(cab, dados); }).Com(b => b.Padding = new Thickness(12, 6)));

        var todas = series.Select(s => Monta(s, marcas, periodo)).ToList();
        var grade = new UniformGrid { Columns = 2 };
        foreach (var s in todas)
        {
            bool aprendendo = s.DiasComDado < 7;
            var g = new Grafico { Height = 70, Margin = new Thickness(0, 10, 0, 0), Valores = s.Valores, Rotulos = s.Dias, Formata = v => Fmt(v, s),
                                  Maximo = Math.Max(1, s.Valores.Where(v => !double.IsNaN(v)).DefaultIfEmpty(1).Max() * 1.15),
                                  // com menos de 7 dias, o "normal deste PC" ainda não vale: sem faixa e sem comparação
                                  FaixaMin = aprendendo ? double.NaN : s.FaixaMin, FaixaMax = aprendendo ? double.NaN : s.FaixaMax, Marcas = s.Marcas };
            g.PedeAmpliar += () => Amplia(s, todas);
            g.MarcaClicada += m => MostraMarca(m);
            var hoje = s.Valores.Where(v => !double.IsNaN(v)).DefaultIfEmpty(double.NaN).Last();
            var antes = s.Valores.Where(v => !double.IsNaN(v)).DefaultIfEmpty(double.NaN).First();
            var topo = new Grid { ColumnDefinitions = new ColumnDefinitions("*,Auto"), Children = {
                T(Maiuscula(s.Rotulo), "rotulo"),
                new Button { Classes = { "link" }, Padding = new Thickness(4), Content = Icones.De("ampliar", 15, Tema.Apagado) }
                    .Com(b => { Grid.SetColumn(b, 1); ToolTip.SetTip(b, "Ampliar (ou clique duas vezes no gráfico)"); b.Click += (_, _) => Amplia(s, todas); }) } };
            var corpo = new StackPanel { Spacing = 4, Children =
            {
                topo,
                new StackPanel { Orientation = Orientation.Horizontal, Children = { T(double.IsNaN(hoje) ? "-" : Num(hoje, s.Casas), "numero"), T(s.Unidade, "unidade") } },
                T(aprendendo ? $"ainda aprendendo este PC ({s.DiasComDado} de 7 dias)" : $"era {Num(antes, s.Casas)} {s.Unidade} em {s.Dias[0]}".Replace("  ", " "), aprendendo ? null : "rotulo", aprendendo ? Tema.Ambar : null, 13),
                g,
            } };
            grade.Children.Add(new Border { Padding = new Thickness(32, 22, 32, 20), BorderBrush = Tema.Linha, BorderThickness = new Thickness(0, 0, 1, 1), Child = corpo });
        }
        var legenda = new WrapPanel { Margin = new Thickness(32, 14) };
        legenda.Children.Add(new Border { Width = 8, Height = 8, Background = Tema.Ambar, Margin = new Thickness(0, 0, 8, 0), VerticalAlignment = VerticalAlignment.Center });
        legenda.Children.Add(T("mudança aplicada (passe o mouse ou clique)", "rotulo", tamanho: 13).Com(t => t.Margin = new Thickness(0, 0, 20, 0)));
        legenda.Children.Add(new Border { Width = 14, Height = 8, Background = new SolidColorBrush(Color.FromArgb(40, 0xEC, 0xE6, 0xD8)), Margin = new Thickness(0, 0, 8, 0), VerticalAlignment = VerticalAlignment.Center });
        legenda.Children.Add(T("o normal deste PC", "rotulo", tamanho: 13).Com(t => t.Margin = new Thickness(0, 0, 20, 0)));
        legenda.Children.Add(T("dia sem leitura fica em branco", "rotulo", tamanho: 13));

        // o que o motor achou fora do normal: clicar abre a explicação
        Control? anomalias = null;
        var an = d.A("anomalias").ToList();
        if (an.Count > 0)
        {
            var p = new StackPanel { Children = { Subtitulo("Fora do normal", null, "alerta") } };
            foreach (var x in an)
            {
                // o mesmo jeito das outras listas (a caixa de expandir cortava o título): quando à vista, o que eu vi em "detalhes"
                string vezes = (x.D("dias") ?? 1) > 1 ? $" · em {Num(x.D("dias"))} dias" : "";
                string conf = x.S("confianca");
                p.Children.Add(Linha(Maiuscula(x.S("titulo")), Quando(x.S("dia") + "T12:00") + vezes,
                    conf == "" ? null : Etiqueta("confiança " + conf, conf == "alta" ? Tema.Verde : conf == "média" ? Tema.Ambar : Tema.Apagado),
                    detalhes: x.S("vi") != "" ? Maiuscula(x.S("vi")) + "." : null));
            }
            anomalias = G(p);
        }

        // o efeito de cada mudança, medida por medida
        Control? efeitos = null;
        var es = d.A("efeitos").ToList();
        if (es.Count > 0)
        {
            var p = new StackPanel { Children = { Subtitulo("O que cada mudança fez", "7 dias antes contra 7 depois.", "grafico") } };
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
            efeitos = G(p);
        }
        // nos jogos: o antes e depois de cada mudança (2c.7)
        Control? jogos = null;
        var js = d.A("jogos").ToList();
        if (js.Count > 0)
        {
            var p = new StackPanel { Children = { Subtitulo("Nos jogos", null, "jogos") } };
            foreach (var c in js)
            {
                string v = c.S("veredito");
                var cor = v.Contains("melhor") ? Tema.Verde : v.Contains("pior") ? Tema.Vermelho : Tema.Apagado;
                p.Children.Add(Linha($"{c.S("jogo")} · {c.S("rotulo")}: {Num(c.D("antes"))} → {Num(c.D("depois"))} {c.S("un")}", $"depois de {c.S("nome_pacote")} ({Quando(c.S("quando"))})", Etiqueta(v == "" ? "?" : v, cor)));
            }
            jogos = G(p);
        }
        Monta(cab, tend, S(new StackPanel { Children = { per, grade, legenda } }), anomalias, efeitos, jogos);
    }

    /// <summary>A marca clicada: o que foi aplicado nesse dia e, se já deu para medir, o que mudou.</summary>
    void MostraMarca(MarcaGrafico m)
    {
        var j = Janela.Atual!;
        var corpo = new StackPanel { Spacing = 8, MaxWidth = 560 };
        var titulo = m.Texto.Split(" · ")[0];
        var ef = dados.A("efeitos").FirstOrDefault(e => titulo.Contains(e.S("titulo")));
        if (ef != null)
            foreach (var x in ef.A("medidas").Where(x => x.S("veredito") != "poucas medidas"))
            {
                int c = (int)(x.D("casas") ?? 0);
                corpo.Children.Add(Item($"{Num(x.D("antes"), c)} → {Num(x.D("depois"), c)} {x.S("unidade")} ({x.S("veredito")})", x.S("veredito") == "melhorou" ? Tema.Verde : x.S("veredito") == "piorou" ? Tema.Vermelho : Tema.Apagado, Maiuscula(x.S("rotulo"))));
            }
        if (corpo.Children.Count == 0) corpo.Children.Add(T("Ainda poucas medidas depois desta mudança para dizer o que ela fez. O Katharos compara sozinho, 7 dias antes e depois.", "sub", quebra: true));
        j.MostraCaixa(Janela.Caixa("Aplicado: " + m.Texto, corpo, new StackPanel { Orientation = Orientation.Horizontal, Spacing = 10, HorizontalAlignment = HorizontalAlignment.Right, Margin = new Thickness(0, 12, 0, 0),
            Children = { Botao("Ver no Desfazer", false, () => { j.FechaCaixa(); Abre("desfazer"); }), Botao("Fechar", true, j.FechaCaixa) } }), true);
    }

    /// <summary>
    /// O gráfico grande: eixos com valores e datas, a faixa do normal, as marcas com o nome. A roda aproxima e afasta, arrastar escolhe
    /// um trecho, "Ver tudo" volta. Dá para pôr uma segunda medida junto (escala própria, em verde) e ligar ou desligar cada uma. Esc fecha.
    /// </summary>
    void Amplia(Serie s, List<Serie> todas)
    {
        var j = Janela.Atual!;
        var g = new Grafico { Height = Math.Max(300, (j.Bounds.Height > 0 ? j.Bounds.Height : 800) - 330), Eixos = true, Valores = s.Valores, Rotulos = s.Dias, Formata = v => Fmt(v, s),
                              Maximo = Math.Max(1, s.Valores.Where(v => !double.IsNaN(v)).DefaultIfEmpty(1).Max() * 1.15),
                              FaixaMin = s.DiasComDado < 7 ? double.NaN : s.FaixaMin, FaixaMax = s.DiasComDado < 7 ? double.NaN : s.FaixaMax, Marcas = s.Marcas };
        g.MarcaClicada += MostraMarca;
        var verTudo = Botao("Ver tudo", false, () => g.VerTudo()).Com(b => b.IsVisible = false);
        g.ZoomMudou += () => verTudo.IsVisible = g.ComZoom;
        Button Chave(string texto, IBrush cor, Func<bool> ligado, Action troca)
        {
            var b = new Button { Classes = { "link" } };
            void Pinta() => b.Content = new StackPanel { Orientation = Orientation.Horizontal, Spacing = 8, Opacity = ligado() ? 1 : .4, Children = { new Border { Width = 14, Height = 3, Background = cor, VerticalAlignment = VerticalAlignment.Center }, T(texto, null, Tema.Texto, 13) } };
            Pinta();
            b.Click += (_, _) => { troca(); Pinta(); };
            ToolTip.SetTip(b, "Mostrar ou esconder");
            return b;
        }
        var legenda = new StackPanel { Orientation = Orientation.Horizontal, Spacing = 6 };
        legenda.Children.Add(Chave(Maiuscula(s.Rotulo), Tema.Ambar, () => g.Mostra1, () => g.Mostra1 = !g.Mostra1));
        var comparar = new ComboBox { PlaceholderText = "Comparar com…", MinWidth = 220, ItemsSource = todas.Where(x => x != s).Select(x => Maiuscula(x.Rotulo)).Prepend("Nada").ToList() };
        Control? chave2 = null;
        comparar.SelectionChanged += (_, _) =>
        {
            if (chave2 != null) legenda.Children.Remove(chave2);
            var outra = todas.FirstOrDefault(x => Maiuscula(x.Rotulo) == comparar.SelectedItem as string);
            if (outra == null) { g.Valores2 = null; return; }
            g.Valores2 = outra.Valores; g.Mostra2 = true; g.Formata2 = v => Fmt(v, outra);
            g.Maximo2 = Math.Max(1, outra.Valores.Where(v => !double.IsNaN(v)).DefaultIfEmpty(1).Max() * 1.15);
            chave2 = Chave(Maiuscula(outra.Rotulo) + " (escala própria)", Tema.Verde, () => g.Mostra2, () => g.Mostra2 = !g.Mostra2);
            legenda.Children.Add(chave2);
        };
        var topo = new Grid { ColumnDefinitions = new ColumnDefinitions("*,Auto,Auto"), Children = { legenda, verTudo.Com(b => { Grid.SetColumn(b, 1); b.Margin = new Thickness(0, 0, 10, 0); }), comparar.Com(c => Grid.SetColumn(c, 2)) } };
        var corpo = new StackPanel { Spacing = 12, Children = { topo, g, T("Roda: zoom · arrastar: trecho · Esc fecha", "rotulo", tamanho: 12.5) } };
        j.MostraCaixa(Janela.Caixa(Maiuscula(s.Rotulo), corpo, Botao("Fechar", true, j.FechaCaixa).Com(b => b.HorizontalAlignment = HorizontalAlignment.Right)), true);
    }
}
