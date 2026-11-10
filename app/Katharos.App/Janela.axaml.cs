using Avalonia.Controls;
using Avalonia.Interactivity;
using Avalonia.Markup.Xaml;
using Katharos.App.Telas;

namespace Katharos.App;

public partial class Janela : Window
{
    public Janela()
    {
        AvaloniaXamlLoader.Load(this);
        foreach (var b in this.FindControl<StackPanel>("Nav")!.Children.OfType<Button>())
            b.Click += Navega;
        this.FindControl<Button>("BtConfig")!.Click += Navega;
        Mostra("inicio");
    }

    void Navega(object? o, RoutedEventArgs e)
    {
        if (o is Button b && b.Tag is string t) Mostra(t);
    }

    /// <summary>Troca a tela e marca o item da navegação (o protótipo só tem Início, Otimizar e Ao vivo).</summary>
    public void Mostra(string tela)
    {
        Control c = tela switch
        {
            "otimizar" => new Otimizar(),
            "aovivo" => new AoVivo(),
            "inicio" => new Inicio(),
            _ => new EmBreve(tela),
        };
        if (c is Inicio i) i.Pede += Mostra;
        this.FindControl<ContentControl>("Tela")!.Content = c;
        foreach (var b in this.FindControl<StackPanel>("Nav")!.Children.OfType<Button>().Append(this.FindControl<Button>("BtConfig")!))
            b.Classes.Set("ativo", (string?)b.Tag == tela);
    }
}
