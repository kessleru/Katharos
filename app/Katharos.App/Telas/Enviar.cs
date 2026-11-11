using System.Text.Json.Nodes;
using Avalonia;
using Avalonia.Controls;
using Avalonia.Controls.Primitives;
using Avalonia.Layout;
using Avalonia.Media;
using static Katharos.App.Ui;

namespace Katharos.App.Telas;

/// <summary>
/// Enviar: o relatório do Katharos, a opinião da pessoa, ou os dois juntos. O motor monta o pacote já limpo de dado pessoal; a pessoa
/// vê o resumo e o JSON exato antes de mandar; só sai quando ela clica em Enviar. Sem internet, fica guardado para mandar depois.
/// </summary>
public class Enviar : Tela
{
    readonly string referencia;
    string tipo = "ambos", fbTipo = "problema";
    int? nota;
    readonly HashSet<string> secoes = new();
    bool primeira = true;
    readonly TextBox texto = new()
    {
        AcceptsReturn = true, TextWrapping = TextWrapping.Wrap, MinHeight = 120, MaxHeight = 280, MaxLength = 4000,
        Watermark = "O que aconteceu, o que você esperava que acontecesse, ou o que gostaria que o Katharos fizesse.",
    };
    readonly TextBox contato = new() { Watermark = "Opcional: e-mail ou Discord, se quiser resposta", MaxLength = 120, MinWidth = 340 };

    public Enviar(string arg = "")
    {
        referencia = arg;
        if (arg != "") texto.Text = $"Apareceu o erro {arg}. ";
    }

    protected override async Task Carrega()
    {
        var cab = Cabecalho("Enviar relatório", "Mande o relatório do Katharos, a sua opinião, ou os dois. Ajuda a consertar erros e a saber o que funciona de verdade. Nada sai sem você ver antes.");
        Monta(cab, Carregando("Lendo").secao);
        var d = await Servico.Le("envio_secoes");
        if (primeira) { primeira = false; foreach (var s in d.A("secoes")) secoes.Add(s.S("id")); }
        Desenha(cab, d);
    }

    static void Solta(Control c) { if (c.Parent is Panel p) p.Children.Remove(c); }

