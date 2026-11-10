

# ███████████████████████████████████████████████████████████████████████████
#
#   PARTE 1 · CONHECER O PC
#   perfil (o que o PC tem e usa), medidas (antes/depois) e o raio-x com recomendações
#
# ███████████████████████████████████████████████████████████████████████████

PERFIL_PS = r'''
$cs = Tenta { Get-CimInstance Win32_ComputerSystem }
$os = Tenta { Get-CimInstance Win32_OperatingSystem }
$cv = Tenta { Get-ItemProperty 'HKLM:\SOFTWARE\Microsoft\Windows NT\CurrentVersion' }
$cpu = Tenta { Get-CimInstance Win32_Processor | Select-Object -First 1 }
$enc = Tenta { Get-CimInstance Win32_SystemEnclosure | Select-Object -First 1 }
$bat = Tenta { Get-CimInstance Win32_Battery | Select-Object -First 1 }
$chassi = @(); if ($enc) { $chassi = @($enc.ChassisTypes) }
$notebook = [bool]$bat -or (@($chassi | Where-Object { $_ -in 8,9,10,11,12,14,18,21,30,31,32 }).Count -gt 0)
$tablet = (@($chassi | Where-Object { $_ -in 30,31,32 }).Count -gt 0) -or [bool](Tenta { Get-ItemProperty 'HKLM:\SYSTEM\CurrentControlSet\Control\PriorityControl' -Name ConvertibleSlateMode -ErrorAction Stop })

# disco do sistema
$tipoC = 'desconhecido'; $barC = ''; $saudeC = ''; $modeloC = ''; $desgC = $null; $tempC = $null; $horasC = $null; $errC = $null
try {
    $part = Get-Partition -DriveLetter C -ErrorAction Stop
    $pd = Get-PhysicalDisk | Where-Object { $_.DeviceId -eq [string]$part.DiskNumber } | Select-Object -First 1
    if ($pd) { $tipoC = [string]$pd.MediaType; $barC = [string]$pd.BusType; $saudeC = [string]$pd.HealthStatus; $modeloC = ([string]$pd.FriendlyName).Trim()
        $rc = Tenta { $pd | Get-StorageReliabilityCounter -ErrorAction Stop } $null
        if ($rc) { $desgC = $rc.Wear; $tempC = $rc.Temperature; $horasC = $rc.PowerOnHours; $errC = [long]$rc.ReadErrorsUncorrected + [long]$rc.WriteErrorsUncorrected } }
    if ($tipoC -eq 'Unspecified' -and $barC -eq 'NVMe') { $tipoC = 'SSD' }
    if ($tipoC -eq 'Unspecified' -and $modeloC -match 'SSD|NVMe|Solid') { $tipoC = 'SSD' }
} catch {}
$discos = @(Tenta { Get-PhysicalDisk -ErrorAction Stop | Sort-Object DeviceId | ForEach-Object { [pscustomobject]@{ modelo = ([string]$_.FriendlyName).Trim(); tipo = [string]$_.MediaType; barramento = [string]$_.BusType; gb = [math]::Round([double]$_.Size / 1GB, 0); saude = [string]$_.HealthStatus } } } @())
$ld = Tenta { Get-CimInstance Win32_LogicalDisk -Filter "DeviceID='C:'" }
$livreC = 0; $totalC = 0; if ($ld) { $livreC = [math]::Round($ld.FreeSpace / 1GB, 1); $totalC = [math]::Round($ld.Size / 1GB, 1) }

$pentes = @(Tenta { Get-CimInstance Win32_PhysicalMemory } @())
$arr = Tenta { Get-CimInstance Win32_PhysicalMemoryArray | Select-Object -First 1 }
$slots = 0; if ($arr) { $slots = [int]$arr.MemoryDevices }

function TemClasse([string]$C) { return [bool](Get-PnpDevice -Class $C -PresentOnly -ErrorAction SilentlyContinue | Where-Object { $_.Status -eq 'OK' } | Select-Object -First 1) }
$impressoras = @(Tenta { Get-Printer -ErrorAction Stop | Where-Object { $_.PortName -notmatch 'PORTPROMPT|XPS|nul|SHRFAX|OneNote|PDF|Microsoft' -and $_.Name -notmatch 'PDF|XPS|OneNote|Fax' } } @())
$ap = Tenta { Get-AppxPackage -ErrorAction Stop | Select-Object -ExpandProperty Name } @()
$prog = @(Get-ItemProperty 'HKLM:\Software\Microsoft\Windows\CurrentVersion\Uninstall\*','HKLM:\Software\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall\*','HKCU:\Software\Microsoft\Windows\CurrentVersion\Uninstall\*' -ErrorAction SilentlyContinue | Where-Object { $_.DisplayName } | ForEach-Object { [string]$_.DisplayName })
function TemProg([string]$P) { return [bool]($prog | Where-Object { $_ -match $P } | Select-Object -First 1) }
function TemApp([string]$P) { return [bool]($ap | Where-Object { $_ -match $P } | Select-Object -First 1) }

$jogos = @()
foreach ($par in @(@('Steam','^Steam$'), @('Epic Games','Epic Games Launcher'), @('Battle.net','Battle\.net'), @('Riot','Riot Client|Riot Vanguard|League of Legends|VALORANT'), @('EA app','^EA app$|^EA$|Origin'), @('Ubisoft','Ubisoft Connect|Uplay'), @('GOG','GOG GALAXY'), @('Rockstar','Rockstar Games Launcher'), @('Minecraft','Minecraft'))) {
    if (TemProg $par[1]) { $jogos += $par[0] }
}
if (TemApp '^Microsoft\.GamingApp$') { $jogos += 'Xbox (app)' }
$oemGamer = @()
foreach ($par in @(@('Alienware Command Center','Alienware Command Center|AWCC'), @('Armoury Crate','Armoury Crate'), @('Lenovo Vantage','Lenovo Vantage|LenovoVantage'), @('NitroSense','NitroSense|PredatorSense'), @('MSI Center','MSI Center|Dragon Center'), @('OMEN Gaming Hub','OMEN Gaming Hub|OMEN Command Center'))) {
    if ((TemProg $par[1]) -or (TemApp ($par[1] -replace ' ', ''))) { $oemGamer += $par[0] }
}

$av = @(Tenta { Get-CimInstance -Namespace root\SecurityCenter2 -ClassName AntiVirusProduct -ErrorAction Stop | ForEach-Object {
    $estado = '{0:X6}' -f [int]$_.productState
    [pscustomobject]@{ nome = [string]$_.displayName; ativo = ($estado.Substring(2, 2) -in '10','11') }
} } @())
$mp = Tenta { Get-MpComputerStatus -ErrorAction Stop }
$od = Join-Path $env:USERPROFILE 'OneDrive'
$odUsado = $false
if ($env:OneDrive -and (Test-Path -LiteralPath $env:OneDrive)) { $odUsado = [bool](Get-ChildItem -LiteralPath $env:OneDrive -Force -ErrorAction SilentlyContinue | Where-Object { $_.Name -notmatch '^desktop\.ini$|^\.' } | Select-Object -First 1) }
$plano = Tenta { (powercfg /getactivescheme | Out-String).Trim() } ''
$gpus = @(Tenta { Get-CimInstance Win32_VideoController | ForEach-Object { [string]$_.Name } } @())
$dono = Tenta { (Get-CimInstance Win32_Process -Filter "Name='explorer.exe'" | Select-Object -First 1 | Invoke-CimMethod -MethodName GetOwner).User } ''
$pf = Tenta { Get-CimInstance Win32_PageFileSetting } $null
$pfAuto = Tenta { (Get-CimInstance Win32_ComputerSystem).AutomaticManagedPagefile } $true
$mm = Tenta { (Get-MMAgent -ErrorAction Stop).MemoryCompression } $null
$pentesL = @($pentes | ForEach-Object { [pscustomobject]@{ gb = [math]::Round([double]$_.Capacity / 1GB, 0); mhz = [int]$_.ConfiguredClockSpeed; mhz_max = [int]$_.Speed; fab = ([string]$_.Manufacturer).Trim(); modelo = ([string]$_.PartNumber).Trim() } })
# o AdapterRAM do WMI para em 4 GB; o registro do driver de vídeo guarda o tamanho certo
$vram = @{}
Get-ChildItem 'HKLM:\SYSTEM\CurrentControlSet\Control\Class\{4d36e968-e325-11ce-bfc1-08002be10318}' -ErrorAction SilentlyContinue | ForEach-Object {
    $r = Get-ItemProperty -LiteralPath $_.PSPath -ErrorAction SilentlyContinue
    if ($r -and $r.DriverDesc) {
        $q = $r.'HardwareInformation.qwMemorySize'; if ($null -eq $q) { $q = $r.'HardwareInformation.MemorySize' }
        if ($q -is [byte[]]) { $bb = [byte[]](@($q) + @(0, 0, 0, 0, 0, 0, 0, 0)); $q = [BitConverter]::ToUInt64($bb, 0) }
        if ($q) { $vram[([string]$r.DriverDesc).Trim()] = [math]::Round([double]$q / 1GB, 1) }
    }
}
$placa = Tenta { Get-CimInstance Win32_BaseBoard | Select-Object -First 1 }
$bios = Tenta { Get-CimInstance Win32_BIOS | Select-Object -First 1 }
$tiposRam = @{ 20 = 'DDR'; 21 = 'DDR2'; 24 = 'DDR3'; 26 = 'DDR4'; 29 = 'LPDDR3'; 30 = 'LPDDR4'; 34 = 'DDR5'; 35 = 'LPDDR5' }
$tipoRam = ''; foreach ($pm in $pentes) { $c = [int]$pm.SMBIOSMemoryType; if ($tiposRam.ContainsKey($c)) { $tipoRam = $tiposRam[$c]; break } }
$memDisp = Tenta { [double](Get-CimInstance Win32_PerfFormattedData_PerfOS_Memory -ErrorAction Stop).AvailableMBytes / 1024 } $null
$video = @(Tenta { Get-CimInstance Win32_VideoController -ErrorAction Stop | ForEach-Object { $nm = ([string]$_.Name).Trim(); [pscustomobject]@{ nome = $nm; vram_gb = $(if ($vram.ContainsKey($nm)) { $vram[$nm] } elseif ([double]$_.AdapterRAM -gt 0) { [math]::Round([double]$_.AdapterRAM / 1GB, 1) } else { $null }); integrada = ($nm -match 'Intel\(R\) (UHD|HD|Iris)|Intel.*Graphics$|AMD Radeon\(TM\) Graphics|Radeon\(TM\) (Vega|[0-9]+M) |Radeon Graphics$|Vega [0-9]+ Graphics'); driver = [string]$_.DriverVersion; driver_data = $(if ($_.DriverDate) { ([datetime]$_.DriverDate).ToString('s') } else { '' }); basico = ([string]$_.Name -match 'Basic Display|Basic Render|sico da Microsoft') } } } @())
$tela = Tenta {
    Add-Type -Namespace Katharos -Name Tela -ErrorAction Stop -MemberDefinition '
[StructLayout(LayoutKind.Sequential, CharSet = CharSet.Ansi)] public struct DEVMODE { [MarshalAs(UnmanagedType.ByValTStr, SizeConst = 32)] public string dmDeviceName; public short dmSpecVersion; public short dmDriverVersion; public short dmSize; public short dmDriverExtra; public int dmFields; public int dmPositionX; public int dmPositionY; public int dmDisplayOrientation; public int dmDisplayFixedOutput; public short dmColor; public short dmDuplex; public short dmYResolution; public short dmTTOption; public short dmCollate; [MarshalAs(UnmanagedType.ByValTStr, SizeConst = 32)] public string dmFormName; public short dmLogPixels; public int dmBitsPerPel; public int dmPelsWidth; public int dmPelsHeight; public int dmDisplayFlags; public int dmDisplayFrequency; public int dmICMMethod; public int dmICMIntent; public int dmMediaType; public int dmDitherType; public int dmReserved1; public int dmReserved2; public int dmPanningWidth; public int dmPanningHeight; }
[DllImport("user32.dll", CharSet = CharSet.Ansi)] public static extern bool EnumDisplaySettings(string dev, int modo, ref DEVMODE dm);'
    $dm = New-Object 'Katharos.Tela+DEVMODE'
    $dm.dmSize = [int16][System.Runtime.InteropServices.Marshal]::SizeOf($dm)
    if (-not [Katharos.Tela]::EnumDisplaySettings($null, -1, [ref]$dm)) { throw 'sem tela' }
    $tw = $dm.dmPelsWidth; $th = $dm.dmPelsHeight; $thz = $dm.dmDisplayFrequency; $tmax = $thz; $ti = 0
    while ($ti -lt 2000 -and [Katharos.Tela]::EnumDisplaySettings($null, $ti, [ref]$dm)) { if ($dm.dmPelsWidth -eq $tw -and $dm.dmPelsHeight -eq $th -and $dm.dmDisplayFrequency -gt $tmax) { $tmax = $dm.dmDisplayFrequency }; $ti++ }
    @{ largura = $tw; altura = $th; hz = $thz; hz_max = $tmax }
} $null
$trim = Tenta { $q = (fsutil behavior query DisableDeleteNotify | Out-String); if ($q -match '(?m)^\s*(?:NTFS\s+)?DisableDeleteNotify\s*=\s*(\d)') { $Matches[1] -eq '0' } else { $null } } $null
$uptime = 0; if ($os) { $uptime = [math]::Round(((Get-Date) - $os.LastBootUpTime).TotalHours, 1) }
$pend = (Test-Path 'HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Component Based Servicing\RebootPending') -or (Test-Path 'HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\WindowsUpdate\Auto Update\RebootRequired')
$build = 0; if ($os) { $build = [int]$os.BuildNumber }
$rdp = (Tenta { (Get-ItemProperty 'HKLM:\SYSTEM\CurrentControlSet\Control\Terminal Server' -ErrorAction Stop).fDenyTSConnections } 1) -eq 0
$winrm = [bool](Get-ChildItem 'HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\WSMAN\Listener' -ErrorAction SilentlyContinue | Select-Object -First 1)
$ssh = (Test-Path (Join-Path $env:USERPROFILE '.ssh\id_*')) -or (Test-Path (Join-Path $env:USERPROFILE '.ssh\config'))
$wsl = [bool](Get-ChildItem 'HKCU:\Software\Microsoft\Windows\CurrentVersion\Lxss' -ErrorAction SilentlyContinue | Select-Object -First 1)
$hyperv = [bool](Get-Service vmcompute -ErrorAction SilentlyContinue)
$docker = [bool](Get-Service com.docker.service -ErrorAction SilentlyContinue) -or (TemProg 'Docker Desktop')
$fh = [bool](Tenta { (Get-ItemProperty 'HKCU:\Software\Microsoft\Windows\CurrentVersion\FileHistory' -ErrorAction Stop).ProtectedUpToTime })
$camera = (TemClasse 'Camera') -or (TemClasse 'Image')
$mdm = [bool](Tenta { Get-ChildItem 'HKLM:\SOFTWARE\Microsoft\Enrollments' -ErrorAction Stop | Where-Object { $e = Get-ItemProperty $_.PSPath -ErrorAction SilentlyContinue
    $e -and $e.ProviderID -eq 'MS DM Server' -and [int]$e.EnrollmentState -eq 1 -and @(6, 13) -contains [int]$e.EnrollmentType -and "$($e.UPN)" -match '@' -and "$($e.DiscoveryServiceFullURL)" } | Select-Object -First 1 })
$aad = (Tenta { (& dsregcmd.exe /status 2>$null | Out-String) -match 'AzureAdJoined\s*:\s*YES' } $false)
$gerenciado = $mdm -or $aad -or [bool]$cs.PartOfDomain
$porque = @(); if ([bool]$cs.PartOfDomain) { $porque += 'domínio ' + [string]$cs.Domain }; if ($aad) { $porque += 'Azure AD (conta de trabalho ou escola)' }; if ($mdm) { $porque += 'gestão remota (MDM, como o Intune)' }

Dado 'perfil' @{
    so = @{ nome = [string]$os.Caption; versao = [string]$cv.DisplayVersion; build = $build; win11 = ($build -ge 22000); edicao = [string]$cv.EditionID; idioma = (Get-Culture).Name; instalado = ([string]$os.InstallDate) }
    pc = @{ placa = $(if ($placa) { (([string]$placa.Manufacturer).Trim() + ' ' + ([string]$placa.Product).Trim()).Trim() } else { '' }); bios = $(if ($bios) { ([string]$bios.SMBIOSBIOSVersion).Trim() } else { '' }); bios_data = $(if ($bios -and $bios.ReleaseDate) { ([datetime]$bios.ReleaseDate).ToString('yyyy-MM-dd') } else { '' }); fabricante = ([string]$cs.Manufacturer).Trim(); modelo = ([string]$cs.Model).Trim(); notebook = $notebook; tablet = $tablet; dominio = [bool]$cs.PartOfDomain; gerenciado = $gerenciado; gerenciado_por = ($porque -join ', '); bateria = [bool]$bat }
    cpu = @{ nome = (([string]$cpu.Name).Trim() -replace '\s+', ' '); nucleos = [int]$cpu.NumberOfCores; threads = [int]$cpu.NumberOfLogicalProcessors; mhz = [int]$cpu.MaxClockSpeed; l3_mb = [math]::Round([double]$cpu.L3CacheSize / 1024, 0); virtualizacao = [bool]$cpu.VirtualizationFirmwareEnabled; fabricante = ([string]$cpu.Manufacturer).Trim() }
    ram = @{ total = [math]::Round([double]$cs.TotalPhysicalMemory / 1GB, 1); usada = $(if ($null -ne $memDisp) { [math]::Round([math]::Max(0, [double]$os.TotalVisibleMemorySize / 1MB - $memDisp), 1) } else { [math]::Round(([double]$os.TotalVisibleMemorySize - [double]$os.FreePhysicalMemory) / 1MB, 1) }); tipo = $tipoRam; slots = $slots; ocupados = $pentes.Count; pentes = (Lista $pentesL) }
    disco = @{ tipo = $tipoC; barramento = $barC; saude = $saudeC; livre = $livreC; total = $totalC; trim = $trim; modelo = $modeloC; desgaste = $desgC; temperatura = $tempC; horas = $horasC; erros = $errC }
    discos = (Lista $discos)
    gpus = (Lista $gpus)
    video = (Lista $video)
    tela = $tela
    tem = @{ impressora = ($impressoras.Count -gt 0); scanner = (TemClasse 'Image'); camera = $camera; smartcard = (TemClasse 'SmartCardReader'); bluetooth = (TemClasse 'Bluetooth'); biometria = (TemClasse 'Biometric'); rdp = $rdp; winrm = $winrm; ssh = $ssh; wsl = $wsl; hyperv = $hyperv; docker = $docker; historico_arquivos = $fh; office = (TemProg '^Microsoft (Office|365)'); visualstudio = (TemProg '^Visual Studio (Community|Professional|Enterprise|Build Tools)|^Microsoft Visual Studio'); onedrive_usado = $odUsado; onedrive = (Test-Path "$env:LOCALAPPDATA\Microsoft\OneDrive\OneDrive.exe") -or (Test-Path "$env:ProgramFiles\Microsoft OneDrive\OneDrive.exe"); brave = (TemProg '^Brave'); chrome = (TemProg '^Google Chrome'); firefox = (TemProg 'Mozilla Firefox'); edge = (Test-Path "${env:ProgramFiles(x86)}\Microsoft\Edge\Application\msedge.exe"); nvidia = [bool]($gpus | Where-Object { $_ -match 'NVIDIA' }); amd = [bool]($gpus | Where-Object { $_ -match 'AMD|Radeon' }); winget = [bool](Get-Command winget.exe -ErrorAction SilentlyContinue); devdrive = [bool](Tenta { Get-Volume -ErrorAction Stop | Where-Object { $_.FileSystemType -eq 'ReFS' -and $_.DriveLetter } | Select-Object -First 1 }) }
    jogos = (Lista $jogos)
    oem_gamer = (Lista $oemGamer)
    antivirus = (Lista $av)
    defender = @{ tempo_real = [bool]$mp.RealTimeProtectionEnabled; ativo = [bool]$mp.AntivirusEnabled; modo = [string]$mp.AMRunningMode }
    energia = @{ plano = $plano }
    memoria = @{ pagefile_auto = [bool]$pfAuto; pagefile_config = [bool]$pf; compressao = $mm }
    sistema = @{ uptime_h = $uptime; reinicio_pendente = $pend; admin = ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator); dono_explorer = [string]$dono; usuario = $env:USERNAME }
}
'''

