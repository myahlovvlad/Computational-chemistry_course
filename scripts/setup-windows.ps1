param([ValidateSet('base','chem','quantum-core')][string]$Profile = 'base')
$ErrorActionPreference = 'Stop'
$courseRoot = Split-Path -Parent $PSScriptRoot
$env:PYTHONUTF8 = '1'
$env:PYTHONNOUSERSITE = '1'
$uvCommand = Get-Command uv -ErrorAction SilentlyContinue
if ($uvCommand) {
    $courseUv = $uvCommand.Source
} else {
    # Bootstrap изолирован от глобальных пакетов пользователя.
    $bootstrap = Join-Path $PSScriptRoot 'environment/.uv-bootstrap'
    $bootstrapPython = Join-Path $bootstrap 'Scripts/python.exe'
    if (!(Test-Path -LiteralPath $bootstrapPython)) {
        & python -m venv $bootstrap
        if ($LASTEXITCODE -ne 0) { throw 'Нужен установленный Python 3.12 x64.' }
    }
    & $bootstrapPython -m pip install uv==0.13.8
    if ($LASTEXITCODE -ne 0) { throw 'Не удалось установить uv в bootstrap.' }
    $courseUv = Join-Path $bootstrap 'Scripts/uv.exe'
}
& python (Join-Path $PSScriptRoot 'setup_environment.py') --profile $Profile --uv $courseUv
if ($LASTEXITCODE -ne 0) { throw 'Установка профиля не завершена; прочитайте фактическую ошибку выше.' }
Write-Output "Выберите в Notebook ядро: Курс химии v2 · $Profile · uv"
