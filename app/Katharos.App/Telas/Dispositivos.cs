using System.Text.Json.Nodes;
using Avalonia;
using Avalonia.Controls;
using Avalonia.Layout;
using Avalonia.Media;
using static Katharos.App.Ui;

namespace Katharos.App.Telas;

/// <summary>
/// Mouse, teclado, fone e controle ligados agora (fase 1 do plano de dispositivos sem fio). Mostra a bateria quando o Windows já sabe
/// (Bluetooth). Nos receptores 2.4 GHz a bateria e o DPI ficam para as próximas fases, protocolo por protocolo; enquanto isso a tela diz
/// "ainda não leio" em vez de chutar. Só lê: nada é enviado ao aparelho.
/// </summary>
public class Dispositivos : Tela
{
    protected override async Task Carrega()
    {
        var cab = Cabecalho("Dispositivos", "Mouse, teclado, fone e controle. Só lê.", Botao("Ler de novo", false, async () => await Recarrega()));
        var g = Servico.Guardado("dispositivos");
        if (g != null) Desenha(cab, g); else Monta(cab, Carregando("Procurando os aparelhos ligados").secao);
        var d = await Servico.Le("dispositivos");
        // uma leitura vazia logo depois de uma cheia é falha de leitura, não aparelho que sumiu: fica a anterior (antes a tela alternava)
        if (g != null && g.A("dispositivos").Any() && !d.A("dispositivos").Any()) return;
        if (g == null || g.ToJsonString() != d?.ToJsonString()) Desenha(cab, d);
    }

    static string Tipo(string t) => t switch { "mouse" => "Mouse", "teclado" => "Teclado", "fone" => "Fone", "controle" => "Controle", "microfone" => "Microfone", "receptor" => "Receptor sem fio", _ => "Outro" };

    void Desenha(Control cab, JsonNode? d)
    {
        var ds = d.A("dispositivos").ToList();
        if (ds.Count == 0)
        {
            Monta(cab, Vazio("Nenhum aparelho encontrado", "Conecte o mouse, o teclado ou o fone (ou o receptor deles) e leia de novo."));
            return;
        }
        var principais = ds.Where(x => x.S("tipo") != "outro").ToList();
        var outros = ds.Where(x => x.S("tipo") == "outro").ToList();
        var lista = new StackPanel { Children = { Subtitulo("Ligados agora", $"{ds.Count} {(ds.Count == 1 ? "aparelho" : "aparelhos")}", "dispositivos") } };
        // fichas em duas colunas; bateria baixa primeiro
        var fichas = new Avalonia.Controls.Primitives.UniformGrid { Columns = 2 };
        foreach (var x in principais.OrderBy(x => x.D("bateria") is double b && b <= 20 || x.S("bateria_nivel") is "baixa" or "vazia" ? 0 : 1)) fichas.Children.Add(Aparelho(x));
        lista.Children.Add(new Border { Margin = new Thickness(32, 0, 32, 0), BorderBrush = Tema.Linha, BorderThickness = new Thickness(1, 1, 0, 0), Child = fichas });
        var partes = new List<Control?> { cab, G(lista) };
        if (outros.Count > 0)
        {
            var o = new StackPanel { Children = { Subtitulo("Outros", "aparelhos USB e Bluetooth que não são de entrada nem de som", "mais") } };
            var fo = new Avalonia.Controls.Primitives.UniformGrid { Columns = 2 };
            foreach (var x in outros) fo.Children.Add(Aparelho(x));
            o.Children.Add(new Border { Margin = new Thickness(32, 0, 32, 18), BorderBrush = Tema.Linha, BorderThickness = new Thickness(1, 1, 0, 0), Child = fo });
            partes.Add(G(o));
        }
        partes.Add(S(new StackPanel { Margin = new Thickness(32, 18), Spacing = 6, Children = {
            T("A bateria aparece quando o Windows sabe (Bluetooth). Controles Xbox: pelo próprio Windows. Nos receptores 2.4 GHz, a bateria e o DPI vêm marca por marca; até lá, \"ainda não leio\" em vez de chute. O Katharos só lê: nunca muda nada no aparelho.", "rotulo", quebra: true) } }));
        Monta(partes.ToArray());
    }

