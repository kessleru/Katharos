using System.Text.Json.Nodes;
using Avalonia.Controls;
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
        var cab = Cabecalho("Raio-x", "O que deixa este PC lento e o que fazer. Só lê: nada muda.", Botao("Fazer de novo", false, async () => { rodar = true; await Recarrega(); }));
        if (rodar) { rodar = false; await Roda(cab); return; }
        var rx = await Servico.Le("raiox_guardado");
        if (rx == null) { Monta(cab, Vazio("Ainda não tem raio-x", "Leva de 1 a 3 minutos. Pode usar o PC enquanto isso.", Botao("Fazer o raio-x", true, async () => { rodar = true; await Recarrega(); }))); return; }
        Monta(cab, Resultado(rx, rx["pc"], Quando(rx.S("quando"))));
    }

    async Task Roda(Control cab)
    {
        var (sec, passo, barra) = Carregando("Lendo o PC");
        Monta(cab, sec);
        var r = await Servico.Le("raiox", null, (tipo, dados) => Dispatcher.UIThread.Post(() =>
        {
            if (tipo != "etapa") return;
            passo.Text = Primeira(dados.S("texto"));
            if (dados.D("de") is double de && de > 0) { barra.IsIndeterminate = false; barra.Maximum = de; barra.Value = dados.D("n") ?? 0; }
        }));
        Monta(cab, Resultado(r, r?["pc"], "agora"));
    }

    Control Resultado(JsonNode? rx, JsonNode? pc, string quando)
    {
        var p = new StackPanel();
        double? nota = rx.D("nota");
        var pesa = rx.A("pesa").Select(x => $"{x.S("titulo")} (−{Num(x.D("pontos"))})").ToList();
        p.Children.Add(S(Celulas(
            Numero("Nota do PC", Num(nota), "de 100", (nota >= 80 ? "bem cuidado" : nota >= 55 ? "dá para melhorar" : "precisa de atenção") + " · " + quando,
                   nota >= 80 ? Tema.Verde : nota >= 55 ? Tema.Ambar : Tema.Vermelho,
                   pesa.Count > 0 ? T("O que mais tira ponto: " + string.Join("; ", pesa), "rotulo", tamanho: 13, quebra: true).Com(t => t.Margin = new Avalonia.Thickness(0, 6, 0, 0)) : null),
            PcInfo(pc))));
        var achados = rx.A("achados").ToList();
        var lista = new StackPanel { Children = { Subtitulo(achados.Count == 0 ? "Nada a resolver" : "O que fazer, do mais importante para o menos", achados.Count == 0 ? "O raio-x não achou problema neste PC." : null) } };
        foreach (var a in achados)
        {
            var (g, cor) = Gravidade((int)(a.D("impacto") ?? 0));
            string texto = a.S("evidencia") + (string.IsNullOrWhiteSpace(a.S("faz")) ? "" : "\n" + a.S("faz"));
            string cmd = a.S("comando");
            lista.Children.Add(Linha(a.S("titulo"), texto, Etiqueta(g, cor), cmd == "" ? null : Botao("Resolver", false, () => Abre(Sugestoes.TelaDo(cmd)))));
        }
        p.Children.Add(S(lista));
        // I21: o que o motor viu com o tempo (sessões de jogo, o normal deste PC, eventos do Windows); sem dado, diz que ainda não sabe
        var mot = rx?["motor"];
        var ma = mot.A("achados").ToList();
        if (ma.Count > 0 || mot.B("ainda_nao_sei"))
        {
            var m = new StackPanel { Children = { Subtitulo("O que o acompanhamento viu com o tempo", ma.Count > 0 ? "Medido nos jogos e no dia a dia, não só agora." : null) } };
            if (ma.Count == 0)
                m.Children.Add(Linha("Ainda não sei", "Com o acompanhamento ligado e algumas sessões de jogo, aqui aparece o que segura este PC com o tempo (calor, CPU freando, RAM cheia, travadas).",
                                     null, Botao("Ligar o acompanhamento", false, () => Abre("aovivo"))));
            foreach (var x in ma)
            {
                string conf = x.S("confianca");
                m.Children.Add(Linha(x.S("titulo"), Primeira(x.S("vi")) + ". Fonte: " + x.S("fonte") + ".", Etiqueta("confiança " + conf, conf == "alta" ? Tema.Verde : conf == "média" ? Tema.Ambar : Tema.Apagado),
                                     Botao("Por quê", false, () => Abre("sugestoes"))));
            }
            p.Children.Add(S(m));
        }
        return p;
    }

    static Control PcInfo(JsonNode? pc)
    {
        var p = new StackPanel { Spacing = 6 };
        p.Children.Add(T("Este PC", "rotulo"));
        foreach (var (rot, chave) in new[] { ("Modelo", "modelo"), ("Windows", "windows"), ("Processador", "cpu"), ("Memória", "ram"), ("Disco C:", "disco"), ("Vídeo", "video") })
        {
            string v = pc.S(chave);
            if (v == "") continue;
            p.Children.Add(new Grid { ColumnDefinitions = new ColumnDefinitions("110,*"), Children = { T(rot, "rotulo", tamanho: 13.5), T(v, null, Tema.Osso, 13.5, true).Com(t => Grid.SetColumn(t, 1)) } });
        }
        if (p.Children.Count == 1) p.Children.Add(T("Aparece depois de fazer o raio-x de novo.", "rotulo"));
        return new Border { Padding = new Avalonia.Thickness(32, 24), Child = p };
    }

    static string Primeira(string s) => string.IsNullOrEmpty(s) ? s : char.ToUpper(s[0]) + s[1..];
}
