# 完全清理所有邮件文件脚本
# 清理所有邮件但保留目录结构以确保系统功能正常

param(
    [switch]$DryRun = $false
)

Write-Host "Complete Email Cleanup Script" -ForegroundColor Red
Write-Host "=============================" -ForegroundColor Red
Write-Host "WARNING: This will delete ALL email files!" -ForegroundColor Yellow
Write-Host ""

$EmailFolder = "received_emails"
$SentAttachmentsFolder = "sent_attachments"
$TempAttachmentsFolder = "temp_attachments"
$FrontendQueueFolder = "frontend_queue"

Write-Host "Target folders:" -ForegroundColor Yellow
Write-Host "  - $EmailFolder" -ForegroundColor White
Write-Host "  - $SentAttachmentsFolder" -ForegroundColor White
Write-Host "  - $TempAttachmentsFolder" -ForegroundColor White
Write-Host "  - $FrontendQueueFolder" -ForegroundColor White
Write-Host "Mode: $(if($DryRun) {'Preview (no deletion)'} else {'Complete cleanup'})" -ForegroundColor Yellow
Write-Host ""

# 检查文件夹是否存在
$foldersToClean = @()
if (Test-Path $EmailFolder) { $foldersToClean += $EmailFolder }
if (Test-Path $SentAttachmentsFolder) { $foldersToClean += $SentAttachmentsFolder }
if (Test-Path $TempAttachmentsFolder) { $foldersToClean += $TempAttachmentsFolder }
if (Test-Path $FrontendQueueFolder) { $foldersToClean += $FrontendQueueFolder }

if ($foldersToClean.Count -eq 0) {
    Write-Host "No email folders found to clean" -ForegroundColor Green
    exit 0
}

# 分析所有文件
Write-Host "Analyzing all email files..." -ForegroundColor Cyan
$AllFiles = @()
$TotalSize = 0

foreach ($folder in $foldersToClean) {
    $folderFiles = Get-ChildItem $folder -Recurse -File -ErrorAction SilentlyContinue
    if ($folderFiles) {
        $AllFiles += $folderFiles
        $folderSize = ($folderFiles | Measure-Object -Property Length -Sum).Sum
        $TotalSize += $folderSize
        Write-Host "  $folder : $($folderFiles.Count) files ($([math]::Round($folderSize/1MB, 2)) MB)" -ForegroundColor Gray
    }
}

$TotalFiles = $AllFiles.Count

Write-Host ""
Write-Host "Total analysis:" -ForegroundColor White
Write-Host "  Total files: $TotalFiles" -ForegroundColor White
Write-Host "  Total size: $([math]::Round($TotalSize/1MB, 2)) MB" -ForegroundColor White
Write-Host ""

if ($TotalFiles -eq 0) {
    Write-Host "No files to clean" -ForegroundColor Green
    exit 0
}

# 按文件类型分组显示
Write-Host "File types to delete:" -ForegroundColor White
$AllFiles | Group-Object Extension | Sort-Object Count -Descending | ForEach-Object {
    $ext = if($_.Name) { $_.Name } else { "(no extension)" }
    $size = ($_.Group | Measure-Object -Property Length -Sum).Sum
    Write-Host "  $ext : $($_.Count) files ($([math]::Round($size/1MB, 2)) MB)" -ForegroundColor Gray
}
Write-Host ""

# 显示最大的文件
Write-Host "Largest files (top 10):" -ForegroundColor White
$AllFiles | Sort-Object Length -Descending | Select-Object -First 10 | ForEach-Object {
    Write-Host "  $($_.Name) - $([math]::Round($_.Length/1MB, 2)) MB" -ForegroundColor Gray
}
Write-Host ""

