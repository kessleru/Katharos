using Avalonia;
using Avalonia.Controls;
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
        {
            if (Servico.Exemplo) d.MainWindow = new Janela();
            else
            {
                // a tela de abertura prepara tudo (motor, guardados, a conferência do que o Início cita); a janela principal abre já pronta
                d.ShutdownMode = ShutdownMode.OnExplicitShutdown;
                var ab = new Abertura();
                d.MainWindow = ab;
                ab.Opened += async (_, _) =>
                {
                    await ab.Prepara();
                    var j = new Janela();
                    d.MainWindow = j;
                    j.Show();
                    d.ShutdownMode = ShutdownMode.OnMainWindowClose;
                    await ab.Sai();
                };
            }
        }
        base.OnFrameworkInitializationCompleted();
    }
}
