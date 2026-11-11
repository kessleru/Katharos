using Avalonia;
using Avalonia.Controls;
using Avalonia.Input;
using Avalonia.Interactivity;
using Avalonia.Layout;
using Avalonia.Markup.Xaml;
using Avalonia.Threading;
using Katharos.App.Telas;
using static Katharos.App.Ui;

namespace Katharos.App;

public partial class Janela : Window
{
    public static Janela? Atual { get; private set; }
    readonly DispatcherTimer relogio = new() { Interval = TimeSpan.FromSeconds(2) };
    TaskCompletionSource<bool>? resposta;
    bool caixaFechavel;

    public Janela()
    {
        AvaloniaXamlLoader.Load(this);
        Atual = this;
        foreach (var b in Botoes()) b.Click += Navega;
        this.FindControl<TextBlock>("Versao")!.Text = typeof(Janela).Assembly.GetName().Version is { } v ? $"{v.Major}.{v.Minor}" : "4.0";
        relogio.Tick += (_, _) => AtualizaEstado();
        relogio.Start();
        AtualizaEstado();
        KeyDown += (_, e) => { if (e.Key == Key.Escape && caixaFechavel && resposta != null) Responde(false); };
        Closing += async (_, _) => await Servico.Fecha();
        Mostra("inicio");
        Opened += async (_, _) =>
        {
            try { var c = await Servico.Le("config_ler"); await Atualizacao.Confere(c?["atualizacoes"].S("valor", "avisar") ?? "avisar"); }
            catch (Exception e) { Registro.Escreve("atualização: " + e.Message); }
        };
        Atualizacao.Mudou += () => Dispatcher.UIThread.Post(() => { if (this.FindControl<ContentControl>("Tela")!.Content is Inicio i) _ = i.Recarrega(); });
    }

    /// <summary>A raiz da janela (as fotos e os vídeos põem por cima o cursor e movem a câmera aqui).</summary>
    public Grid Raiz => this.FindControl<Grid>("RaizGrade")!;

    IEnumerable<Button> Botoes() => this.FindControl<StackPanel>("Nav")!.Children.OfType<Button>().Append(this.FindControl<Button>("BtConfig")!);

    void Navega(object? o, RoutedEventArgs e)
    {
        if (o is Button b && b.Tag is string t) Mostra(t);
    }

    /// <summary>Troca a tela. "otimizar:servicos" abre Otimizar com a área de serviços aberta.</summary>
    public void Mostra(string pedido)
    {
        var partes = pedido.Split(':', 2);
        string tela = partes[0], arg = partes.Length > 1 ? partes[1] : "";
        Tela c = tela switch
        {
            "raiox" => new Raiox(arg == "rodar"),
            "otimizar" => new Otimizar(arg),
            "aovivo" => new AoVivo(),
            "jogos" => new Jogos(),
            "sugestoes" => new Sugestoes(),
            "desfazer" => new Desfazer(),
            "config" => new Configuracoes(),
            "aviso" => new Aviso(arg),
            _ => new Inicio(),
        };
        c.Pede += Mostra;
        this.FindControl<ContentControl>("Tela")!.Content = c;
        foreach (var b in Botoes()) b.Classes.Set("ativo", (string?)b.Tag == (tela == "aviso" ? "otimizar" : tela));
    }

    /// <summary>O estado do acompanhamento, lido do arquivo que o segundo plano grava (nunca o que foi pedido: o que está acontecendo).</summary>
    void AtualizaEstado()
    {
        var a = Servico.Agora();
        var luz = this.FindControl<Avalonia.Controls.Shapes.Ellipse>("Luz")!;
        var est = this.FindControl<TextBlock>("Estado")!;
        var mais = this.FindControl<TextBlock>("EstadoMais")!;
        if (a == null) { luz.Fill = Tema.Apagado; est.Text = "Acompanhamento desligado"; mais.Text = "ligue em Ao vivo"; return; }
        luz.Fill = Tema.Verde;
        est.Text = a["jogo"] is { } j ? "Jogando: " + j.S("nome") : "Acompanhando o PC";
        mais.Text = "leve: " + Num(a["segundo_plano"].D("cpu_pct"), 1) + " % da CPU";
    }

    // ───── painel por cima (confirmação, progresso, resultado) ─────

    public void MostraCaixa(Control conteudo, bool fechavel = false)
    {
        caixaFechavel = fechavel;
        this.FindControl<ContentControl>("CaixaConteudo")!.Content = conteudo;
        this.FindControl<Border>("Veu")!.IsVisible = true;
    }

    public void FechaCaixa()
    {
        this.FindControl<Border>("Veu")!.IsVisible = false;
        this.FindControl<ContentControl>("CaixaConteudo")!.Content = null;
    }

    /// <summary>Pergunta com dois botões que dizem o que fazem. Esc = não.</summary>
    public Task<bool> Confirma(string titulo, Control corpo, string sim, string nao = "Voltar", bool perigo = false)
    {
        resposta = new TaskCompletionSource<bool>();
        var b = new StackPanel { Orientation = Orientation.Horizontal, Spacing = 10, HorizontalAlignment = HorizontalAlignment.Right, Margin = new Thickness(0, 18, 0, 0) };
        b.Children.Add(Botao(nao, false, () => Responde(false)));
        var bs = Botao(sim, true, () => Responde(true));
        if (perigo) { bs.Classes.Remove("primario"); bs.Classes.Add("contorno"); bs.Foreground = Tema.Vermelho; bs.BorderBrush = Tema.Vermelho; }
        b.Children.Add(bs);
        MostraCaixa(Caixa(titulo, corpo, b), true);
        bs.Focus();
        return resposta.Task;
    }

    void Responde(bool r)
    {
        var x = resposta; resposta = null;
        FechaCaixa();
        x?.TrySetResult(r);
    }

    public static Control Caixa(string titulo, Control corpo, Control? rodape = null)
    {
        var p = new StackPanel { Margin = new Thickness(28, 24), Spacing = 10 };
        p.Children.Add(T(titulo, "forte", tamanho: 19, quebra: true));
        p.Children.Add(corpo);
        if (rodape != null) p.Children.Add(rodape);
        return new ScrollViewer { Content = p, HorizontalScrollBarVisibility = Avalonia.Controls.Primitives.ScrollBarVisibility.Disabled };
    }
}