TEMP_GPU_PS = r'''
# GPU pelo driver de vídeo (D3DKMT, o mesmo dado do Gerenciador de Tarefas). Só nas leituras que você pede, nunca na coleta de fundo.
function KGpuTemp {
    if (-not ('KatharosGpu' -as [type])) {
        Add-Type -ErrorAction Stop -TypeDefinition @'
using System; using System.Runtime.InteropServices;
public static class KatharosGpu {
    [StructLayout(LayoutKind.Sequential)] struct LUID { public uint Low; public int High; }
    [StructLayout(LayoutKind.Sequential)] struct INFO { public uint hAdapter; public LUID Luid; public uint Sources; public int Precise; }
    [StructLayout(LayoutKind.Sequential)] struct ENUM2 { public uint Num; public IntPtr pAdapters; }
    [StructLayout(LayoutKind.Sequential)] struct QUERY { public uint hAdapter; public int Type; public IntPtr pData; public uint Size; }
    [StructLayout(LayoutKind.Sequential)] struct PERF { public uint Index; public ulong MemFreq, MaxMemFreq, MaxMemFreqOC, MemBw, PcieBw; public uint Fan, Power, Temperature; public byte Override; }
    [StructLayout(LayoutKind.Sequential)] struct CLOSE { public uint hAdapter; }
    [DllImport("gdi32.dll")] static extern int D3DKMTEnumAdapters2(ref ENUM2 e);
    [DllImport("gdi32.dll")] static extern int D3DKMTQueryAdapterInfo(ref QUERY q);
    [DllImport("gdi32.dll")] static extern int D3DKMTCloseAdapter(ref CLOSE c);
    public static double Maxima() {
        var e = new ENUM2(); D3DKMTEnumAdapters2(ref e);
        if (e.Num == 0 || e.Num > 16) return -1;
        int ti = Marshal.SizeOf(typeof(INFO)), tp = Marshal.SizeOf(typeof(PERF));
        IntPtr buf = Marshal.AllocHGlobal(ti * (int)e.Num); double max = -1;
        try {
            e.pAdapters = buf;
            if (D3DKMTEnumAdapters2(ref e) != 0) return -1;
            for (int i = 0; i < e.Num; i++) {
                var a = (INFO)Marshal.PtrToStructure(new IntPtr(buf.ToInt64() + (long)i * ti), typeof(INFO));
                IntPtr pb = Marshal.AllocHGlobal(tp);
                try {
                    Marshal.StructureToPtr(new PERF(), pb, false);
                    var q = new QUERY { hAdapter = a.hAdapter, Type = 62, pData = pb, Size = (uint)tp };
                    if (D3DKMTQueryAdapterInfo(ref q) == 0) {
                        var p = (PERF)Marshal.PtrToStructure(pb, typeof(PERF));
                        double t = p.Temperature / 10.0;
                        if (t > 5 && t < 125 && t > max) max = t;
                    }
                } finally { Marshal.FreeHGlobal(pb); var c = new CLOSE { hAdapter = a.hAdapter }; D3DKMTCloseAdapter(ref c); }
            }
        } finally { Marshal.FreeHGlobal(buf); }
        return max;
    }
}
'@
    }
    $t = [KatharosGpu]::Maxima()
    if ($t -gt 0) { [math]::Round($t, 0) } else { $null }
}
function KNvTemp {
    $smi = Get-Command nvidia-smi.exe -ErrorAction SilentlyContinue | Select-Object -First 1
    if (-not $smi) { return $null }
    $l = Tenta { (& $smi.Source --query-gpu=temperature.gpu --format=csv,noheader,nounits 2>$null | Select-Object -First 1) } $null; $d = 0.0
    if ($l -and [double]::TryParse("$l".Trim(), [ref]$d) -and $d -gt 5) { [math]::Round($d, 0) } else { $null }
}
'''

TEMP_PS = r'''
# temperatura da CPU e da GPU: tenta do mais certo para o mais pobre e diz de onde veio
function LeTemperaturas([bool]$GpuTambem = $true) {
    $r = @{ cpu = $null; cpu_fonte = $null; gpu = $null; gpu_fonte = $null }
    # 1) LibreHardwareMonitor ou OpenHardwareMonitor abertos: leem o sensor de verdade (CPU Package, Tctl/Tdie, GPU Core)
    foreach ($ns in 'root\LibreHardwareMonitor', 'root\OpenHardwareMonitor') {
        $s = @(Tenta { Get-CimInstance -Namespace $ns -ClassName Sensor -Filter "SensorType='Temperature'" -ErrorAction Stop } @())
        if (-not $s.Count) { continue }
        $c = @($s | Where-Object { "$($_.Identifier)" -match 'cpu' -and $_.Value -gt 5 -and $_.Value -lt 125 })
        $cp = @($c | Where-Object { $_.Name -match 'Package|Tctl|Tdie|Core Average' })
        if ($cp.Count) { $c = $cp }
        if ($null -eq $r.cpu -and $c.Count) { $r.cpu = [math]::Round(($c | Measure-Object Value -Maximum).Maximum, 0); $r.cpu_fonte = ($ns -split '\\')[1] }
        $g = @($s | Where-Object { "$($_.Identifier)" -match 'gpu' -and $_.Value -gt 5 -and $_.Value -lt 125 })
        $gc = @($g | Where-Object { $_.Name -match 'GPU Core|^Core' })
        if ($gc.Count) { $g = $gc }
        if ($null -eq $r.gpu -and $g.Count) { $r.gpu = [math]::Round(($g | Measure-Object Value -Maximum).Maximum, 0); $r.gpu_fonte = ($ns -split '\\')[1] }
    }
    # 2) CPU pela zona térmica do ACPI, que o Windows mostra sem programa extra. 298, 300 e 301 K são o valor fixo de muitas placas-mãe: não é leitura.
    if ($null -eq $r.cpu) {
        $k = @(Tenta { Get-CimInstance Win32_PerfFormattedData_Counters_ThermalZoneInformation -ErrorAction Stop | ForEach-Object { if ([double]$_.HighPrecisionTemperature -gt 0) { [double]$_.HighPrecisionTemperature / 10 } else { [double]$_.Temperature } } } @())
        $k += @(Tenta { Get-CimInstance -Namespace root\wmi -ClassName MSAcpi_ThermalZoneTemperature -ErrorAction Stop | ForEach-Object { [double]$_.CurrentTemperature / 10 } } @())
        $z = @($k | Where-Object { $v = $_; -not (@(298.15, 300, 301) | Where-Object { [math]::Abs($v - $_) -lt .25 }) } | ForEach-Object { $_ - 273.15 } | Where-Object { $_ -gt 15 -and $_ -lt 120 })
        if ($z.Count) { $r.cpu = [math]::Round(($z | Measure-Object -Maximum).Maximum, 0); $r.cpu_fonte = 'zona térmica' }
    }
    # 3) GPU pelo driver de vídeo, o mesmo dado do Gerenciador de Tarefas (Windows 10 2004 ou mais novo; placas dedicadas)
    if ($GpuTambem -and $null -eq $r.gpu) {
        $g = $null; if (Get-Command KGpuTemp -ErrorAction SilentlyContinue) { $g = Tenta { KGpuTemp } $null }
        if ($null -ne $g) { $r.gpu = $g; $r.gpu_fonte = 'driver de vídeo' }
    }
    # 4) GPU NVIDIA pela ferramenta da própria NVIDIA (só nas leituras que você pede; a coleta de fundo chama a dela fora de jogo)
    if ($GpuTambem -and $null -eq $r.gpu -and (Get-Command KNvTemp -ErrorAction SilentlyContinue)) {
        $g = Tenta { KNvTemp } $null
        if ($null -ne $g) { $r.gpu = $g; $r.gpu_fonte = 'ferramenta da NVIDIA' }
    }
    $r
}
'''

