using Avalonia.Controls;
using Avalonia.Markup.Xaml;

namespace Katharos.App.Telas;

public partial class Otimizar : UserControl
{
    public Otimizar()
    {
        AvaloniaXamlLoader.Load(this);
        this.FindControl<ItemsControl>("Modos")!.ItemsSource = Exemplo.Modos;
        this.FindControl<ItemsControl>("Areas")!.ItemsSource = Exemplo.Areas;
        int mudam = Exemplo.Areas.Sum(a => a.Itens.Count(i => i.Marcado && !i.JaFeito));
        int feitos = Exemplo.Areas.Sum(a => a.Itens.Count(i => i.JaFeito));
        // o botão diz exatamente o que acontece ao clicar
        this.FindControl<TextBlock>("Resumo")!.Text = $"{mudam} mudanças marcadas · {feitos} itens já estão feitos";
        this.FindControl<Button>("BtAplicar")!.Content = $"Aplicar {mudam} mudanças";
    }
}
