using System.Runtime.InteropServices;
using Avalonia;
using Avalonia.Animation;
using Avalonia.Controls;
using Avalonia.Media;
using Avalonia.Media.Transformation;
using Avalonia.Threading;

namespace Katharos.App;

/// <summary>
/// Os movimentos da interface: curtos (até 250 ms), só opacidade e deslocamento (RenderTransform, que não refaz o layout), nunca em
/// loop. Nada de desfoque, sombra animada, partícula ou animar o tamanho das coisas (isso refaz o layout a cada quadro e pesa em PC fraco).
/// Com "Mostrar animações no Windows" desligado (Acessibilidade > Efeitos visuais) ou "animações" desligado nas Configurações, tudo
/// aparece parado, na hora.
/// </summary>
public static class Movimento
{
    /// <summary>A opção das Configurações (true = ligadas). A janela lê ao abrir.</summary>
    public static bool Ligado = true;

    public static bool Reduzido => !Ligado || Servico.Exemplo || !AnimacoesDoWindows();

    static bool? doWindows;
    static DateTime lidoEm;
    // SPI_GETCLIENTAREAANIMATION: o "Mostrar animações no Windows"; relido a cada minuto (a pessoa pode mudar com o Katharos aberto)
    [DllImport("user32.dll")] static extern bool SystemParametersInfo(uint acao, uint p1, ref bool valor, uint p2);
    static bool AnimacoesDoWindows()
    {
        if (!OperatingSystem.IsWindows()) return true;
        if (doWindows is bool b && (DateTime.Now - lidoEm).TotalSeconds < 60) return b;
        bool v = true;
        try { if (!SystemParametersInfo(0x1042, 0, ref v, 0)) v = true; } catch { v = true; }
        doWindows = v; lidoEm = DateTime.Now;
        return v;
    }

    static readonly TransformOperations Parado = TransformOperations.Parse("none");

    /// <summary>Aparece: desvanece e sobe poucos pixels (troca de tela, área que abre, caixa, resultado).</summary>
    public static void Entra(Control c, double dy = 6, int ms = 150)
    {
        if (Reduzido) return;
        var t = TimeSpan.FromMilliseconds(Math.Min(ms, 250));
        c.Opacity = 0;
        c.RenderTransform = TransformOperations.Parse($"translateY({dy.ToString(System.Globalization.CultureInfo.InvariantCulture)}px)");
        c.Transitions = new Transitions
        {
            new DoubleTransition { Property = Visual.OpacityProperty, Duration = t, Easing = new Avalonia.Animation.Easings.CubicEaseOut() },
            new TransformOperationsTransition { Property = Visual.RenderTransformProperty, Duration = t, Easing = new Avalonia.Animation.Easings.CubicEaseOut() },
        };
        // no próximo quadro (já medido), vai para o lugar; depois as transições saem, para nada ficar animando à toa
        Dispatcher.UIThread.Post(() => { c.Opacity = 1; c.RenderTransform = Parado; }, DispatcherPriority.Render);
        DispatcherTimer.RunOnce(() => c.Transitions = null, t + TimeSpan.FromMilliseconds(60));
    }

    /// <summary>Destaca por um instante (a área para onde um botão levou a pessoa): fundo âmbar fraco que se apaga.</summary>
    public static void Destaca(Border b)
    {
        var antes = b.Background;
        b.Background = Tema.AmbarFraco;
        if (Reduzido) { DispatcherTimer.RunOnce(() => b.Background = antes, TimeSpan.FromMilliseconds(1600)); return; }
        DispatcherTimer.RunOnce(() =>
        {
            b.Transitions = new Transitions { new BrushTransition { Property = Border.BackgroundProperty, Duration = TimeSpan.FromMilliseconds(240) } };
            b.Background = antes ?? Brushes.Transparent;
            DispatcherTimer.RunOnce(() => b.Transitions = null, TimeSpan.FromMilliseconds(320));
        }, TimeSpan.FromMilliseconds(1100));
    }

    /// <summary>O número conta até o valor novo (a nota, o ganho), em 250 ms. Com movimento reduzido, troca na hora.</summary>
    public static void Conta(TextBlock t, double de, double para, Func<double, string> texto)
    {
        if (Reduzido || Math.Abs(para - de) < 0.01) { t.Text = texto(para); return; }
        var ini = DateTime.Now;
        var rel = new DispatcherTimer { Interval = TimeSpan.FromMilliseconds(16) };
        rel.Tick += (_, _) =>
        {
            double f = Math.Min(1, (DateTime.Now - ini).TotalMilliseconds / 250);
            double e = 1 - Math.Pow(1 - f, 3);
            t.Text = texto(de + (para - de) * e);
            if (f >= 1) rel.Stop();
        };
        rel.Start();
    }

    /// <summary>Um "✓" que acaba de aparecer ganha um pequeno destaque (cresce e volta), só uma vez.</summary>
    public static void Marca(Control c)
    {
        if (Reduzido) return;
        var t = TimeSpan.FromMilliseconds(180);
        c.RenderTransform = TransformOperations.Parse("scale(1.25)");
        c.Transitions = new Transitions { new TransformOperationsTransition { Property = Visual.RenderTransformProperty, Duration = t } };
        Dispatcher.UIThread.Post(() => c.RenderTransform = Parado, DispatcherPriority.Render);
        DispatcherTimer.RunOnce(() => c.Transitions = null, t + TimeSpan.FromMilliseconds(60));
    }
}