    static Control Aparelho(JsonNode x)
    {
        string fab = x.S("fabricante"), con = x.S("conexao") switch { "bluetooth" => "Bluetooth", "sem fio" => "sem fio", _ => "USB ou receptor" };
        string sub = string.Join(" · ", new[] { Tipo(x.S("tipo")), fab, con }.Where(s => s != ""));
        string icone = x.S("tipo") switch { "mouse" => "dispositivos", "teclado" => "teclado", "fone" => "fone", "controle" => "controle", "microfone" => "microfone", "receptor" => "receptor", _ => "mais" };
        // a ficha: ícone grande, nome, de onde é e a bateria num anel (referência: iStat Menus e Teenage Engineering)
        Control bateria;
        if (x.D("bateria") is double b)
        {
            var cor = b <= 15 ? Tema.Vermelho : b <= 30 ? Tema.Ambar : Tema.Verde;
            bateria = new Avalonia.Controls.Grid { Width = 64, Height = 64, Children = {
                new Katharos.App.Controles.Anel { Valor = b, Cor = cor, Espessura = 4 },
                T(Num(b) + "%", null, Tema.Osso, 15).Com(t => { t.FontFamily = Tema.Mono; t.HorizontalAlignment = HorizontalAlignment.Center; t.VerticalAlignment = VerticalAlignment.Center; }) } };
        }
        else if (x.S("bateria_nivel") != "")
        {
            string n = x.S("bateria_nivel");
            double v = n switch { "cheia" => 100, "média" => 60, "baixa" => 25, _ => 5 };
            bateria = new Avalonia.Controls.Grid { Width = 64, Height = 64, Children = {
                new Katharos.App.Controles.Anel { Valor = v, Cor = v <= 25 ? Tema.Vermelho : Tema.Verde, Espessura = 4 },
                T(n, "rotulo", tamanho: 11.5).Com(t => { t.HorizontalAlignment = HorizontalAlignment.Center; t.VerticalAlignment = VerticalAlignment.Center; }) } };
        }
        else bateria = T(x.S("conexao") == "bluetooth" ? "sem bateria\ninformada" : "bateria:\nainda não leio", "rotulo", tamanho: 12).Com(t => { t.TextAlignment = TextAlignment.Right; t.VerticalAlignment = VerticalAlignment.Center; });
        var meio = new StackPanel { Spacing = 3, VerticalAlignment = VerticalAlignment.Center, Children = {
            T(x.S("nome"), null, Tema.Osso, 15, true).Com(t => t.FontWeight = FontWeight.SemiBold), T(sub, "rotulo", tamanho: 12.5, quebra: true) } };
        if (!x.B("ok")) meio.Children.Add(Etiqueta("com problema", Tema.Vermelho));
        var g = new Avalonia.Controls.Grid { ColumnDefinitions = new ColumnDefinitions("Auto,*,Auto"), Children = {
            Icones.De(icone, 28, Tema.Ambar).Com(c => { c.VerticalAlignment = VerticalAlignment.Center; c.Margin = new Thickness(0, 0, 16, 0); }),
            meio.Com(m => Avalonia.Controls.Grid.SetColumn(m, 1)), bateria.Com(c => { Avalonia.Controls.Grid.SetColumn(c, 2); c.Margin = new Thickness(12, 0, 0, 0); }) } };
        var ficha = new Border { Padding = new Thickness(24, 20), BorderBrush = Tema.Linha, BorderThickness = new Thickness(0, 0, 1, 1), Child = g };
        string ids = x.S("vid") != "" ? $"VID {x.S("vid")} · PID {x.S("pid")}" : "";
        if (x.S("nome_windows") != "" && x.S("nome_windows") != x.S("nome")) ids += (ids != "" ? " · " : "") + "no Windows: " + x.S("nome_windows");
        if (ids != "") { ToolTip.SetTip(ficha, ids); ToolTip.SetShowDelay(ficha, 500); }
        return ficha;
    }
}