    void Desenha(Control cab, JsonNode? d)
    {
        Solta(texto); Solta(contato);
        void Refaz() => Desenha(cab, d);

        // 1. o que mandar
        var cartoes = new UniformGrid { Columns = 3, Margin = new Thickness(32, 0, 32, 26) };
        foreach (var (id, nome, explica) in new[] {
            ("ambos", "Relatório e feedback", "O relatório do Katharos e o que você tem a dizer. É o que mais ajuda."),
            ("relatorio", "Só o relatório", "Erros, o que foi aplicado e o que cada otimização rendeu neste PC."),
            ("feedback", "Só o feedback", "Um problema, uma ideia ou um elogio, sem dados do PC.") })
            cartoes.Children.Add(Cartao(nome, explica, tipo == id, () => { tipo = id; Refaz(); }));
        var partes = new List<Control?> { cab, S(new StackPanel { Children = { Subtitulo("1. O que mandar"), cartoes } }) };

        // 2. o feedback
        if (tipo != "relatorio")
        {
            var tipos = new StackPanel { Orientation = Orientation.Horizontal, Spacing = 8 };
            foreach (var (id, rot) in new[] { ("problema", "Problema"), ("ideia", "Ideia"), ("elogio", "Elogio"), ("outro", "Outro") })
                tipos.Children.Add(Botao(rot, fbTipo == id, () => { fbTipo = id; Refaz(); }));
            var notas = new StackPanel { Orientation = Orientation.Horizontal, Spacing = 6 };
            for (int i = 1; i <= 5; i++) { int n = i; notas.Children.Add(Botao(n.ToString(), nota == n, () => { nota = nota == n ? null : n; Refaz(); })); }
            var f = new StackPanel { Spacing = 14, Margin = new Thickness(32, 0, 32, 26), Children = {
                Rotulado("É sobre", tipos), Rotulado("Conte", texto),
                Rotulado("Como está o Katharos para você? (opcional, de 1 a 5)", notas), Rotulado("Para eu te responder", contato) } };
            partes.Add(S(new StackPanel { Children = { Subtitulo("2. O seu feedback"), f } }));
        }

        // 3. o relatório
        if (tipo != "feedback")
        {
            var lista = new StackPanel { Margin = new Thickness(32, 0, 32, 22), Spacing = 10 };
            foreach (var s in d.A("secoes"))
            {
                string id = s.S("id");
                var cx = new CheckBox { IsChecked = secoes.Contains(id), Content = new StackPanel { Spacing = 2, Children = {
                    T(s.S("titulo"), null, Tema.Osso, 15).Com(t => t.FontWeight = FontWeight.SemiBold), T(s.S("explica"), "rotulo", tamanho: 13.5, quebra: true) } } };
                cx.IsCheckedChanged += (_, _) => { if (cx.IsChecked == true) secoes.Add(id); else secoes.Remove(id); };
                lista.Children.Add(cx);
            }
            partes.Add(S(new StackPanel { Children = { Subtitulo(tipo == "ambos" ? "3. O que o relatório leva" : "2. O que o relatório leva",
                "Tudo vem do que o Katharos já guardou neste PC. Desmarque o que não quiser mandar."), lista } }));
        }

        // a ação, com para onde vai e o que nunca vai
        var privacidade = T("Vai para um repositório privado do criador do Katharos. Não vai: o seu nome de usuário, o nome do PC, e-mail (só o contato que você escrever), IP, arquivos ou pastas pessoais. "
                            + "Um número aleatório deste PC vai junto, só para contar PCs diferentes. Antes de sair você vê o texto exato. Para apagar um envio, mande o código dele num feedback.", "rotulo", quebra: true);
        var acao = new Grid { ColumnDefinitions = new ColumnDefinitions("*,Auto"), Margin = new Thickness(32, 22), Children = {
            privacidade.Com(t => { t.MaxWidth = 720; t.HorizontalAlignment = HorizontalAlignment.Left; t.VerticalAlignment = VerticalAlignment.Center; }),
            Botao("Revisar e enviar", true, async () => await Revisa(cab, d)).Com(b => { Grid.SetColumn(b, 1); b.Margin = new Thickness(24, 0, 0, 0); }) } };
        partes.Add(S(acao));

        // esperando para enviar (sem internet na hora) e os já enviados
        var pend = Envio.Pendentes();
        if (pend.Count > 0)
        {
            var p = new StackPanel { Children = { Subtitulo("Esperando para enviar", "Não deu para mandar na hora (sem internet ou o servidor fora). Só sai quando você clicar.") } };
            foreach (var (arq, quando, t) in pend)
            {
                var bts = new StackPanel { Orientation = Orientation.Horizontal, Spacing = 8, Children = {
                    Botao("Enviar agora", true, async () => await MandaPendente(arq, t)),
                    Botao("Apagar", false, () => { Envio.Apaga(arq); _ = Recarrega(); }) } };
                p.Children.Add(Linha(Nome(t), quando == default ? "" : "guardado " + Quando(quando.ToString("s")), null, bts));
            }
            partes.Add(S(p));
        }
        var env = d.A("envios").ToList();
        if (env.Count > 0)
        {
            var p = new StackPanel { Children = { Subtitulo("Já enviados deste PC", "Guarde o código: com ele dá para pedir para apagar o envio.") } };
            foreach (var x in env.Take(10))
            {
                string cod = x.S("codigo");
                p.Children.Add(Linha(cod, $"{Nome(x.S("tipo"))} · {Quando(x.S("quando"))} · Katharos {x.S("versao")}", null, Botao("Copiar código", false, async () => await Copia(cod))));
            }
            partes.Add(S(p));
        }
        Monta(partes.ToArray());
    }

    static string Nome(string t) => t switch { "ambos" => "Relatório e feedback", "feedback" => "Feedback", "relatorio" => "Relatório", _ => "Envio" };

    static Control Rotulado(string rotulo, Control c) => new StackPanel { Spacing = 6, Children = { T(rotulo, "rotulo"), c } };

    static Control Cartao(string nome, string explica, bool esc, Action clique)
    {
        var topo = new Grid { ColumnDefinitions = new ColumnDefinitions("*,Auto"), Children = { T(nome, "forte", tamanho: 16, quebra: true) } };
        if (esc) topo.Children.Add(T("escolhido", null, Tema.Ambar, 12).Com(t => { t.FontFamily = Tema.Mono; t.Margin = new Thickness(10, 3, 0, 0); Grid.SetColumn(t, 1); }));
        var b = new Button
        {
            Padding = new Thickness(0), Margin = new Thickness(0, 0, 12, 0), Background = Brushes.Transparent,
            HorizontalAlignment = HorizontalAlignment.Stretch, HorizontalContentAlignment = HorizontalAlignment.Stretch,
            Content = new Border
            {
                BorderBrush = esc ? Tema.Ambar : Tema.Linha, Background = esc ? Tema.AmbarFraco : Brushes.Transparent, BorderThickness = new Thickness(1),
                CornerRadius = new CornerRadius(2), Padding = new Thickness(20, 18), Child = new StackPanel { Spacing = 6, Children = { topo, T(explica, null, null, 14, true) } },
            },
        };
        b.Click += (_, _) => clique();
        return b;
    }

