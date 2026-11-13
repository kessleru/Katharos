using Microsoft.Win32;

namespace Katharos.App;

/// <summary>
/// Abrir com o Windows, como o Discord (pedido do dono, 13/11): uma entrada em HKCU\...\Run aponta para o lançador da instalação
/// (Katharos.exe na pasta acima de "current", que sobrevive às atualizações) com "--inicio-windows". Nessa abertura, o Program confere
/// a versão nova antes de mostrar a janela. Desligar em Configurações tira a entrada.
/// </summary>
public static class AbrirComWindows
{
    const string Chave = @"Software\Microsoft\Windows\CurrentVersion\Run";
    const string Nome = "Katharos";

    static string? Lancador()
    {
        // instalado (Velopack): %LOCALAPPDATA%\Katharos\Katharos.exe chama current\Katharos.exe com os mesmos argumentos
        var acima = Path.GetFullPath(Path.Combine(AppContext.BaseDirectory, ".."));
        var stub = Path.Combine(acima, "Katharos.exe");
        if (File.Exists(stub) && Directory.Exists(Path.Combine(AppContext.BaseDirectory, "python"))) return stub;
        return null;   // sem instalação (rodando de uma pasta de teste): não mexe na inicialização do Windows
    }

    public static async Task Aplica()
    {
        if (!OperatingSystem.IsWindows()) return;
        try
        {
            var c = await Servico.Le("config_ler");
            bool quer = c?["abrir-com-windows"].S("valor", "sim") != "nao";
            using var k = Registry.CurrentUser.CreateSubKey(Chave, true);
            var l = Lancador();
            if (quer && l != null) k.SetValue(Nome, $"\"{l}\" --inicio-windows");
            else if (!quer && k.GetValue(Nome) != null) k.DeleteValue(Nome, false);
        }
        catch (Exception e) { Registro.Escreve("abrir com o Windows: " + e.Message); }
    }
}
