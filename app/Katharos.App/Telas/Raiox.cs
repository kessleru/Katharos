using System.Text.Json.Nodes;
using Avalonia.Controls;
using Avalonia.Media;
using Avalonia.Layout;
using Avalonia.Threading;
using static Katharos.App.Ui;

namespace Katharos.App.Telas;

/// <summary>Raio-x: mostra o último e roda um novo na hora que a pessoa pedir (só lê). Cada achado leva ao lugar que resolve.</summary>
public class Raiox : Tela
{
    bool rodar;
    public Raiox(bool rodarJa = false) { rodar = rodarJa; }

    protected override async Task Carrega()
    {
        var cab = Cabecalho("Raio-x", "Só lê: nada muda.", Botao("Fazer de novo", false, async () => { rodar = true; await Recarrega(); }));
        if (rodar) { rodar = false; await Roda(cab); return; }
        // o guardado aparece na hora; a resposta do motor (com o que foi resolvido desde então) troca por cima quando chega
        if (Servico.Guardado("raiox_guardado") is JsonNode g) Monta(cab, Resultado(g, g["pc"], Quando(g.S("quando"))));
        else Monta(cab, Carregando("Lendo o último raio-x").secao);
        var rx = await Servico.Le("raiox_guardado");
        if (rx == null) { Monta(cab, Vazio("Ainda não tem raio-x", "Leva de 1 a 3 minutos. Pode usar o PC enquanto isso.", Botao("Fazer o raio-x", true, async () => { rodar = true; await Recarrega(); }))); return; }
        Monta(cab, Resultado(rx, rx["pc"], Quando(rx.S("quando"))));
    }

    /// <summary>
    /// Enquanto lê: cada parte que termina entra numa lista com ✓ (o motor lê várias ao mesmo tempo, então elas chegam fora de ordem),
    /// a barra anda só com etapa real e o relógio mostra quanto já foi. Pode trocar de tela: a leitura continua.
    /// </summary>
    async Task Roda(Control cab)
    {
        var (pn, passo, barra) = Andamento("Medindo o PC em repouso (o raio-x só lê: nada muda)");
        pn.Margin = new Avalonia.Thickness(32, 40); barra.MaxWidth = 480; barra.HorizontalAlignment = HorizontalAlignment.Left;
        var feitos = new StackPanel { Spacing = 6, Margin = new Avalonia.Thickness(0, 14, 0, 0) };
        pn.Children.Add(feitos);
        var relogio = System.Diagnostics.Stopwatch.StartNew();
        var sec = S(pn);
        Monta(cab, sec);
        try
        {
            var r = await Servico.Le("raiox", null, (tipo, dados) => Dispatcher.UIThread.Post(() =>
            {
                if (tipo != "etapa") return;
                string txt = Primeira(dados.S("texto"));
                if ((dados.D("n") ?? 0) > 0)
                {
                    feitos.Children.Add(Item(T(txt, "rotulo", tamanho: 13.5), Tema.Verde));
                    Movimento.Entra(feitos.Children[^1], 3);
                    passo.Text = (dados.D("n") ?? 0) >= (dados.D("de") ?? 99) ? "Analisando o que foi lido" : "Lendo o resto ao mesmo tempo";
                }
                else passo.Text = txt;
                if (dados.D("de") is double de && de > 0) { barra.IsIndeterminate = false; barra.Maximum = de; barra.Value = dados.D("n") ?? 0; }
            }));
            Registro.Escreve($"raio-x: {relogio.ElapsedMilliseconds} ms");
            Monta(cab, Resultado(r, r?["pc"], $"agora, em {(int)Math.Round(relogio.Elapsed.TotalSeconds)} s"));
        }
        catch (Exception e) { Monta(cab, Erro(e, () => { rodar = true; _ = Recarrega(); })); }
    }

    // as categorias do diagnóstico, na ordem em que aparecem na nota, com o teto de pontos de cada uma (o mesmo do motor)
    static readonly (string nome, int teto)[] Categorias = { ("segurança", 30), ("saúde", 30), ("disco", 20), ("memória", 20), ("inicialização", 10), ("jogos", 15), ("geral", 15) };
    static int Peso(JsonNode a) => (int)(a.D("impacto") ?? 0) switch { 3 => 15, 2 => 7, 1 => 2, _ => 0 };   // o mesmo PESO_NOTA do motor

    static string Cat(JsonNode a) => Rotas.Categoria(a.S("categoria"), a.S("titulo"), a.S("comando"));