INICIO_PS = r'''
# o que abre com o Windows, como o Gerenciador de Tarefas vê: registro (Run), pasta Inicializar, apps da Loja e tarefas no logon.
# ligado: o Gerenciador de Tarefas não marcou como desativado (vale a marca do usuário OU a da máquina).
# existe: o programa ainda está no disco (entrada de programa desinstalado não abre nada e não conta).
function _Aprovado([string[]]$Chaves, [string]$Nome) {
    foreach ($ap in $Chaves) { $b = Tenta { (Get-Item -LiteralPath $ap -ErrorAction Stop).GetValue($Nome) } $null; if ($b -is [byte[]] -and $b.Length -gt 0 -and ($b[0] % 2) -eq 1) { return $false } }
    return $true
}
function _ExeDe([string]$Cmd) {
    $c = [Environment]::ExpandEnvironmentVariables($Cmd.Trim())
    if ($c -match '^"([^"]+)"') { return $Matches[1] }
    if ($c -match '^(.+?\.(exe|bat|cmd|com|vbs|ps1|lnk))(\s|$)') { return $Matches[1] }
    return ($c -split '\s+')[0]
}
function _Existe([string]$Exe) {
    if (-not $Exe) { return $false }
    if ($Exe -notmatch '[\\/]') { return $true }   # só o nome (ctfmon, rundll32...): o Windows acha no PATH
    return [bool](Test-Path -LiteralPath $Exe -ErrorAction SilentlyContinue)
}
function ListaInicio {
    $r = New-Object System.Collections.Generic.List[object]
    $base = 'Software\Microsoft\Windows\CurrentVersion\Explorer\StartupApproved\'
    $runs = @(
        @('HKCU:\Software\Microsoft\Windows\CurrentVersion\Run', @("HKCU:\$($base)Run")),
        @('HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Run', @("HKLM:\$($base)Run", "HKCU:\$($base)Run")),
        @('HKLM:\SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Run', @("HKLM:\$($base)Run32", "HKCU:\$($base)Run32")))
    foreach ($par in $runs) {
        $it = Tenta { Get-Item -LiteralPath $par[0] -ErrorAction Stop } $null
        if (-not $it) { continue }
        foreach ($n in $it.GetValueNames()) {
            if (-not $n) { continue }
            $cmd = [string]$it.GetValue($n)
            if (-not $cmd.Trim()) { continue }
            $exe = _ExeDe $cmd
            $r.Add([pscustomobject]@{ tipo = 'run'; nome = $n; cmd = $cmd; exe = $exe; ap = $par[1][0]; ligado = (_Aprovado $par[1] $n); existe = (_Existe $exe) })
        }
    }
    foreach ($par in @(@("$env:APPDATA\Microsoft\Windows\Start Menu\Programs\Startup", @("HKCU:\$($base)StartupFolder")), @("$env:ProgramData\Microsoft\Windows\Start Menu\Programs\StartUp", @("HKLM:\$($base)StartupFolder", "HKCU:\$($base)StartupFolder")))) {
        foreach ($f in @(Get-ChildItem -LiteralPath $par[0] -File -ErrorAction SilentlyContinue | Where-Object { $_.Name -ne 'desktop.ini' })) {
            $alvo = $f.FullName
            if ($f.Extension -eq '.lnk') { $alvo = Tenta { (New-Object -ComObject WScript.Shell).CreateShortcut($f.FullName).TargetPath } $f.FullName; if (-not $alvo) { $alvo = $f.FullName } }
            $r.Add([pscustomobject]@{ tipo = 'pasta'; nome = $f.Name; cmd = $f.FullName; exe = $alvo; ap = $par[1][0]; ligado = (_Aprovado $par[1] $f.Name); existe = (_Existe $alvo) })
        }
    }
    # apps da Loja: só os que ainda estão instalados (o registro guarda o estado de apps que já saíram)
    $inst = @{}; foreach ($pk in @(Tenta { Get-AppxPackage -ErrorAction Stop } @())) { $inst[[string]$pk.PackageFamilyName] = $true }
    $sa = 'HKCU:\Software\Classes\Local Settings\Software\Microsoft\Windows\CurrentVersion\AppModel\SystemAppData'
    foreach ($pkg in @(Get-ChildItem -LiteralPath $sa -ErrorAction SilentlyContinue)) {
        if ($inst.Count -and -not $inst.ContainsKey($pkg.PSChildName)) { continue }
        foreach ($tk in @(Get-ChildItem -LiteralPath $pkg.PSPath -ErrorAction SilentlyContinue | Where-Object { $null -ne (Get-ItemProperty -LiteralPath $_.PSPath -Name State -ErrorAction SilentlyContinue) })) {
            $st = (Get-ItemProperty -LiteralPath $tk.PSPath -Name State).State
            $r.Add([pscustomobject]@{ tipo = 'loja'; nome = ($pkg.PSChildName -replace '_.*$', '') + ' (' + $tk.PSChildName + ')'; cmd = $pkg.PSChildName; exe = ''; ap = $tk.PSPath; ligado = ($st -eq 2 -or $st -eq 4); existe = $true })
        }
    }
    # tarefas agendadas no logon, fora as do Windows e as do próprio Katharos
    foreach ($tk in @(Get-ScheduledTask -ErrorAction SilentlyContinue | Where-Object { $_.State -ne 'Disabled' -and $_.TaskPath -notmatch '^\\Microsoft\\' -and $_.TaskName -notmatch '^Katharos' -and @($_.Triggers | Where-Object { $_.CimClass.CimClassName -eq 'MSFT_TaskLogonTrigger' -and $_.Enabled -ne $false }).Count -gt 0 })) {
        $exe = [Environment]::ExpandEnvironmentVariables((@($tk.Actions | ForEach-Object { [string]$_.Execute }) | Select-Object -First 1))
        $r.Add([pscustomobject]@{ tipo = 'tarefa'; nome = $tk.TaskName; cmd = (@($tk.Actions | ForEach-Object { [string]$_.Execute }) -join ' '); exe = $exe; ap = ($tk.TaskPath + $tk.TaskName); ligado = $true; existe = (_Existe ($exe.Trim('"'))) })
    }
    return ,$r.ToArray()
}
'''

MEDIDAS_PS = TEMP_GPU_PS + TEMP_PS + INICIO_PS + r'''
$os = Get-CimInstance Win32_OperatingSystem
$amostras = @()
for ($i = 0; $i -lt 4; $i++) {
    $p = Tenta { Get-CimInstance Win32_PerfFormattedData_PerfOS_Processor -Filter "Name='_Total'" -ErrorAction Stop }
    $q = Tenta { Get-CimInstance Win32_PerfFormattedData_Counters_ProcessorInformation -Filter "Name='_Total'" -ErrorAction Stop }
    $dk = Tenta { Get-CimInstance Win32_PerfFormattedData_PerfDisk_PhysicalDisk -Filter "Name='_Total'" -ErrorAction Stop }
    $me = Tenta { Get-CimInstance Win32_PerfFormattedData_PerfOS_Memory -ErrorAction Stop }
    if ($p) { $amostras += [pscustomobject]@{ dpc = [double]$p.PercentDPCTime; irq = [double]$p.PercentInterruptTime; disco = $(if ($dk) { [math]::Max(0, [math]::Min(100, 100 - [double]$dk.PercentIdleTime)) } else { $null }); fila = $(if ($dk) { [double]$dk.AvgDiskQueueLength } else { $null }); pag = $(if ($me) { [double]$me.PagesInputPersec } else { $null }); cpu = $(if ($q -and $null -ne $q.PercentProcessorUtility) { [math]::Min(100, [double]$q.PercentProcessorUtility) } else { [double]$p.PercentProcessorTime }); kernel = [double]$p.PercentPrivilegedTime; perf = $(if ($q) { [double]$q.PercentProcessorPerformance } else { $null }); limite = $(if ($q) { [double]$q.PercentPerformanceLimit } else { $null }) } }
    Start-Sleep -Milliseconds 900
}
function Media($c) { $v = @($amostras | ForEach-Object { $_.$c } | Where-Object { $null -ne $_ }); if ($v.Count) { [math]::Round(($v | Measure-Object -Average).Average, 1) } else { $null } }
$tt = LeTemperaturas $true
$temp = $tt.cpu
$gpuUso = Tenta { $g = @(Get-CimInstance Win32_PerfFormattedData_GPUPerformanceCounters_GPUEngine -Filter "Name LIKE '%engtype_3D%'" -ErrorAction Stop); if ($g.Count) { [math]::Min(100, [math]::Round(($g | Measure-Object -Property UtilizationPercentage -Sum).Sum, 0)) } else { $null } } $null
$vramUso = Tenta { $g = @(Get-CimInstance Win32_PerfFormattedData_GPUPerformanceCounters_GPUAdapterMemory -ErrorAction Stop); if ($g.Count) { [math]::Round(([double]($g | Measure-Object -Property DedicatedUsage -Maximum).Maximum) / 1GB, 2) } else { $null } } $null
$boot = Tenta { $e = Get-WinEvent -FilterHashtable @{ LogName = 'Microsoft-Windows-Diagnostics-Performance/Operational'; Id = 100 } -MaxEvents 1 -ErrorAction Stop; [int](([xml]$e.ToXml()).Event.EventData.Data | Where-Object Name -eq 'BootTime').'#text' } $null
$ld = Get-CimInstance Win32_LogicalDisk -Filter "DeviceID='C:'"
$mem = Tenta { Get-CimInstance Win32_PerfFormattedData_PerfOS_Memory -ErrorAction Stop } $null
$li = ListaInicio
$run = @($li | Where-Object { $_.ligado -and $_.existe }).Count
Dado 'medidas' @{
    data = (Get-Date).ToString('s')
    uptime_h = [math]::Round(((Get-Date) - $os.LastBootUpTime).TotalHours, 2)
    cpu = (Media 'cpu'); kernel = (Media 'kernel'); desempenho = (Media 'perf'); limite = (Media 'limite')
    dpc = (Media 'dpc'); interrupcoes = (Media 'irq'); disco_ativo = (Media 'disco'); fila_disco = (Media 'fila'); paginas_s = (Media 'pag')
    ram_disponivel = $(if ($mem) { [math]::Round([double]$mem.AvailableMBytes / 1024, 2) } else { $null })
    commit_pct = $(if ($mem -and [double]$mem.CommitLimit -gt 0) { [math]::Round(100 * [double]$mem.CommittedBytes / [double]$mem.CommitLimit, 0) } else { $null })
    ram_total = [math]::Round($os.TotalVisibleMemorySize / 1MB, 2)
    ram_usada = $(if ($mem) { [math]::Round([math]::Max(0, $os.TotalVisibleMemorySize / 1MB - [double]$mem.AvailableMBytes / 1024), 2) } else { [math]::Round(($os.TotalVisibleMemorySize - $os.FreePhysicalMemory) / 1MB, 2) })
    processos = @(Get-Process).Count
    servicos = @(Get-Service | Where-Object Status -eq 'Running').Count
    inicializacao = $run
    livre_c = [math]::Round($ld.FreeSpace / 1GB, 1)
    temperatura = $temp
    temp_fonte = $tt.cpu_fonte
    temperatura_gpu = $tt.gpu
    gpu_uso = $gpuUso
    vram_usada = $vramUso
    temp_gpu_fonte = $tt.gpu_fonte
    boot_s = $(if ($boot) { [math]::Round($boot / 1000, 1) } else { $null })
}
'''


