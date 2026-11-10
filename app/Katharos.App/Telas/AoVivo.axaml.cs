using Avalonia.Controls;
using Avalonia.Markup.Xaml;

namespace Katharos.App.Telas;

public partial class AoVivo : UserControl
{
    public AoVivo()
    {
        AvaloniaXamlLoader.Load(this);
        this.FindControl<ItemsControl>("Metricas")!.ItemsSource = Exemplo.Metricas;
    }
}

/// <summary>Telas que o protótipo ainda não tem: dizem isso, sem fingir.</summary>
public class EmBreve : UserControl
{
    public EmBreve(string tela)
    {
        Content = new TextBlock
        {
            Text = "Esta tela entra depois do protótipo (" + tela + ").", Margin = new Avalonia.Thickness(72, 48),
            Foreground = Tema.Apagado, FontSize = 15,
        };
    }
}
