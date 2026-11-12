using System.Text.Json.Nodes;
using Avalonia;
using Avalonia.Controls;
using Avalonia.Input;
using Avalonia.Layout;
using Avalonia.Media;
using static Katharos.App.Ui;

namespace Katharos.App.Telas;

/// <summary>
/// Central de inteligência (I17, I18, I25): o diagnóstico (o que eu vi, por que acho que é isso, o que eu faria, o que mudaria a minha
/// conclusão), as propostas com previsão, risco e como desfazer, a linha do tempo do que foi aplicado (previsto x aconteceu) e a caixa
/// "pergunte ao Katharos". Tudo vem do motor deste PC; nada muda sem a pessoa.
/// </summary>
public class Sugestoes : Tela
{
    protected override async Task Carrega()
    {
        var cab = Cabecalho("Central", null);
        Monta(cab, Carregando("Pensando com as medidas deste PC").secao);
        var d = await Servico.Le("sugestoes");
        var diags = d.A("diagnosticos").ToList();
        var props = d.A("propostas").ToList();
        var tempo = d.A("linha_do_tempo").ToList();
        var res = d.A("resultados").ToList();

        Control? diagnostico = null;
        if (diags.Count > 0)
        {
            var p = new StackPanel { Children = { Subtitulo("Diagnóstico", null, "alvo") } };
            foreach (var g in diags) p.Children.Add(Diagnostico(g));
            diagnostico = G(p);
        }

        Control? propostas = null;
        if (props.Count > 0)
        {
            var p = new StackPanel { Children = { Subtitulo("O que eu faria", null, "lampada") } };
            foreach (var x in props) p.Children.Add(Proposta(x));
            propostas = G(p);
        }

        // o que foi aplicado: previsto x aconteceu (verde, cinza ou vermelho), com o desfazer onde piorou e o "ajudou?"
        Control? linha = null;
        if (tempo.Count > 0 || res.Count > 0)
        {
            var p = new StackPanel { Children = { Subtitulo("O que eu previ e o que aconteceu", "7 dias antes contra 7 depois.", "grafico") } };
            foreach (var r in tempo.Count > 0 ? tempo : res) p.Children.Add(Resultado(r));
            linha = G(p);
        }

        if (diagnostico == null && propostas == null && linha == null)
        {
            Monta(cab, Pergunta(), Vazio("Ainda não sei", "Para concluir algo com confiança, eu preciso de alguns dias de medida (o acompanhamento ligado) ou de algumas sessões de jogo. Sem número, eu não proponho nada.",
                                         Botao("Ver o acompanhamento", false, () => Abre("aovivo"))));
            return;
        }
        Monta(cab, diagnostico, propostas, linha, Pergunta());
    }

    static Control Bloco(string rotulo, string texto) => new StackPanel { Spacing = 2, Children = { T(rotulo, "rotulo"), T(texto, null, Tema.Osso, 14, true) } };

    Control Diagnostico(JsonNode g)
    {
        string conf = g.S("confianca");
        var ev = string.Join("; ", g.A("evidencias").Select(x => x.ToString()));
        var desc = g.A("descartadas").Select(x => $"{x.S("causa")} ({x.S("motivo")})").ToList();
        var corpo = new StackPanel { Spacing = 10, Margin = new Thickness(0, 6, 0, 0) };
        corpo.Children.Add(Bloco("O que eu vi", Primeira(ev) + "."));
        corpo.Children.Add(Bloco("Por que acho que é isso", $"A causa com mais evidência é {g.S("nome")}." + (desc.Count > 0 ? " Descartei: " + string.Join("; ", desc) + "." : "")));
        corpo.Children.Add(Bloco("O que eu faria", Primeira(g.S("faria")) + "."));
        corpo.Children.Add(Bloco("O que mudaria a minha conclusão", Primeira(g.S("mudaria")) + "."));
        var cab = new Grid { ColumnDefinitions = new ColumnDefinitions("*,Auto"), Children = { T($"{g.S("titulo")}: {g.S("nome")}", "forte", tamanho: 17) } };
        cab.Children.Add(Etiqueta("confiança " + conf, conf == "alta" ? Tema.Verde : conf == "média" ? Tema.Ambar : Tema.Apagado).Com(e => Grid.SetColumn(e, 1)));
        return new Border { Padding = new Thickness(32, 18), BorderBrush = Tema.Linha, BorderThickness = new Thickness(0, 1, 0, 0), Child = new StackPanel { Children = { cab, corpo } } };
    }