    /// <summary>Monta pelo motor, mostra o resumo e o JSON exato, e só manda se a pessoa clicar em Enviar.</summary>
    async Task Revisa(Control cab, JsonNode? d)
    {
        var j = Janela.Atual!;
        var r = await Servico.Le("envio_montar", new { tipo, secoes = secoes.ToArray(), feedback = new { tipo = fbTipo, texto = texto.Text ?? "", nota, contato = contato.Text ?? "" } });
        string json = r?["pacote"]?.ToJsonString() ?? "";
        var corpo = new StackPanel { Spacing = 8 };
        foreach (var x in r.A("resumo"))
            corpo.Children.Add(new TextBlock { TextWrapping = TextWrapping.Wrap, FontSize = 14, Foreground = Tema.Texto, Inlines = new Avalonia.Controls.Documents.InlineCollection {
                new Avalonia.Controls.Documents.Run(x.S("titulo") + ": ") { Foreground = Tema.Osso, FontWeight = FontWeight.SemiBold }, new Avalonia.Controls.Documents.Run(x.S("texto")) } });
        corpo.Children.Add(T($"{Num((r.D("bytes") ?? 0) / 1024.0, 1)} KB, já sem dado pessoal" + (r?["pacote"]?["encurtado"] != null ? "; as listas mais longas foram encurtadas para caber" : "") + ".", "rotulo", quebra: true));
        var exato = new SelectableTextBlock { Text = r.S("json"), FontFamily = Tema.Mono, FontSize = 11.5, Foreground = Tema.Texto, TextWrapping = TextWrapping.Wrap };
        corpo.Children.Add(new Expander { Header = "Ver o texto exato que vai sair", HorizontalAlignment = HorizontalAlignment.Stretch, Margin = new Thickness(0, 6, 0, 0),
            Content = new ScrollViewer { MaxHeight = 240, Content = exato } });
        if (!await j.Confirma(tipo == "feedback" ? "Mandar o feedback?" : tipo == "relatorio" ? "Mandar o relatório?" : "Mandar o relatório e o feedback?", corpo, "Enviar")) return;
        await Manda(json, tipo, null);
    }

    async Task MandaPendente(string arq, string t)
    {
        string json;
        try { json = await File.ReadAllTextAsync(arq); }
        catch (Exception e) { MostraErro(e, "Não deu para ler o envio guardado"); return; }
        await Manda(json, t, arq);
    }

    async Task Manda(string json, string t, string? pendente)
    {
        var j = Janela.Atual!;
        j.MostraCaixa(Janela.Caixa("Enviando", Andamento("Mandando para o servidor do Katharos").painel));
        Trabalho.Comeca("Enviando…");
        try
        {
            string codigo = await Envio.Manda(json);
            if (pendente != null) Envio.Apaga(pendente);
            try { await Servico.Le("envio_registrar", new { codigo, tipo = t }); } catch (Exception e) { Registro.Escreve("registrar envio: " + e.Message); }
            var cod = new SelectableTextBlock { Text = codigo, FontFamily = Tema.Mono, FontSize = 26, Foreground = Tema.Ambar };
            var corpo = new StackPanel { Spacing = 10, Children = { T("Chegou. Obrigado: é com isso que o Katharos melhora.", "sub", quebra: true), cod,
                T("Guarde o código. Com ele dá para pedir para apagar o envio. Ele também fica nesta tela.", "rotulo", quebra: true) } };
            j.MostraCaixa(Janela.Caixa("Enviado", corpo, new StackPanel { Orientation = Orientation.Horizontal, Spacing = 10, HorizontalAlignment = HorizontalAlignment.Right, Margin = new Thickness(0, 12, 0, 0),
                Children = { Botao("Copiar código", false, async () => await Copia(codigo)), Botao("Fechar", true, () => { j.FechaCaixa(); _ = Recarrega(); }) } }), true);
            if (pendente == null && t != "relatorio") { texto.Text = ""; nota = null; }
        }
        catch (Exception e)
        {
            string? guardado = null;
            if (pendente == null) try { guardado = Envio.Guarda(json, t); } catch (Exception x) { Registro.Escreve("guardar envio: " + x.Message); }
            MostraErro(e, "Não deu para enviar agora", guardado != null || pendente != null
                ? "Nada foi enviado. O envio ficou guardado neste PC, em \"Esperando para enviar\" nesta tela: mande de lá quando quiser."
                : "Nada foi enviado.");
            _ = Recarrega();
        }
        finally { Trabalho.Termina(); }
    }
}
