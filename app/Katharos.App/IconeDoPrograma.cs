using System.Runtime.InteropServices;
using Avalonia;
using Avalonia.Controls;
using Avalonia.Media.Imaging;
using Avalonia.Platform;

namespace Katharos.App;

/// <summary>
/// O ícone de um programa, tirado do próprio .exe pelo Windows (o mesmo que o Explorer mostra). Só lê o arquivo; nada roda. Fica guardado
/// na memória enquanto a janela está aberta. Fora do Windows, ou se não houver ícone, volta o desenho genérico de programa.
/// </summary>
public static class IconeDoPrograma
{
    static readonly Dictionary<string, Bitmap?> lidos = new(StringComparer.OrdinalIgnoreCase);

    /// <summary>O ícone do .exe; sem ele (programa sem caminho conhecido, ou fora do Windows), a inicial do nome num quadrado.</summary>
    public static Control De(string? exe, double tamanho = 22, string? nome = null)
    {
        var bmp = Bitmap(exe);
        if (bmp != null) return new Image { Source = bmp, Width = tamanho, Height = tamanho };
        return Inicial(nome ?? Path.GetFileNameWithoutExtension(exe ?? ""), tamanho);
    }

    /// <summary>A inicial do programa num quadrado de contorno, com um tom que é sempre o mesmo para o mesmo nome.</summary>
    public static Control Inicial(string nome, double tamanho = 22)
    {
        nome = (nome ?? "").Trim();
        if (nome == "") return Icones.De("programa", tamanho * 0.8, Tema.Apagado).Com(c => c.Margin = new Thickness(tamanho * 0.1));
        // tons da paleta do Katharos (nada de cor nova): âmbar, verde, osso e texto, escolhidos pelo nome
        var tons = new[] { Tema.Ambar, Tema.Verde, Tema.Osso, Tema.Texto };
        int h = 0; foreach (char c in nome.ToLowerInvariant()) h = (h * 31 + c) & 0x7fffffff;
        var cor = tons[h % tons.Length];
        return new Border
        {
            Width = tamanho, Height = tamanho, BorderBrush = cor, BorderThickness = new Thickness(1), CornerRadius = new CornerRadius(3),
            Child = new TextBlock { Text = char.ToUpperInvariant(nome[0]).ToString(), Foreground = cor, FontFamily = Tema.Mono, FontSize = tamanho * 0.5,
                                    HorizontalAlignment = Avalonia.Layout.HorizontalAlignment.Center, VerticalAlignment = Avalonia.Layout.VerticalAlignment.Center },
        };
    }

    static Bitmap? Bitmap(string? exe)
    {
        if (!OperatingSystem.IsWindows() || string.IsNullOrWhiteSpace(exe)) return null;
        exe = Environment.ExpandEnvironmentVariables(exe.Trim('"'));
        lock (lidos) if (lidos.TryGetValue(exe, out var b)) return b;
        Bitmap? r = null;
        try { if (File.Exists(exe)) r = Le(exe); }
        catch (Exception e) { Registro.Escreve("ícone de " + exe + ": " + e.Message); }
        lock (lidos) lidos[exe] = r;
        return r;
    }

    [StructLayout(LayoutKind.Sequential, CharSet = CharSet.Unicode)]
    struct SHFILEINFO { public IntPtr hIcon; public int iIcon; public uint dwAttributes; [MarshalAs(UnmanagedType.ByValTStr, SizeConst = 260)] public string szDisplayName; [MarshalAs(UnmanagedType.ByValTStr, SizeConst = 80)] public string szTypeName; }
    [StructLayout(LayoutKind.Sequential)] struct ICONINFO { public bool fIcon; public int xHotspot, yHotspot; public IntPtr hbmMask, hbmColor; }
    [StructLayout(LayoutKind.Sequential)] struct BITMAP { public int bmType, bmWidth, bmHeight, bmWidthBytes; public ushort bmPlanes, bmBitsPixel; public IntPtr bmBits; }
    [StructLayout(LayoutKind.Sequential)] struct BITMAPINFOHEADER { public int biSize, biWidth, biHeight; public ushort biPlanes, biBitCount; public int biCompression, biSizeImage, biXPelsPerMeter, biYPelsPerMeter, biClrUsed, biClrImportant; }

    [DllImport("shell32.dll", CharSet = CharSet.Unicode)] static extern IntPtr SHGetFileInfo(string caminho, uint atributos, ref SHFILEINFO info, uint tamanho, uint flags);
    [DllImport("user32.dll")] static extern bool GetIconInfo(IntPtr icone, out ICONINFO info);
    [DllImport("user32.dll")] static extern bool DestroyIcon(IntPtr icone);
    [DllImport("gdi32.dll")] static extern int GetObject(IntPtr h, int tamanho, out BITMAP b);
    [DllImport("gdi32.dll")] static extern bool DeleteObject(IntPtr h);
    [DllImport("gdi32.dll")] static extern int GetDIBits(IntPtr dc, IntPtr bmp, uint inicio, uint linhas, [Out] byte[] bits, ref BITMAPINFOHEADER info, uint uso);
    [DllImport("user32.dll")] static extern IntPtr GetDC(IntPtr janela);
    [DllImport("user32.dll")] static extern int ReleaseDC(IntPtr janela, IntPtr dc);

    static Bitmap? Le(string exe)
    {
        var info = new SHFILEINFO();
        const uint SHGFI_ICON = 0x100, SHGFI_LARGEICON = 0x0;
        SHGetFileInfo(exe, 0, ref info, (uint)Marshal.SizeOf<SHFILEINFO>(), SHGFI_ICON | SHGFI_LARGEICON);
        if (info.hIcon == IntPtr.Zero) return null;
        try
        {
            if (!GetIconInfo(info.hIcon, out var ii)) return null;
            try
            {
                if (ii.hbmColor == IntPtr.Zero || GetObject(ii.hbmColor, Marshal.SizeOf<BITMAP>(), out var bm) == 0) return null;
                int w = bm.bmWidth, h = bm.bmHeight;
                var cab = new BITMAPINFOHEADER { biSize = Marshal.SizeOf<BITMAPINFOHEADER>(), biWidth = w, biHeight = -h, biPlanes = 1, biBitCount = 32 };
                var px = new byte[w * h * 4];
                var dc = GetDC(IntPtr.Zero);
                try { if (GetDIBits(dc, ii.hbmColor, 0, (uint)h, px, ref cab, 0) == 0) return null; }
                finally { ReleaseDC(IntPtr.Zero, dc); }
                // ícone antigo, sem transparência própria: tudo opaco (a máscara não é lida; o fundo do card é escuro e liso)
                bool temAlfa = false;
                for (int i = 3; i < px.Length; i += 4) if (px[i] != 0) { temAlfa = true; break; }
                if (!temAlfa) for (int i = 3; i < px.Length; i += 4) px[i] = 255;
                var wb = new WriteableBitmap(new PixelSize(w, h), new Vector(96, 96), PixelFormat.Bgra8888, AlphaFormat.Unpremul);
                using (var l = wb.Lock())
                    for (int y = 0; y < h; y++) Marshal.Copy(px, y * w * 4, l.Address + y * l.RowBytes, w * 4);
                return wb;
            }
            finally { if (ii.hbmColor != IntPtr.Zero) DeleteObject(ii.hbmColor); if (ii.hbmMask != IntPtr.Zero) DeleteObject(ii.hbmMask); }
        }
        finally { DestroyIcon(info.hIcon); }
    }
}
