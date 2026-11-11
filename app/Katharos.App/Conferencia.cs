using System.Text.Json.Nodes;
using Avalonia.Threading;

namespace Katharos.App;

/// <summary>
/// Confere o "já está assim" sem atrapalhar ninguém: uma área por vez, numa fila que vive fora das telas (trocar de tela não cancela).
/// O motor atende um pedido por vez; por isso cada pedido é de uma área só, e as outras telas continuam lendo entre uma área e outra.
/// A área que a pessoa abriu ou vai aplicar passa na frente. O resultado chega item a item para quem estiver olhando (Otimizar, a
/// caixa "Aplicar esta correção", a tela de inicialização), que atualizam só a linha, sem refazer a tela nem desmarcar nada.
/// </summary>
public static class Conferencia
{
    /// <summary>Uma área foi conferida: o nome e a área como o motor manda (com os itens e o "ja" de cada um).</summary>
    public static event Action<string, JsonNode>? AreaPronta;
    /// <summary>O texto de andamento mudou ("Conferindo privacidade · 2 de 9").</summary>
    public static event Action? Mudou;

    static readonly LinkedList<string> fila = new();
    static readonly HashSet<string> forcadas = new();
    static bool rodando;
    static int feitas, total;
    static string? atual;
    public static DateTime? UltimaVez { get; private set; }
    public static string? Erro { get; private set; }

    public static bool Rodando => rodando;
    public static bool NaFila(string area) => atual == area || fila.Contains(area);

    /// <summary>"Conferindo serviços · 2 de 9", ou "" quando parado.</summary>
    public static string Texto => rodando && atual != null ? $"Conferindo {Nomes.GetValueOrDefault(atual, atual)} · {Math.Min(feitas + 1, total)} de {total}" : "";

    /// <summary>Os títulos das áreas (o Otimizar preenche quando lê a lista), só para o texto de andamento.</summary>
    public static readonly Dictionary<string, string> Nomes = new();

    /// <summary>
    /// Põe áreas na fila. frente: passam na frente (a área que a pessoa abriu). forcar: joga fora o que está guardado delas antes
    /// (depois de aplicar ou desfazer, ou "Ler de novo").
    /// </summary>
    public static void Pede(IEnumerable<string> areas, bool frente = false, bool forcar = false)
    {
        if (Servico.Exemplo) return;
        foreach (var a in frente ? areas.Reverse() : areas)
        {
            if (forcar) forcadas.Add(a);
            if (a == atual && !forcar) continue;
            if (fila.Contains(a)) { if (!frente) continue; fila.Remove(a); total--; }
            if (frente) fila.AddFirst(a); else fila.AddLast(a);
            total++;
        }
        if (!rodando && fila.Count > 0) _ = Roda();
        Mudou?.Invoke();
    }

    static async Task Roda()
    {
        rodando = true; Erro = null;
        try
        {
            while (fila.Count > 0)
            {
                atual = fila.First!.Value; fila.RemoveFirst();
                bool forca = forcadas.Remove(atual);
                Mudou?.Invoke();
                try
                {
                    // o modo não muda o "já está assim" (só o que vem marcado), e quem ouve só usa o "ja": um modo fixo basta
                    var d = await Servico.Le("itens", new { modo = "seguro", conferir = true, areas = new[] { atual }, forcar = forca ? new[] { atual } : Array.Empty<string>() });
                    var area = (d?["areas"] as JsonArray)?.FirstOrDefault();
                    if (area != null) { var nome = atual; Dispatcher.UIThread.Post(() => AreaPronta?.Invoke(nome, area)); }
                }
                catch (Exception e)
                {
                    // uma área que falhou não segura as outras; o erro aparece na linha de andamento e vai para o registro
                    Erro = e.Message;
                    Registro.Escreve($"conferência de {atual}: {e.Message}");
                }
                feitas++;
            }
            UltimaVez = DateTime.Now;
        }
        finally
        {
            rodando = false; atual = null; feitas = 0; total = 0;
            Dispatcher.UIThread.Post(() => Mudou?.Invoke());
        }
    }
}