def perfil_pc(ctx, forca=False):
    """O que este PC tem e usa (cache da sessão). Decide o que cada item recomenda."""
    if ctx.perfil and not forca:
        return ctx.perfil
    if not WINDOWS:
        ctx.perfil = PERFIL_VAZIO
        return ctx.perfil
    with Progresso(ctx.t, None, 'conhecendo o PC') as pr:
        s = roda_ps(ctx.t, PERFIL_PS, 'perfil', minutos=3, mostra=False, pr=pr)
    p = s.dados.get('perfil') or PERFIL_VAZIO
    ctx.perfil = p
    ctx.mult = fator_hardware(p)
    if p is not PERFIL_VAZIO:
        rel_pc(p)
        if not so_reconhecido(p):
            if ctx.args is not None:
                ctx.args.modo = 'seguro'
            ctx.t.aviso('Não reconheci esta versão do Windows (só conheço Windows 10 e 11). Por segurança, '
                        'só vão marcados os itens do modo seguro, e você pode ver cada item antes de confirmar.')
    return p


PERFIL_VAZIO = {'so': {'win11': False, 'build': 0, 'nome': '', 'versao': '', 'edicao': ''},
                'pc': {'fabricante': '', 'modelo': '', 'notebook': False, 'tablet': False, 'dominio': False, 'bateria': False},
                'cpu': {}, 'ram': {'total': 8, 'usada': 0}, 'disco': {'tipo': 'SSD', 'livre': 100, 'total': 200},
                'gpus': [], 'tem': {}, 'jogos': [], 'oem_gamer': [], 'antivirus': [], 'defender': {},
                'energia': {}, 'memoria': {}, 'sistema': {}}


def texto_cpu(p):
    n = re.sub(r'\((R|TM)\)|CPU @.*$|\s+Processor$', '', str(pf(p, 'cpu.nome', '') or '').strip()).strip()
    nuc, thr = pf(p, 'cpu.nucleos', 0) or 0, pf(p, 'cpu.threads', 0) or 0
    extra = [f'{nuc} núcleos, {thr} threads' if nuc else '', f'L3 {pf(p, "cpu.l3_mb")} MB' if pf(p, 'cpu.l3_mb') else '']
    return ' · '.join(x for x in [n] + extra if x)


def texto_ram(p):
    tipo = pf(p, 'ram.tipo') or ''
    pentes = [x for x in lista(pf(p, 'ram.pentes')) if isinstance(x, dict)]
    mhz = max((x.get('mhz') or 0 for x in pentes), default=0)
    canal = ''
    if len(pentes) == 1:
        canal = 'um pente só (canal simples)'
    elif len(pentes) >= 2:
        canal = f'{len(pentes)} pentes'
    partes = [gb(pf(p, 'ram.total')), ' '.join(x for x in (tipo, f'{mhz} MHz' if mhz else '') if x), canal,
              f'{pf(p, "ram.ocupados", "?")} de {pf(p, "ram.slots", "?")} slots']
    return ' · '.join(x for x in partes if x)


def texto_disco(p):
    partes = [' '.join(x for x in (str(pf(p, 'disco.tipo', '') or ''), str(pf(p, 'disco.barramento', '') or '')) if x), str(pf(p, 'disco.modelo') or ''),
              f'{gb(pf(p, "disco.livre"))} livres de {gb(pf(p, "disco.total"))}']
    d = pf(p, 'disco.desgaste')
    if isinstance(d, (int, float)) and d > 0:
        partes.append(f'{br(d, 0)} % de desgaste')
    tc = pf(p, 'disco.temperatura')
    if isinstance(tc, (int, float)) and 0 < tc < 100:
        partes.append(f'{br(tc, 0)} °C')
    return ' · '.join(x for x in partes if x)


def texto_video(p):
    vs = [v for v in lista(pf(p, 'video')) if isinstance(v, dict) and v.get('nome')]
    if not vs:
        return ', '.join(lista(p.get('gpus')))
    return ', '.join(v['nome'] + (f' ({br(v["vram_gb"], 0 if v["vram_gb"] >= 2 else 1)} GB)' if isinstance(v.get('vram_gb'), (int, float)) and v['vram_gb'] > 0 else '')
                     + (' integrada' if v.get('integrada') else '') for v in vs)


def texto_placa(p):
    b = pf(p, 'pc.bios')
    return str(pf(p, 'pc.placa') or '') + (f' · BIOS {b}' + (f' de {pf(p, "pc.bios_data")}' if pf(p, 'pc.bios_data') else '') if b else '')


def pf(p, caminho, padrao=None):
    """Lê p['a']['b'] com 'a.b'."""
    v = p
    for k in caminho.split('.'):
        if not isinstance(v, dict):
            return padrao
        v = v.get(k)
    return padrao if v is None else v


def so_reconhecido(p):
    """O build do Windows foi lido e é de Windows 10 ou 11 (10240 ou mais)? Sem isso, os itens que dependem de versão
    não têm base para decidir."""
    return (pf(p, 'so.build', 0) or 0) >= 10240


def eh_hd(p):
    return str(pf(p, 'disco.tipo', '')).upper() == 'HDD'


def eh_ssd(p):
    return str(pf(p, 'disco.tipo', '')).upper() == 'SSD'


def joga(p):
    return bool(lista(pf(p, 'jogos', [])))


def fabricante(p):
    f = str(pf(p, 'pc.fabricante', '')).lower()
    for nome, padrao in (('dell', 'dell|alienware'), ('hp', 'hewlett|^hp'), ('lenovo', 'lenovo'), ('acer', 'acer'),
                         ('asus', 'asus'), ('msi', 'micro-star|msi'), ('samsung', 'samsung'), ('positivo', 'positivo')):
        if re.search(padrao, f):
            return nome
    return f.split()[0] if f else ''


def fator_hardware(p):
    m = 1.0
    if eh_hd(p) or pf(p, 'disco.tipo') in ('desconhecido', 'Unspecified', None):
        m *= 2
    if (pf(p, 'ram.total', 8) or 8) < 6:
        m *= 1.5
    return m


def mede(ctx, rotulo='medindo'):
    if not WINDOWS:
        return {}
    with Progresso(ctx.t, None, rotulo) as pr:
        s = roda_ps(ctx.t, MEDIDAS_PS, 'medidas', minutos=2, mostra=False, pr=pr)
    m = s.dados.get('medidas') or {}
    try:
        completa_temperaturas(m)
    except Exception as e:
        LOG.escreve(f'temperatura pelo executável: {e!r}')
    return m


def salva_medida(m, nome):
    if m:
        grava_json(pasta('medidas') / f'{carimbo()}-{nome}.json', m)
        if not nome.startswith('antes-'):   # toda medida completa tenta fechar os ensaios da prova de ganho
            try:
                fecha_ensaios(m)
            except Exception as e:
                LOG.escreve(f'ensaios não fecharam: {e!r}')


def medidas_salvas():
    return sorted(pasta('medidas').glob('*.json'))


LINHAS_MEDIDA = [
    ('cpu', 'CPU em repouso', '%', 'menor'), ('kernel', 'tempo de kernel', '%', 'menor'),
    ('desempenho', 'clock (desempenho)', '%', 'maior'), ('ram_usada', 'RAM em uso', 'GB', 'menor'),
    ('disco_ativo', 'disco ocupado', '%', 'menor'),
    ('processos', 'processos', '', 'menor'), ('servicos', 'serviços rodando', '', 'menor'),
    ('inicializacao', 'abrem com o Windows', '', 'menor'), ('livre_c', 'livre em C:', 'GB', 'maior'),
    ('temperatura', 'temperatura da CPU', '°C', 'menor'), ('temperatura_gpu', 'temperatura da GPU', '°C', 'menor'),
    ('gpu_uso', 'GPU em uso', '%', 'menor'), ('vram_usada', 'memória de vídeo em uso', 'GB', 'menor'), ('boot_s', 'último boot', 's', 'menor'),
]


def _fmt_medida(v, un):
    if v in (None, ''):
        return '-'
    casas = 0 if un in ('', '%', '°C') else 1
    return br(v, casas) + (' ' + un if un else '')


def mostra_medidas(t, atual, antes=None):
    linhas = []
    for chave, rot, un, melhor in LINHAS_MEDIDA:
        a = atual.get(chave)
        if antes is None:
            linhas.append([rot, _fmt_medida(a, un)])
            continue
        b = antes.get(chave)
        dif = ''
        if isinstance(a, (int, float)) and isinstance(b, (int, float)) and a != b:
            d = a - b
            bom = (d < 0) == (melhor == 'menor')
            dif = t.p(('+' if d > 0 else '') + _fmt_medida(d, un), 'verde' if bom else 'amarelo')
        linhas.append([rot, _fmt_medida(b, un), _fmt_medida(a, un), dif])
    if antes is None:
        t.tabela(['medida', 'agora'], linhas, alinha='ed')
    else:
        t.tabela(['medida', 'antes', 'agora', 'mudou'], linhas, alinha='eddd')


def ferramenta_medir(ctx, args):
    t = ctx.t
    t.aba('CPU, kernel, clock, RAM, processos, serviços, inicialização, disco, temperatura e boot')
    t.paragrafo('Meça com o PC parado (sem programas abertos) para comparar de forma justa. As próprias consultas '
                'custam um pouco de CPU; o número em repouso real é um pouco menor.', 2, 'apagado')
    m = mede(ctx)
    if not m:
        t.erro('não consegui medir (só funciona no Windows).')
        return 1
    salvas = medidas_salvas()
    antes = le_json(salvas[0], None) if salvas else None
    salva_medida(m, 'medir')
    if not eh_admin():
        t.nota('  temperatura e tempo de boot só aparecem como administrador.')
    t.titulo('agora' if antes is None else f'comparado com a primeira medida ({salvas[0].name[:10]})')
    mostra_medidas(t, m, antes)
    if m.get('limite') is not None and m['limite'] < 95:
        t.aviso(f'O processador está limitado a {br(m["limite"], 0)}% (calor, carregador fraco ou plano de energia).')
    return 0


# ─────────────── raio-x: diagnóstico completo ───────────────

