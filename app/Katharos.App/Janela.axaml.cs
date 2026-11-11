using Avalonia;
using System.Text.Json.Nodes;
using Avalonia.Controls;
using Avalonia.Controls.Documents;
using Avalonia.Input;
using Avalonia.Interactivity;
using Avalonia.Layout;
using Avalonia.Markup.Xaml;
using Avalonia.Media;
using Avalonia.Threading;
using Katharos.App.Telas;
using static Katharos.App.Ui;

namespace Katharos.App;

public partial class Janela : Window
{
    public static Janela? Atual { get; private set; }
    readonly DispatcherTimer relogio = new() { Interval = TimeSpan.FromSeconds(2) };
    TaskCompletionSource<bool>? resposta;
    bool caixaFechavel, lendoAgora;
    JsonNode? ultimoAgora = Servico.Agora();

    public Janela()
    {
        AvaloniaXamlLoader.Load(this);
        Atual = this;
        foreach (var b in Botoes()) b.Click += Navega;
        this.FindControl<TextBlock>("Versao")!.Text = typeof(Janela).Assembly.GetName().Version is { } v ? $"{v.Major}.{v.Minor}.{v.Build}" : "4.1.0";
        relogio.Tick += async (_, _) =>
        {
            if (!lendoAgora)
            {   // lido fora da linha da tela: um disco lento nunca trava a janela
                lendoAgora = true;
                try { ultimoAgora = await Task.Run(Servico.Agora); } finally { lendoAgora = false; }
            }
            AtualizaEstado();
            if (SegundoPlano.TelaPedida() is string t) { Mostra(t); if (WindowState == WindowState.Minimized) WindowState = WindowState.Normal; Activate(); }
        };
        relogio.Start();
        AtualizaEstado();
        KeyDown += (_, e) => { if (e.Key == Key.Escape && caixaFechavel) { if (resposta != null) Responde(false); else FechaCaixa(); } };
        Closing += async (_, _) => { if (Atualizacao.AoFechar) SegundoPlano.PedeParaSair(reabrir: true); await Servico.Fecha(); };
        Mostra(Program.TelaInicial);
        Opened += async (_, _) =>
        {
            if (!Servico.Exemplo) await SegundoPlano.ReabreSePreciso();
            try { var c = await Servico.Le("config_ler"); await Atualizacao.Confere(c?["atualizacoes"].S("valor", "avisar") ?? "avisar", c?["canal"].S("valor", "estavel") ?? "estavel"); }
            catch (Exception e) { Registro.Escreve("atualização: " + e.Message); }
            // depois de atualizar: o que mudou, uma vez por versão (instalação nova não mostra)
            if (!Servico.Exemplo) await MostraNovidades(soSePrecisa: true);
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
            "historico" => new Historico(),
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
    public void AtualizaEstado()
    {
        var luz = this.FindControl<Avalonia.Controls.Shapes.Ellipse>("Luz")!;
        var est = this.FindControl<TextBlock>("Estado")!;
        var mais = this.FindControl<TextBlock>("EstadoMais")!;
        // trabalhando de verdade (não esperando a pessoa responder a uma pergunta)
        if (Trabalho.Ativo && resposta == null) { luz.Fill = Tema.Ambar; est.Text = Trabalho.Texto; mais.Text = "aguarde: está fazendo"; return; }
        var a = ultimoAgora;
        if (a == null) { luz.Fill = Tema.Apagado; est.Text = "Acompanhamento desligado"; mais.Text = "ligue em Ao vivo"; return; }
        luz.Fill = Tema.Verde;
        est.Text = a["jogo"] is { } j ? "Jogando: " + j.S("nome") : "Acompanhando o PC";
        mais.Text = "leve: " + Num(a["segundo_plano"].D("cpu_pct"), 1) + " % da CPU";
    }

    /// <summary>As novidades das versões (do CHANGELOG, embutido no motor). Ao abrir, só se a versão mudou desde a última vista, e marca
    /// como vista na hora; pelas Configurações, sempre.</summary>
    public async Task MostraNovidades(bool soSePrecisa)
    {
        JsonNode? d;
        try { d = await Servico.Le("novidades"); }
        catch (Exception e) { Registro.Escreve("novidades: " + e.Message); if (!soSePrecisa) MostraErro(e); return; }
        if (d == null || (soSePrecisa && !d.B("mostrar"))) return;
        if (soSePrecisa && this.FindControl<Border>("Veu")!.IsVisible) return;   // já há uma caixa aberta (confirmação, erro): não cobre
        var corpo = new StackPanel { Spacing = 18, MaxWidth = 620 };
        foreach (var v in d.A("versoes"))
        {
            var p = new StackPanel { Spacing = 8 };
            p.Children.Add(T(v.S("versao") + " · " + v.S("data"), "rotulo"));
            if (v.S("resumo") != "") p.Children.Add(T(v.S("resumo"), "sub", quebra: true));
            foreach (var i in v.A("itens"))
            {
                var t = T("", "sub", quebra: true);
                t.Inlines = new InlineCollection();
                if (i.S("titulo") != "") t.Inlines.Add(new Run(i.S("titulo") + ": ") { Foreground = Tema.Osso, FontWeight = FontWeight.SemiBold });
                t.Inlines.Add(new Run(i.S("texto")));
                p.Children.Add(t);
            }
            corpo.Children.Add(p);
        }
        var ok = Botao("Entendi", true, FechaCaixa);
        var rodape = new StackPanel { Orientation = Orientation.Horizontal, HorizontalAlignment = HorizontalAlignment.Right, Margin = new Thickness(0, 12, 0, 0), Children = { ok } };
        MostraCaixa(Caixa(soSePrecisa ? "Novidades da " + d.S("versao") : "Novidades", corpo, rodape), true);
        ok.Focus();
        if (soSePrecisa)
            try { await Servico.Le("novidades", new { vista = true }); }   // vista ao aparecer: fechar a janela sem clicar não repete
            catch (Exception e) { Registro.Escreve("novidades: marcar como vista: " + e.Message); }
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
