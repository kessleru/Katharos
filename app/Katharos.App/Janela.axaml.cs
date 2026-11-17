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
        foreach (var b in Botoes())
        {
            b.Click += Navega;
            // ícone à esquerda de cada item do menu (acha sem ler); o texto continua o mesmo
            string icone = (string?)b.Tag switch { "inicio" => "inicio", "raiox" => "raiox", "otimizar" => "otimizar", "aovivo" => "aovivo", "memoria" => "memoria",
                                                   "historico" => "historico", "desfazer" => "desfazer", "enviar" => "enviar", "config" => "config", _ => "info" };
            if (b.Content is string texto)
                b.Content = new StackPanel { Orientation = Orientation.Horizontal, Spacing = 12, Children = { Icones.De(icone, 16, Tema.Apagado), new TextBlock { Text = texto, VerticalAlignment = VerticalAlignment.Center } } };
        }
        this.FindControl<TextBlock>("Versao")!.Text = typeof(Janela).Assembly.GetName().Version is { } v ? $"{v.Major}.{v.Minor}.{v.Build}" : "4.4.0";
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
        KeyDown += (_, e) =>
        {
            if (e.Key == Key.Escape && caixaFechavel) { if (resposta != null) Responde(false); else FechaCaixa(); }
            // Ctrl+K: ir para qualquer tela ou área digitando (UI 2); não abre por cima de outra caixa
            else if (e.Key == Key.K && e.KeyModifiers.HasFlag(KeyModifiers.Control) && !this.FindControl<Border>("Veu")!.IsVisible) { Paleta.Abre(this); e.Handled = true; }
        };
        Closing += async (_, _) => { if (Atualizacao.AoFechar) SegundoPlano.PedeParaSair(reabrir: true); await Servico.Fecha(); };
        Mostra(Program.TelaInicial);
        Opened += async (_, _) =>
        {
            if (!Servico.Exemplo) await SegundoPlano.ReabreSePreciso();
            try { var c = await Servico.Le("config_ler"); await Atualizacao.Confere(c?["atualizacoes"].S("valor", "avisar") ?? "avisar", c?["canal"].S("valor", "estavel") ?? "estavel"); }
            catch (Exception e) { Registro.Escreve("atualização: " + e.Message); }
            // depois de atualizar: o que mudou, uma vez por versão (instalação nova não mostra)
            if (!Servico.Exemplo) await MostraNovidades(soSePrecisa: true);
            // relatório semanal (com aviso na primeira vez) e o "abrir com o Windows", conforme as Configurações
            if (!Servico.Exemplo) { _ = AbrirComWindows.Aplica(); _ = Task.Delay(TimeSpan.FromSeconds(20)).ContinueWith(_ => Dispatcher.UIThread.Post(async () => await RelatorioAutomatico.Confere(this))); }
        };
        Atualizacao.Pergunta += v => Dispatcher.UIThread.Post(() => PerguntaAtualizacao(v));
        new DispatcherTimer(TimeSpan.FromMinutes(1), DispatcherPriority.Background, async (_, _) =>
        {
            if (Atualizacao.Ocupado || Conferencia.Rodando) return;
            await Servico.FechaSeParado(WindowState == WindowState.Minimized || !IsVisible);
        }).Start();
        // a janela aberta o dia todo também confere (a cada 3 h; a conferência em si respeita "atualizações: nunca")
        new DispatcherTimer(TimeSpan.FromHours(3), DispatcherPriority.Background, async (_, _) =>
        {
            try { var c = await Servico.Le("config_ler"); await Atualizacao.Confere(c?["atualizacoes"].S("valor", "avisar") ?? "avisar", c?["canal"].S("valor", "estavel") ?? "estavel"); }
            catch (Exception e) { Registro.Escreve("atualização: " + e.Message); }
        }).Start();
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
        // o raio-x rodando e o relatório com texto escrito continuam os mesmos ao voltar (relatório ELQUQN: trocar de tela apagava o texto
        // e parecia parar o raio-x)
        bool podeVoltar = (tela == "raiox" && arg is "" or "rodar") || (tela == "enviar" && arg == "");   // raio-x já rodando: "rodar" mostra o que roda
        if (podeVoltar && vivas.TryGetValue(tela, out var viva) && viva.Manter)
        {
            MostraTela(viva, tela);
            return;
        }
        Tela c = tela switch
        {
            "raiox" => new Raiox(arg == "rodar"),
            "otimizar" => new Otimizar(arg),
            "aovivo" => new AoVivo(),
            "jogos" => new Jogos(),
            "historico" => new Historico(),
            "desfazer" => new Desfazer(),
            "config" => new Configuracoes(),
            "aviso" => new Aviso(arg),
            "detalhe" => new Detalhe(),
            "inicializacao" => new Inicializacao(),
            "memoria" => new Memoria(),
            "enviar" => new Enviar(arg),
            _ => new Inicio(),
        };
        c.Pede += Mostra;
        if (tela is "raiox" or "enviar") vivas[tela] = c;
        MostraTela(c, tela);
    }

    readonly Dictionary<string, Tela> vivas = new();

    void MostraTela(Tela c, string tela)
    {
        this.FindControl<ContentControl>("Tela")!.Content = c;
        Movimento.Entra(c);
        // telas que se abrem de dentro de outra acendem o item do menu de onde vieram
        string menu = tela switch { "aviso" or "inicializacao" => "otimizar", "detalhe" or "jogos" => "inicio", _ => tela };
        foreach (var b in Botoes()) b.Classes.Set("ativo", (string?)b.Tag == menu);
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
        var corpo = new StackPanel { Spacing = 18, MaxWidth = 620, HorizontalAlignment = HorizontalAlignment.Left };
        foreach (var v in d.A("versoes"))
        {
            var p = new StackPanel { Spacing = 8 };
            p.Children.Add(T(v.S("versao") + " · " + v.S("data"), "rotulo"));
            if (v.S("resumo") != "") p.Children.Add(T(v.S("resumo"), "sub", quebra: true));
            foreach (var i in v.A("itens")) p.Children.Add(Item(i.S("texto"), titulo: i.S("titulo")));
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

    Border? aviso;
    /// <summary>Aviso flutuante (UI 2): uma frase curta no canto de baixo, que some sozinha em 4 s. Para o que deu certo e não pede
    /// resposta ("salvo", "pronto"); o que pede atenção continua na caixa do meio.</summary>
    public void Aviso(string texto)
    {
        var raiz = this.FindControl<Grid>("RaizGrade")!;
        if (aviso != null) raiz.Children.Remove(aviso);
        aviso = new Border
        {
            Background = Tema.Painel, BorderBrush = Tema.LinhaForte, BorderThickness = new Thickness(1), Padding = new Thickness(16, 10),
            HorizontalAlignment = HorizontalAlignment.Right, VerticalAlignment = VerticalAlignment.Bottom, Margin = new Thickness(0, 0, 24, 24),
            Child = new StackPanel { Orientation = Orientation.Horizontal, Spacing = 10, Children = { Icones.De("ok", 16, Tema.Verde), Ui.T(texto, null, Tema.Osso, 14) } },
        };
        raiz.Children.Add(aviso);
        var este = aviso;
        DispatcherTimer.RunOnce(() => { raiz.Children.Remove(este); if (aviso == este) aviso = null; }, TimeSpan.FromSeconds(4));
    }

    /// <summary>Versão nova baixada com a janela aberta: reiniciar já ou deixar para quando fechar. Nunca no meio de uma mudança no PC nem
    /// por cima de outra caixa (aí fica o cartão do Início, e entra ao fechar).</summary>
    void PerguntaAtualizacao(string v)
    {
        if (Atualizacao.Ocupado || this.FindControl<Border>("Veu")!.IsVisible) { Atualizacao.NaProximaVez(); return; }
        var b = new StackPanel { Orientation = Orientation.Horizontal, Spacing = 10, HorizontalAlignment = HorizontalAlignment.Right, Margin = new Thickness(0, 18, 0, 0) };
        b.Children.Add(Botao("Na próxima vez", false, () => { Atualizacao.NaProximaVez(); FechaCaixa(); }));
        var ja = Botao("Reiniciar agora", true, () => { FechaCaixa(); if (!Atualizacao.Aplica()) Atualizacao.NaProximaVez(); });
        b.Children.Add(ja);
        MostraCaixa(Caixa($"Versão {v} pronta", T("Já baixada. Reiniciar leva segundos e nada do que você fez se perde. \"Na próxima vez\" troca quando você fechar o Katharos.", "sub", quebra: true), b), true);
        ja.Focus();
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
        // um corpo reaproveitado (a caixa "Lendo…" que vira a caixa de verdade) ainda está na caixa anterior: solta antes
        if (corpo.Parent is Panel pai) pai.Children.Remove(corpo);
        p.Children.Add(corpo);
        if (rodape != null) p.Children.Add(rodape);
        return new ScrollViewer { Content = p, HorizontalScrollBarVisibility = Avalonia.Controls.Primitives.ScrollBarVisibility.Disabled };
    }
}
