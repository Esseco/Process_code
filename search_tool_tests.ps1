$ErrorActionPreference = 'Stop'
$databaseRoot = Get-ChildItem -LiteralPath 'E:\' -Directory | Where-Object { $_.Name -like '1-XRD*' } | ForEach-Object { Join-Path $_.FullName 'Exp_inorganic-all' } | Where-Object { Test-Path $_ } | Select-Object -First 1
$server = Join-Path $databaseRoot 'search_tool_server.ps1'
. $server -TestMode

function Assert-Equal($actual, $expected, $name) {
    if ($actual -ne $expected) { throw "$name failed: '$actual' != '$expected'" }
}

$els = @(Parse-FormulaElements 'Na (Co O2)')
Assert-Equal (($els | Sort-Object) -join ',') 'Co,Na,O' 'formula parsing'
Assert-Equal (Get-OutputFolderName -Composition 'Na-CO-O' -SpaceGroup '62' -Date '20261026') '20261026_Na-CO-O_spacegroup62' 'folder naming'
$info = Get-SpaceGroupInfoFromLines @('_space_group_IT_number 62', "_space_group_name_H-M_alt 'P n m a'")
Assert-Equal $info.Number 62 'space-group number'
Assert-Equal $info.Name 'P n m a' 'space-group name'
$rows = @(
    [pscustomobject]@{ CollectionCode='1'; StructuredFormula='Na Co O'; HMS='P n m a' },
    [pscustomobject]@{ CollectionCode='2'; StructuredFormula='Na Co O F'; HMS='P 1' }
)
Assert-Equal (@(Filter-IndexRows -Rows $rows -Elements @('Na','Co','O') -Mode exact).Count) 1 'exact filtering'
Assert-Equal (@(Filter-IndexRows -Rows $rows -Elements @('Na','Co','O') -Mode contains).Count) 2 'contains filtering'
$request = Convert-RequestJsonToHashtable '{"composition":"Na-Co-O","spaceGroup":"194"}'
Assert-Equal $request.composition 'Na-Co-O' 'request JSON composition'
Assert-Equal $request.spaceGroup '194' 'request JSON space group'
$fixture = Join-Path ([System.IO.Path]::GetTempPath()) ('search_index_' + [guid]::NewGuid().ToString('N') + '.txt')
try {
    [System.IO.File]::WriteAllText($fixture, "CollectionCode`tHMS`tStructuredFormula`tStructureType`tTitle`tAuthors`tReference`tQuality`n10`tP 1`tNa Co O`t`t`t`t`t10`n")
    $loaded = @(Read-IndexFileFast $fixture)
    Assert-Equal $loaded.Count 1 'fast index row count'
    Assert-Equal $loaded[0].CollectionCode '10' 'fast index collection code'
    Assert-Equal $loaded[0].StructuredFormula 'Na Co O' 'fast index formula'
} finally {
    if (Test-Path $fixture) { Remove-Item $fixture -Force }
}
$cacheFixture = Join-Path ([System.IO.Path]::GetTempPath()) ('search_cache_' + [guid]::NewGuid().ToString('N') + '.bin')
try {
    $cacheRows = @([pscustomobject]@{ CollectionCode='10'; HMS='P 1'; StructuredFormula='Na Co O'; ElementSet='Na|Co|O' })
    Write-IndexCache -Rows $cacheRows -Path $cacheFixture
    $cacheLoaded = @(Read-IndexCache -Path $cacheFixture)
    Assert-Equal $cacheLoaded.Count 1 'cache row count'
    Assert-Equal $cacheLoaded[0].ElementSet 'Na|Co|O' 'cache element set'
} finally {
    if (Test-Path $cacheFixture) { Remove-Item $cacheFixture -Force }
}
Assert-Equal (@(Get-SpaceGroupNumberCatalog).Count) 230 'space-group number catalog'
'PASS'
