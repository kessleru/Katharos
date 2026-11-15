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
        if (g == null || g.ToJsonString() != d?.ToJsonString()) Desenha(cab, d);
    }

    static string Tipo(string t) => t switch { "mouse" => "Mouse", "teclado" => "Teclado", "fone" => "Fone", "controle" => "Controle", "receptor" => "Receptor sem fio", _ => "Outro" };

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
        foreach (var x in principais) lista.Children.Add(Aparelho(x));
        var partes = new List<Control?> { cab, G(lista) };
        if (outros.Count > 0)
        {
            var o = new StackPanel { Children = { Subtitulo("Outros", "aparelhos USB e Bluetooth que não são de entrada nem de som", "mais") } };
            foreach (var x in outros) o.Children.Add(Aparelho(x));
            partes.Add(G(o));
        }
        partes.Add(S(new StackPanel { Margin = new Thickness(32, 18), Spacing = 6, Children = {
            T("A bateria aparece quando o Windows sabe (Bluetooth). Nos receptores 2.4 GHz, a bateria e o DPI vêm nas próximas versões, marca por marca; até lá, \"ainda não leio\" em vez de chute.", "rotulo", quebra: true) } }));
        Monta(partes.ToArray());
    }

    static Control Aparelho(JsonNode x)
    {
        string fab = x.S("fabricante"), con = x.S("conexao") == "bluetooth" ? "Bluetooth" : "USB ou receptor";
        string sub = string.Join(" · ", new[] { Tipo(x.S("tipo")), fab, con }.Where(s => s != ""));
        Control direita;
        if (x.D("bateria") is double b)
        {
            var cor = b <= 15 ? Tema.Vermelho : b <= 30 ? Tema.Ambar : Tema.Verde;
            direita = new StackPanel { Spacing = 4, HorizontalAlignment = HorizontalAlignment.Right, Children = {
                T(Num(b) + " %", null, Tema.Osso, 17).Com(t => { t.FontFamily = Tema.Mono; t.HorizontalAlignment = HorizontalAlignment.Right; }),
                new ProgressBar { Minimum = 0, Maximum = 100, Value = b, Width = 90, Height = 4, MinHeight = 4, Foreground = cor, Background = Tema.Linha, CornerRadius = new CornerRadius(0) } } };
        }
        else direita = T(x.S("conexao") == "bluetooth" ? "sem bateria informada" : "bateria: ainda não leio", "rotulo", tamanho: 12.5);
        var linha = Linha(x.S("nome"), sub, x.B("ok") ? null : Etiqueta("com problema", Tema.Vermelho), direita, x.S("tipo") switch { "mouse" => "dispositivos", "teclado" => "teclado", "fone" => "fone", "controle" => "controle", _ => "mais" });
        string ids = x.S("vid") != "" ? $"VID {x.S("vid")} · PID {x.S("pid")}" : "";
        if (x.S("nome_windows") != "" && x.S("nome_windows") != x.S("nome")) ids += (ids != "" ? " · " : "") + "no Windows: " + x.S("nome_windows");
        if (ids != "") { ToolTip.SetTip(linha, ids); ToolTip.SetShowDelay(linha, 500); }
        return linha;
    }
}