DIAG_PS = INICIO_PS + r'''
$dias60 = (Get-Date).AddDays(-60)
Vivo 'processos que mais gastam'
$a = @{}; foreach ($p in Get-Process) { try { $a[$p.Id] = $p.TotalProcessorTime.TotalMilliseconds } catch {} }
Start-Sleep -Seconds 4
$nucleos = [Environment]::ProcessorCount
$top = foreach ($p in Get-Process) { try { if ($a.ContainsKey($p.Id)) { [pscustomobject]@{ n = $p.ProcessName; cpu = [math]::Round(($p.TotalProcessorTime.TotalMilliseconds - $a[$p.Id]) / 40 / $nucleos, 1); mb = [math]::Round($p.WorkingSet64 / 1MB) } } } catch {} }
$porNome = $top | Group-Object n | ForEach-Object { [pscustomobject]@{ n = $_.Name; cpu = [math]::Round(($_.Group | Measure-Object cpu -Sum).Sum, 1); mb = [math]::Round(($_.Group | Measure-Object mb -Sum).Sum); qtd = $_.Count } }
# quem é cada um: a descrição e a empresa que o próprio arquivo do programa declara (o mesmo que o Gerenciador de Tarefas mostra).
# Path usa a consulta limitada do Windows (a do Gerenciador de Tarefas); a descrição é lida do arquivo, não do processo.
# cuidado com ban: com um anti-cheat rodando (jogo aberto), nem esta consulta leve é feita; os nomes bastam
$inf = @{}
$antiCheat = @('easyanticheat', 'easyanticheat_eos', 'beservice', 'vgc', 'vgtray', 'faceit', 'faceitclient', 'faceit-ac', 'battleye', 'eac_launcher')
$comAC = [bool](@($top | Where-Object { $antiCheat -contains ([string]$_.n).ToLower() }).Count)
foreach ($x in @(@($porNome | Sort-Object cpu -Descending | Select-Object -First 8) + @($porNome | Sort-Object mb -Descending | Select-Object -First 8))) {
    if ($comAC) { break }
    if (-not $x -or $inf.ContainsKey($x.n)) { continue }
    $cam = Tenta { (Get-Process -Name $x.n -ErrorAction Stop | Where-Object { $_.Path } | Select-Object -First 1).Path } $null
    $vi = $null; if ($cam) { $vi = Tenta { [Diagnostics.FileVersionInfo]::GetVersionInfo($cam) } $null }
    $inf[$x.n] = @{ desc = $(if ($vi) { ([string]$vi.FileDescription).Trim() } else { '' }); emp = $(if ($vi) { ([string]$vi.CompanyName).Trim() } else { '' }); pasta = $(if ($cam) { Split-Path $cam -Parent } else { '' }) }
}
$porNome = @($porNome | ForEach-Object { $i = $inf[$_.n]; if ($i) { $_ | Add-Member -NotePropertyName desc -NotePropertyValue $i.desc -PassThru | Add-Member -NotePropertyName emp -NotePropertyValue $i.emp -PassThru | Add-Member -NotePropertyName pasta -NotePropertyValue $i.pasta -PassThru } else { $_ } })
Dado 'top_cpu' (Lista ($porNome | Sort-Object cpu -Descending | Select-Object -First 8))
Dado 'top_ram' (Lista ($porNome | Sort-Object mb -Descending | Select-Object -First 8))

$io = @(Tenta { Get-CimInstance Win32_PerfFormattedData_PerfProc_Process -ErrorAction Stop | Where-Object { @('_Total','Idle') -notcontains $_.Name -and [double]$_.IODataBytesPersec -gt 1MB } | ForEach-Object { [pscustomobject]@{ n = ([string]$_.Name -replace '#\d+$', ''); mbs = [math]::Round([double]$_.IODataBytesPersec / 1MB, 1) } } } @())
Dado 'top_io' (Lista ($io | Group-Object n | ForEach-Object { [pscustomobject]@{ n = $_.Name; mbs = [math]::Round(($_.Group | Measure-Object mbs -Sum).Sum, 1) } } | Sort-Object mbs -Descending | Select-Object -First 5))

Vivo 'quem chama o WMI'
$wmiCpu = ($porNome | Where-Object { $_.n -eq 'WmiPrvSE' } | Measure-Object cpu -Sum).Sum
$wmi = @()
if ($wmiCpu -gt 1.5) {
    $ev = @(Get-WinEvent -LogName 'Microsoft-Windows-WMI-Activity/Operational' -MaxEvents 400 -ErrorAction SilentlyContinue | Where-Object { $_.Id -eq 11 })
    $wmi = $ev | ForEach-Object { if ($_.Message -match 'ClientProcessId\s*=\s*(\d+)') { [int]$Matches[1] } } | Group-Object | Sort-Object Count -Descending | Select-Object -First 5 | ForEach-Object {
        $pp = Get-Process -Id ([int]$_.Name) -ErrorAction SilentlyContinue
        [pscustomobject]@{ processo = $(if ($pp) { $pp.ProcessName } else { 'pid ' + $_.Name }); consultas = $_.Count }
    }
}
Dado 'wmi' @{ cpu = [double]$wmiCpu; clientes = (Lista $wmi) }

Vivo 'inicializacao'
# só o que abre de verdade: desativado no Gerenciador de Tarefas e programa que já saiu do PC não contam
$ini = @(ListaInicio | ForEach-Object { $_ } | Where-Object { $_.ligado -and $_.existe } | ForEach-Object { [pscustomobject]@{ nome = $(if ($_.tipo -eq 'pasta') { [IO.Path]::GetFileNameWithoutExtension($_.nome) } else { $_.nome }); onde = $_.tipo; cmd = $_.cmd } })
Dado 'inicializacao' (Lista $ini)

Vivo 'boot'
$kinds = @{ 101 = 'programa'; 102 = 'driver'; 103 = 'servico'; 106 = 'tarefa'; 109 = 'dispositivo' }
$bootEv = @(Get-WinEvent -FilterHashtable @{ LogName = 'Microsoft-Windows-Diagnostics-Performance/Operational'; Id = @(101,102,103,106,109); StartTime = $dias60 } -ErrorAction SilentlyContinue)
$bootRows = foreach ($e in $bootEv) { $d = @{}; ([xml]$e.ToXml()).Event.EventData.Data | ForEach-Object { $d[$_.Name] = $_.'#text' }; $nm = $d.FriendlyName; if (-not $nm) { $nm = $d.Name }; [pscustomobject]@{ tipo = $kinds[$e.Id]; nome = [string]$nm; ms = [int]$d.DegradationTime } }
Dado 'boot' (Lista ($bootRows | Group-Object tipo, nome | ForEach-Object { [pscustomobject]@{ tipo = $_.Group[0].tipo; nome = $_.Group[0].nome; vezes = $_.Count; s = [math]::Round(($_.Group | Measure-Object ms -Average).Average / 1000, 1) } } | Sort-Object s -Descending | Select-Object -First 8))
$bootT = @(Get-WinEvent -FilterHashtable @{ LogName = 'Microsoft-Windows-Diagnostics-Performance/Operational'; Id = 100 } -MaxEvents 5 -ErrorAction SilentlyContinue | ForEach-Object { [math]::Round([int](([xml]$_.ToXml()).Event.EventData.Data | Where-Object Name -eq 'BootTime').'#text' / 1000, 1) })
Dado 'boot_tempos' (Lista $bootT)

Vivo 'servicos de terceiros'
$terc = @(Get-CimInstance Win32_Service -ErrorAction SilentlyContinue | Where-Object { $_.State -eq 'Running' -and $_.PathName -and $_.PathName -notmatch '\\Windows\\(system32|SysWOW64|servicing|Microsoft\.NET)\\|\\Windows Defender\\|\\Microsoft\\Edge|MsMpEng|NisSrv|SecurityHealth' } | ForEach-Object { [pscustomobject]@{ nome = $_.Name; exibe = $_.DisplayName; modo = $_.StartMode } })
Dado 'terceiros' (Lista $terc)

Vivo 'restos de programas'
$orfaos = @(Get-CimInstance Win32_Service -ErrorAction SilentlyContinue | Where-Object { $_.PathName -and $_.PathName -notmatch 'svchost|\\Windows\\' } | ForEach-Object {
    $exe = $_.PathName; if ($exe -match '^"([^"]+)"') { $exe = $Matches[1] } elseif ($exe -match '^(\S+\.exe)') { $exe = $Matches[1] }
    if ($exe -match '\.exe$' -and -not (Test-Path -LiteralPath ([Environment]::ExpandEnvironmentVariables($exe)))) { [pscustomobject]@{ nome = $_.Name; exibe = $_.DisplayName; exe = $exe } }
})
Dado 'servicos_orfaos' (Lista $orfaos)

Vivo 'tarefas agendadas'
$suspeitas = @(); $orfas = @()
foreach ($tk in @(Get-ScheduledTask -ErrorAction SilentlyContinue | Where-Object { $_.State -ne 'Disabled' })) {
    foreach ($ac in @($tk.Actions)) {
        $exe = [Environment]::ExpandEnvironmentVariables([string]$ac.Execute).Trim('"')
        if (-not $exe) { continue }
        $rep = $null
        foreach ($tr in @($tk.Triggers)) { if ($tr.Repetition -and $tr.Repetition.Interval) { $rep = [string]$tr.Repetition.Interval } }
        $curta = $false
        if ($rep -match '^PT(\d+)M$' -and [int]$Matches[1] -le 15) { $curta = $true }
        if ($rep -match '^PT\d+S$') { $curta = $true }
        if ($exe -match '\\AppData\\|\\Temp\\|\\Users\\Public\\' -and $exe -match '\.(exe|bat|cmd|vbs|js|ps1|scr)$') {
            $suspeitas += [pscustomobject]@{ tarefa = ($tk.TaskPath + $tk.TaskName); exe = $exe; repete = $rep; curta = $curta }
        }
        if ($exe -match '^[A-Za-z]:\\' -and $exe -match '\.exe$' -and $tk.TaskPath -notmatch '^\\Microsoft\\' -and -not (Test-Path -LiteralPath $exe)) {
            $orfas += [pscustomobject]@{ tarefa = ($tk.TaskPath + $tk.TaskName); exe = $exe }
        }
    }
}
Dado 'tarefas_suspeitas' (Lista $suspeitas)
Dado 'tarefas_orfas' (Lista $orfas)
$ameacas = @(Tenta { Get-MpThreatDetection -ErrorAction Stop | Where-Object { $_.InitialDetectionTime -gt $dias60 } } @())
Dado 'ameacas' @{ qtd = $ameacas.Count; ultimas = (Lista ($ameacas | Select-Object -First 5 | ForEach-Object { [pscustomobject]@{ quando = ([datetime]$_.InitialDetectionTime).ToString('s'); id = [string]$_.ThreatID } })) }

Vivo 'saude'
$smart = @(Tenta { Get-PhysicalDisk | ForEach-Object { $r = $_ | Get-StorageReliabilityCounter -ErrorAction SilentlyContinue; [pscustomobject]@{ disco = $_.FriendlyName; tipo = [string]$_.MediaType; saude = [string]$_.HealthStatus; temp = $r.Temperature; horas = $r.PowerOnHours; desgaste = $r.Wear; erros = $r.ReadErrorsTotal } } } @())
Dado 'smart' (Lista $smart)
$falha = [bool](Tenta { Get-CimInstance -Namespace root\wmi -ClassName MSStorageDriver_FailurePredictStatus -ErrorAction Stop | Where-Object PredictFailure } $null)
$crash = @(Get-WinEvent -FilterHashtable @{ LogName = 'System'; Id = 41,1001,6008; StartTime = $dias60 } -ErrorAction SilentlyContinue | Where-Object { $_.ProviderName -match 'Kernel-Power|BugCheck|EventLog' }).Count
$telaAzul = @(Get-WinEvent -FilterHashtable @{ LogName = 'System'; ProviderName = 'Microsoft-Windows-WER-SystemErrorReporting','BugCheck'; StartTime = $dias60 } -ErrorAction SilentlyContinue).Count
# só erros (nível 1 e 2): avisos de pendrive tirado sem ejetar e de nova tentativa de leitura são ruído e davam alarme falso
$discoErr = @(Get-WinEvent -FilterHashtable @{ LogName = 'System'; ProviderName = 'disk','Ntfs','storahci','stornvme','iaStorA'; Level = 1,2; StartTime = $dias60 } -ErrorAction SilentlyContinue).Count
$devs = @(Get-CimInstance Win32_PnPEntity -ErrorAction SilentlyContinue | Where-Object { $_.ConfigManagerErrorCode -ne 0 } | ForEach-Object { [pscustomobject]@{ nome = [string]$_.Name; classe = [string]$_.PNPClass; codigo = [int]$_.ConfigManagerErrorCode } })
$erros = @(Get-WinEvent -FilterHashtable @{ LogName = 'System'; Level = 1,2; StartTime = (Get-Date).AddDays(-7) } -ErrorAction SilentlyContinue | Group-Object ProviderName | Sort-Object Count -Descending | Select-Object -First 6 | ForEach-Object { [pscustomobject]@{ fonte = $_.Name; qtd = $_.Count } })
$bios = Tenta { Get-CimInstance Win32_BIOS } $null
$sb = Tenta { Confirm-SecureBootUEFI -ErrorAction Stop } $null
$bl = Tenta { [string](Get-BitLockerVolume -MountPoint 'C:' -ErrorAction Stop).ProtectionStatus } ''
$ultAtual = Tenta { (Get-HotFix | Where-Object InstalledOn | Sort-Object InstalledOn -Descending | Select-Object -First 1).InstalledOn.ToString('s') } ''
$trocas = @(Get-WinEvent -FilterHashtable @{ LogName = 'System'; ProviderName = 'Microsoft-Windows-UserModePowerService'; Id = 12; StartTime = (Get-Date).AddDays(-14) } -MaxEvents 30 -ErrorAction SilentlyContinue | ForEach-Object { if ($_.Message -match '([A-Za-z]:\\[^\r\n]+?\.exe)') { Split-Path $Matches[1] -Leaf } } | Group-Object | Sort-Object Count -Descending | Select-Object -First 4 | ForEach-Object { [pscustomobject]@{ processo = $_.Name; vezes = $_.Count } })
$bat = $null
if (Get-CimInstance Win32_Battery -ErrorAction SilentlyContinue) {
    $arq = Join-Path $env:TEMP 'katharos-bateria.html'
    powercfg /batteryreport /output $arq | Out-Null
    $h = Get-Content $arq -Raw -ErrorAction SilentlyContinue
    $proj = $null; $cheia = $null
    if ($h -match '(?:DESIGN CAPACITY|CAPACIDADE DE DESIGN|CAPACIDADE DO PROJETO)</span></td><td>([\d\.,\s]+) mWh') { $proj = [double]($Matches[1] -replace '[^\d]', '') }
    if ($h -match '(?:FULL CHARGE CAPACITY|CAPACIDADE DE CARGA TOTAL|CAPACIDADE DE CARGA COMPLETA)</span></td><td>([\d\.,\s]+) mWh') { $cheia = [double]($Matches[1] -replace '[^\d]', '') }
    if ($proj -and $cheia) { $bat = [math]::Round($cheia / $proj * 100) }
    Remove-Item $arq -ErrorAction SilentlyContinue
}
$fw = @($devs | Where-Object { $_.classe -eq 'Firmware' })
Dado 'saude' @{ falha_iminente = $falha; desligamentos = $crash; telas_azuis = $telaAzul; erros_disco = $discoErr; dispositivos = (Lista $devs); erros_7d = (Lista $erros); bios = $(if ($bios) { [string]$bios.SMBIOSBIOSVersion } else { '' }); bios_data = $(if ($bios -and $bios.ReleaseDate) { ([datetime]$bios.ReleaseDate).ToString('s') } else { '' }); secure_boot = $sb; bitlocker = $bl; ultima_atualizacao = $ultAtual; trocas_plano = (Lista $trocas); bateria_saude = $bat; firmware_erro = ($fw.Count -gt 0) }

Vivo 'espaco em disco'
$L = $env:LOCALAPPDATA
$caches = @(
    @('temporarios do usuario', $env:TEMP), @('temporarios do Windows', "$env:WINDIR\Temp"),
    @('downloads do Windows Update', "$env:WINDIR\SoftwareDistribution\Download"),
    @('Otimizacao de Entrega', "$env:WINDIR\ServiceProfiles\NetworkService\AppData\Local\Microsoft\Windows\DeliveryOptimization\Cache"),
    @('relatorios de erro', "$env:ProgramData\Microsoft\Windows\WER"), @('dumps de travamento', "$L\CrashDumps"),
    @('logs de instalacao (Panther)', "$env:WINDIR\Panther"), @('logs do Windows (CBS)', "$env:WINDIR\Logs\CBS"),
    @('cache de shaders DirectX', "$L\D3DSCache"), @('cache de shaders NVIDIA', "$L\NVIDIA\DXCache"), @('cache OpenGL NVIDIA', "$L\NVIDIA\GLCache"), @('cache de shaders AMD', "$L\AMD\DxCache"),
    @('instaladores baixados guardados', "$L\Downloaded Installations"), @('miniaturas', "$L\Microsoft\Windows\Explorer"),
    @('cache do npm', "$L\npm-cache"), @('cache do pip', "$L\pip\Cache"), @('cache do Yarn', "$L\Yarn\Cache"),
    @('cache do Chrome', "$L\Google\Chrome\User Data\Default\Cache"), @('cache do Edge', "$L\Microsoft\Edge\User Data\Default\Cache"), @('cache do Brave', "$L\BraveSoftware\Brave-Browser\User Data\Default\Cache"),
    @('Windows.old', "$env:SystemDrive\Windows.old")
)
$cs = foreach ($c in $caches) { $b = TamanhoPasta $c[1]; if ($b -gt 50MB) { [pscustomobject]@{ nome = $c[0]; gb = [math]::Round($b / 1GB, 2) } } }
Dado 'caches' (Lista ($cs | Sort-Object gb -Descending))
$hib = Tenta { [math]::Round((Get-Item "$env:SystemDrive\hiberfil.sys" -Force -ErrorAction Stop).Length / 1GB, 1) } 0
$res = Tenta { [string](Get-WindowsReservedStorageState -ErrorAction Stop).ReservedStorageState } ''
Dado 'arquivos_sistema' @{ hiberfil_gb = $hib; armazenamento_reservado = $res }
$odProj = @()
if ($env:OneDrive -and (Test-Path -LiteralPath $env:OneDrive)) {
    $odProj = @(Get-ChildItem -LiteralPath $env:OneDrive -Directory -Recurse -Depth 4 -Filter node_modules -ErrorAction SilentlyContinue | Select-Object -First 10 | ForEach-Object { $_.Parent.FullName })
}
Dado 'onedrive_projetos' (Lista $odProj)

Vivo 'programas instalados'
$progs = @(Get-ItemProperty 'HKLM:\Software\Microsoft\Windows\CurrentVersion\Uninstall\*','HKLM:\Software\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall\*','HKCU:\Software\Microsoft\Windows\CurrentVersion\Uninstall\*' -ErrorAction SilentlyContinue | Where-Object { $_.DisplayName -and -not $_.SystemComponent -and -not $_.ParentKeyName } | ForEach-Object { [string]$_.DisplayName } | Sort-Object -Unique)
Dado 'programas' (Lista $progs)
$apps = @(Tenta { Get-AppxPackage -ErrorAction Stop | Where-Object { -not $_.IsFramework -and $_.SignatureKind -ne 'System' -and -not $_.NonRemovable } | ForEach-Object { [string]$_.Name } } @())
Dado 'apps' (Lista $apps)
'''