    Control Resultado(JsonNode? rx, JsonNode? pc, string quando)
    {
        var p = new StackPanel();
        double? nota = rx.D("nota"), notaRx = rx.D("nota_raiox");
        var achados = rx.A("achados").ToList();
        var abertos = achados.Where(a => a.S("resolvido") == "").ToList();
        var resolvidos = achados.Where(a => a.S("resolvido") != "").ToList();
        // quanto cada categoria tira (do motor; se for um raio-x antigo, a mesma conta aqui)
        var tira = Categorias.ToDictionary(c => c.nome, c => (int)(rx?["categorias"]?[c.nome] is JsonNode v ? (double?)v.GetValue<double>() ?? 0
                                                                     : Math.Min(c.teto, abertos.Where(a => Cat(a) == c.nome).Sum(Peso))));

        // 1) a nota e de onde vêm os pontos: uma barra por categoria (cheia = o máximo que ela pode tirar)
        var cor = nota >= 80 ? Tema.Verde : nota >= 55 ? Tema.Ambar : Tema.Vermelho;
        var notaP = new StackPanel { Spacing = 4, Children = {
            T("Nota do PC", "rotulo"),
            new StackPanel { Orientation = Orientation.Horizontal, Children = { T(Num(nota), "numero").Com(t => t.FontSize = 44), T("de 100", "unidade") } },
            T(nota >= 80 ? "bem cuidado" : nota >= 55 ? "dá para melhorar" : "precisa de atenção", null, cor, 14),
            T("raio-x " + quando + (notaRx is double nr && nota is double nn && nr != nn ? $" · era {Num(nr)} antes do que você resolveu" : ""), "rotulo", tamanho: 12.5, quebra: true),
            Link("Como a nota é feita", () => Conceitos.Abre("nota")).Com(l => { l.Margin = new Avalonia.Thickness(-8, 4, 0, 0); l.HorizontalAlignment = HorizontalAlignment.Left; }) } };
        var barras = new StackPanel { Spacing = 10 };
        foreach (var (nome, teto) in Categorias)
        {
            int pts = tira.GetValueOrDefault(nome);
            if (nome is "jogos" or "geral" && pts == 0) continue;   // só aparecem quando têm algo
            var barra = new Grid { Height = 4, ColumnDefinitions = new ColumnDefinitions($"{Math.Max(pts, 0.001)}*,{Math.Max(teto - pts, 0.001)}*"), VerticalAlignment = VerticalAlignment.Center,
                Children = { new Border { Background = pts == 0 ? Tema.Linha : pts >= teto * 0.6 ? Tema.Vermelho : Tema.Ambar, CornerRadius = new Avalonia.CornerRadius(1) },
                             new Border { Background = Tema.Linha }.Com(b => Grid.SetColumn(b, 1)) } };
            var linha = new Grid { ColumnDefinitions = new ColumnDefinitions("Auto,118,*,64") };
            linha.Children.Add(Icones.De(Icones.DaCategoria(nome), 16, pts > 0 ? Tema.Texto : Tema.Apagado).Com(i => i.Margin = new Avalonia.Thickness(0, 0, 10, 0)));
            linha.Children.Add(T(Maiuscula(nome), null, pts > 0 ? Tema.Osso : Tema.Apagado, 13.5).Com(t => { Grid.SetColumn(t, 1); t.VerticalAlignment = VerticalAlignment.Center; }));
            linha.Children.Add(barra.Com(b => Grid.SetColumn(b, 2)));
            linha.Children.Add(T(pts > 0 ? $"−{pts}" : "ok", null, pts > 0 ? Tema.Osso : Tema.Verde, 13).Com(t => { Grid.SetColumn(t, 3); t.FontFamily = Tema.Mono; t.HorizontalAlignment = HorizontalAlignment.Right; t.VerticalAlignment = VerticalAlignment.Center; }));
            ToolTip.SetTip(linha, pts > 0 ? $"Tira {pts} de no máximo {teto} pontos" : "Nada nesta parte tira ponto");
            barras.Children.Add(linha);
        }
        p.Children.Add(S(new Katharos.App.Controles.Fileira { Esquerda = notaP.Com(n => n.Margin = new Avalonia.Thickness(0, 0, 40, 0)),
                                                           Meio = new StackPanel { Spacing = 12, Children = { T("De onde vêm os pontos", "rotulo"), barras } },
                                                           Margin = new Avalonia.Thickness(32, 26) }));

        // 2) o que achou, por categoria (da que mais tira ponto para a que menos); o resolvido depois deste raio-x fica no fim, apagado
        if (abertos.Count == 0)
            p.Children.Add(S(new StackPanel { Children = { Subtitulo("Nada a resolver", resolvidos.Count > 0 ? "O que o raio-x tinha achado já foi resolvido." : "O raio-x não achou problema neste PC.", "ok") } }));
        foreach (var cat in abertos.GroupBy(Cat).OrderByDescending(g => tira.GetValueOrDefault(g.Key)).ThenByDescending(g => g.Max(a => a.D("impacto") ?? 0)))
        {
            int pts = tira.GetValueOrDefault(cat.Key);
            int pior = (int)cat.Max(a => a.D("impacto") ?? 0);
            var corCat = pior >= 3 ? Tema.Vermelho : pior == 2 ? Tema.Ambar : Tema.LinhaForte;
            var linhas = cat.OrderByDescending(a => a.D("impacto") ?? 0).Select(a =>
            {
                var (g, corG) = Gravidade((int)(a.D("impacto") ?? 0));
                return Linha(a.S("titulo"), a.S("evidencia"), Etiqueta(g, corG), Detalhe.Botoes(a, Abre, "Raio-x"));
            }).ToList();
            p.Children.Add(Grupo(Maiuscula(cat.Key), cat.Count() == 1 ? "1 achado" : $"{cat.Count()} achados", Icones.DaCategoria(cat.Key), linhas,
                                 pts > 0 ? $"−{pts} na nota" : "não tira ponto", pior >= 2 ? corCat : null));
        }
        if (resolvidos.Count > 0)
            p.Children.Add(Grupo("Resolvido depois deste raio-x", "Não conta mais na nota.", "ok",
                                 resolvidos.Select(a => Linha(a.S("titulo"), Maiuscula(a.S("resolvido")) + ".", Etiqueta("resolvido", Tema.Verde), Detalhe.Botoes(a, Abre, "Raio-x"))).ToList(),
                                 null, Tema.Verde).Com(g => g.Opacity = 0.8));
        // 3) o que o motor viu com o tempo (sessões de jogo, o normal deste PC, eventos do Windows); sem dado, diz que ainda não sabe
        var mot = rx?["motor"];
        var ma = mot.A("achados").ToList();
        if (ma.Count > 0 || mot.B("ainda_nao_sei"))
        {
            var m = new StackPanel { Children = { Subtitulo("O que o acompanhamento viu com o tempo", ma.Count > 0 ? "Medido nos jogos e no dia a dia, não só agora." : null, "aovivo") } };
            if (ma.Count == 0)
                m.Children.Add(Linha("Ainda não sei", "Com o acompanhamento ligado e algumas sessões de jogo, aqui aparece o que segura este PC com o tempo (calor, CPU freando, RAM cheia, travadas).",
                                     null, Botao("Ligar o acompanhamento", false, () => Abre("aovivo"))));
            foreach (var x in ma)
            {
                string conf = x.S("confianca");
                m.Children.Add(Linha(x.S("titulo"), Primeira(x.S("vi")) + ". Fonte: " + x.S("fonte") + ".", Etiqueta("confiança " + conf, conf == "alta" ? Tema.Verde : conf == "média" ? Tema.Ambar : Tema.Apagado),
                                     Link("Por quê", () => Abre("sugestoes"))));
            }
            p.Children.Add(S(m));
        }
        // 4) este PC (o hardware que o raio-x leu), por último: é referência, não coisa a fazer
        p.Children.Add(S(PcInfo(pc)));
        return p;
    }