    Control Proposta(JsonNode x)
    {
        string conf = x.S("confianca"), id = x.S("id"), cmd = x.S("comando");
        var exp = x["explicacao"];
        string area = cmd.Split(' ')[0];
        var bt = new StackPanel { Orientation = Orientation.Horizontal, Spacing = 8 };
        bt.Children.Add(Botao("Agora não", false, async () => { await Servico.Le("dispensar", new { id }); await Recarrega(); }).Com(b => ToolTip.SetTip(b, "Esconde por 30 dias.")));
        bt.Children.Add(Botao("Não me importa", false, async () => { await Servico.Le("responder", new { id, resposta = "nao-importa" }); await Recarrega(); }).Com(b => ToolTip.SetTip(b, "Não proponho mais isto.")));
        bt.Children.Add(Detalhe.Botoes(x, Abre, "Central"));
        var texto = new List<string> { exp.S("vi", x.S("porque")) };
        if (exp.S("faria") != "") texto.Add("O que eu faria: " + exp.S("faria"));
        var prev = x["previsao"];
        if (prev.S("texto") != "") texto.Add("O que espero: " + prev.S("texto") + ".");
        if (x.S("risco") != "") texto.Add("Risco: " + x.S("risco") + ".");
        if (x.S("desfazer") != "") texto.Add("Como desfazer: " + ComoDesfazer(x.S("desfazer")) + ".");
        // o que é certo (o Windows registrou) separado do que é provável (a causa): nunca "confiança alta" numa causa que só se investiga
        var selo = x.S("certeza") != "" ? Etiqueta("aconteceu · causa " + x.S("causa", "provável"), Tema.Ambar)
                                         : Etiqueta("confiança " + conf, conf == "alta" ? Tema.Verde : conf == "média" ? Tema.Ambar : Tema.Apagado);
        return Linha(x.S("titulo"), string.Join("\n", texto), selo, bt);
    }

    Control Resultado(JsonNode r)
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

    // "Pergunte ao Katharos": responde com o que o motor concluiu neste PC e os comandos que tratam do assunto. Nada sai do PC.
    Control Pergunta()
    {
        var caixa = new TextBox { Watermark = "Por que meu jogo trava?", MinWidth = 360, FontSize = 15 };
        var resposta = new StackPanel { Spacing = 8, Margin = new Thickness(0, 12, 0, 0) };
        async Task Pergunta()
        {
            string q = (caixa.Text ?? "").Trim();
            if (q.Length < 3) return;
            resposta.Children.Clear();
            resposta.Children.Add(T("Pensando...", "rotulo"));
            try
            {
                var r = await Servico.Le("perguntar", new { texto = q });
                resposta.Children.Clear();
                resposta.Children.Add(T(r.S("resposta"), null, Tema.Osso, 15, true));
                var cmds = r.A("comandos").Take(4).ToList();
                if (cmds.Count > 0)
                {
                    var bts = new WrapPanel();
                    foreach (var c in cmds)
                    {
                        string area = c.S("area"), tipo = c.S("tipo");
                        string destino = tipo == "item" ? "otimizar:" + area : Rotas.Tela(c.S("id")) ?? "";
                        var cc = c; 
                        bts.Children.Add(Botao(Primeira(c.S("titulo")), false, () =>
                        {
                            if (destino != "") Abre(destino);
                            else { Detalhe.Prepara(new JsonObject { ["titulo"] = cc.S("titulo"), ["comando"] = cc.S("id"), ["origem"] = "Pergunte ao Katharos" }, "resolver"); Abre("detalhe"); }
                        }).Com(b => b.Margin = new Thickness(0, 0, 8, 8)));
                    }
                    resposta.Children.Add(bts);
                }
            }
            catch (Exception e) { resposta.Children.Clear(); resposta.Children.Add(T("Não consegui responder: " + e.Message, "rotulo", quebra: true)); }
        }
        caixa.KeyDown += async (_, e) => { if (e.Key == Key.Enter) await Pergunta(); };
        var linha = new StackPanel { Orientation = Orientation.Horizontal, Spacing = 10, Children = { caixa, Botao("Perguntar", true, async () => await Pergunta()) } };
        return S(new StackPanel { Margin = new Thickness(32, 22, 32, 26), Children = { T("Pergunte ao Katharos", "forte"), T("Responde com o que ele mediu neste PC. Nada sai do computador.", "rotulo").Com(t => t.Margin = new Thickness(0, 2, 0, 10)), linha, resposta } });
    }

    /// <summary>Mantido para quem ainda chama: o destino de um comando (sem tela própria, o Detalhe).</summary>
    public static string TelaDo(string cmd) => Rotas.Tela(cmd) ?? "sugestoes";
    static string Primeira(string s) => string.IsNullOrEmpty(s) ? s : Maiuscula(s);
}