QUEIXAS = [
    ('lento', 'lento ou travando no dia a dia'),
    ('boot', 'demora para ligar, muita coisa abrindo junto'),
    ('disco', 'disco cheio'),
    ('calor', 'esquenta demais ou ventoinha alta mesmo parado'),
    ('bateria', 'bateria dura pouco'),
    ('jogos', 'jogos com FPS baixo ou engasgando'),
    ('privacidade', 'propaganda, sugestões e IA que não pedi'),
    ('tudo', 'não sei, só quero que fique melhor'),
]


def pergunta_queixas(t, args):
    """A pergunta do começo: o que mais incomoda. Só prioriza; o diagnóstico olha tudo do mesmo jeito."""
    if getattr(args, 'queixas', None):
        return [q.strip() for q in args.queixas.split(',') if q.strip()]
    if not t.interativo or getattr(args, 'sim', False):
        return ['tudo']
    t.titulo('o que mais incomoda neste PC?')
    for i, (_, txt) in enumerate(QUEIXAS, 1):
        t.escreve(f'  {t.p(f"{i:>2}", "destaque", True)}  {t.p(txt, "texto")}')
    t.escreve()
    t.paragrafo('Pode marcar várias, separadas por espaço (ex.: 1 3). Isso só muda a ordem do que eu mostro: '
                'a análise é sempre completa.', 2, 'apagado')
    r = t.pergunta('queixas', '8')
    nums = [int(x) for x in re.findall(r'\d+', r) if 0 < int(x) <= len(QUEIXAS)]
    return [QUEIXAS[n - 1][0] for n in nums] or ['tudo']


class Achado:
    """Uma dor encontrada: impacto (3 alto, 2 médio, 1 baixo, 0 só informa e não tira ponto da nota),
    evidência medida e o que fazer."""

    def __init__(self, impacto, queixas, titulo, evidencia, faz='', comando=''):
        self.impacto, self.queixas, self.titulo = impacto, set(queixas), titulo
        self.evidencia, self.faz, self.comando = evidencia, faz, comando


