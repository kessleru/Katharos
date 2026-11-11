using Avalonia;
using Avalonia.Controls.ApplicationLifetimes;
using Avalonia.Markup.Xaml;

namespace Katharos.App;

public partial class App : Application
{
    public override void Initialize() => AvaloniaXamlLoader.Load(this);

    public override void OnFrameworkInitializationCompleted()
    {
        // rede de segurança: erro que escapou de uma tela vira a caixa de erro e fica no registro; o aplicativo não fecha
        Avalonia.Threading.Dispatcher.UIThread.UnhandledException += (_, e) => { e.Handled = true; Ui.MostraErro(e.Exception); };
        TaskScheduler.UnobservedTaskException += (_, e) => { Registro.Escreve("tarefa: " + e.Exception); e.SetObserved(); };
        if (ApplicationLifetime is IClassicDesktopStyleApplicationLifetime d)
            d.MainWindow = new Janela();
        base.OnFrameworkInitializationCompleted();
    }
}
