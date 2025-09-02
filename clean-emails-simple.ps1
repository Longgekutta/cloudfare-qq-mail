# Simple email cleanup script
param(
    [int]$DaysToKeep = 30,
    [switch]$DryRun = $false
)

Write-Host "Email Cleanup Script" -ForegroundColor Green
Write-Host "===================" -ForegroundColor Green

$EmailFolder = "received_emails"
$CutoffDate = (Get-Date).AddDays(-$DaysToKeep)

Write-Host "Target folder: $EmailFolder" -ForegroundColor Yellow
Write-Host "Keep files after: $($CutoffDate.ToString('yyyy-MM-dd HH:mm:ss'))" -ForegroundColor Yellow
Write-Host "Mode: $(if($DryRun) {'Preview (no deletion)'} else {'Actual cleanup'})" -ForegroundColor Yellow
Write-Host ""

if (-not (Test-Path $EmailFolder)) {
    Write-Host "Error: Email folder not found: $EmailFolder" -ForegroundColor Red
    exit 1
}

# Get all files
Write-Host "Analyzing files..." -ForegroundColor Cyan
$AllFiles = Get-ChildItem $EmailFolder -Recurse -File
$TotalFiles = $AllFiles.Count
$TotalSize = ($AllFiles | Measure-Object -Property Length -Sum).Sum

Write-Host "Current status:" -ForegroundColor White
Write-Host "  Total files: $TotalFiles" -ForegroundColor White
Write-Host "  Total size: $([math]::Round($TotalSize/1MB, 2)) MB" -ForegroundColor White
Write-Host ""

# Find files to delete
$FilesToDelete = $AllFiles | Where-Object { $_.LastWriteTime -lt $CutoffDate }
$FilesToKeep = $AllFiles | Where-Object { $_.LastWriteTime -ge $CutoffDate }

$DeleteCount = $FilesToDelete.Count
$DeleteSize = ($FilesToDelete | Measure-Object -Property Length -Sum).Sum
$KeepCount = $FilesToKeep.Count

Write-Host "Cleanup statistics:" -ForegroundColor Yellow
Write-Host "  Will delete: $DeleteCount files ($([math]::Round($DeleteSize/1MB, 2)) MB)" -ForegroundColor Red
Write-Host "  Will keep: $KeepCount files" -ForegroundColor Green
Write-Host "  Space saved: $([math]::Round($DeleteSize/1MB, 2)) MB" -ForegroundColor Cyan
Write-Host ""

if ($DeleteCount -eq 0) {
    Write-Host "No files to clean" -ForegroundColor Green
    exit 0
}

# Show file types
Write-Host "File types to delete:" -ForegroundColor White
$FilesToDelete | Group-Object Extension | Sort-Object Count -Descending | ForEach-Object {
    $ext = if($_.Name) { $_.Name } else { "(no extension)" }
    $size = ($_.Group | Measure-Object -Property Length -Sum).Sum
    Write-Host "  $ext : $($_.Count) files ($([math]::Round($size/1MB, 2)) MB)" -ForegroundColor Gray
}
Write-Host ""

if ($DryRun) {
    Write-Host "PREVIEW MODE - Files that would be deleted (first 20):" -ForegroundColor Yellow
    $FilesToDelete | Select-Object -First 20 | ForEach-Object {
        Write-Host "  $($_.FullName) ($([math]::Round($_.Length/1KB, 2)) KB)" -ForegroundColor Gray
    }
    if ($DeleteCount -gt 20) {
        Write-Host "  ... and $($DeleteCount - 20) more files" -ForegroundColor Gray
    }
    Write-Host ""
    Write-Host "To actually clean, run: .\clean-emails-simple.ps1 -DaysToKeep $DaysToKeep" -ForegroundColor Cyan
} else {
    Write-Host "WARNING: About to delete $DeleteCount files, freeing $([math]::Round($DeleteSize/1MB, 2)) MB" -ForegroundColor Yellow
    $confirm = Read-Host "Continue? (y/N)"
    
    if ($confirm -eq 'y' -or $confirm -eq 'Y') {
        Write-Host ""
        Write-Host "Starting cleanup..." -ForegroundColor Red
        
        $DeletedCount = 0
        $DeletedSize = 0
        
        foreach ($file in $FilesToDelete) {
            try {
                $fileSize = $file.Length
                Remove-Item $file.FullName -Force
                $DeletedCount++
                $DeletedSize += $fileSize
                
                if ($DeletedCount % 100 -eq 0) {
                    Write-Host "  Deleted $DeletedCount/$DeleteCount files..." -ForegroundColor Gray
                }
            }
            catch {
                Write-Host "  Failed to delete: $($file.FullName) - $($_.Exception.Message)" -ForegroundColor Red
            }
        }
        
        Write-Host ""
        Write-Host "Cleanup completed!" -ForegroundColor Green
        Write-Host "  Deleted $DeletedCount files" -ForegroundColor Green
        Write-Host "  Freed $([math]::Round($DeletedSize/1MB, 2)) MB space" -ForegroundColor Green
        
        # Clean empty folders
        Write-Host ""
        Write-Host "Cleaning empty folders..." -ForegroundColor Cyan
        Get-ChildItem $EmailFolder -Recurse -Directory | Where-Object { 
            (Get-ChildItem $_.FullName -Recurse -File).Count -eq 0 
        } | Remove-Item -Recurse -Force
        
        Write-Host "Empty folder cleanup completed" -ForegroundColor Green
    } else {
        Write-Host "Operation cancelled by user" -ForegroundColor Yellow
    }
}

Write-Host ""
Write-Host "Script completed" -ForegroundColor Green