def analisa(p, m, d):
    """As regras do diagnóstico. p = perfil, m = medidas, d = dados do raio-x."""
    A = []
    ram_t = pf(p, 'ram.total', 0) or 0
    ram_u = m.get('ram_usada') or pf(p, 'ram.usada', 0) or 0
    livre = pf(p, 'disco.livre', 0) or 0
    total = pf(p, 'disco.total', 1) or 1
    ini = lista(d.get('inicializacao'))
    saude = d.get('saude') or {}

    if eh_hd(p):
        A.append(Achado(3, ['lento', 'boot', 'tudo', 'jogos'], 'O Windows está num HD mecânico',
                        'O disco do sistema é HDD: é o maior gargalo possível hoje.',
                        'Trocar por um SSD (de preferência com o Windows instalado do zero) é o maior ganho que existe. '
                        'Até lá: manter SysMain e Inicialização rápida, desfragmentar e reduzir escrita em segundo plano.', 'disco'))
    if ram_t and ram_t <= 4.5:
        A.append(Achado(3, ['lento', 'tudo', 'jogos'], 'Pouca memória RAM',
                        f'{gb(ram_t)} instalados; o Windows sozinho usa perto de 3 GB.',
                        'Aumentar para 8 GB ou mais. Enquanto isso: menos coisas na inicialização e em segundo plano.', 'inicializacao'))
    elif ram_t and ram_u / ram_t > 0.7:
        A.append(Achado(2, ['lento', 'tudo', 'jogos'], 'RAM quase cheia em repouso',
                        f'{gb(ram_u)} de {gb(ram_t)} em uso com o PC parado ({br(100 * ram_u / ram_t, 0)}%).',
                        'Tirar programas da inicialização e serviços de fabricante; se continuar alto, mais RAM.', 'inicializacao'))
    slots, ocup = pf(p, 'ram.slots', 0) or 0, pf(p, 'ram.ocupados', 0) or 0
    if slots > ocup and ocup == 1:
        A.append(Achado(1, ['jogos', 'lento', 'tudo'], 'Memória em canal único',
                        f'{ocup} de {slots} slots ocupados.',
                        'Um segundo pente igual ativa o dual channel, que ajuda muito o vídeo integrado.'))
    pct = 100 * livre / total
    if pct < 15:
        A.append(Achado(3 if pct < 8 else 2, ['disco', 'lento', 'tudo'], 'Pouco espaço livre em C:',
                        f'{gb(livre)} livres ({br(pct, 0)}%). Abaixo de 15% o Windows fica lento e as atualizações falham.',
                        'Limpar caches e temporários, e ver os arquivos grandes.', 'limpar'))
    caches = lista(d.get('caches'))
    soma = sum(c.get('gb', 0) for c in caches if c.get('nome') != 'Windows.old')
    if soma > 2:
        maiores = ', '.join(f'{c["nome"]} {gb(c["gb"])}' for c in caches[:3])
        A.append(Achado(2 if soma > 8 else 1, ['disco', 'tudo'], 'Caches e temporários acumulados',
                        f'{gb(soma)} que se recriam sozinhos. Maiores: {maiores}.', 'Limpar com segurança.', 'limpar'))
    if any(c.get('nome') == 'Windows.old' for c in caches):
        w = next(c['gb'] for c in caches if c.get('nome') == 'Windows.old')
        A.append(Achado(2, ['disco', 'tudo'], 'Windows.old ocupando espaço', f'{gb(w)} da versão anterior do Windows.',
                        'Pode sair se você não pretende voltar à versão anterior.', 'limpar'))
    n_ini = len(ini)
    if n_ini > 8:
        A.append(Achado(3 if n_ini > 14 else 2, ['boot', 'lento', 'tudo'], 'Muita coisa abrindo com o Windows',
                        f'{n_ini} itens na inicialização: ' + ', '.join(i.get('nome', '') for i in ini[:6]) + ('…' if n_ini > 6 else ''),
                        'Desligar o que não precisa abrir sozinho (o Gerenciador de Tarefas usa o mesmo mecanismo).', 'inicializacao'))
    boots = [b for b in lista(d.get('boot_tempos')) if isinstance(b, (int, float))]
    if boots and boots[0] > 60:
        culpados = ', '.join(f'{b.get("nome")} {br(b.get("s"), 1)} s' for b in lista(d.get('boot'))[:3])
        A.append(Achado(2, ['boot', 'tudo'], 'Boot demorado', f'Último boot: {br(boots[0], 0)} s. Mais atrasaram: {culpados or "sem registro"}.',
                        'Inicialização, serviços de terceiros com início atrasado e, em HD, otimização do boot.', 'disco'))
    ativos = [a for a in lista(p.get('antivirus')) if a.get('ativo')]
    modo_def = str(pf(p, 'defender.modo', '') or '').lower()
    if 'passive' in modo_def or 'passivo' in modo_def or 'edr' in modo_def or pf(p, 'defender.tempo_real') is False:
        ativos = [a for a in ativos if 'defender' not in str(a.get('nome', '')).lower()]   # o Defender só olha: não briga com o outro
    terceiros = [a for a in ativos if 'defender' not in str(a.get('nome', '')).lower()]
    if len(ativos) > 1:
        A.append(Achado(3, ['lento', 'tudo', 'jogos'], 'Dois antivírus ativos ao mesmo tempo',
                        ', '.join(a['nome'] for a in ativos) + '. Eles brigam pelo disco e pela CPU.',
                        'Ficar com um só. A decisão é sua: o katharos só remove antivírus de fábrica (McAfee, Norton) se você marcar.', 'programas'))
    elif terceiros and re.search(r'mcafee|norton|avast|avg|avira', terceiros[0].get('nome', ''), re.I):
        A.append(Achado(2, ['lento', 'tudo'], 'Antivírus de fábrica ou gratuito pesado', terceiros[0]['nome'],
                        'O Defender do Windows protege bem e pesa menos. Remover só se você não pagou por ele.', 'programas'))
    if not ativos and not pf(p, 'defender.tempo_real') and not lista(p.get('antivirus')):
        A.append(Achado(3, ['tudo'], 'PC sem proteção em tempo real', 'Nenhum antivírus ativo.',
                        'Abra Segurança do Windows e ligue a proteção em tempo real (o katharos nunca desliga isso).'))
    cpu = m.get('cpu')
    if cpu is not None and cpu > 20 and (pf(p, 'sistema.uptime_h', 1) or 0) >= 0.17:
        tops = lista(d.get('top_cpu'))
        top = explica_processos(tops, 'cpu', '%')
        q = quem_e(tops[0].get('n')) if tops else None
        A.append(Achado(2, ['lento', 'calor', 'bateria', 'tudo'], 'CPU ocupada com o PC parado',
                        f'{br(cpu, 0)}% em repouso (kernel {br(m.get("kernel"), 0)}%). Quem mais gasta: {top}.',
                        (f'O primeiro é {q[0]}: {q[1]}.' if q else 'Ver o que é cada um; serviços de fabricante e atualizadores costumam ser a causa.'),
                        (q[2] if q and q[2] else 'servicos')))

    # ── sinais medidos: memória de verdade, disco que não para, drivers interrompendo ──
    commit = m.get('commit_pct')
    if commit is not None and commit >= 90:
        A.append(Achado(3, ['lento', 'tudo', 'jogos'], 'Memória no limite',
                        f'{br(commit, 0)}% do que o Windows consegue prometer aos programas (RAM + arquivo de paginação) já está comprometido'
                        + (f'; {gb(m["ram_disponivel"])} disponíveis.' if m.get('ram_disponivel') is not None else '.'),
                        'Passando de 100% os programas fecham sozinhos. Feche o que mais usa memória, deixe o arquivo de paginação '
                        'automático e, se for sempre assim, este PC precisa de mais RAM. Mais usam: '
                        + (explica_processos(lista(d.get('top_ram')), 'mb', 'MB') or 'sem registro') + '.', 'memoria'))
    elif (m.get('paginas_s') or 0) > 300 and m.get('ram_disponivel') is not None and ram_t and m['ram_disponivel'] / ram_t < 0.12:
        A.append(Achado(2, ['lento', 'tudo'], 'Windows buscando memória no disco',
                        f'{br(m["paginas_s"], 0)} páginas por segundo lidas do arquivo de paginação, com só {gb(m["ram_disponivel"])} disponíveis.',
                        'É o que faz tudo "engasgar" ao trocar de janela. Menos programas abertos juntos ou mais RAM.', 'inicializacao'))
    ativo = m.get('disco_ativo')
    if ativo is not None and ativo >= 50:
        io = lista(d.get('top_io'))
        quem = ', '.join(f'{x.get("n")} {br(x.get("mbs"), 1)} MB/s' + (f' ({quem_e(x.get("n"))[0]})' if quem_e(x.get('n')) else '') for x in io[:3])
        A.append(Achado(3 if eh_hd(p) else 2, ['lento', 'boot', 'tudo'], 'Disco ocupado sem parar com o PC parado',
                        f'{br(ativo, 0)}% do tempo ocupado em repouso (fila de {br(m.get("fila_disco") or 0, 1)}). '
                        + (f'Quem mais lê e grava agora: {quem}.' if quem else 'Nenhum programa se destacou na leitura: pode ser o próprio disco lento.'),
                        ('Em HD é o clássico "disco a 100%": o Windows fica esperando o disco. ' if eh_hd(p) else '')
                        + 'Espere atualizações e antivírus terminarem; se for sempre assim, reduza a escrita em segundo plano.', 'disco'))
    dpc = (m.get('dpc') or 0) + (m.get('interrupcoes') or 0)
    if dpc >= 5:
        A.append(Achado(2, ['jogos', 'lento', 'tudo'], 'Drivers interrompendo o processador',
                        f'{br(dpc, 1)}% da CPU em interrupções e DPC com o PC parado (o normal é abaixo de 2%).',
                        'É a causa mais comum de áudio picotando e de engasgos em jogos mesmo com FPS alto. Quase sempre é driver de rede, '
                        'de áudio ou de vídeo desatualizado, ou um dispositivo USB com defeito: veja os drivers antigos em "saude".', 'saude'))

    # ── o que o hardware entrega e não está sendo usado ──
    pentes = [x for x in lista(pf(p, 'ram.pentes')) if isinstance(x, dict)]
    lentos = [x for x in pentes if (x.get('mhz') or 0) > 0 and (x.get('mhz_max') or 0) >= 2666 and x['mhz'] <= 0.85 * x['mhz_max']]
    if lentos and not pf(p, 'pc.notebook'):
        A.append(Achado(2 if joga(p) else 1, ['jogos', 'lento', 'tudo'], 'Memória rodando abaixo da velocidade dela',
                        f'Os pentes são de {lentos[0]["mhz_max"]} MHz e estão a {lentos[0]["mhz"]} MHz.',
                        'Parece que o perfil XMP (Intel) ou EXPO/DOCP (AMD) está desligado na BIOS. Ligar é uma opção só na tela da BIOS e '
                        'dá ganho real em jogos. O Katharos não mexe na BIOS: procure "XMP" no manual da placa-mãe.'))
    tamanhos = {x.get('gb') for x in pentes if x.get('gb')}
    if len(pentes) >= 2 and len(tamanhos) > 1:
        A.append(Achado(0, ['jogos', 'tudo'], 'Pentes de memória de tamanhos diferentes',
                        ' + '.join(f'{x.get("gb")} GB' for x in pentes) + '.',
                        'Funciona, mas só a parte igual trabalha em canal duplo. Numa troca futura, prefira dois pentes iguais.'))
    tela = pf(p, 'tela') or {}
    if isinstance(tela, dict) and (tela.get('hz_max') or 0) >= (tela.get('hz') or 0) + 15 and (tela.get('hz') or 0) > 0:
        A.append(Achado(2, ['jogos', 'tudo'], f'Monitor de {tela["hz_max"]} Hz rodando a {tela["hz"]} Hz',
                        f'Na resolução atual ({tela.get("largura")}×{tela.get("altura")}) a tela aceita {tela["hz_max"]} Hz.',
                        'Você pagou por uma tela mais fluida e não está usando: Configurações > Sistema > Tela > Tela avançada > '
                        'Taxa de atualização. Em notebook na bateria, a taxa menor economiza energia.'))
    videos = [v for v in lista(pf(p, 'video')) if isinstance(v, dict)]
    if any(v.get('basico') for v in videos):
        A.append(Achado(3, ['lento', 'jogos', 'tudo'], 'Placa de vídeo sem driver',
                        'O Windows está usando o "Adaptador de Vídeo Básico da Microsoft": sem aceleração, tudo é desenhado pelo processador.',
                        'Instale o driver do fabricante da placa (NVIDIA, AMD ou Intel) ou rode o Windows Update até ele aparecer.', 'atualizar'))
    for v in videos:
        if v.get('basico') or not re.search(r'nvidia|geforce|radeon|amd|arc', str(v.get('nome', '')), re.I):
            continue
        try:
            meses = (datetime.now() - datetime.fromisoformat(str(v.get('driver_data'))[:19])).days / 30.4
        except ValueError:
            continue
        if meses >= 12:
            A.append(Achado(2 if joga(p) and meses >= 18 else 1, ['jogos', 'tudo'], 'Driver da placa de vídeo antigo',
                            f'{v.get("nome")}: driver {v.get("driver")} de {str(v.get("driver_data"))[:10]} (há {br(meses, 0)} meses).',
                            'Jogos novos dependem de driver novo. Baixe no site da NVIDIA ou da AMD (o Katharos não baixa nada).'))
            break
    desg, terr, tdisco = pf(p, 'disco.desgaste'), pf(p, 'disco.erros'), pf(p, 'disco.temperatura')
    if isinstance(terr, (int, float)) and terr > 0:
        A.append(Achado(3, ['disco', 'lento', 'tudo'], 'O disco do sistema tem erros de leitura ou gravação',
                        f'{int(terr)} erros que o próprio disco não conseguiu corrigir (contador de confiabilidade do Windows).',
                        'Faça cópia dos seus arquivos agora e planeje trocar o disco. Erros que o disco não corrige costumam aumentar.'))
    elif isinstance(desg, (int, float)) and desg >= 80:
        A.append(Achado(2, ['disco', 'tudo'], 'SSD perto do fim da vida útil', f'Desgaste em {br(desg, 0)} % pelo próprio SSD.',
                        'Ainda funciona, mas mantenha cópia dos seus arquivos e planeje a troca.'))
    if isinstance(tdisco, (int, float)) and 65 <= tdisco < 100:
        A.append(Achado(1, ['calor', 'disco'], 'Disco quente', f'{br(tdisco, 0)} °C no disco do sistema.',
                        'SSD NVMe acima de 70 °C perde velocidade para se proteger. Um dissipador ou mais ventilação no gabinete resolve.'))
    if eh_ssd(p) and pf(p, 'disco.trim') is False:
        A.append(Achado(2, ['lento', 'tudo'], 'TRIM desligado no SSD',
                        'O Windows não está avisando o SSD sobre os blocos livres.',
                        'Sem TRIM o SSD fica mais lento para gravar com o tempo e se desgasta mais. O pacote de disco liga de novo.', 'disco'))
    w = d.get('wmi') or {}
    if (w.get('cpu') or 0) > 2:
        cli = ', '.join(f'{c.get("processo")} ({c.get("consultas")})' for c in lista(w.get('clientes'))[:3])
        A.append(Achado(2, ['calor', 'bateria', 'lento', 'tudo'], 'WMI gastando CPU parado',
                        f'WmiPrvSE com {br(w.get("cpu"), 1)}% de CPU. Quem mais consulta: {cli or "não registrado"}.',
                        'Normalmente é software de fabricante (centrais de jogo, assistentes de suporte). Atualizar ou deixar em manual.', 'servicos'))
    na_bateria = bool(pf(p, 'pc.notebook') and (d.get('energia') or {}).get('na_bateria'))
    if m.get('limite') is not None and m['limite'] < 85 and not na_bateria:
        A.append(Achado(2, ['calor', 'lento', 'jogos', 'tudo'], 'Processador sendo limitado',
                        f'O Windows diz que o processador está limitado a {br(m["limite"], 0)}% do que poderia (contador "% Performance Limit")'
                        + (f', com {br(m["temperatura"], 0)} °C.' if m.get('temperatura') else '.'),
                        'Calor (poeira, pasta térmica), carregador fraco ou plano de energia. Limpe as saídas de ar.'))
    if (m.get('temperatura') or 0) >= (80 if m.get('temp_fonte') not in (None, 'zona térmica') else 90):
        A.append(Achado(2, ['calor', 'tudo'], 'Temperatura alta em repouso', f'{br(m["temperatura"], 0)} °C (lido por: {m.get("temp_fonte") or "zona térmica"}).',
                        'Limpar ventoinhas; em notebook, usar o plano "fresco" (mínimo de CPU 5% e turbo eficiente).', 'energia'))
    trocas = lista(saude.get('trocas_plano'))
    if trocas:
        A.append(Achado(1, ['calor', 'bateria', 'tudo'], 'Programa trocando o plano de energia',
                        ', '.join(f'{x.get("processo")} ({x.get("vezes")}x)' for x in trocas) + ' nos últimos 14 dias.',
                        'Centrais de fabricante forçam "Alto desempenho". Ajuste o perfil no app e use o plano de energia daqui.', 'energia'))
    if pf(p, 'pc.notebook') and saude.get('bateria_saude') and saude['bateria_saude'] < 70:
        A.append(Achado(2, ['bateria', 'tudo'], 'Bateria gasta', f'{saude["bateria_saude"]}% da capacidade original.',
                        'Abaixo de 60 a 70%, só a troca resolve. O plano "fresco" economiza o que dá.', 'energia'))
    if saude.get('falha_iminente'):
        A.append(Achado(3, ['tudo', 'lento'], 'DISCO PODE FALHAR', 'O próprio disco avisa falha iminente (SMART).',
                        'Faça backup agora e troque o disco.'))
    for s in lista(d.get('smart')):
        if (s.get('erros') or 0) > 0 or (s.get('desgaste') or 0) > 80:
            A.append(Achado(2, ['tudo'], f'Disco {s.get("disco")} com sinais de desgaste',
                            f'Erros de leitura: {s.get("erros")}, desgaste: {s.get("desgaste")}%.', 'Backup em dia e acompanhar.'))
    if (saude.get('desligamentos') or 0) >= 3:
        azuis = saude.get('telas_azuis') or 0
        A.append(Achado(2 if azuis else 1, ['tudo', 'lento'], 'Telas azuis ou desligamentos inesperados',
                        f'{saude["desligamentos"]} desligamentos sem aviso nos últimos 60 dias'
                        + (f', {azuis} com tela azul.' if azuis else ' (nenhuma tela azul: pode ser queda de energia ou botão de desligar segurado).'),
                        'Reparar o sistema e conferir drivers, fonte e temperatura.', 'reparar'))
    if (saude.get('erros_disco') or 0) > 5:
        A.append(Achado(2, ['tudo'], 'Erros de disco no registro de eventos', f'{saude["erros_disco"]} erros (não avisos) dos drivers de disco nos últimos 60 dias, no Visualizador de Eventos.', 'Verificar o disco (chkdsk).', 'reparar'))
    devs = lista(saude.get('dispositivos'))
    if devs:
        A.append(Achado(1, ['tudo'], 'Dispositivos com problema', ', '.join(f'{x.get("nome")} (código {x.get("codigo")})' for x in devs[:4]),
                        'Atualizar ou reinstalar o driver. Código 31 duplicado costuma ser resto de reinstalação.'))
    if saude.get('firmware_erro'):
        A.append(Achado(2, ['tudo'], 'Atualização de BIOS/firmware falhando',
                        'O dispositivo "System Firmware" está com erro (quase sempre por causa do BitLocker).',
                        'Atualize a BIOS pelo site do fabricante. Antes, suspenda o BitLocker você mesmo: '
                        'manage-bde -protectors -disable C: -RebootCount 3'))
    susp = lista(d.get('tarefas_suspeitas'))
    if susp:
        A.append(Achado(3 if any(x.get('curta') for x in susp) else 2, ['tudo', 'lento'], 'Tarefas agendadas suspeitas',
                        ', '.join(f'{x.get("tarefa")} → {x.get("exe")}' + (' (repete a cada poucos minutos)' if x.get('curta') else '') for x in susp[:3]),
                        'Programa rodando de AppData/Temp é padrão comum de malware. Confira cada um e faça uma verificação completa no Defender.'))
    ame = d.get('ameacas') or {}
    if ame.get('qtd'):
        A.append(Achado(2, ['tudo'], 'O Defender encontrou ameaças', f'{ame["qtd"]} nos últimos 60 dias.',
                        'Abra Segurança do Windows > Histórico de proteção e confira se foram removidas.'))
    orf = lista(d.get('servicos_orfaos')) + lista(d.get('tarefas_orfas'))
    if orf:
        A.append(Achado(1, ['tudo', 'boot'], 'Restos de programas desinstalados',
                        f'{len(orf)} serviços ou tarefas apontando para programas que não existem mais.',
                        'Desligar as tarefas e serviços órfãos.', 'servicos'))
    odp = lista(d.get('onedrive_projetos'))
    if odp:
        A.append(Achado(2, ['lento', 'disco', 'tudo'], 'Projetos de código dentro do OneDrive',
                        f'{len(odp)} pastas com node_modules sendo sincronizadas, ex.: {caminho_curto(odp[0])}.',
                        'Mover os projetos para fora do OneDrive (copie, confira e só depois apague o original).'))
    if (pf(p, 'sistema.uptime_h', 0) or 0) > 24 * 7:
        A.append(Achado(1, ['lento', 'tudo'], 'PC ligado há muitos dias', f'{br(pf(p, "sistema.uptime_h") / 24, 0)} dias sem reiniciar.',
                        'Reiniciar (não só suspender) limpa vazamentos de memória.'))
    if pf(p, 'sistema.reinicio_pendente'):
        A.append(Achado(1, ['tudo'], 'Atualização esperando reinício', 'O Windows pediu para reiniciar.', 'Reinicie quando puder.'))
    ult = saude.get('ultima_atualizacao')
    try:
        if ult and (datetime.now() - datetime.fromisoformat(ult[:19])).days > 45:
            A.append(Achado(2, ['tudo'], 'Windows sem atualizar há tempo', f'Última atualização instalada em {ult[:10]}.', 'Atualizar.', 'atualizar'))
    except ValueError:
        pass
    if not pf(p, 'memoria.pagefile_auto', True) and not pf(p, 'memoria.pagefile_config', True):
        A.append(Achado(2, ['lento', 'tudo'], 'Memória virtual desligada', 'Sem arquivo de paginação.',
                        'Ninguém recomenda desligar: programas fecham sozinhos sem ela. O pacote de disco volta para automático.', 'disco'))
    if pf(p, 'memoria.compressao') is False and ram_t < 16:
        A.append(Achado(1, ['lento', 'tudo'], 'Compressão de memória desligada', f'Com {gb(ram_t)}, ela ajuda.', 'O pacote de disco liga de novo.', 'disco'))
    if not pf(p, 'so.win11') and pf(p, 'so.build', 0):
        A.append(Achado(1, ['tudo'], 'Windows 10 sem suporte', 'O suporte comum acabou em outubro de 2025.',
                        'Atualize para o 11 se o processador for compatível; senão, o Defender e o navegador atualizados seguram por um tempo.'))
    if pf(p, 'pc.dominio'):
        A.append(Achado(0, ['tudo'], 'PC de empresa (domínio)', 'Políticas da empresa podem desfazer ou bloquear ajustes.',
                        'Use o modo seguro e combine com o TI antes de remover programas.'))
    plano = str(pf(p, 'energia.plano', '')).lower()
    if not pf(p, 'pc.notebook') and re.search(r'equilibrado|balanced|economia|power saver', plano):
        A.append(Achado(1, ['lento', 'jogos', 'tudo'], 'Desktop no plano Equilibrado', 'Plano ativo: ' + plano.split('(')[-1].rstrip(')'),
                        'Num desktop, o plano de desempenho mantém o clock alto sem custo de bateria.', 'energia'))
    if pf(p, 'pc.notebook') and re.search(r'alto desempenho|high performance|desempenho m|ultimate', plano):
        A.append(Achado(1, ['calor', 'bateria', 'tudo'], 'Notebook em plano de alto desempenho', 'Plano ativo: ' + plano.split('(')[-1].rstrip(')'),
                        'Esquenta e gasta bateria. O plano "fresco" (mínimo 5%, turbo eficiente) costuma resolver ventoinha alta.', 'energia'))
    if joga(p):
        A.append(Achado(0, ['jogos'], 'Ajustes para jogos disponíveis', 'Launchers encontrados: ' + ', '.join(lista(p.get('jogos'))),
                        'Modo de Jogo, prioridade dos jogos, Game DVR desligado e mais (cada um explicado).', 'jogos'))
    for nome in lista(p.get('oem_gamer')):
        A.append(Achado(0, ['calor', 'bateria', 'jogos'], f'{nome} instalado',
                        'Centrais de fabricante costumam forçar alto desempenho e consultar o WMI sem parar.',
                        'Use o perfil Equilibrado ou Silencioso nele no dia a dia; versões antigas pesam mais (atualize pelo site do fabricante).'))
    if 'privacidade' not in ja_aplicados():
        A.append(Achado(0, ['privacidade', 'tudo'], 'Telemetria, anúncios e IA do Windows',
                        'Ligados por padrão em toda instalação.', 'Desligar por políticas oficiais (reversível).', 'privacidade'))
    dev = any(pf(p, 'tem.' + k) for k in ('wsl', 'docker', 'visualstudio', 'ssh')) or bool(shutil.which('git'))
    if dev and pf(p, 'so.win11') and (pf(p, 'so.build', 0) or 0) >= 22621 and not pf(p, 'tem.devdrive') and (pf(p, 'disco.livre', 0) or 0) > 60:
        A.append(Achado(0, ['lento', 'tudo'], 'Projetos sem Unidade de Desenvolvimento (Dev Drive)',
                        'Há ferramentas de programação aqui e nenhum volume ReFS.',
                        'No Windows 11 dá para criar uma Unidade de Desenvolvimento, bem mais rápida para node_modules, builds e git: '
                        'Configurações > Sistema > Armazenamento > Configurações avançadas > Discos e volumes > Criar unidade de desenvolvimento. '
                        'O Katharos só orienta, porque criar mexe em partição.'))
    return A


