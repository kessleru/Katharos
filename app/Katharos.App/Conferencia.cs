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
    static readonly HashSet<string> emCurso = new();
    public static DateTime? UltimaVez { get; private set; }
    public static string? Erro { get; private set; }

    public static bool Rodando => rodando;
    public static bool NaFila(string area) => emCurso.Contains(area) || fila.Contains(area);

    /// <summary>"Conferindo serviços · 2 de 9", ou "" quando parado.</summary>
    public static string Texto => rodando ? $"Conferindo {(atual != null ? Nomes.GetValueOrDefault(atual, atual) : "")}{(emCurso.Count > 1 ? $" e mais {emCurso.Count - 1}" : "")} · {Math.Min(feitas, total)} de {total} prontas" : "";

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
            if (emCurso.Contains(a) && !forcar) continue;
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
            // tudo o que está na fila vai num pedido só: o motor confere várias áreas ao mesmo tempo (e as grandes em pedaços) e manda
            // cada uma assim que termina (evento "area"). O que chegar na fila enquanto isso vai no próximo pedido.
            while (fila.Count > 0)
            {
                var lote = fila.ToList(); fila.Clear();
                var forca = lote.Where(forcadas.Contains).ToArray();
                foreach (var a in forca) forcadas.Remove(a);
                emCurso.Clear(); foreach (var a in lote) emCurso.Add(a);
                atual = lote[0];
                Mudou?.Invoke();
                try
                {
                    // o modo não muda o "já está assim" (só o que vem marcado), e quem ouve só usa o "ja": um modo fixo basta
                    var d = await Servico.Le("itens", new { modo = "seguro", conferir = true, areas = lote, forcar = forca }, (t, dd) =>
                    {
                        if (t == "area" && dd != null)
                        {
                            var nome = dd.S("nome"); var copia = dd.DeepClone();
                            Dispatcher.UIThread.Post(() =>
                            {
                                emCurso.Remove(nome); feitas++;
                                atual = emCurso.FirstOrDefault();
                                AreaPronta?.Invoke(nome, copia);
                                Mudou?.Invoke();
                            });
                        }
                    });
                    // área que não precisava conferir não manda evento: avisa com a resposta
                    foreach (var area in d.A("areas"))
                    {
                        var nome = area.S("nome"); var copia = area.DeepClone();
                        Dispatcher.UIThread.Post(() => { if (emCurso.Remove(nome)) { feitas++; AreaPronta?.Invoke(nome, copia); } });
                    }
                }
                catch (Exception e)
                {
                    // um lote que falhou não segura os próximos; o erro aparece na linha de andamento e vai para o registro
                    Erro = e.Message;
                    Registro.Escreve($"conferência de {string.Join(", ", lote)}: {e.Message}");
                }
            }
            UltimaVez = DateTime.Now;
        }
        finally
        {
            Dispatcher.UIThread.Post(() => { rodando = false; atual = null; feitas = 0; total = 0; emCurso.Clear(); Mudou?.Invoke(); });
        }
    }
}
