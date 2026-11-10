using Avalonia.Controls;
using Avalonia.Markup.Xaml;

namespace Katharos.App.Telas;

public partial class Inicio : UserControl
{
    /// <summary>Pede à janela para abrir outra tela (os botões do Início levam para o lugar certo).</summary>
    public event Action<string>? Pede;

    public Inicio()
    {
        AvaloniaXamlLoader.Load(this);
        this.FindControl<ItemsControl>("Achados")!.ItemsSource = Exemplo.Achados;
        this.FindControl<Button>("BtVer")!.Click += (_, _) => Pede?.Invoke("raiox");
        this.FindControl<Button>("BtRefazer")!.Click += (_, _) => Pede?.Invoke("raiox");
        this.FindControl<Button>("BtDesfazer")!.Click += (_, _) => Pede?.Invoke("desfazer");
    }
}
