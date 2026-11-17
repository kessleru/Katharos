using System.Text.Json.Nodes;
using Avalonia;
using Avalonia.Controls;
using Avalonia.Input;
using Avalonia.Layout;
using Avalonia.Media;
using static Katharos.App.Ui;

namespace Katharos.App.Telas;

/// <summary>
/// O que o motor concluiu neste PC: o diagnóstico, as propostas ("o que eu faria") e o que aconteceu depois de cada mudança. Até a 4.5
/// era a tela Central; na 5.0.0 (pedido do dono) a tela saiu: as propostas e o diagnóstico ficam no Início, e "o que eu previ e o que
/// aconteceu" no Histórico. Nada muda sem a pessoa.
/// </summary>
public static class Inteligencia
{
    /// <summary>Diagnóstico e propostas para o Início (no máximo 2 propostas à vista, o resto em "ver todas"). Null quando não há nada.</summary>
    public static Control? ParaOInicio(JsonNode? d, Action<string> abre, Func<Task> recarrega)
    {
        var diags = d.A("diagnosticos").ToList();
        var props = d.A("propostas").ToList();
        if (diags.Count == 0 && props.Count == 0) return null;
        var p = new StackPanel { Children = { Subtitulo("O que eu faria", props.Count > 0 ? "com as medidas deste PC; nada muda sem você" : null, "lampada") } };
        foreach (var g in diags.Take(1)) p.Children.Add(Diagnostico(g));
        foreach (var x in props.Take(2)) p.Children.Add(Proposta(x, abre, recarrega));
        if (props.Count > 2)
        {
            var resto = new StackPanel();
            foreach (var x in props.Skip(2)) resto.Children.Add(Proposta(x, abre, recarrega));
            resto.IsVisible = false;
            p.Children.Add(new Border { Padding = new Thickness(32, 10, 32, 14), BorderBrush = Tema.Linha, BorderThickness = new Thickness(0, 1, 0, 0),
                Child = Link($"Ver as outras {props.Count - 2}", () => { resto.IsVisible = true; }) });
            p.Children.Add(resto);
        }
        return G(p);
    }

    /// <summary>O que foi aplicado: previsto contra o que aconteceu (para o Histórico). Null quando não há nada.</summary>
    public static Control? ParaOHistorico(JsonNode? d, Action<string> abre, Func<Task> recarrega)
    {
        var tempo = d.A("linha_do_tempo").ToList();
        var res = d.A("resultados").ToList();
        if (tempo.Count == 0 && res.Count == 0) return null;
        var p = new StackPanel { Children = { Subtitulo("O que eu previ e o que aconteceu", "7 dias antes contra 7 depois.", "grafico") } };
        foreach (var r in tempo.Count > 0 ? tempo : res) p.Children.Add(Resultado(r, abre, recarrega));
        return G(p);
    }

    static Control Bloco(string rotulo, string texto) => new StackPanel { Spacing = 2, Children = { T(rotulo, "rotulo"), T(texto, null, Tema.Osso, 14, true) } };

    static Control Diagnostico(JsonNode g)
    {
        string conf = g.S("confianca");
        var ev = string.Join("; ", g.A("evidencias").Select(x => x.ToString()));
        var desc = g.A("descartadas").Select(x => $"{x.S("causa")} ({x.S("motivo")})").ToList();
        var corpo = new StackPanel { Spacing = 10, Margin = new Thickness(0, 6, 0, 0) };
        // à vista: a conclusão e o que fazer. O porquê (o que vi, o que descartei, o que mudaria) fica em "detalhes"
        corpo.Children.Add(Bloco("O que eu faria", Primeira(g.S("faria")) + "."));
        corpo.Children.Add(Detalhes(new StackPanel { Spacing = 10, Children = {
            Bloco("O que eu vi", Primeira(ev) + "."),
            Bloco("Por que acho que é isso", $"A causa com mais evidência é {g.S("nome")}." + (desc.Count > 0 ? " Descartei: " + string.Join("; ", desc) + "." : "")),
            Bloco("O que mudaria a minha conclusão", Primeira(g.S("mudaria")) + ".") } }));
        var cab = new StackPanel { Spacing = 6, Children = {
            Etiqueta("confiança " + conf, conf == "alta" ? Tema.Verde : conf == "média" ? Tema.Ambar : Tema.Apagado).Com(e => e.HorizontalAlignment = HorizontalAlignment.Left),
            T($"{g.S("titulo")}: {g.S("nome")}", "forte", tamanho: 17, quebra: true) } };
        return new Border { Padding = new Thickness(32, 18), BorderBrush = Tema.Linha, BorderThickness = new Thickness(0, 1, 0, 0), Child = new StackPanel { Children = { cab, corpo } } };
    }