    static Control PcInfo(JsonNode? pc)
    {
        var p = new StackPanel { Children = { Subtitulo("Este PC", null, "cpu") } };
        var g = new Grid { ColumnDefinitions = new ColumnDefinitions("140,*"), Margin = new Avalonia.Thickness(32, 4, 32, 24) };
        int r = 0;
        foreach (var (rot, chave) in new[] { ("Modelo", "modelo"), ("Windows", "windows"), ("Processador", "cpu"), ("Memória", "ram"), ("Disco C:", "disco"), ("Vídeo", "video") })
        {
            string v = pc.S(chave);
            if (v == "") continue;
            g.RowDefinitions.Add(new RowDefinition(GridLength.Auto));
            g.Children.Add(T(rot, "rotulo", tamanho: 13.5).Com(t => { Grid.SetRow(t, r); t.Margin = new Avalonia.Thickness(0, 5); }));
            g.Children.Add(T(v, null, Tema.Osso, 13.5, true).Com(t => { Grid.SetRow(t, r); Grid.SetColumn(t, 1); t.Margin = new Avalonia.Thickness(0, 5); }));
            r++;
        }
        if (r == 0) g.Children.Add(T("Aparece depois de fazer o raio-x de novo.", "rotulo"));
        p.Children.Add(g);
        return p;
    }

    static string Primeira(string s) => string.IsNullOrEmpty(s) ? s : char.ToUpper(s[0]) + s[1..];
}
