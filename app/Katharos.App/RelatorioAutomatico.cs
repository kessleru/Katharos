using System.Text.Json.Nodes;
using Avalonia.Controls;
using Avalonia.Layout;
using static Katharos.App.Ui;

namespace Katharos.App;

/// <summary>
/// Relatório automático, uma vez por semana (pedido do dono, 13/11: ligado por padrão, com aviso e um clique para desligar).
/// Antes do primeiro envio a pessoa vê o aviso; enquanto não viu, nada sai. Vai só o relatório (o mesmo da tela Enviar, já sem
/// dado pessoal), nunca o feedback. Desligar em Configurações > Relatório automático, ou no próprio aviso.
/// </summary>
public static class RelatorioAutomatico
{
    static string Casa => Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.UserProfile), ".katharos");
    static string ArqAviso => Path.Combine(Casa, "aviso-relatorio-automatico.txt");
    static string ArqUltimo => Path.Combine(Casa, "relatorio-automatico.txt");

    /// <summary>Na abertura: mostra o aviso uma vez; depois, se passou uma semana do último, monta e manda sem incomodar.</summary>
    public static async Task Confere(Janela j)
    {
        if (Servico.Exemplo) return;
        try
        {
            var c = await Servico.Le("config_ler");
            if (c?["relatorio-automatico"].S("valor", "semanal") == "nunca") return;
            if (!File.Exists(ArqAviso)) { MostraAviso(j); return; }   // primeiro o aviso; o primeiro envio fica para a próxima abertura
            if (File.Exists(ArqUltimo) && (DateTime.Now - File.GetLastWriteTime(ArqUltimo)).TotalDays < 7) return;
            var s = await Servico.Le("envio_secoes");
            var secoes = s.A("secoes").Select(x => x.S("id")).Where(x => x != "").ToArray();
            var r = await Servico.Le("envio_montar", new { tipo = "relatorio", secoes, feedback = new { tipo = "outro", texto = "", nota = (int?)null, contato = "" } });
            string json = r?["pacote"]?.ToJsonString() ?? "";
            if (json == "") return;
            string codigo = await Envio.Manda(json);
            Directory.CreateDirectory(Casa);
            File.WriteAllText(ArqUltimo, DateTime.Now.ToString("s") + " " + codigo);
            try { await Servico.Le("envio_registrar", new { codigo, tipo = "relatorio" }); } catch { }
            Registro.Escreve("relatório automático enviado: " + codigo);
        }
        catch (Exception e) { Registro.Escreve("relatório automático: " + e.Message); }   // sem internet: tenta na próxima abertura
    }

    static void MostraAviso(Janela j)
    {
        void Marca() { try { Directory.CreateDirectory(Casa); File.WriteAllText(ArqAviso, DateTime.Now.ToString("s")); } catch { } }
        var corpo = new StackPanel { Spacing = 10, Children = {
            T("Uma vez por semana o Katharos manda o relatório dele: erros, o que foi aplicado e o que cada mudança rendeu. Sem o seu nome, o nome do PC, IP ou arquivos.", "sub", quebra: true),
            T("Dá para desligar agora ou quando quiser, em Configurações.", "rotulo", quebra: true) } };
        var botoes = new StackPanel { Orientation = Orientation.Horizontal, Spacing = 10, HorizontalAlignment = HorizontalAlignment.Right, Margin = new Avalonia.Thickness(0, 12, 0, 0),
            Children = {
                Botao("Desligar o envio", false, async () =>
                {
                    Marca();
                    try { await Servico.Le("config_gravar", new { chave = "relatorio-automatico", valor = "nunca" }); } catch (Exception e) { Registro.Escreve("relatório automático: " + e.Message); }
                    j.FechaCaixa();
                }),
                Botao("Manter ligado", true, () => { Marca(); j.FechaCaixa(); }) } };
        j.MostraCaixa(Janela.Caixa("Relatório automático ligado", corpo, botoes), false);
    }
}