    static Control Proposta(JsonNode x, Action<string> Abre, Func<Task> Recarrega)
    {
        string conf = x.S("confianca"), id = x.S("id"), cmd = x.S("comando");
        var exp = x["explicacao"];
        string area = cmd.Split(' ')[0];
        var bt = new StackPanel { Orientation = Orientation.Horizontal, Spacing = 8 };
        bt.Children.Add(Botao("Agora não", false, async () => { await Servico.Le("dispensar", new { id }); await Recarrega(); }).Com(b => ToolTip.SetTip(b, "Esconde por 30 dias.")));
        bt.Children.Add(Botao("Não me importa", false, async () => { await Servico.Le("responder", new { id, resposta = "nao-importa" }); await Recarrega(); }).Com(b => ToolTip.SetTip(b, "Não proponho mais isto.")));
        bt.Children.Add(Detalhe.Botoes(x, Abre, "Início"));
        // à vista só o que eu vi (uma frase); o plano, a previsão, o risco e como desfazer ficam em "detalhes"
        var texto = new List<string>();
        if (exp.S("faria") != "") texto.Add("O que eu faria: " + exp.S("faria"));
        var prev = x["previsao"];
        if (prev.S("texto") != "") texto.Add("O que espero: " + prev.S("texto") + ".");
        if (x.S("risco") != "") texto.Add("Risco: " + x.S("risco") + ".");
        if (x.S("desfazer") != "") texto.Add("Como desfazer: " + ComoDesfazer(x.S("desfazer")) + ".");
        // o que é certo (o Windows registrou) separado do que é provável (a causa): nunca "confiança alta" numa causa que só se investiga
        var selo = x.S("certeza") != "" ? Etiqueta("aconteceu · causa " + x.S("causa", "provável"), Tema.Ambar)
                                         : Etiqueta("confiança " + conf, conf == "alta" ? Tema.Verde : conf == "média" ? Tema.Ambar : Tema.Apagado);
        return Linha(x.S("titulo"), Primeira(exp.S("vi", x.S("porque"))), selo, bt, detalhes: texto.Count > 0 ? string.Join("\n", texto) : null);
    }

    static Control Resultado(JsonNode r, Action<string> Abre, Func<Task> Recarrega)
    {
        string id = r.S("id"), cor = r.S("cor"), ver = r.S("veredito");
        var c = cor == "verde" ? Tema.Verde : cor == "vermelho" ? Tema.Vermelho : Tema.Apagado;
        // números pequenos com fração (GB de RAM) ficam com uma casa: "6,6 → 6,5", não "7 → 6"
        static string N(double v) => Num(v, Math.Abs(v) < 100 && Math.Abs(v - Math.Round(v)) > 0.001 ? 1 : 0);
        string num = r.D("antes") is double a && r.D("depois") is double b ? $": {N(a)} → {N(b)} {r.S("un")}" : "";
        string texto = r.S("texto") != "" ? r.S("texto") : $"Previ {r.S("previsto")}; {ver}{num}.";
        string q = r?["qualidade"].S("texto") ?? "";
        if (q != "" && r?["qualidade"].S("nivel") != "") texto += " " + Maiuscula(q) + ".";
        var bt = new StackPanel { Orientation = Orientation.Horizontal, Spacing = 8 };
        if (r.S("desfazer") != "") bt.Children.Add(Botao("Desfazer", true, () => Abre("desfazer")));
        if (r.S("respondido") == "" && ver != "cedo para dizer")
        {
            bt.Children.Add(Botao("Ajudou", false, async () => { await Servico.Le("responder", new { id, resposta = "sim" }); await Recarrega(); }));
            bt.Children.Add(Botao("Não ajudou", false, async () => { await Servico.Le("responder", new { id, resposta = "nao" }); await Recarrega(); }));
        }
        string quando = r.S("quando") != "" ? $" ({Quando(r.S("quando"))})" : "";
        return Linha(r.S("titulo") + quando, texto, Etiqueta(ver == "" ? "?" : ver, c), bt.Children.Count > 0 ? bt : null);
    }

    /// <summary>Mantido para quem ainda chama: o destino de um comando (sem tela própria, o Detalhe).</summary>
    public static string TelaDo(string cmd) => Rotas.Tela(cmd) ?? "inicio";
    static string Primeira(string s) => string.IsNullOrEmpty(s) ? s : Maiuscula(s);
}