PESO_NOTA = {3: 14, 2: 6, 1: 2, 0: 0}   # quanto cada achado tira da nota; os informativos (0) não tiram nada


def nota_pc(achados):
    pontos = 100 - sum(PESO_NOTA.get(a.impacto, 0) for a in achados)
    return max(5, min(100, pontos))


def pesa_na_nota(achados, limite=3):
    """Os achados que mais tiram ponto, para a nota se explicar: [(título, pontos)]."""
    com_peso = sorted((a for a in achados if PESO_NOTA.get(a.impacto, 0)), key=lambda a: -PESO_NOTA[a.impacto])
    return [(a.titulo, PESO_NOTA[a.impacto]) for a in com_peso[:limite]]


def ja_aplicados():
    """Os pacotes que já foram aplicados neste PC (pelos backups guardados). Vazio se não dá para saber."""
    try:
        return {nome for _, nome, _ in pacotes_aplicados_dt()}
    except Exception:
        return set()


def raiox_dados(p, m, d, achados, queixas):
    """O raio-x como dados para o relatório único (tudo o que veio do PC é limpo lá, ao gravar)."""
    saude = d.get('saude') or {}
    return {
        'nota': nota_pc(achados), 'queixas': list(queixas),
        'achados': [{'titulo': a.titulo, 'impacto': a.impacto, 'evidencia': a.evidencia, 'faz': a.faz, 'comando': a.comando}
                    for a in sorted(achados, key=lambda a: (-a.impacto, a.titulo))],
        'medidas': {k: m.get(k) for k, *_ in LINHAS_MEDIDA},
        'inicializacao': [f'{i.get("nome")} ({i.get("onde")})' for i in lista(d.get('inicializacao'))],
        'boot': [f'{b.get("tipo")}: {b.get("nome")}, {br(b.get("s"), 1)} s em média ({b.get("vezes")}x)' for b in lista(d.get('boot'))],
        'top': [[x.get('n'), f'{br(x.get("cpu"), 1)}%', f'{x.get("mb")} MB'] for x in lista(d.get('top_ram'))],
        'nao_reconhecidos': [str(x.get('n')) for x in lista(d.get('top_cpu')) + lista(d.get('top_ram')) if not quem_e(x.get('n')) and not x.get('desc')][:12],
        'hardware': {'pentes': lista(pf(p, 'ram.pentes')), 'video': lista(pf(p, 'video')), 'tela': pf(p, 'tela'), 'trim': pf(p, 'disco.trim')},
        'programas': [str(x) for x in lista(d.get('programas'))][:300],
        'bios': f'{saude.get("bios", "")} {str(saude.get("bios_data", ""))[:10]}'.strip(),
    }


def ferramenta_raiox(ctx, args):
    t = ctx.t
    t.aba('diagnóstico completo, só leitura: o que deixa este PC lento e o que fazer')
    if not WINDOWS:
        t.erro('O katharos só funciona no Windows.')
        return 1
    queixas = pergunta_queixas(t, args)
    t.titulo('medindo')
    p = perfil_pc(ctx, forca=True)
    m = mede(ctx, 'medidas em repouso')
    with Progresso(t, None, 'analisando tudo') as pr:
        s = roda_ps(t, DIAG_PS, 'raiox', minutos=8, mostra=False, pr=pr, mult=ctx.mult)
    d = s.dados
    salva_medida(m, 'raiox')
    achados = analisa(p, m, d)
    ctx.achados = achados
    nota = nota_pc(achados)

    t.titulo('este PC')
    t.chaves([
        ('modelo', f'{pf(p, "pc.fabricante", "")} {pf(p, "pc.modelo", "")}'.strip() + (' · notebook' if pf(p, 'pc.notebook') else ' · desktop')),
        ('Windows', f'{pf(p, "so.nome", "")} {pf(p, "so.versao", "")}'.replace('Microsoft ', '')),
        ('processador', texto_cpu(p)),
        ('RAM', texto_ram(p)),
        ('disco C:', texto_disco(p)),
        ('vídeo', texto_video(p)),
    ] + ([('placa-mãe', texto_placa(p))] if pf(p, 'pc.placa') else []) + [
    ])
    t.titulo('em repouso')
    mostra_medidas(t, m)
    if not eh_admin():
        t.nota('  temperatura e tempo de boot só aparecem como administrador.')
    t.titulo('nota')
    cor = 'verde' if nota >= 80 else ('amarelo' if nota >= 55 else 'vermelho')
    t.barra('saúde geral', nota, 100, t.p(f'{nota}/100', cor, True), cor)
    pesos = pesa_na_nota(achados)
    if pesos:
        t.paragrafo('O que mais tira ponto: ' + '; '.join(f'{ti} (-{pt})' for ti, pt in pesos) + '.', 2, 'apagado')
    if (pf(p, 'sistema.uptime_h', 1) or 0) < 0.2:
        t.paragrafo('O PC ligou há poucos minutos: o Windows ainda está terminando de abrir e as medidas em repouso saem piores. '
                    'Para um número justo, rode de novo daqui a 10 minutos.', 2, 'amarelo')
    tops = [x for x in lista(d.get('top_cpu')) if (x.get('cpu') or 0) >= 0.5][:5]
    if tops:
        t.titulo('quem mais gasta agora')
        t.tabela(['processo', 'CPU', 'RAM', 'o que é'],
                 [[str(x.get('n')), br(x.get('cpu'), 1) + '%', f'{x.get("mb")} MB', o_que_e(x)] for x in tops],
                 alinha='edde')

    nomes = dict(QUEIXAS)
    if 'tudo' not in queixas:
        t.titulo('o que você relatou')
        for q in queixas:
            cs = [a for a in achados if q in a.queixas and a.impacto >= 2] or [a for a in achados if q in a.queixas]
            if cs:
                t.item('●', 'amarelo', nomes.get(q, q), t.p(pl(len(cs), 'causa'), 'amarelo'))
                for a in cs[:3]:
                    t.paragrafo('· ' + a.titulo, 6, 'sub')
            else:
                t.item('○', 'apagado', nomes.get(q, q), t.p('não confirmada pelas medidas', 'apagado'))
    t.titulo('o que encontrei' if 'tudo' in queixas else 'o que mais encontrei')
    ordem = sorted(achados, key=lambda a: (-(bool(a.queixas & set(queixas))), -a.impacto))
    for a in ordem:
        icone, c = {3: ('■', 'vermelho'), 2: ('●', 'amarelo'), 1: ('·', 'azul'), 0: ('○', 'apagado')}[a.impacto]
        t.item(icone, c, a.titulo, t.p(a.comando, 'destaque') if a.comando else '')
        t.paragrafo(a.evidencia, 6, 'sub')
        if a.faz:
            t.paragrafo(a.faz, 6, 'apagado')
    rel_secao('raiox', raiox_dados(p, m, d, achados, queixas))
    comandos = []
    for a in ordem:
        if a.comando and a.comando not in comandos:
            comandos.append(a.comando)
    t.titulo('resumo', caixa=True)
    t.chaves([('nota', t.p(f'{nota}/100', cor, True)), ('achados', str(sum(a.impacto > 0 for a in achados))),
              ('alto impacto', t.p(str(sum(a.impacto == 3 for a in achados)), 'vermelho')),
              ('sugestão', ' · '.join(comandos[:6]) or 'nada')])
    t.relatorio(rel_md_path(), 'relatório único', recuo=2)
    if comandos and t.interativo and not args.teste:
        t.fecha_caixa()
        t.escreve()
        t.paragrafo('Quer abrir agora as telas sugeridas, uma de cada vez? Em cada uma você vê tudo explicado '
                    'e escolhe o que aplicar. s = sim, Enter = não', 2, 'apagado')
        if t.pergunta('abrir sugestões').strip().lower() in ('s', 'sim'):
            ctx.proximos = comandos
    return 0
