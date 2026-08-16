# Simple complete email cleanup script
param([switch]$DryRun = $false)

Write-Host "Complete Email Cleanup Script" -ForegroundColor Red
Write-Host "=============================" -ForegroundColor Red

$folders = @("received_emails", "sent_attachments", "temp_attachments", "frontend_queue")
$allFiles = @()
$totalSize = 0

Write-Host "Analyzing folders..." -ForegroundColor Cyan
foreach ($folder in $folders) {
    if (Test-Path $folder) {
        $files = Get-ChildItem $folder -Recurse -File -ErrorAction SilentlyContinue
        if ($files) {
            $allFiles += $files
            $folderSize = ($files | Measure-Object -Property Length -Sum).Sum
            $totalSize += $folderSize
            Write-Host "  $folder : $($files.Count) files ($([math]::Round($folderSize/1MB, 2)) MB)" -ForegroundColor Gray
        }
    }
}

Write-Host ""
Write-Host "Total: $($allFiles.Count) files, $([math]::Round($totalSize/1MB, 2)) MB" -ForegroundColor White
Write-Host ""

if ($allFiles.Count -eq 0) {
    Write-Host "No files to clean" -ForegroundColor Green
    exit 0
}

# Show file types
Write-Host "File types:" -ForegroundColor White
$allFiles | Group-Object Extension | Sort-Object Count -Descending | ForEach-Object {
    $ext = if($_.Name) { $_.Name } else { "(no ext)" }
    $size = ($_.Group | Measure-Object -Property Length -Sum).Sum
    Write-Host "  $ext : $($_.Count) files ($([math]::Round($size/1MB, 2)) MB)" -ForegroundColor Gray
}
Write-Host ""

if ($DryRun) {
    Write-Host "PREVIEW MODE - Would delete all files" -ForegroundColor Yellow
    Write-Host "Space to be freed: $([math]::Round($totalSize/1MB, 2)) MB" -ForegroundColor Cyan
    Write-Host "To actually clean: .\clean-all-simple.ps1" -ForegroundColor Cyan
} else {
    Write-Host "WARNING: Will delete ALL $($allFiles.Count) email files!" -ForegroundColor Red
    Write-Host "Space to be freed: $([math]::Round($totalSize/1MB, 2)) MB" -ForegroundColor Yellow
    Write-Host ""
    
    $confirm = Read-Host "Type 'DELETE ALL' to confirm"
    
    if ($confirm -eq 'DELETE ALL') {
        Write-Host ""
        Write-Host "Deleting files..." -ForegroundColor Red
        
        $deleted = 0
        $deletedSize = 0
        
        foreach ($file in $allFiles) {
            try {
                $size = $file.Length
                Remove-Item $file.FullName -Force
                $deleted++
                $deletedSize += $size
                
                if ($deleted % 100 -eq 0) {
                    Write-Host "  Deleted $deleted/$($allFiles.Count) files..." -ForegroundColor Gray
                }
            }
            catch {
                Write-Host "  Failed: $($file.FullName)" -ForegroundColor Red
            }
        }
        
        Write-Host ""
        Write-Host "Cleanup completed!" -ForegroundColor Green
        Write-Host "  Deleted: $deleted files" -ForegroundColor Green
        Write-Host "  Freed: $([math]::Round($deletedSize/1MB, 2)) MB" -ForegroundColor Green
        
        # Clean empty directories but keep main folders
        Write-Host ""
        Write-Host "Cleaning empty directories..." -ForegroundColor Cyan
        foreach ($folder in $folders) {
            if (Test-Path $folder) {
                Get-ChildItem $folder -Recurse -Directory | Sort-Object FullName -Descending | ForEach-Object {
                    if ((Get-ChildItem $_.FullName -Recurse -File).Count -eq 0) {
                        Remove-Item $_.FullName -Recurse -Force -ErrorAction SilentlyContinue
                    }
                }
                
                # Create .gitkeep to preserve folder structure
                $gitkeep = Join-Path $folder ".gitkeep"
                "# Preserve directory structure" | Out-File -FilePath $gitkeep -Encoding UTF8 -ErrorAction SilentlyContinue
            }
        }
        
        Write-Host "Directory structure preserved with .gitkeep files" -ForegroundColor Green
        
    } else {
        Write-Host "Operation cancelled" -ForegroundColor Yellow
    }
}

Write-Host ""
Write-Host "Script completed" -ForegroundColor Green