if ($DryRun) {
    Write-Host "PREVIEW MODE - All files would be deleted" -ForegroundColor Yellow
    Write-Host "Total space that would be freed: $([math]::Round($TotalSize/1MB, 2)) MB" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "To actually clean, run: .\clean-all-emails.ps1" -ForegroundColor Cyan
} else {
    Write-Host "DANGER: About to delete ALL $TotalFiles email files!" -ForegroundColor Red
    Write-Host "This will free $([math]::Round($TotalSize/1MB, 2)) MB of space" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "This action cannot be undone!" -ForegroundColor Red
    Write-Host ""
    
    $confirm1 = Read-Host "Type 'DELETE ALL' to confirm (case sensitive)"
    
    if ($confirm1 -eq 'DELETE ALL') {
        $confirm2 = Read-Host "Are you absolutely sure? Type 'YES' to proceed"
        
        if ($confirm2 -eq 'YES') {
            Write-Host ""
            Write-Host "Starting complete cleanup..." -ForegroundColor Red
            
            $DeletedCount = 0
            $DeletedSize = 0
            $FailedCount = 0
            
            foreach ($file in $AllFiles) {
                try {
                    $fileSize = $file.Length
                    Remove-Item $file.FullName -Force
                    $DeletedCount++
                    $DeletedSize += $fileSize
                    
                    if ($DeletedCount % 100 -eq 0) {
                        Write-Host "  Deleted $DeletedCount/$TotalFiles files..." -ForegroundColor Gray
                    }
                }
                catch {
                    $FailedCount++
                    Write-Host "  Failed to delete: $($file.FullName) - $($_.Exception.Message)" -ForegroundColor Red
                }
            }
            
            Write-Host ""
            Write-Host "File deletion completed!" -ForegroundColor Green
            Write-Host "  Successfully deleted: $DeletedCount files" -ForegroundColor Green
            Write-Host "  Failed to delete: $FailedCount files" -ForegroundColor Red
            Write-Host "  Space freed: $([math]::Round($DeletedSize/1MB, 2)) MB" -ForegroundColor Green
            
            # 清理空文件夹但保留主目录
            Write-Host ""
            Write-Host "Cleaning empty subdirectories..." -ForegroundColor Cyan
            
            foreach ($folder in $foldersToClean) {
                if (Test-Path $folder) {
                    # 删除空的子目录，但保留主目录
                    Get-ChildItem $folder -Recurse -Directory | Sort-Object FullName -Descending | ForEach-Object {
                        if ((Get-ChildItem $_.FullName -Recurse -File).Count -eq 0) {
                            try {
                                Remove-Item $_.FullName -Recurse -Force
                                Write-Host "  Removed empty directory: $($_.Name)" -ForegroundColor Gray
                            }
                            catch {
                                Write-Host "  Failed to remove directory: $($_.FullName)" -ForegroundColor Red
                            }
                        }
                    }
                }
            }
            
            Write-Host ""
            Write-Host "Creating .gitkeep files to preserve directory structure..." -ForegroundColor Cyan
            
            # 在主目录中创建.gitkeep文件以保持目录结构
            foreach ($folder in $foldersToClean) {
                if (Test-Path $folder) {
                    $gitkeepPath = Join-Path $folder ".gitkeep"
                    try {
                        "# This file keeps the directory in git" | Out-File -FilePath $gitkeepPath -Encoding UTF8
                        Write-Host "  Created .gitkeep in $folder" -ForegroundColor Gray
                    }
                    catch {
                        Write-Host "  Failed to create .gitkeep in $folder" -ForegroundColor Red
                    }
                }
            }
            
            Write-Host ""
            Write-Host "Complete cleanup finished!" -ForegroundColor Green
            Write-Host "All email files have been deleted while preserving directory structure" -ForegroundColor Green
            Write-Host "System functionality should remain intact" -ForegroundColor Green

        } else {
            Write-Host "Second confirmation failed. Operation cancelled." -ForegroundColor Yellow
        }
    } else {
        Write-Host "First confirmation failed. Operation cancelled." -ForegroundColor Yellow
    }
}

Write-Host ""
Write-Host "Script completed" -ForegroundColor Green
