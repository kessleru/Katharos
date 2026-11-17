using Avalonia;
using Avalonia.Controls;
using Avalonia.Input;
using Avalonia.Layout;
using static Katharos.App.Ui;

namespace Katharos.App;

/// <summary>
/// Ctrl+K (UI 2): digite para ir a uma tela ou a uma área do Otimizar ("serviços", "copilot", "raio-x", "desfazer"). Só navega: nada
/// muda no PC daqui. Enter abre o primeiro; as setas escolhem.
/// </summary>
public static class Paleta
{
    static readonly (string titulo, string destino, string palavras)[] Destinos =
    {
        ("Início", "inicio", "inicio começo nota propostas o que eu faria"),
        ("Raio-x", "raiox", "raio-x raiox diagnostico problema achados"),
        ("Fazer o raio-x agora", "raiox:rodar", "rodar raio-x agora ler pc"),
        ("Otimizar", "otimizar", "otimizar modos aplicar ajustes"),
        ("Otimizar: Serviços", "otimizar:servicos", "servicos serviços fax impressão"),
        ("Otimizar: Privacidade e propaganda", "otimizar:privacidade", "privacidade propaganda telemetria anuncios"),
        ("Otimizar: IA do Windows", "otimizar:ia", "ia copilot recall inteligencia"),
        ("Otimizar: Visual e barra de tarefas", "otimizar:visual", "visual barra tarefas lupa widgets"),
        ("Otimizar: Jogos", "otimizar:jogos", "jogos game mode xbox fps"),
        ("Otimizar: Energia", "otimizar:energia", "energia plano desempenho"),
        ("Otimizar: Inicialização", "otimizar:inicializacao", "inicializacao boot iniciar com windows"),
        ("Otimizar: Rede e DNS", "otimizar:rede", "rede dns internet ping"),
        ("Otimizar: Limpeza (manutenção)", "otimizar:limpar", "limpeza limpar temporarios lixo"),
        ("Programas que abrem com o Windows", "inicializacao", "inicializacao programas startup"),
        ("Ao vivo", "aovivo", "ao vivo agora cpu gpu temperatura"),
        ("Memória", "memoria", "memoria ram programas"),
        ("Jogos", "jogos", "jogos sessoes fps"),
        ("Histórico", "historico", "historico grafico medidas calendario"),
        ("Desfazer", "desfazer", "desfazer voltar reverter"),
        ("Enviar relatório", "enviar", "enviar relatorio feedback erro"),
        ("Configurações", "config", "configuracoes preferencias conferir autoteste"),
    };

    static string Limpa(string s) => new string(s.ToLowerInvariant().Normalize(System.Text.NormalizationForm.FormD)
        .Where(c => System.Globalization.CharUnicodeInfo.GetUnicodeCategory(c) != System.Globalization.UnicodeCategory.NonSpacingMark).ToArray());

    public static void Abre(Janela j)
    {
        var caixa = new TextBox { Watermark = "Ir para… (ex.: serviços, copilot, desfazer)", FontSize = 15, MinWidth = 420 };
        var lista = new StackPanel { Spacing = 2, Margin = new Thickness(0, 10, 0, 0) };
        int escolhido = 0;
        List<(string titulo, string destino, string palavras)> achados = Destinos.ToList();
        void Vai(string destino) { j.FechaCaixa(); j.Mostra(destino); }
        void Desenha()
        {
            var q = Limpa(caixa.Text ?? "").Trim();
            achados = q == "" ? Destinos.ToList()
                : Destinos.Where(d => q.Split(' ', StringSplitOptions.RemoveEmptyEntries).All(p => Limpa(d.titulo + " " + d.palavras).Contains(p))).ToList();
            escolhido = Math.Clamp(escolhido, 0, Math.Max(0, achados.Count - 1));
            lista.Children.Clear();
            if (achados.Count == 0) { lista.Children.Add(T("Nada com esse nome.", "rotulo")); return; }
            for (int i = 0; i < Math.Min(8, achados.Count); i++)
            {
                var d = achados[i];
                var b = new Button { Content = T(d.titulo, null, i == escolhido ? Tema.Ambar : Tema.Osso, 14), HorizontalAlignment = HorizontalAlignment.Stretch,
                                     HorizontalContentAlignment = HorizontalAlignment.Left, Background = i == escolhido ? Tema.AmbarFraco : Avalonia.Media.Brushes.Transparent,
                                     Padding = new Thickness(10, 7) };
                string destino = d.destino;
                b.Click += (_, _) => Vai(destino);
                lista.Children.Add(b);
            }
        }
        caixa.TextChanged += (_, _) => { escolhido = 0; Desenha(); };
        caixa.KeyDown += (_, e) =>
        {
            if (e.Key == Key.Down) { escolhido++; Desenha(); e.Handled = true; }
            else if (e.Key == Key.Up) { escolhido--; Desenha(); e.Handled = true; }
            else if (e.Key == Key.Enter && achados.Count > 0) { Vai(achados[escolhido].destino); e.Handled = true; }
        };
        Desenha();
        j.MostraCaixa(Janela.Caixa("Ir para", new StackPanel { Children = { caixa, lista } }), true);
        Avalonia.Threading.Dispatcher.UIThread.Post(() => caixa.Focus());
    }
}
